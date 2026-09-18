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
    "slope_in_degrees": "slope_range_text",
    "river_distance_metres": "river_distance_range_text",
    "land_cover_km2_only_flash_flood_affected_area_covered": "land_cover_range_text",
    "land_cover_km_only_flash_flood_affected_area_covered": "land_cover_range_text",
    "co2_emissions_in_tons_year": "co2_emissions_tons_year",
    "co2_emissions_tons_year": "co2_emissions_tons_year",
    "forest_cover": "forest_cover_pct_text",
    "estimated_trees_km2": "tree_density_text",
    "estimated_trees_km_2": "tree_density_text",
    "estimated_trees_km2": "tree_density_text",
    "estimated_trees": "tree_density_text",
}

CANONICAL_COLUMNS = [
    "event_id", "location", "event_date", "duration_text", "temperature_change_text", "rain_3weeks_text",
    "wind_before", "wind_after", "glacier_impact", "glof_risk", "peak_waterlevel_text", "regularity",
    "return_interval_text", "snowmelt", "cloudburst", "steep_topography", "landslide", "deforestation",
    "encroachment", "major_causes", "casualties", "victims", "severity_index_text", "slope_range_text",
    "river_distance_range_text", "land_cover_range_text", "source_file", "source_row_number",
]
_NUMERIC_COLUMNS = [
    "peak_waterlevel_m", "severity_index", "slope_min_deg", "slope_max_deg", "slope_mid_deg",
    "river_distance_min_m", "river_distance_max_m", "river_distance_mid_m",
    "land_cover_min_km2", "land_cover_max_km2", "land_cover_mid_km2", "co2_emissions_tons_year",
    "forest_cover_pct", "tree_density_per_km2",
]


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


def _extract_range(value: object, upper_default: float | None = None) -> tuple[float, float]:
    if pd.isna(value):
        return np.nan, np.nan
    text = str(value).strip().lower().replace(",", "")
    numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        if upper_default is not None and "vertical" in text:
            return upper_default, upper_default
        return np.nan, np.nan
    if any(token in text for token in ("greater than", "more than", "above", "over", "greater")):
        return numbers[0], upper_default if upper_default is not None else numbers[0]
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])


def _range_columns(series: pd.Series, upper_default: float | None = None) -> pd.DataFrame:
    values = series.map(lambda value: _extract_range(value, upper_default))
    return pd.DataFrame(values.tolist(), index=series.index)


def normalize_event_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    result = df.copy()
    result.columns = [_normalize_name(c) for c in result.columns]
    result = result.rename(columns={c: _COLUMN_ALIASES[c] for c in result.columns if c in _COLUMN_ALIASES})
    if result.columns.duplicated().any():
        raise ValueError(f"Duplicate canonical columns: {result.columns[result.columns.duplicated()].tolist()}")
    return result


def clean_past_events_data(df: pd.DataFrame, source_file: str | Path) -> pd.DataFrame:
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
    slope = _range_columns(result.get("slope_range_text", pd.Series(index=result.index, dtype="string")), upper_default=90.0)
    river_distance = _range_columns(result.get("river_distance_range_text", pd.Series(index=result.index, dtype="string")))
    land_cover = _range_columns(result.get("land_cover_range_text", pd.Series(index=result.index, dtype="string")))
    result["slope_min_deg"], result["slope_max_deg"] = slope[0], slope[1]
    result["slope_mid_deg"] = slope.mean(axis=1)
    result["river_distance_min_m"], result["river_distance_max_m"] = river_distance[0], river_distance[1]
    result["river_distance_mid_m"] = river_distance.mean(axis=1)
    result["land_cover_min_km2"], result["land_cover_max_km2"] = land_cover[0], land_cover[1]
    result["land_cover_mid_km2"] = land_cover.mean(axis=1)
    result["co2_emissions_tons_year"] = result.get("co2_emissions_tons_year", pd.Series(index=result.index, dtype="string")).map(_extract_number)
    result["forest_cover_pct"] = result.get("forest_cover_pct_text", pd.Series(index=result.index, dtype="string")).map(_extract_number)
    result["tree_density_per_km2"] = result.get("tree_density_text", pd.Series(index=result.index, dtype="string")).map(_extract_number)
    result["source_file"] = Path(source_file).as_posix()
    result["source_row_number"] = np.arange(1, len(result) + 1, dtype=np.int64)
    result = result.dropna(subset=["event_id", "event_date"]).copy()
    result = result.drop_duplicates(subset=["event_id"], keep="first").reset_index(drop=True)

    for column in CANONICAL_COLUMNS:
        if column not in result:
            result[column] = pd.NA
    for column in CANONICAL_COLUMNS:
        if column not in {"event_date", "source_row_number"}:
            result[column] = result[column].astype("string")
    result["event_date"] = pd.to_datetime(result["event_date"], errors="coerce")
    result["source_row_number"] = pd.to_numeric(result["source_row_number"], errors="coerce").astype("Int64")
    for column in _NUMERIC_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Float64")
    return result[CANONICAL_COLUMNS + _NUMERIC_COLUMNS]
