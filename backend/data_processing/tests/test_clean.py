import numpy as np
import pandas as pd
import pytest

from data_processing.clean import coerce_datetime, fill_numeric_median, normalize_column_names


def test_normalize_column_names_rejects_collisions():
    with pytest.raises(ValueError, match="Duplicate column"):
        normalize_column_names(pd.DataFrame({"A-B": [1], "a b": [2]}))


def test_all_missing_median_stays_missing():
    result = fill_numeric_median(pd.DataFrame({"x": [np.nan, np.nan]}), ["x"])
    assert result["x"].isna().all()


def test_coerce_datetime_accepts_mixed_values():
    result = coerce_datetime(pd.DataFrame({"d": ["07-05-2026 20:00", "bad"]}), ["d"], dayfirst=True)
    assert result.loc[0, "d"] == pd.Timestamp("2026-05-07 20:00")
    assert pd.isna(result.loc[1, "d"])
