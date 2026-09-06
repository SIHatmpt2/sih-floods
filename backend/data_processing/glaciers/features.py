"""Leakage-safe temporal features for glacier/lake change records."""

from __future__ import annotations

import pandas as pd

NON_MODEL_COLUMNS = {
    "glacier_lake", "year", "melting_rate_text", "flood_cause", "river_originating", "source_file",
    "source_row_number",
}


def add_glacier_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add year-over-year area change and backward-looking glacier change features."""
    required = {"glacier_lake", "year", "area_km2"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    result = df.copy()
    result["year"] = pd.to_numeric(result["year"], errors="coerce")
    result["area_km2"] = pd.to_numeric(result["area_km2"], errors="coerce")
    result = result.sort_values(["glacier_lake", "year"], kind="stable").reset_index(drop=True)
    grouped = result.groupby("glacier_lake", sort=False)["area_km2"]

    result["previous_year"] = result.groupby("glacier_lake", sort=False)["year"].shift(1)
    result["previous_area_km2"] = grouped.shift(1)
    result["area_change_1y_km2"] = result["area_km2"] - result["previous_area_km2"]
    result["area_change_1y_pct"] = result["area_change_1y_km2"] / result["previous_area_km2"] * 100
    result["cumulative_area_change_km2"] = result["area_km2"] - grouped.transform("first")
    result["cumulative_area_change_pct"] = result["cumulative_area_change_km2"] / grouped.transform("first") * 100
    result["is_area_declining"] = result["area_change_1y_km2"].lt(0).astype("Int8")
    result["is_flood_cause_reported"] = result["flood_cause"].fillna("").str.lower().ne("no").astype("Int8")
    return result


def select_numeric_features(df: pd.DataFrame, target_column: str | None = None) -> pd.DataFrame:
    """Return numeric model features while excluding identifiers and optional target."""
    excluded = NON_MODEL_COLUMNS | ({target_column} if target_column else set())
    numeric = df.select_dtypes(include=["number", "bool"]).copy()
    columns = [c for c in numeric.columns if c not in excluded]
    if not columns:
        raise ValueError("No numeric glacier features found")
    return numeric[columns]
