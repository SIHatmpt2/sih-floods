"""Deterministic transformations for cleaned CWC rainfall observations."""

from __future__ import annotations

import pandas as pd


def transform_rainfall_data(df: pd.DataFrame) -> pd.DataFrame:
    """Sort observations by station/time and add leakage-safe calendar fields."""
    required = {"station_id", "observed_at", "rainfall_mm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    result = df.copy()
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result["rainfall_mm"] = pd.to_numeric(result["rainfall_mm"], errors="coerce")
    result = result.dropna(subset=["station_id", "observed_at"])
    result = result.sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)
    result["year"] = result["observed_at"].dt.year.astype("int16")
    result["month"] = result["observed_at"].dt.month.astype("int8")
    result["day_of_year"] = result["observed_at"].dt.dayofyear.astype("int16")
    result["day_of_week"] = result["observed_at"].dt.dayofweek.astype("int8")
    result["hour"] = result["observed_at"].dt.hour.astype("int8")
    result["is_weekend"] = (result["day_of_week"] >= 5).astype("int8")
    result["is_monsoon"] = result["month"].isin([6, 7, 8, 9]).astype("int8")
    return result
