"""Leakage-safe temporal features for rainfall ML models."""

from __future__ import annotations

import pandas as pd

LAG_WINDOWS = (1, 3, 6, 12, 24)
ACCUMULATION_WINDOWS = (3, 6, 12, 24, 72)
NON_MODEL_COLUMNS = {
    "station_id", "station", "agency", "state", "district", "tehsil", "block", "village", "river", "basin",
    "tributary", "subtributary", "subsubtributary", "local_river", "source_file", "observed_at",
    "state_lgd_code", "district_lgd_code", "latitude", "longitude", "source_row_number",
}


def _time_rolling(result: pd.DataFrame, window: str, func: str, min_periods: int) -> pd.Series:
    """Compute a time-based rolling statistic independently for each station."""
    output = pd.Series(index=result.index, dtype="float64")
    for _, group in result.groupby("station_id", sort=False):
        values = group.set_index("observed_at")["rainfall_mm"]
        rolled = getattr(values.rolling(window=window, min_periods=min_periods), func)()
        output.loc[group.index] = rolled.to_numpy()
    return output


def add_rainfall_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add backward-looking rainfall lags, time-window accumulations and intensity statistics."""
    required = {"station_id", "observed_at", "rainfall_mm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    result = df.copy()
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result["rainfall_mm"] = pd.to_numeric(result["rainfall_mm"], errors="coerce")
    result = result.dropna(subset=["station_id", "observed_at"])
    result = result.sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)

    grouped = result.groupby("station_id", sort=False)["rainfall_mm"]
    for window in LAG_WINDOWS:
        result[f"rainfall_lag_{window}h"] = grouped.shift(window)

    for window in ACCUMULATION_WINDOWS:
        result[f"rainfall_{window}h_sum"] = _time_rolling(result, f"{window}h", "sum", 1)

    result["rainfall_24h_mean"] = _time_rolling(result, "24h", "mean", 2)
    result["rainfall_24h_max"] = _time_rolling(result, "24h", "max", 1)
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
