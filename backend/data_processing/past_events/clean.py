"""Cleaning and canonicalization for historical flood-event data."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

_COLUMN_ALIASES = {
    "event_id": "event_id", "location": "location", "date": "event_date", "time_period": "duration_text",
    "temp_change": "temperature_change_text", "rain_3weeks": "rain_3weeks_text", "wind_before": "wind_before",
    "wind_after": "wind_after", "glacier_impact": "glacier_impact", "glof_risk": "glof_risk",
    "peak_waterlevel": "peak_waterlevel_text", "regularity": "regularity", "interval": "return_interval_text",
    "snowmelt": "snowmelt", "cloudburst": "cloudburst", "steep_topography": "steep_topography",
    "landslide": "landslide", "deforestation": "deforestation", "enroachment": "encroachment",
    "encroachment": "encroachment", "major_causes": "major_causes", "casualties": "casualties",
    "victims": "victims", "severity_index": "severity_index_text",
}

CANONICAL_COLUMNS = [
    "event_id", "location", "event_date", "duration_text", "temperature_change_text", "rain_3weeks_text",
    "wind_before", "wind_after", "glacier_impact", "glof_risk", "peak_waterlevel_text", "regularity",
    "return_interval_text", "snowmelt", "cloudburst", "steep_topography", "landslide", "deforestation",
    "encroachment", "major_causes", "casualties", "victims", "severity_index_text", "source_file",
    "source_row_number",
]
_NUMERIC_COLUMNS = ["peak_waterlevel_m", "severity_index"]


def _normalize_name(name: object) -> str:
    value = str(name).replace("\ufeff", "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _nullify_text(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip()
    return values.mask(values.str.lower().isin({"", "-", "--", "nan", "none", "null", "n/a", "na"}))


def _extract_number(value: object) -> float:
    if pd.isna(value):
        return np.nan
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group()) if match else np.nan


def normalize_event_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize historical flood-event headers into stable canonical names."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    result = df.copy()
    result.columns = [_normalize_name(c) for c in result.columns]
    result = result.rename(columns={c: _COLUMN_ALIASES[c] for c in result.columns if c in _COLUMN_ALIASES})
    if result.columns.duplicated().any():
        raise ValueError(f"Duplicate canonical columns: {result.columns[result.columns.duplicated()].tolist()}")
    return result


def clean_past_events_data(df: pd.DataFrame, source_file: str | Path) -> pd.DataFrame:
    """Clean one historical flood-event export while retaining source attributes."""
    result = normalize_event_columns(df)
    required = {"event_id", "location", "event_date"}
    missing = required - set(result.columns)
    if missing:
        raise ValueError(f"Missing required flood-event columns: {sorted(missing)}")
    for column in result.columns:
        result[column] = _nullify_text(result[column])

    result["event_date"] = pd.to_datetime(result["event_date"], format="mixed", dayfirst=True, errors="coerce")
    result["peak_waterlevel_m"] = result.get("peak_waterlevel_text", pd.Series(index=result.index, dtype="string")).map(_extract_number)
    result["severity_index"] = result.get("severity_index_text", pd.Series(index=result.index, dtype="string")).map(_extract_number)
    result["source_file"] = Path(source_file).as_posix()
    result["source_row_number"] = np.arange(1, len(result) + 1, dtype=np.int64)
    result = result.dropna(subset=["event_id", "event_date"]).copy()
    result = result.drop_duplicates(subset=["event_id"], keep="first").reset_index(drop=True)

    for column in CANONICAL_COLUMNS:
        if column not in result:
            result[column] = pd.NA
    for column in ["event_id", "location", "duration_text", "temperature_change_text", "rain_3weeks_text", "wind_before", "wind_after", "glacier_impact", "glof_risk", "peak_waterlevel_text", "regularity", "return_interval_text", "snowmelt", "cloudburst", "steep_topography", "landslide", "deforestation", "encroachment", "major_causes", "casualties", "victims", "severity_index_text", "source_file"]:
        result[column] = result[column].astype("string")
    result["event_date"] = pd.to_datetime(result["event_date"], errors="coerce")
    result["source_row_number"] = pd.to_numeric(result["source_row_number"], errors="coerce").astype("Int64")
    result["peak_waterlevel_m"] = pd.to_numeric(result["peak_waterlevel_m"], errors="coerce").astype("Float64")
    result["severity_index"] = pd.to_numeric(result["severity_index"], errors="coerce").astype("Float64")
    return result[CANONICAL_COLUMNS + _NUMERIC_COLUMNS]
