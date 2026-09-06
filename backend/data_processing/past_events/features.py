"""Features for historical flood-event records."""

from __future__ import annotations

import pandas as pd

NON_MODEL_COLUMNS = {
    "event_id", "location", "event_date", "duration_text", "temperature_change_text",
    "rain_3weeks_text", "wind_before", "wind_after", "glacier_impact", "glof_risk",
    "peak_waterlevel_text", "regularity", "return_interval_text", "snowmelt", "cloudburst",
    "steep_topography", "landslide", "deforestation", "encroachment", "major_causes",
    "casualties", "victims", "severity_index_text", "source_file", "source_row_number",
}


def add_event_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic calendar and event-severity features without altering source fields."""
    if "event_date" not in df.columns:
        raise ValueError("Missing required event_date column")
    result = df.copy()
    result["event_date"] = pd.to_datetime(result["event_date"], errors="coerce")
    result["event_year"] = result["event_date"].dt.year.astype("Int16")
    result["event_month"] = result["event_date"].dt.month.astype("Int8")
    result["event_day_of_year"] = result["event_date"].dt.dayofyear.astype("Int16")
    result["event_day_of_week"] = result["event_date"].dt.dayofweek.astype("Int8")
    result["is_monsoon"] = result["event_month"].isin([6, 7, 8, 9]).astype("Int8")
    result["is_glof_related"] = result["glof_risk"].fillna("").str.lower().str.contains("high|critical|probable|suspected", regex=True).astype("Int8")
    result["is_glacier_impact_reported"] = result["glacier_impact"].fillna("").str.lower().ne("no").astype("Int8")
    return result


def select_numeric_features(df: pd.DataFrame, target_column: str | None = None) -> pd.DataFrame:
    """Return numeric model features while excluding identifiers and optional target."""
    excluded = NON_MODEL_COLUMNS | ({target_column} if target_column else set())
    numeric = df.select_dtypes(include=["number", "bool"]).copy()
    columns = [c for c in numeric.columns if c not in excluded]
    if not columns:
        raise ValueError("No numeric flood-event features found")
    return numeric[columns]
