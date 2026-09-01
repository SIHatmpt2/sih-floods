"""Cleaning and canonicalization for Central Water Commission rainfall data."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

_COLUMN_ALIASES = {
    "sl_no": "source_row_number",
    "station": "station",
    "agency": "agency",
    "state_lgd_code": "state_lgd_code",
    "state": "state",
    "district_lgd_code": "district_lgd_code",
    "district": "district",
    "tehsil": "tehsil",
    "block": "block",
    "village": "village",
    "river": "river",
    "basin": "basin",
    "tributary": "tributary",
    "subtributary": "subtributary",
    "subsubtributary": "subsubtributary",
    "local_river": "local_river",
    "latitude": "latitude",
    "longitude": "longitude",
    "data_acquisition_time": "observed_at",
    "telemetry_hourly_rainfall_mm": "rainfall_mm",
    "telemetry_hourly_rainfall_m_m": "rainfall_mm",
    "telemetry_hourly_rainfall": "rainfall_mm",
    "rainfall_mm": "rainfall_mm",
    "rainfall": "rainfall_mm",
}

CANONICAL_COLUMNS = [
    "station_id", "station", "agency", "state", "district", "tehsil", "block", "village",
    "river", "basin", "tributary", "subtributary", "subsubtributary", "local_river",
    "state_lgd_code", "district_lgd_code", "latitude", "longitude", "observed_at",
    "rainfall_mm", "source_file", "source_row_number",
]

_TEXT_COLUMNS = [
    "station", "agency", "state", "district", "tehsil", "block", "village", "river", "basin",
    "tributary", "subtributary", "subsubtributary", "local_river", "source_file",
]
_FLOAT_COLUMNS = ["latitude", "longitude", "rainfall_mm"]
_INT_COLUMNS = ["state_lgd_code", "district_lgd_code", "source_row_number"]


def _normalize_name(name: object) -> str:
    value = str(name).replace("\ufeff", "").strip().lower()
    for char in "()/\\-.:;":
        value = value.replace(char, " ")
    return "_".join(value.split()).strip("_")


def normalize_cwc_rainfall_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map common CWC rainfall headers to the canonical schema."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    result = df.copy()
    result.columns = [_normalize_name(c) for c in result.columns]
    result = result.rename(columns={c: _COLUMN_ALIASES[c] for c in result.columns if c in _COLUMN_ALIASES})
    if result.columns.duplicated().any():
        raise ValueError(f"Duplicate canonical columns: {result.columns[result.columns.duplicated()].tolist()}")
    return result


def _nullify_text(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip()
    return values.mask(values.str.lower().isin({"", "-", "--", "nan", "none", "null", "n/a", "na"}))


def _station_id(row: pd.Series) -> str:
    parts = [row.get("agency"), row.get("station"), row.get("state"), row.get("district"), row.get("latitude"), row.get("longitude")]
    text = "|".join("" if pd.isna(v) else str(v).strip().lower() for v in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _apply_schema(result: pd.DataFrame) -> pd.DataFrame:
    for column in CANONICAL_COLUMNS:
        if column not in result:
            result[column] = pd.NA
    for column in _TEXT_COLUMNS:
        result[column] = result[column].astype("string")
    for column in _FLOAT_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Float64")
    for column in _INT_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce").round().astype("Int64")
    result["station_id"] = result["station_id"].astype("string")
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    return result[CANONICAL_COLUMNS]


def clean_cwc_rainfall_data(df: pd.DataFrame, source_file: str | Path) -> pd.DataFrame:
    """Clean one CWC rainfall export; missing rainfall remains missing."""
    result = normalize_cwc_rainfall_columns(df)
    source = Path(source_file).as_posix()

    for column in _TEXT_COLUMNS:
        if column in result:
            result[column] = _nullify_text(result[column])
    for column in _FLOAT_COLUMNS + _INT_COLUMNS:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce")

    missing = [c for c in ("observed_at", "station", "rainfall_mm") if c not in result.columns]
    if missing:
        raise ValueError(f"Missing required CWC rainfall columns in {source_file}: {missing}")

    result["observed_at"] = pd.to_datetime(
        _nullify_text(result["observed_at"]), format="mixed", dayfirst=True, errors="coerce"
    )
    result["rainfall_mm"] = pd.to_numeric(result["rainfall_mm"], errors="coerce")
    result.loc[result["rainfall_mm"] < 0, "rainfall_mm"] = np.nan
    result.loc[~result["latitude"].between(-90, 90), "latitude"] = np.nan
    result.loc[~result["longitude"].between(-180, 180), "longitude"] = np.nan
    result["station_id"] = result.apply(_station_id, axis=1)
    result["source_file"] = source

    invalid_dates = int(result["observed_at"].isna().sum())
    missing_stations = int(result["station"].isna().sum())
    invalid_rainfall = int(result["rainfall_mm"].isna().sum())
    if invalid_dates or missing_stations or invalid_rainfall:
        LOGGER.warning(
            "%s: invalid timestamps=%d, missing stations=%d, missing/invalid rainfall=%d",
            source, invalid_dates, missing_stations, invalid_rainfall,
        )

    result = result.dropna(subset=["observed_at", "station"]).copy()
    before = len(result)
    result = result.sort_values(["station_id", "observed_at"], kind="stable")
    result = result.drop_duplicates(["station_id", "observed_at"], keep="first").reset_index(drop=True)
    LOGGER.info("Cleaned %s: %d rows retained, %d duplicates removed", source, len(result), before - len(result))
    return _apply_schema(result)
