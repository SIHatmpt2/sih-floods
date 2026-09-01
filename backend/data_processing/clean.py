"""
Generic DataFrame cleaning utilities.

This module contains reusable DataFrame transformations and validations.
Dataset-specific business rules should not be implemented here.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


_NULL_TEXT_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
}


def normalize_column_name(name: object) -> str:
    """Convert a column name to lowercase snake_case."""
    value = str(name).strip().replace("\ufeff", "").lower()

    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize all DataFrame column names.

    Raises
    ------
    ValueError
        If normalization produces duplicate or empty column names.
    """
    result = df.copy()

    normalized_columns = [
        normalize_column_name(column)
        for column in result.columns
    ]

    empty_columns = [
        original
        for original, normalized in zip(
            result.columns,
            normalized_columns,
        )
        if not normalized
    ]

    if empty_columns:
        raise ValueError(
            "Column names cannot be empty after normalization: "
            f"{empty_columns}"
        )

    result.columns = normalized_columns

    duplicated = result.columns[
        result.columns.duplicated()
    ].tolist()

    if duplicated:
        raise ValueError(
            "Duplicate column names after normalization: "
            f"{sorted(set(duplicated))}"
        )

    return result


def coerce_numeric(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Convert specified columns to numeric values.

    Invalid values are converted to NaN.
    Missing columns are ignored.
    """
    result = df.copy()

    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result


def coerce_datetime(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Convert specified columns to pandas datetime.

    Invalid values are converted to NaT.
    Missing columns are ignored.
    """
    result = df.copy()

    for column in columns:
        if column in result.columns:
            result[column] = pd.to_datetime(
                result[column],
                errors="coerce",
            )

    return result


def fill_numeric_median(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Fill missing numeric values with each column's median.

    Columns containing no valid numeric values use 0.0 as a fallback.
    Missing columns are ignored.
    """
    result = df.copy()

    for column in columns:
        if column not in result.columns:
            continue

        values = pd.to_numeric(
            result[column],
            errors="coerce",
        )

        median = values.median()

        if pd.isna(median):
            median = 0.0

        result[column] = values.fillna(median)

    return result


def fill_numeric_zero(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Fill missing numeric values with zero.

    Missing columns are ignored.
    """
    result = df.copy()

    for column in columns:
        if column in result.columns:
            result[column] = result[column].fillna(0)

    return result


def fill_text(
    df: pd.DataFrame,
    columns: list[str],
    default: str = "unknown",
) -> pd.DataFrame:
    """
    Fill missing text or categorical values.

    Empty strings and common null-like strings are treated as missing.

    Missing columns are ignored.
    """
    result = df.copy()

    for column in columns:
        if column not in result.columns:
            continue

        values = (
            result[column]
            .astype("string")
            .str.strip()
        )

        null_mask = values.str.lower().isin(
            _NULL_TEXT_VALUES
        )

        values = values.mask(null_mask)

        result[column] = values.fillna(default)

    return result


def validate_non_negative(
    df: pd.DataFrame,
    columns: list[str],
) -> None:
    """
    Validate that specified numeric fields contain no negative values.

    Invalid or non-numeric values are ignored by this validation.

    Raises
    ------
    ValueError
        If one or more negative values are found.
    """
    violations: dict[str, int] = {}

    for column in columns:
        if column not in df.columns:
            continue

        values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid = values.notna() & values.lt(0)
        count = int(invalid.sum())

        if count:
            violations[column] = count

    if violations:
        details = ", ".join(
            f"{column}={count}"
            for column, count in violations.items()
        )

        raise ValueError(
            f"Negative values detected: {details}"
        )


def remove_duplicates(
    df: pd.DataFrame,
    subset: list[str],
) -> pd.DataFrame:
    """
    Remove duplicate records using specified columns.

    Raises
    ------
    ValueError
        If one or more columns in ``subset`` are missing.
    """
    result = df.copy()

    missing_columns = [
        column
        for column in subset
        if column not in result.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns for duplicate removal: "
            f"{missing_columns}"
        )

    return (
        result
        .drop_duplicates(
            subset=subset,
            keep="first",
        )
        .reset_index(drop=True)
    )


def replace_infinite_values(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Replace positive and negative infinity with NaN.
    """
    result = df.copy()

    numeric_columns = result.select_dtypes(
        include=np.number,
    ).columns

    if len(numeric_columns):
        result[numeric_columns] = result[
            numeric_columns
        ].replace(
            [np.inf, -np.inf],
            np.nan,
        )

    return result
