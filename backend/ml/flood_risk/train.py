"""Train and evaluate the V1 XGBoost flood-risk model.

The training set is filtered to rows with complete core rainfall features.
Evaluation is chronological: older observations are used for training,
a later slice tunes the decision threshold, and the newest slice is held out
as the untouched final test set.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

from ml.flood_risk.dataset import TARGET_COLUMN

LOGGER = logging.getLogger(__name__)

DEFAULT_DATASET = Path("apps/risk/data/processed/training_v1.parquet")
DEFAULT_MODEL = Path("models/flood_risk_v1.json")
DEFAULT_METADATA = Path("models/flood_risk_v1.metadata.json")

FEATURE_COLUMNS = [
    "rainfall_24h", "rainfall_48h", "rainfall_72h", "rainfall_7d", "rainfall_30d",
    "water_level_m", "water_level_delta_1h", "water_level_pct_change_1h",
    "water_level_lag_1h", "water_level_lag_3h", "water_level_lag_6h",
    "water_level_lag_12h", "water_level_lag_24h",
    "water_level_rolling_mean_6h", "water_level_rolling_max_6h", "water_level_rolling_std_6h",
    "water_level_rolling_mean_24h", "water_level_rolling_max_24h", "water_level_rolling_std_24h",
    "discharge_cumecs", "discharge_delta_1h", "discharge_pct_change_1h",
    "discharge_lag_1h", "discharge_lag_3h", "discharge_lag_6h", "discharge_lag_12h", "discharge_lag_24h",
    "discharge_rolling_mean_6h", "discharge_rolling_max_6h", "discharge_rolling_std_6h",
    "discharge_rolling_mean_24h", "discharge_rolling_max_24h", "discharge_rolling_std_24h",
    "flood_count_1y", "flood_count_3y", "flood_count_5y",
    "days_since_last_flood", "historical_max_severity", "historical_mean_severity",
    "historical_glof_count", "month", "day_of_year", "is_monsoon",
    "glacier_area_km2", "glacier_area_change_1y_km2", "glacier_area_change_1y_pct",
    "glacier_cumulative_area_change_km2", "glacier_cumulative_area_change_pct",
    "glacier_elevation_m", "glacier_melting_rate_min_km_per_year",
    "glacier_melting_rate_max_km_per_year",
]

CORE_RAINFALL = ["rainfall_24h", "rainfall_48h", "rainfall_72h"]


def load_training_rows(path: Path) -> pd.DataFrame:
    LOGGER.info("Reading training data: %s", path)
    df = pd.read_parquet(path)
    missing = [c for c in ["station_id", "observed_at", TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Training dataset missing required columns: {missing}")
    usable_features = [c for c in FEATURE_COLUMNS if c in df.columns]
    if not usable_features:
        raise ValueError("No supported feature columns found in training dataset")
    df["observed_at"] = pd.to_datetime(df["observed_at"], errors="coerce")
    df = df.dropna(subset=["station_id", "observed_at", TARGET_COLUMN])
    df = df.loc[df[CORE_RAINFALL].notna().all(axis=1)].copy()
    for column in usable_features:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype("int8")
    return df.sort_values("observed_at", kind="stable").reset_index(drop=True)


def chronological_split(df: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_fraction < 0.5:
        raise ValueError("test_fraction must be between 0 and 0.5")
    cutoff = int(len(df) * (1.0 - test_fraction))
    cutoff = max(1, min(cutoff, len(df) - 1))
    train = df.iloc[:cutoff].copy()
    test = df.iloc[cutoff:].copy()
    return train, test


def evaluate(model: XGBClassifier, x_test: pd.DataFrame, y_test: pd.Series, threshold: float) -> dict[str, object]:
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= threshold).astype(np.int8)
    tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()
    metrics: dict[str, object] = {
        "threshold": float(threshold),
        "roc_auc": float(roc_auc_score(y_test, probabilities)) if y_test.nunique() > 1 else None,
        "pr_auc": float(average_precision_score(y_test, probabilities)) if y_test.sum() else None,
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "positive_rate": float(y_test.mean()),
    }
    return metrics


def evaluate_event_level(
    evaluation: pd.DataFrame,
    threshold: float,
    event_gap_hours: float = 72.0,
) -> dict[str, object]:
    """Evaluate flood detection by event rather than by 15-minute row.

    A flood-labelled window is one event per station until there is a gap
    longer than the target horizon. This prevents a single flood episode from
    being counted hundreds of times simply because the source is sampled
    every 15 minutes. Lead time is measured to the end of the labelled
    positive window because the dataset does not carry a separate event-onset
    timestamp.
    """
    required = {"station_id", "observed_at", TARGET_COLUMN, "probability"}
    missing = sorted(required.difference(evaluation.columns))
    if missing:
        raise ValueError(f"Event evaluation missing required columns: {missing}")
    if event_gap_hours <= 0:
        raise ValueError("event_gap_hours must be greater than 0")

    df = evaluation[["station_id", "observed_at", TARGET_COLUMN, "probability"]].copy()
    df["observed_at"] = pd.to_datetime(df["observed_at"], errors="coerce")
    df["probability"] = pd.to_numeric(df["probability"], errors="coerce")
    df = df.dropna(subset=["station_id", "observed_at", TARGET_COLUMN, "probability"])
    df = df.sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)
    df["alert"] = df["probability"] >= threshold

    positive = df.loc[df[TARGET_COLUMN].eq(1)].copy()
    if positive.empty:
        event_count = 0
        detected_event_count = 0
        lead_times: list[float] = []
    else:
        gaps = positive.groupby("station_id")["observed_at"].diff()
        event_break = gaps.isna() | (gaps > pd.Timedelta(hours=float(event_gap_hours)))
        positive["event_number"] = event_break.groupby(positive["station_id"]).cumsum()
        grouped = positive.groupby(["station_id", "event_number"], sort=False)
        event_count = int(grouped.ngroups)
        detected_event_count = 0
        lead_times = []
        for _, event in grouped:
            alerts = event.loc[event["alert"]]
            if alerts.empty:
                continue
            detected_event_count += 1
            first_alert = alerts["observed_at"].min()
            window_end = event["observed_at"].max()
            lead_times.append(max(0.0, (window_end - first_alert).total_seconds() / 3600.0))

    false_alerts = df.loc[df[TARGET_COLUMN].eq(0) & df["alert"]].copy()
    false_alarm_rows = int(len(false_alerts))
    if false_alerts.empty:
        false_alarm_station_days = 0
    else:
        false_alerts["day"] = false_alerts["observed_at"].dt.floor("D")
        false_alarm_station_days = int(false_alerts[["station_id", "day"]].drop_duplicates().shape[0])

    df["day"] = df["observed_at"].dt.floor("D")
    station_days = int(df[["station_id", "day"]].drop_duplicates().shape[0])
    return {
        "event_gap_hours": float(event_gap_hours),
        "event_count": event_count,
        "detected_event_count": detected_event_count,
        "event_recall": float(detected_event_count / event_count) if event_count else None,
        "mean_lead_time_to_window_end_hours": float(np.mean(lead_times)) if lead_times else None,
        "median_lead_time_to_window_end_hours": float(np.median(lead_times)) if lead_times else None,
        "false_alarm_rows": false_alarm_rows,
        "false_alarm_station_days": false_alarm_station_days,
        "evaluated_station_days": station_days,
        "false_alarms_per_station_day": float(false_alarm_rows / station_days) if station_days else None,
    }


def _threshold_candidates(probabilities: np.ndarray) -> np.ndarray:
    finite = probabilities[np.isfinite(probabilities)]
    if finite.size == 0:
        raise ValueError("Validation predictions contain no finite probabilities")
    lower = max(float(np.min(finite)) * 0.5, 1e-8)
    upper = min(max(float(np.max(finite)) * 1.05, 0.01), 1.0)
    return np.unique(
        np.clip(
            np.concatenate(
                [
                    np.logspace(np.log10(lower), np.log10(upper), 300),
                    np.unique(finite),
                    np.array([0.01, 0.5, 0.99]),
                ]
            ),
            1e-8,
            1.0,
        )
    )


def tune_threshold(model: XGBClassifier, validation: pd.DataFrame, feature_columns: list[str]) -> float:
    """Select an F1 threshold, including the tiny probabilities common in rare-event models."""
    probabilities = model.predict_proba(validation[feature_columns])[:, 1]
    y_validation = validation[TARGET_COLUMN]

    candidates = _threshold_candidates(probabilities)
    best_threshold = 0.5
    best_f1 = -1.0
    for candidate in candidates:
        predictions = (probabilities >= candidate).astype(np.int8)
        score = f1_score(y_validation, predictions, zero_division=0)
        if score > best_f1:
            best_f1 = float(score)
            best_threshold = float(candidate)

    LOGGER.info("Validation threshold tuning: threshold=%.8g f1=%.4f", best_threshold, best_f1)
    return best_threshold


def tune_threshold_event_aware(
    model: XGBClassifier,
    validation: pd.DataFrame,
    feature_columns: list[str],
    target_event_recall: float = 0.8,
    event_gap_hours: float = 72.0,
) -> float:
    """Choose the highest threshold that still reaches the target event recall.

    Candidate thresholds are the maximum model score within each positive
    event. Therefore, among thresholds meeting the recall target, the chosen
    threshold is as high as possible, which minimizes false alarms without
    sacrificing the requested event-detection rate. The validation set alone
    determines the threshold; the final test set is never used for tuning.
    """
    if not 0 < target_event_recall <= 1:
        raise ValueError("target_event_recall must be in (0, 1]")
    if event_gap_hours <= 0:
        raise ValueError("event_gap_hours must be greater than 0")

    probabilities = model.predict_proba(validation[feature_columns])[:, 1]
    evaluation = validation[["station_id", "observed_at", TARGET_COLUMN]].copy()
    evaluation["probability"] = probabilities
    positive = evaluation.loc[evaluation[TARGET_COLUMN].eq(1)].copy()
    if positive.empty:
        raise ValueError("Validation split contains no positive flood events")

    positive = positive.sort_values(["station_id", "observed_at"], kind="stable")
    gaps = positive.groupby("station_id")["observed_at"].diff()
    event_break = gaps.isna() | (gaps > pd.Timedelta(hours=float(event_gap_hours)))
    positive["event_number"] = event_break.groupby(positive["station_id"]).cumsum()
    event_max_scores = positive.groupby(["station_id", "event_number"], sort=False)["probability"].max()
    event_count = int(len(event_max_scores))
    required_events = max(1, int(math.ceil(target_event_recall * event_count)))

    ranked = np.sort(event_max_scores.to_numpy(dtype=float))[::-1]
    threshold = float(ranked[required_events - 1])
    event_metrics = evaluate_event_level(evaluation, threshold, event_gap_hours)
    LOGGER.info(
        "Event-aware threshold tuning: target_event_recall=%.3f threshold=%.8g event_recall=%.4f false_alarm_station_days=%d false_alarms_per_station_day=%.4f",
        target_event_recall,
        threshold,
        event_metrics["event_recall"],
        event_metrics["false_alarm_station_days"],
        event_metrics["false_alarms_per_station_day"],
    )
    return threshold


def train_model(train: pd.DataFrame, validation: pd.DataFrame, feature_columns: list[str], weight_multiplier: float = 1.0) -> tuple[XGBClassifier, float]:
    x_train = train[feature_columns]
    y_train = train[TARGET_COLUMN]

    positives = int(y_train.sum())
    negatives = int(len(y_train) - positives)
    if positives == 0:
        raise ValueError("Training split contains no positive flood examples")
    if weight_multiplier <= 0:
        raise ValueError("weight_multiplier must be greater than 0")

    base_scale_pos_weight = negatives / positives
    scale_pos_weight = base_scale_pos_weight * weight_multiplier
    LOGGER.info(
        "Train rows=%d positives=%d negatives=%d positive_rate=%.6f scale_pos_weight=%.4f (base=%.4f multiplier=%.3f)",
        len(train), positives, negatives, positives / len(train), scale_pos_weight, base_scale_pos_weight, weight_multiplier,
    )

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="aucpr",
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=scale_pos_weight,
        max_delta_step=1,
        tree_method="hist",
        n_jobs=max(1, min(4, os.cpu_count() or 1)),
        random_state=42,
    )
    model.fit(x_train, y_train, eval_set=[(validation[feature_columns], validation[TARGET_COLUMN])], verbose=False)
    return model, float(scale_pos_weight)


def train(
    dataset_path: Path,
    model_path: Path,
    metadata_path: Path,
    test_fraction: float,
    threshold: float,
    weight_multiplier: float,
    target_event_recall: float = 0.8,
) -> dict[str, object]:
    df = load_training_rows(dataset_path)
    if df.empty:
        raise ValueError("No usable training rows after rainfall-complete filtering")
    train_val_df, test_df = chronological_split(df, test_fraction)
    train_df, validation_df = chronological_split(train_val_df, test_fraction=0.25)
    feature_columns = [c for c in FEATURE_COLUMNS if c in df.columns and df[c].notna().any()]
    if not feature_columns:
        raise ValueError("No non-empty feature columns available")

    LOGGER.info("Rows: total=%d train=%d validation=%d test=%d features=%d", len(df), len(train_df), len(validation_df), len(test_df), len(feature_columns))
    LOGGER.info("Date split: train=%s -> %s, validation=%s -> %s, test=%s -> %s", train_df.observed_at.min(), train_df.observed_at.max(), validation_df.observed_at.min(), validation_df.observed_at.max(), test_df.observed_at.min(), test_df.observed_at.max())

    model, scale_pos_weight = train_model(train_df, validation_df, feature_columns, weight_multiplier)
    if threshold == 0.5:
        tuned_threshold = tune_threshold_event_aware(model, validation_df, feature_columns, target_event_recall)
        threshold_source = "validation_event_recall"
    else:
        tuned_threshold = threshold
        threshold_source = "cli_override"
        LOGGER.info("Validation threshold tuning skipped: using CLI threshold=%.8g", threshold)

    metrics = evaluate(model, test_df[feature_columns], test_df[TARGET_COLUMN], tuned_threshold)
    validation_metrics = evaluate(model, validation_df[feature_columns], validation_df[TARGET_COLUMN], tuned_threshold)

    test_evaluation = test_df[["station_id", "observed_at", TARGET_COLUMN]].copy()
    test_evaluation["probability"] = model.predict_proba(test_df[feature_columns])[:, 1]
    event_metrics = evaluate_event_level(test_evaluation, tuned_threshold)
    LOGGER.info("Event-level metrics: %s", event_metrics)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(model_path)

    metadata = {
        "model_version": "v1.5",
        "algorithm": "XGBClassifier",
        "target": TARGET_COLUMN,
        "features": feature_columns,
        "core_rainfall_required": CORE_RAINFALL,
        "dataset": str(dataset_path),
        "rows_total": int(len(df)),
        "rows_train": int(len(train_df)),
        "rows_validation": int(len(validation_df)),
        "rows_test": int(len(test_df)),
        "train_date_min": str(train_df.observed_at.min()),
        "train_date_max": str(train_df.observed_at.max()),
        "validation_date_min": str(validation_df.observed_at.min()),
        "validation_date_max": str(validation_df.observed_at.max()),
        "test_date_min": str(test_df.observed_at.min()),
        "test_date_max": str(test_df.observed_at.max()),
        "train_positive_count": int(train_df[TARGET_COLUMN].sum()),
        "train_negative_count": int((train_df[TARGET_COLUMN] == 0).sum()),
        "scale_pos_weight": scale_pos_weight,
        "scale_pos_weight_multiplier": weight_multiplier,
        "validation_positive_count": int(validation_df[TARGET_COLUMN].sum()),
        "test_positive_count": int(test_df[TARGET_COLUMN].sum()),
        "target_event_recall": target_event_recall,
        "threshold_source": threshold_source,
        "threshold": float(tuned_threshold),
        "validation_metrics": validation_metrics,
        "metrics": metrics,
        "event_metrics": event_metrics,
        "model_parameters": model.get_params(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    LOGGER.info("Model written to %s", model_path)
    LOGGER.info("Metrics: %s", metrics)
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the V1.5 XGBoost flood-risk model")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--weight-multiplier",
        type=float,
        default=1.0,
        help="Multiplier applied to the training-split negative/positive class ratio; 1.0 uses the full ratio.",
    )
    parser.add_argument(
        "--target-event-recall",
        type=float,
        default=0.8,
        help="Minimum validation event recall used to select the highest alert threshold; default is 0.8.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    train(
        args.dataset,
        args.model,
        args.metadata,
        args.test_fraction,
        args.threshold,
        args.weight_multiplier,
        args.target_event_recall,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
