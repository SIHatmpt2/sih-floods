"""Leakage-safe temporal features for XGBoost river models."""

from __future__ import annotations

import pandas as pd

from .transform import transform_river_data

LAG_HOURS = (1, 3, 6, 12, 24)
ROLLING_WINDOWS = (6, 24)
NON_MODEL_COLUMNS = {
    "station_id", "station", "agency", "state", "district", "tehsil", "block", "village", "river", "basin",
    "tributary", "subtributary", "subsubtributary", "local_river", "is_discharge_data_available", "source_file",
    "observed_at",
}

# Canonical feature prefixes intentionally describe the measurement rather than
# repeating its storage unit.  This keeps the generated model schema aligned
# with the public data-processing tests and makes feature names consistent
# across water-level and discharge measurements.
_FEATURE_PREFIXES = {
    "water_level_m": "water_level",
    "discharge_cumecs": "discharge",
}


def _feature_prefix(value_column: str) -> str:
    return _FEATURE_PREFIXES.get(value_column, value_column)


def add_river_features(df: pd.DataFrame, value_column: str = "water_level_m") -> pd.DataFrame:
    """Add station-local backward-looking lags, rolling statistics and rates of change."""
    if value_column not in df.columns:
        raise ValueError(f"Missing feature value column: {value_column!r}")
    result = transform_river_data(df)
    result[value_column] = pd.to_numeric(result[value_column], errors="coerce")
    grouped = result.groupby("station_id", sort=False)[value_column]
    prefix = _feature_prefix(value_column)
    for hours in LAG_HOURS:
        result[f"{prefix}_lag_{hours}h"] = grouped.shift(hours)
    for hours in ROLLING_WINDOWS:
        rolling = grouped.rolling(window=hours, min_periods=2)
        result[f"{prefix}_rolling_mean_{hours}h"] = rolling.mean().reset_index(level=0, drop=True)
        result[f"{prefix}_rolling_max_{hours}h"] = rolling.max().reset_index(level=0, drop=True)
        result[f"{prefix}_rolling_std_{hours}h"] = rolling.std().reset_index(level=0, drop=True)
    result[f"{prefix}_delta_1h"] = grouped.diff()
    result[f"{prefix}_pct_change_1h"] = grouped.pct_change(fill_method=None)
    return result


def select_xgboost_features(df: pd.DataFrame, target_column: str | None = None) -> pd.DataFrame:
    """Return numeric model features while excluding identifiers and the optional target."""
    excluded = NON_MODEL_COLUMNS | ({target_column} if target_column else set())
    numeric = df.select_dtypes(include=["number", "bool"]).copy()
    columns = [column for column in numeric.columns if column not in excluded]
    if not columns:
        raise ValueError("No numeric XGBoost features found")
    return numeric[columns]
