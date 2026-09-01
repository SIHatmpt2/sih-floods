"""Generic DataFrame cleaning utilities."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

_NULL_TEXT_VALUES = {"", "nan", "none", "null", "n/a", "na", "-", "--"}


def normalize_column_name(name: object) -> str:
    """Convert a column name to lowercase snake_case."""
    value = str(name).strip().replace("\ufeff", "").lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize all DataFrame column names and reject collisions."""
    result = df.copy()
    normalized = [normalize_column_name(column) for column in result.columns]
    empty = [original for original, name in zip(result.columns, normalized) if not name]
    if empty:
        raise ValueError(f"Column names cannot be empty after normalization: {empty}")
    result.columns = normalized
    duplicated = result.columns[result.columns.duplicated()].tolist()
    if duplicated:
        raise ValueError(f"Duplicate column names after normalization: {sorted(set(duplicated))}")
    return result


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Convert specified columns to numeric values; invalid values become NaN."""
    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def coerce_datetime(df: pd.DataFrame, columns: list[str], formats: list[str] | None = None, dayfirst: bool = False) -> pd.DataFrame:
    """Convert specified columns to datetime; invalid values become NaT.

    ``formats`` may be supplied for sources with known mixed timestamp formats.
    """
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            continue
        values = result[column]
        if formats:
            parsed = pd.Series(pd.NaT, index=result.index, dtype="datetime64[ns]")
            for fmt in formats:
                parsed = parsed.fillna(pd.to_datetime(values, format=fmt, errors="coerce", dayfirst=dayfirst))
            result[column] = parsed
        else:
            result[column] = pd.to_datetime(values, errors="coerce", dayfirst=dayfirst, format="mixed")
    return result


def fill_numeric_median(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Fill missing numeric values with each column median; all-missing stays NaN."""
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            continue
        values = pd.to_numeric(result[column], errors="coerce")
        median = values.median()
        result[column] = values.fillna(median) if pd.notna(median) else values
    return result


def fill_numeric_zero(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Explicitly fill missing numeric values with zero."""
    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = result[column].fillna(0)
    return result


def fill_text(df: pd.DataFrame, columns: list[str], default: str = "unknown") -> pd.DataFrame:
    """Fill missing and common null-like text values with ``default``."""
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            continue
        values = result[column].astype("string").str.strip()
        values = values.mask(values.str.lower().isin(_NULL_TEXT_VALUES))
        result[column] = values.fillna(default)
    return result


def validate_non_negative(df: pd.DataFrame, columns: list[str]) -> None:
    """Raise ValueError when any specified numeric field is negative."""
    violations = {}
    for column in columns:
        if column not in df.columns:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        count = int((values.notna() & values.lt(0)).sum())
        if count:
            violations[column] = count
    if violations:
        raise ValueError("Negative values detected: " + ", ".join(f"{c}={n}" for c, n in violations.items()))


def remove_duplicates(df: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    """Remove duplicate records using required subset columns."""
    result = df.copy()
    missing = [column for column in subset if column not in result.columns]
    if missing:
        raise ValueError(f"Missing columns for duplicate removal: {missing}")
    return result.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)


def replace_infinite_values(df: pd.DataFrame) -> pd.DataFrame:
    """Replace positive and negative infinity in numeric columns with NaN."""
    result = df.copy()
    numeric = result.select_dtypes(include=np.number).columns
    if len(numeric):
        result[numeric] = result[numeric].replace([np.inf, -np.inf], np.nan)
    return result
