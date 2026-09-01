"""
Generic feature-engineering utilities.

Dataset-specific features belong in their respective subpackages.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def safe_ratio(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """
    Calculate a ratio safely.

    Division by zero and infinite values are converted to zero.
    """
    result = (
        numerator
        / denominator.replace(
            0,
            np.nan,
        )
    )

    return (
        result
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0.0)
    )


def min_max_scale(
    series: pd.Series,
) -> pd.Series:
    """
    Min-max scale a Series to [0, 1].

    This is a general-purpose utility.

    IMPORTANT:
        Do not use this function to fit an ML scaler across the
        complete dataset. For model training, the scaler should
        be fitted only on the training split.
    """
    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(
            0.0,
            index=series.index,
        )

    if minimum == maximum:
        return pd.Series(
            0.0,
            index=series.index,
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    )


def rolling_feature(
    series: pd.Series,
    window: int,
    min_periods: int = 1,
) -> pd.Series:
    """
    Calculate a rolling mean.
    """
    return series.rolling(
        window=window,
        min_periods=min_periods,
    ).mean()


def lag_feature(
    series: pd.Series,
    periods: int = 1,
) -> pd.Series:
    """
    Calculate a lagged feature.
    """
    return series.shift(
        periods=periods
    )


def difference_feature(
    series: pd.Series,
    periods: int = 1,
) -> pd.Series:
    """
    Calculate a temporal difference.
    """
    return series.diff(
        periods=periods
    )
