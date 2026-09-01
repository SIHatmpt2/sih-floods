"""Leakage-safe temporal features for rainfall ML models."""

from __future__ import annotations

import pandas as pd

LAG_WINDOWS = (1, 3, 6, 12, 24)
ACCUMULATION_WINDOWS = (3, 6, 12, 24, 72)
NON_MODEL_COLUMNS = {
    "station_id", "station", "agency", "state", "district", "tehsil", "block", "village", "river", "basin",
    "tributary", "subtributary", "subsubtributary", "local_river", "source_file", "observed_at",
}


def add_rainfall_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add backward-looking rainfall lags, accumulations and intensity statistics."""
    if "rainfall_mm" not in df.columns:
        raise ValueError("Missing feature value column: 'rainfall_mm'")
    result = df.copy()
    result = result.sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)
    result["rainfall_mm"] = pd.to_numeric(result["rainfall_mm"], errors="coerce")
    grouped = result.groupby("station_id", sort=False)["rainfall_mm"]
    for window in LAG_WINDOWS:
        result[f"rainfall_lag_{window}h"] = grouped.shift(window)
    for window in ACCUMULATION_WINDOWS:
        result[f"rainfall_{window}h_sum"] = grouped.transform(
            lambda s, w=window: s.rolling(window=w, min_periods=1).sum()
        )
    rolling_24 = grouped.transform(lambda s: s.rolling(window=24, min_periods=2).mean())
    max_24 = grouped.transform(lambda s: s.rolling(window=24, min_periods=1).max())
    result["rainfall_24h_mean"] = rolling_24
    result["rainfall_24h_max"] = max_24
    result["rainfall_delta_1h"] = grouped.diff()
    result["rainfall_pct_change_1h"] = grouped.pct_change(fill_method=None)
    return result


def select_xgboost_features(df: pd.DataFrame, target_column: str | None = None) -> pd.DataFrame:
    """Return numeric model features, excluding identifiers and an optional target."""
    excluded = NON_MODEL_COLUMNS | ({target_column} if target_column else set())
    numeric = df.select_dtypes(include=["number", "bool"]).copy()
    columns = [column for column in numeric.columns if column not in excluded]
    if not columns:
        raise ValueError("No numeric XGBoost features found")
    return numeric[columns]
