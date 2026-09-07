"""Train and evaluate the V1.5 XGBoost flood-risk model."""
from __future__ import annotations

import argparse
import json
import logging
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
DEFAULT_WEIGHT_SWEEP = (0.25, 0.5, 1.0, 2.0, 4.0)
DEFAULT_MIN_CONSECUTIVE_ALERTS = 3
DEFAULT_ALERT_COOLDOWN_HOURS = 24.0
DEFAULT_ALERT_POLICY_SWEEP = ((3, 24.0), (6, 24.0), (3, 48.0), (6, 48.0), (12, 48.0), (12, 72.0))

FEATURE_COLUMNS = [
    "rainfall_24h", "rainfall_48h", "rainfall_72h", "rainfall_7d", "rainfall_30d",
    "water_level_m", "water_level_delta_1h", "water_level_pct_change_1h",
    "water_level_lag_1h", "water_level_lag_3h", "water_level_lag_6h", "water_level_lag_12h", "water_level_lag_24h",
    "water_level_rolling_mean_6h", "water_level_rolling_max_6h", "water_level_rolling_std_6h",
    "water_level_rolling_mean_24h", "water_level_rolling_max_24h", "water_level_rolling_std_24h",
    "discharge_cumecs", "discharge_delta_1h", "discharge_pct_change_1h",
    "discharge_lag_1h", "discharge_lag_3h", "discharge_lag_6h", "discharge_lag_12h", "discharge_lag_24h",
    "discharge_rolling_mean_6h", "discharge_rolling_max_6h", "discharge_rolling_std_6h",
    "discharge_rolling_mean_24h", "discharge_rolling_max_24h", "discharge_rolling_std_24h",
    "flood_count_1y", "flood_count_3y", "flood_count_5y", "days_since_last_flood",
    "historical_max_severity", "historical_mean_severity", "historical_glof_count",
    "glacier_area_km2", "glacier_area_change_1y_km2", "glacier_area_change_1y_pct",
    "glacier_cumulative_area_change_km2", "glacier_cumulative_area_change_pct", "glacier_elevation_m",
    "glacier_melting_rate_min_km_per_year", "glacier_melting_rate_max_km_per_year",
    "month", "day_of_year", "is_monsoon",
]
CORE_RAINFALL = ["rainfall_24h", "rainfall_48h", "rainfall_72h"]


def load_training_rows(path: Path) -> pd.DataFrame:
    LOGGER.info("Reading training data: %s", path)
    df = pd.read_parquet(path)
    missing = [c for c in ["station_id", "observed_at", TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Training dataset missing required columns: {missing}")
    usable = [c for c in FEATURE_COLUMNS if c in df.columns]
    if not usable:
        raise ValueError("No supported feature columns found in training dataset")
    df["observed_at"] = pd.to_datetime(df["observed_at"], errors="coerce")
    df = df.dropna(subset=["station_id", "observed_at", TARGET_COLUMN])
    df = df.loc[df[CORE_RAINFALL].notna().all(axis=1)].copy()
    for c in usable:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype("int8")
    return df.sort_values("observed_at", kind="stable").reset_index(drop=True)


def chronological_split(df: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_fraction < 0.5:
        raise ValueError("test_fraction must be between 0 and 0.5")
    cutoff = max(1, min(int(len(df) * (1 - test_fraction)), len(df) - 1))
    return df.iloc[:cutoff].copy(), df.iloc[cutoff:].copy()


def apply_alert_policy(
    evaluation: pd.DataFrame,
    threshold: float,
    min_consecutive_alerts: int = DEFAULT_MIN_CONSECUTIVE_ALERTS,
    cooldown_hours: float = DEFAULT_ALERT_COOLDOWN_HOURS,
) -> pd.DataFrame:
    required = {"station_id", "observed_at", "probability"}
    missing = sorted(required - set(evaluation.columns))
    if missing:
        raise ValueError(f"Alert policy missing required columns: {missing}")
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    if min_consecutive_alerts < 1:
        raise ValueError("min_consecutive_alerts must be at least 1")
    if cooldown_hours < 0:
        raise ValueError("cooldown_hours must be non-negative")
    df = evaluation.copy()
    df["observed_at"] = pd.to_datetime(df["observed_at"], errors="coerce")
    df["probability"] = pd.to_numeric(df["probability"], errors="coerce")
    df = df.dropna(subset=["station_id", "observed_at", "probability"])
    df = df.sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=False)
    df["raw_alert"] = df["probability"] >= threshold
    df["alert"] = False
    cooldown = pd.Timedelta(hours=float(cooldown_hours))
    for _, group in df.groupby("station_id", sort=False):
        streak = 0
        last_alert_at = None
        for index, row in group.iterrows():
            if not bool(row["raw_alert"]):
                streak = 0
                continue
            streak += 1
            if streak < min_consecutive_alerts:
                continue
            now = row["observed_at"]
            if last_alert_at is None or now - last_alert_at >= cooldown:
                df.at[index, "alert"] = True
                last_alert_at = now
    return df.sort_values("index", kind="stable").drop(columns=["index", "raw_alert"]).reset_index(drop=True)


def evaluate(
    model: XGBClassifier,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float,
    alert_policy: bool = False,
    station_ids: pd.Series | None = None,
    observed_at: pd.Series | None = None,
    min_consecutive_alerts: int = DEFAULT_MIN_CONSECUTIVE_ALERTS,
    cooldown_hours: float = DEFAULT_ALERT_COOLDOWN_HOURS,
) -> dict[str, object]:
    probabilities = model.predict_proba(x_test)[:, 1]
    if alert_policy:
        if station_ids is None or observed_at is None:
            raise ValueError("station_ids and observed_at are required when alert_policy is enabled")
        alerts = apply_alert_policy(
            pd.DataFrame({"station_id": station_ids.to_numpy(), "observed_at": observed_at.to_numpy(), "probability": probabilities}),
            threshold, min_consecutive_alerts, cooldown_hours,
        )["alert"].astype(np.int8).to_numpy()
    else:
        alerts = (probabilities >= threshold).astype(np.int8)
    tn, fp, fn, tp = confusion_matrix(y_test, alerts, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "roc_auc": float(roc_auc_score(y_test, probabilities)) if y_test.nunique() > 1 else None,
        "pr_auc": float(average_precision_score(y_test, probabilities)) if y_test.sum() else None,
        "precision": float(precision_score(y_test, alerts, zero_division=0)),
        "recall": float(recall_score(y_test, alerts, zero_division=0)),
        "f1": float(f1_score(y_test, alerts, zero_division=0)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "positive_rate": float(y_test.mean()),
        "alerts": int(alerts.sum()),
    }


def evaluate_event_level(
    evaluation: pd.DataFrame,
    threshold: float,
    event_gap_hours: float = 72.0,
    min_consecutive_alerts: int = DEFAULT_MIN_CONSECUTIVE_ALERTS,
    cooldown_hours: float = DEFAULT_ALERT_COOLDOWN_HOURS,
) -> dict[str, object]:
    required = {"station_id", "observed_at", TARGET_COLUMN, "probability"}
    missing = sorted(required - set(evaluation.columns))
    if missing:
        raise ValueError(f"Event evaluation missing required columns: {missing}")
    if event_gap_hours <= 0:
        raise ValueError("event_gap_hours must be greater than 0")
    base = evaluation[["station_id", "observed_at", TARGET_COLUMN, "probability"]].copy()
    base["observed_at"] = pd.to_datetime(base["observed_at"], errors="coerce")
    base["probability"] = pd.to_numeric(base["probability"], errors="coerce")
    base = base.dropna(subset=["station_id", "observed_at", TARGET_COLUMN, "probability"])
    df = apply_alert_policy(base, threshold, min_consecutive_alerts, cooldown_hours)
    positive = df.loc[df[TARGET_COLUMN].eq(1)].copy()
    if positive.empty:
        event_count = detected_event_count = 0
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
    false_alarm_station_days = int(false_alerts.assign(day=false_alerts["observed_at"].dt.floor("D"))[["station_id", "day"]].drop_duplicates().shape[0]) if not false_alerts.empty else 0
    station_days = int(df.assign(day=df["observed_at"].dt.floor("D"))[["station_id", "day"]].drop_duplicates().shape[0])
    return {
        "event_gap_hours": float(event_gap_hours),
        "min_consecutive_alerts": int(min_consecutive_alerts),
        "alert_cooldown_hours": float(cooldown_hours),
        "event_count": event_count,
        "detected_event_count": detected_event_count,
        "event_recall": float(detected_event_count / event_count) if event_count else None,
        "mean_lead_time_to_window_end_hours": float(np.mean(lead_times)) if lead_times else None,
        "median_lead_time_to_window_end_hours": float(np.median(lead_times)) if lead_times else None,
        "false_alarm_rows": false_alarm_rows,
        "false_alarm_station_days": false_alarm_station_days,
        "evaluated_station_days": station_days,
        "false_alarms_per_station_day": float(false_alarm_rows / station_days) if station_days else None,
        "alerts": int(df["alert"].sum()),
    }


def _threshold_candidates(probabilities: np.ndarray) -> np.ndarray:
    finite = probabilities[np.isfinite(probabilities)]
    if finite.size == 0:
        raise ValueError("Validation predictions contain no finite probabilities")
    lower = max(float(np.min(finite)) * 0.5, 1e-8)
    upper = min(max(float(np.max(finite)) * 1.05, 0.01), 1.0)
    return np.unique(np.clip(np.concatenate([np.logspace(np.log10(lower), np.log10(upper), 300), np.unique(finite), np.array([0.01, 0.5, 0.99])]), 1e-8, 1.0))


def tune_threshold(model: XGBClassifier, validation: pd.DataFrame, feature_columns: list[str]) -> float:
    probabilities = model.predict_proba(validation[feature_columns])[:, 1]
    y = validation[TARGET_COLUMN]
    best_threshold, best_f1 = 0.5, -1.0
    for candidate in _threshold_candidates(probabilities):
        score = f1_score(y, (probabilities >= candidate).astype(np.int8), zero_division=0)
        if score > best_f1:
            best_f1, best_threshold = float(score), float(candidate)
    LOGGER.info("Validation threshold tuning: threshold=%.8g f1=%.4f", best_threshold, best_f1)
    return best_threshold


def tune_threshold_event_aware(
    model: XGBClassifier,
    validation: pd.DataFrame,
    feature_columns: list[str],
    target_event_recall: float = 0.8,
    event_gap_hours: float = 72.0,
    min_consecutive_alerts: int = DEFAULT_MIN_CONSECUTIVE_ALERTS,
    cooldown_hours: float = DEFAULT_ALERT_COOLDOWN_HOURS,
) -> float:
    probabilities = model.predict_proba(validation[feature_columns])[:, 1]
    evaluation = validation[["station_id", "observed_at", TARGET_COLUMN]].copy()
    evaluation["probability"] = probabilities
    candidates = _threshold_candidates(probabilities)
    feasible = []
    for candidate in candidates:
        m = evaluate_event_level(evaluation, float(candidate), event_gap_hours, min_consecutive_alerts, cooldown_hours)
        if m["event_recall"] is not None and float(m["event_recall"]) >= target_event_recall:
            feasible.append((float(candidate), int(m["false_alarm_station_days"]), int(m["false_alarm_rows"])))
    if feasible:
        threshold = max(feasible, key=lambda item: (item[0], -item[1], -item[2]))[0]
    else:
        fallback = []
        for candidate in candidates:
            m = evaluate_event_level(evaluation, float(candidate), event_gap_hours, min_consecutive_alerts, cooldown_hours)
            fallback.append((float(m["event_recall"] or 0.0), float(candidate), int(m["false_alarm_station_days"]), int(m["false_alarm_rows"])))
        threshold = max(fallback, key=lambda item: (item[0], -item[2], -item[3], item[1]))[1]
    m = evaluate_event_level(evaluation, threshold, event_gap_hours, min_consecutive_alerts, cooldown_hours)
    LOGGER.info(
        "Event-aware threshold tuning: target_event_recall=%.3f threshold=%.8g event_recall=%.4f false_alarm_station_days=%d false_alarms_per_station_day=%.4f min_consecutive=%d cooldown_hours=%.1f",
        target_event_recall, threshold, float(m["event_recall"] or 0.0), int(m["false_alarm_station_days"]), float(m["false_alarms_per_station_day"] or 0.0), min_consecutive_alerts, cooldown_hours,
    )
    return threshold


def select_best_alert_policy_result(results: list[dict[str, object]], target_event_recall: float = 0.8) -> dict[str, object]:
    if not results:
        raise ValueError("Alert policy sweep produced no results")
    feasible = [r for r in results if r.get("event_recall") is not None and float(r["event_recall"]) >= target_event_recall]
    pool = feasible if feasible else results
    if feasible:
        return min(pool, key=lambda r: (int(r["false_alarm_station_days"]), int(r["false_alarm_rows"]), -float(r["event_recall"]), -float(r["threshold"])))
    return max(pool, key=lambda r: (float(r["event_recall"]), -int(r["false_alarm_station_days"]), -int(r["false_alarm_rows"]), float(r["threshold"])))


def tune_alert_policy_event_aware(
    model: XGBClassifier,
    validation: pd.DataFrame,
    feature_columns: list[str],
    threshold: float,
    target_event_recall: float = 0.8,
    event_gap_hours: float = 72.0,
    policy_candidates: tuple[tuple[int, float], ...] = DEFAULT_ALERT_POLICY_SWEEP,
) -> dict[str, object]:
    """Choose confirmation/cooldown settings that reduce false alarms without sacrificing event recall."""
    probabilities = model.predict_proba(validation[feature_columns])[:, 1]
    evaluation = validation[["station_id", "observed_at", TARGET_COLUMN]].copy()
    evaluation["probability"] = probabilities
    results: list[dict[str, object]] = []
    for min_consecutive, cooldown in policy_candidates:
        metrics = evaluate_event_level(evaluation, threshold, event_gap_hours, min_consecutive, cooldown)
        result = {
            "min_consecutive_alerts": int(min_consecutive),
            "alert_cooldown_hours": float(cooldown),
            "threshold": float(threshold),
            "event_recall": metrics["event_recall"],
            "false_alarm_station_days": int(metrics["false_alarm_station_days"]),
            "false_alarm_rows": int(metrics["false_alarm_rows"]),
            "false_alarms_per_station_day": metrics["false_alarms_per_station_day"],
            "alerts": int(metrics["alerts"]),
        }
        results.append(result)
        LOGGER.info(
            "Alert policy experiment: consecutive=%d cooldown_hours=%.1f event_recall=%.4f false_alarm_station_days=%d false_alarms_per_station_day=%.4f alerts=%d",
            min_consecutive, cooldown, float(metrics["event_recall"] or 0.0), int(metrics["false_alarm_station_days"]), float(metrics["false_alarms_per_station_day"] or 0.0), int(metrics["alerts"]),
        )
    best = select_best_alert_policy_result(results, target_event_recall)
    LOGGER.info(
        "Selected alert policy: consecutive=%d cooldown_hours=%.1f threshold=%.8g event_recall=%.4f false_alarm_station_days=%d false_alarms_per_station_day=%.4f",
        int(best["min_consecutive_alerts"]), float(best["alert_cooldown_hours"]), float(best["threshold"]), float(best["event_recall"] or 0.0), int(best["false_alarm_station_days"]), float(best["false_alarms_per_station_day"] or 0.0),
    )
    return best | {"policy_sweep": results}


def train_model(train: pd.DataFrame, validation: pd.DataFrame, feature_columns: list[str], weight_multiplier: float = 1.0) -> tuple[XGBClassifier, float]:
    x_train, y_train = train[feature_columns], train[TARGET_COLUMN]
    positives = int(y_train.sum())
    negatives = int(len(y_train) - positives)
    if positives == 0:
        raise ValueError("Training split contains no positive flood examples")
    if weight_multiplier <= 0:
        raise ValueError("weight_multiplier must be greater than 0")
    base = negatives / positives
    scale = base * weight_multiplier
    LOGGER.info("Train rows=%d positives=%d negatives=%d positive_rate=%.6f scale_pos_weight=%.4f (base=%.4f multiplier=%.3f)", len(train), positives, negatives, positives / len(train), scale, base, weight_multiplier)
    model = XGBClassifier(
        objective="binary:logistic", eval_metric="aucpr", n_estimators=500, learning_rate=0.05,
        max_depth=6, min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=1.0, scale_pos_weight=scale, max_delta_step=1,
        tree_method="hist", n_jobs=max(1, min(4, os.cpu_count() or 1)), random_state=42,
    )
    model.fit(x_train, y_train, eval_set=[(validation[feature_columns], validation[TARGET_COLUMN])], verbose=False)
    return model, float(scale)


def select_best_weight_result(results: list[dict[str, object]]) -> dict[str, object]:
    valid = [r for r in results if r.get("validation_pr_auc") is not None and np.isfinite(float(r["validation_pr_auc"]))]
    if not valid:
        raise ValueError("Weight sweep produced no finite validation PR-AUC values")
    return max(valid, key=lambda r: (float(r["validation_pr_auc"]), -float(r["weight_multiplier"])))


def run_weight_sweep(train: pd.DataFrame, validation: pd.DataFrame, feature_columns: list[str], weight_multipliers: tuple[float, ...]):
    if not weight_multipliers or any(m <= 0 for m in weight_multipliers):
        raise ValueError("weight_multipliers must contain positive numbers")
    results = []
    best_model = None
    best_weight = 0.0
    best_pr_auc = -1.0
    for multiplier in weight_multipliers:
        model, scale = train_model(train, validation, feature_columns, multiplier)
        p = model.predict_proba(validation[feature_columns])[:, 1]
        y = validation[TARGET_COLUMN]
        pr_auc = float(average_precision_score(y, p)) if y.sum() else float("nan")
        roc_auc = float(roc_auc_score(y, p)) if y.nunique() > 1 else None
        results.append({"weight_multiplier": float(multiplier), "scale_pos_weight": float(scale), "validation_pr_auc": pr_auc, "validation_roc_auc": roc_auc})
        LOGGER.info("Weight experiment: multiplier=%.3f scale_pos_weight=%.4f validation_pr_auc=%.6f validation_roc_auc=%s", multiplier, scale, pr_auc, f"{roc_auc:.6f}" if roc_auc is not None else "n/a")
        if pr_auc > best_pr_auc:
            best_pr_auc, best_model, best_weight = pr_auc, model, float(scale)
    best = select_best_weight_result(results)
    LOGGER.info("Selected class weight: multiplier=%.3f scale_pos_weight=%.4f validation_pr_auc=%.6f", float(best["weight_multiplier"]), float(best["scale_pos_weight"]), float(best["validation_pr_auc"]))
    assert best_model is not None
    return best_model, best_weight, results, float(best["weight_multiplier"])


def train(dataset_path: Path, model_path: Path, metadata_path: Path, test_fraction: float, threshold: float, weight_multipliers: tuple[float, ...], target_event_recall: float = 0.8, min_consecutive_alerts: int = DEFAULT_MIN_CONSECUTIVE_ALERTS, cooldown_hours: float = DEFAULT_ALERT_COOLDOWN_HOURS) -> dict[str, object]:
    df = load_training_rows(dataset_path)
    if df.empty:
        raise ValueError("No usable training rows after rainfall-complete filtering")
    train_val, test_df = chronological_split(df, test_fraction)
    train_df, validation_df = chronological_split(train_val, test_fraction=0.25)
    feature_columns = [c for c in FEATURE_COLUMNS if c in df.columns and df[c].notna().any()]
    if not feature_columns:
        raise ValueError("No non-empty feature columns available")
    LOGGER.info("Rows: total=%d train=%d validation=%d test=%d features=%d", len(df), len(train_df), len(validation_df), len(test_df), len(feature_columns))
    LOGGER.info("Date split: train=%s -> %s, validation=%s -> %s, test=%s -> %s", train_df.observed_at.min(), train_df.observed_at.max(), validation_df.observed_at.min(), validation_df.observed_at.max(), test_df.observed_at.min(), test_df.observed_at.max())
    model, scale, weight_sweep, selected_weight = run_weight_sweep(train_df, validation_df, feature_columns, weight_multipliers)
    if threshold == 0.5:
        tuned_threshold = tune_threshold_event_aware(model, validation_df, feature_columns, target_event_recall, min_consecutive_alerts=min_consecutive_alerts, cooldown_hours=cooldown_hours)
        threshold_source = "validation_event_recall_alert_policy"
    else:
        tuned_threshold = threshold
        threshold_source = "cli_override"
        LOGGER.info("Validation threshold tuning skipped: using CLI threshold=%.8g", threshold)
    if threshold_source == "validation_event_recall_alert_policy":
        selected_policy = tune_alert_policy_event_aware(model, validation_df, feature_columns, tuned_threshold, target_event_recall, policy_candidates=DEFAULT_ALERT_POLICY_SWEEP)
        min_consecutive_alerts = int(selected_policy["min_consecutive_alerts"])
        cooldown_hours = float(selected_policy["alert_cooldown_hours"])
    else:
        selected_policy = {"threshold": float(tuned_threshold), "min_consecutive_alerts": min_consecutive_alerts, "alert_cooldown_hours": cooldown_hours, "policy_sweep": []}
    metrics = evaluate(model, test_df[feature_columns], test_df[TARGET_COLUMN], tuned_threshold, True, test_df["station_id"], test_df["observed_at"], min_consecutive_alerts, cooldown_hours)
    validation_metrics = evaluate(model, validation_df[feature_columns], validation_df[TARGET_COLUMN], tuned_threshold, True, validation_df["station_id"], validation_df["observed_at"], min_consecutive_alerts, cooldown_hours)
    test_evaluation = test_df[["station_id", "observed_at", TARGET_COLUMN]].copy()
    test_evaluation["probability"] = model.predict_proba(test_df[feature_columns])[:, 1]
    event_metrics = evaluate_event_level(test_evaluation, tuned_threshold, min_consecutive_alerts=min_consecutive_alerts, cooldown_hours=cooldown_hours)
    LOGGER.info("Event-level metrics: %s", event_metrics)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(model_path)
    metadata = {
        "model_version": "v1.5", "algorithm": "XGBClassifier", "target": TARGET_COLUMN, "features": feature_columns,
        "core_rainfall_required": CORE_RAINFALL, "dataset": str(dataset_path), "rows_total": int(len(df)),
        "rows_train": int(len(train_df)), "rows_validation": int(len(validation_df)), "rows_test": int(len(test_df)),
        "train_date_min": str(train_df.observed_at.min()), "train_date_max": str(train_df.observed_at.max()),
        "validation_date_min": str(validation_df.observed_at.min()), "validation_date_max": str(validation_df.observed_at.max()),
        "test_date_min": str(test_df.observed_at.min()), "test_date_max": str(test_df.observed_at.max()),
        "train_positive_count": int(train_df[TARGET_COLUMN].sum()), "train_negative_count": int((train_df[TARGET_COLUMN] == 0).sum()),
        "scale_pos_weight": scale, "scale_pos_weight_multiplier": selected_weight, "weight_sweep": weight_sweep,
        "validation_positive_count": int(validation_df[TARGET_COLUMN].sum()), "test_positive_count": int(test_df[TARGET_COLUMN].sum()),
        "target_event_recall": target_event_recall, "threshold_source": threshold_source, "threshold": float(tuned_threshold),
        "min_consecutive_alerts": min_consecutive_alerts, "alert_cooldown_hours": cooldown_hours,
        "selected_alert_policy": selected_policy, "validation_metrics": validation_metrics, "metrics": metrics,
        "event_metrics": event_metrics, "model_parameters": model.get_params(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    LOGGER.info("Model written to %s", model_path)
    LOGGER.info("Metrics: %s", metrics)
    return metadata


def _parse_weight_sweep(value: str) -> tuple[float, ...]:
    try:
        values = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("weight sweep must be comma-separated positive numbers") from exc
    if not values or any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("weight sweep must contain positive numbers")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the V1.5 XGBoost flood-risk model")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--weight-sweep", type=_parse_weight_sweep, default=DEFAULT_WEIGHT_SWEEP)
    parser.add_argument("--weight-multiplier", type=float, default=None)
    parser.add_argument("--target-event-recall", type=float, default=0.8)
    parser.add_argument("--min-consecutive-alerts", type=int, default=DEFAULT_MIN_CONSECUTIVE_ALERTS)
    parser.add_argument("--alert-cooldown-hours", type=float, default=DEFAULT_ALERT_COOLDOWN_HOURS)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    weights = (args.weight_multiplier,) if args.weight_multiplier is not None else args.weight_sweep
    train(args.dataset, args.model, args.metadata, args.test_fraction, args.threshold, weights, args.target_event_recall, args.min_consecutive_alerts, args.alert_cooldown_hours)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
