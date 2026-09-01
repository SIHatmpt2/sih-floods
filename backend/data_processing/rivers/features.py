"""Leakage-safe temporal features for XGBoost river models."""

from __future__ import annotations

import pandas as pd

from .transform import transform_river_data

LAG_HOURS = (1, 3, 6, 12, 24)
ROLLING_WINDOWS = (6, 24)


def _station_time_series(result: pd.DataFrame, value_column: str) -> pd.Series:
    return result.groupby("station_id", sort=False, group_keys=False)[value_column].transform(lambda s: s)


def add_river_features(df: pd.DataFrame, value_column: str = "water_level_m") -> pd.DataFrame:
    """Add station-local backward-looking lags, rolling statistics and rates of change."""
    if value_column not in df.columns:
        raise ValueError(f"Missing feature value column: {value_column!r}")
    result = transform_river_data(df)
    result[value_column] = pd.to_numeric(result[value_column], errors="coerce")

    # The CWC feeds are nominally hourly. Shift by observations rather than
    # timestamps so irregular feeds retain a valid "previous observation".
    grouped = result.groupby("station_id", sort=False)[value_column]
    for hours in LAG_HOURS:
        result[f"{value_column}_lag_{hours}h"] = grouped.shift(hours)

    for hours in ROLLING_WINDOWS:
        rolling = grouped.rolling(window=hours, min_periods=2)
        result[f"{value_column}_rolling_mean_{hours}h"] = rolling.mean().reset_index(level=0, drop=True)
        result[f"{value_column}_rolling_max_{hours}h"] = rolling.max().reset_index(level=0, drop=True)
        result[f"{value_column}_rolling_std_{hours}h"] = rolling.std().reset_index(level=0, drop=True)

    result[f"{value_column}_delta_1h"] = grouped.diff()
    result[f"{value_column}_pct_change_1h"] = grouped.pct_change(fill_method=None)
    return result
