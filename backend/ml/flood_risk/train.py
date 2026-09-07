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


def tune_threshold(model: XGBClassifier, validation: pd.DataFrame, feature_columns: list[str]) -> float:
    probabilities = model.predict_proba(validation[feature_columns])[:, 1]
    y_validation = validation[TARGET_COLUMN]
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in np.linspace(0.01, 0.99, 99):
        predictions = (probabilities >= threshold).astype(np.int8)
        score = f1_score(y_validation, predictions, zero_division=0)
        if score > best_f1:
            best_f1 = float(score)
            best_threshold = float(threshold)
    LOGGER.info("Validation threshold tuning: threshold=%.2f f1=%.4f", best_threshold, best_f1)
    return best_threshold


def train_model(train: pd.DataFrame, validation: pd.DataFrame, feature_columns: list[str]) -> XGBClassifier:
    x_train = train[feature_columns]
    y_train = train[TARGET_COLUMN]

    positives = int(y_train.sum())
    negatives = int(len(y_train) - positives)
    if positives == 0:
        raise ValueError("Training split contains no positive flood examples")
    scale_pos_weight = negatives / positives
    LOGGER.info("Train rows=%d positives=%d negatives=%d scale_pos_weight=%.2f", len(train), positives, negatives, scale_pos_weight)

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
        tree_method="hist",
        n_jobs=max(1, min(4, os.cpu_count() or 1)),
        random_state=42,
    )
    model.fit(x_train, y_train, eval_set=[(validation[feature_columns], validation[TARGET_COLUMN])], verbose=False)
    return model


def train(dataset_path: Path, model_path: Path, metadata_path: Path, test_fraction: float, threshold: float) -> dict[str, object]:
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

    model = train_model(train_df, validation_df, feature_columns)
    tuned_threshold = tune_threshold(model, validation_df, feature_columns)
    final_threshold = tuned_threshold if threshold == 0.5 else threshold
    metrics = evaluate(model, test_df[feature_columns], test_df[TARGET_COLUMN], final_threshold)
    validation_metrics = evaluate(model, validation_df[feature_columns], validation_df[TARGET_COLUMN], tuned_threshold)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(model_path)

    metadata = {
        "model_version": "v1",
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
        "validation_positive_count": int(validation_df[TARGET_COLUMN].sum()),
        "test_positive_count": int(test_df[TARGET_COLUMN].sum()),
        "threshold_source": "validation_f1" if threshold == 0.5 else "cli_override",
        "validation_metrics": validation_metrics,
        "metrics": metrics,
        "model_parameters": model.get_params(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    LOGGER.info("Model written to %s", model_path)
    LOGGER.info("Metrics: %s", metrics)
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the V1 XGBoost flood-risk model")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    train(args.dataset, args.model, args.metadata, args.test_fraction, args.threshold)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
