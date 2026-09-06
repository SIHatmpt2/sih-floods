"""Cleaning and canonicalization for glacier/lake change data."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

_COLUMN_ALIASES = {
    "glacier_lake": "glacier_lake",
    "year": "year",
    "area_km2": "area_km2",
    "elevation_metre": "elevation_m",
    "melting_rate_vertical_thinning": "melting_rate_text",
    "flood_cause": "flood_cause",
    "river_originating": "river_originating",
}

CANONICAL_COLUMNS = [
    "glacier_lake", "year", "area_km2", "elevation_m", "melting_rate_text",
    "melting_rate_min_km_per_year", "melting_rate_max_km_per_year", "flood_cause",
    "river_originating", "source_file", "source_row_number",
]


def _normalize_name(name: object) -> str:
    value = str(name).replace("\ufeff", "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _nullify_text(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip()
    return values.mask(values.str.lower().isin({"", "-", "--", "nan", "none", "null", "n/a", "na"}))


def _rate_bounds(value: object) -> tuple[float, float]:
    if pd.isna(value):
        return np.nan, np.nan
    numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(value))]
    if not numbers:
        return np.nan, np.nan
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers), max(numbers)


def normalize_glacier_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize glacier/lake headers into stable canonical names."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    result = df.copy()
    result.columns = [_normalize_name(c) for c in result.columns]
    result = result.rename(columns={c: _COLUMN_ALIASES[c] for c in result.columns if c in _COLUMN_ALIASES})
    if result.columns.duplicated().any():
        raise ValueError(f"Duplicate canonical columns: {result.columns[result.columns.duplicated()].tolist()}")
    return result


def clean_glacier_data(df: pd.DataFrame, source_file: str | Path) -> pd.DataFrame:
    """Clean one glacier/lake change export while preserving source measurements."""
    result = normalize_glacier_columns(df)
    required = {"glacier_lake", "year", "area_km2", "elevation_m"}
    missing = required - set(result.columns)
    if missing:
        raise ValueError(f"Missing required glacier columns: {sorted(missing)}")

    for column in result.columns:
        result[column] = _nullify_text(result[column])

    result["year"] = pd.to_numeric(result["year"], errors="coerce").round().astype("Int64")
    result["area_km2"] = pd.to_numeric(result["area_km2"], errors="coerce")
    result["elevation_m"] = pd.to_numeric(result["elevation_m"].str.replace(",", "", regex=False), errors="coerce")
    rates = result.get("melting_rate_text", pd.Series(index=result.index, dtype="string")).map(_rate_bounds)
    result["melting_rate_min_km_per_year"] = rates.map(lambda x: x[0])
    result["melting_rate_max_km_per_year"] = rates.map(lambda x: x[1])
    result["source_file"] = Path(source_file).as_posix()
    result["source_row_number"] = np.arange(1, len(result) + 1, dtype=np.int64)

    result = result.dropna(subset=["glacier_lake", "year"]).copy()
    result = result.drop_duplicates(subset=["glacier_lake", "year"], keep="first").reset_index(drop=True)
    for column in CANONICAL_COLUMNS:
        if column not in result:
            result[column] = pd.NA

    text_columns = ["glacier_lake", "melting_rate_text", "flood_cause", "river_originating", "source_file"]
    for column in text_columns:
        result[column] = result[column].astype("string")
    for column in ["area_km2", "elevation_m", "melting_rate_min_km_per_year", "melting_rate_max_km_per_year"]:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Float64")
    result["year"] = pd.to_numeric(result["year"], errors="coerce").astype("Int64")
    result["source_row_number"] = pd.to_numeric(result["source_row_number"], errors="coerce").astype("Int64")
    return result[CANONICAL_COLUMNS]
