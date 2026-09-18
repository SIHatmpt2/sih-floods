"""Train and evaluate the V2 XGBoost flood-risk model."""
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
DEFAULT_DATASET = Path("apps/risk/data/processed/v2_train.parquet")
DEFAULT_MODEL = Path("models/flood_risk_v2.json")
DEFAULT_METADATA = Path("models/flood_risk_v2.metadata.json")
DEFAULT_WEIGHT_SWEEP = (0.25, 0.5, 1.0, 2.0, 4.0)
DEFAULT_MIN_CONSECUTIVE_ALERTS = 6
DEFAULT_ALERT_COOLDOWN_HOURS = 72.0
DEFAULT_ALERT_POLICY_SWEEP = ((1, 24.0), (2, 24.0), (3, 24.0), (6, 24.0), (12, 24.0), (1, 48.0), (2, 48.0), (3, 48.0), (6, 48.0), (12, 48.0), (18, 48.0), (24, 48.0), (6, 72.0), (12, 72.0), (18, 72.0), (24, 72.0))
DEFAULT_HARD_NEGATIVE_FRACTION = 0.05
DEFAULT_HARD_NEGATIVE_MULTIPLIER = 3.0

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
    "historical_slope_min_deg", "historical_slope_max_deg", "historical_slope_mid_deg",
    "historical_river_distance_min_m", "historical_river_distance_max_m", "historical_river_distance_mid_m",
    "historical_land_cover_min_km2", "historical_land_cover_max_km2", "historical_land_cover_mid_km2",
    "co2_ppm", "co2_monthly_change_ppm", "co2_yearly_change_ppm", "co2_regional_anomaly_ppm",
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

