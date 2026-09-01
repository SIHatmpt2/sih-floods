"""
Cleaning logic for historical flood-event records.
"""

from __future__ import annotations

import logging

import pandas as pd

from ..clean import (
    coerce_datetime,
    coerce_numeric,
    fill_numeric_median,
    fill_numeric_zero,
    fill_text,
    normalize_column_names,
    remove_duplicates,
    validate_non_negative,
)

LOGGER = logging.getLogger(__name__)


REQUIRED_COLUMNS = {
    "event_id",
    "location",
    "date",
}


NUMERIC_COLUMNS = [
    "temp_change",
    "rain_3weeks",
    "wind_before",
    "wind_after",
    "regularity",
    "interval",
    "snowmelt",
    "casualties",
    "victims",
    "peak_waterlevel",
    "severity_index",
]


ZERO_FILL_COLUMNS = [
    "casualties",
    "victims",
]


BINARY_COLUMNS = [
    "cloudburst",
    "steep_topography",
    "landslide",
    "deforestation",
    "encroachment",
]


TEXT_COLUMNS = [
    "location",
    "glacier_impact",
    "glof_risk",
    "major_causes",
    "time_period",
]


COLUMN_ALIASES = {
    "eventid": "event_id",
    "event_id": "event_id",

    "event_date": "date",
    "eventdate": "date",

    "coordinates": "location",
    "coordinate": "location",

    "temperature_change": "temp_change",
    "temperature_delta": "temp_change",

    "rainfall_3weeks": "rain_3weeks",
    "rainfall_21_days": "rain_3weeks",
    "rain_21_days": "rain_3weeks",

    "wind_speed_before": "wind_before",
    "wind_speed_after": "wind_after",

    "snow_melt": "snowmelt",

    "cloud_burst": "cloudburst",
    "steep_terrain": "steep_topography",
    "steep_slope": "steep_topography",

    "encroachment": "encroachment",
    "encroachment_flag": "encroachment",
    "enroachment": "encroachment",

    "deaths": "casualties",
    "fatalities": "casualties",

    "affected_people": "victims",

    "peak_water_level": "peak_waterlevel",

    "severity": "severity_index",
    "severity_score": "severity_index",
}


def _apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply known alternative column names.

    Raises
    ------
    ValueError
        If alias mapping produces duplicate column names.
    """
    result = df.copy()

    rename_map = {
        column: COLUMN_ALIASES[column]
        for column in result.columns
        if column in COLUMN_ALIASES
    }

    result = result.rename(columns=rename_map)

    if result.columns.duplicated().any():
        duplicated = (
            result.columns[result.columns.duplicated()]
            .tolist()
        )

        raise ValueError(
            "Duplicate columns after alias mapping: "
            f"{duplicated}"
        )

    return result


def _normalize_binary(series: pd.Series) -> pd.Series:
    """
    Convert common Boolean/binary representations to 0/1.

    Recognized values include:

    - true / false
    - yes / no
    - y / n
    - present / absent
    - 1 / 0

    Unknown values become NaN.
    """
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    numeric = numeric.where(
        numeric.isin([0, 1])
    )

    text = (
        series
        .astype("string")
        .str.strip()
        .str.lower()
    )

    mapping = {
        "true": 1,
        "false": 0,
        "yes": 1,
        "no": 0,
        "y": 1,
        "n": 0,
        "present": 1,
        "absent": 0,
        "1": 1,
        "0": 0,
    }

    return numeric.fillna(text.map(mapping))


def _normalize_event_id(series: pd.Series) -> pd.Series:
    """
    Normalize event identifiers without unnecessarily changing
    their semantic value.
    """
    result = (
        series
        .astype("string")
        .str.strip()
    )

    # Convert values such as "123.0" to "123" when they are
    # clearly integer-like numeric identifiers.
    numeric = pd.to_numeric(
        result,
        errors="coerce",
    )

    integer_like = (
        numeric.notna()
        & (numeric % 1 == 0)
    )

    result.loc[integer_like] = (
        numeric.loc[integer_like]
        .astype("Int64")
        .astype("string")
    )

    return result


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate historical flood-event data.

    Processing includes:

    1. Validate input.
    2. Normalize column names.
    3. Apply known schema aliases.
    4. Validate required columns.
    5. Convert dates.
    6. Remove records with invalid dates.
    7. Convert numeric attributes.
    8. Normalize binary fields.
    9. Impute missing numeric values.
    10. Fill missing text values.
    11. Validate non-negative fields.
    12. Normalize and validate Event_ID.
    13. Remove duplicate Event_ID records.
    14. Return a clean, re-indexed DataFrame.

    Parameters
    ----------
    df:
        Raw flood-event DataFrame.

    Returns
    -------
    pandas.DataFrame
        Cleaned flood-event data.

    Raises
    ------
    TypeError
        If df is not a pandas DataFrame.

    ValueError
        If the input is empty, required columns are missing,
        invalid Event_ID values are found, or no records remain.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "df must be a pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Flood-event dataset is empty."
        )

    # ---------------------------------------------------------
    # Normalize schema
    # ---------------------------------------------------------

    result = normalize_column_names(df)

    result = _apply_column_aliases(result)

    missing_columns = (
        REQUIRED_COLUMNS
        - set(result.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required flood-event columns: "
            f"{sorted(missing_columns)}"
        )

    # ---------------------------------------------------------
    # Date
    # ---------------------------------------------------------

    result = coerce_datetime(
        result,
        ["date"],
    )

    invalid_dates = result["date"].isna()

    if invalid_dates.any():
        dropped = int(invalid_dates.sum())

        LOGGER.warning(
            "Dropping %d records with invalid dates.",
            dropped,
        )

        result = result.loc[
            ~invalid_dates
        ].copy()

    if result.empty:
        raise ValueError(
            "No records remain after removing invalid dates."
        )

    # ---------------------------------------------------------
    # Numeric columns
    # ---------------------------------------------------------

    numeric_columns = [
        column
        for column in NUMERIC_COLUMNS
        if column in result.columns
    ]

    result = coerce_numeric(
        result,
        numeric_columns,
    )

    # ---------------------------------------------------------
    # Binary columns
    # ---------------------------------------------------------

    for column in BINARY_COLUMNS:
        if column not in result.columns:
            continue

        result[column] = (
            _normalize_binary(result[column])
            .fillna(0)
            .astype("int8")
        )

    # ---------------------------------------------------------
    # Missing numeric values
    # ---------------------------------------------------------

    median_columns = [
        column
        for column in numeric_columns
        if column not in ZERO_FILL_COLUMNS
    ]

    median_columns = [
        column
        for column in median_columns
        if column in result.columns
    ]

    if median_columns:
        result = fill_numeric_median(
            result,
            median_columns,
        )

    zero_columns = [
        column
        for column in ZERO_FILL_COLUMNS
        if column in result.columns
    ]

    if zero_columns:
        result = fill_numeric_zero(
            result,
            zero_columns,
        )

    # ---------------------------------------------------------
    # Missing text values
    # ---------------------------------------------------------

    text_columns = [
        column
        for column in TEXT_COLUMNS
        if column in result.columns
    ]

    if text_columns:
        result = fill_text(
            result,
            text_columns,
            default="unknown",
        )

    # ---------------------------------------------------------
    # Non-negative validation
    # ---------------------------------------------------------

    non_negative_columns = [
        "rain_3weeks",
        "interval",
        "snowmelt",
        "casualties",
        "victims",
        "peak_waterlevel",
    ]

    non_negative_columns = [
        column
        for column in non_negative_columns
        if column in result.columns
    ]

    if non_negative_columns:
        validate_non_negative(
            result,
            non_negative_columns,
        )

    # ---------------------------------------------------------
    # Event identifier
    # ---------------------------------------------------------

    result["event_id"] = _normalize_event_id(
        result["event_id"]
    )

    missing_event_ids = (
        result["event_id"].isna()
        | result["event_id"].eq("")
    )

    if missing_event_ids.any():
        raise ValueError(
            "Found "
            f"{int(missing_event_ids.sum())} records "
            "with missing Event_ID."
        )

    # ---------------------------------------------------------
    # Deduplication
    # ---------------------------------------------------------

    before = len(result)

    result = remove_duplicates(
        result,
        ["event_id"],
    )

    removed = before - len(result)

    LOGGER.info(
        "Removed %d duplicate event records.",
        removed,
    )

    if result.empty:
        raise ValueError(
            "No records remain after cleaning."
        )

    # ---------------------------------------------------------
    # Final cleanup
    # ---------------------------------------------------------

    return result.reset_index(drop=True)
