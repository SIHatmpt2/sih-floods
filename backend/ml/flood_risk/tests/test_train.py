"""Tests for the V1 XGBoost training helpers."""

import numpy as np
import pandas as pd

from ml.flood_risk.dataset import TARGET_COLUMN
from ml.flood_risk.train import chronological_split, load_training_rows, tune_threshold


def test_chronological_split_preserves_time_order():
    df = pd.DataFrame(
        {
            "station_id": ["a"] * 5,
            "observed_at": pd.date_range("2025-01-01", periods=5, freq="h"),
            TARGET_COLUMN: [0, 1, 0, 0, 1],
            "rainfall_24h": [1, 2, 3, 4, 5],
            "rainfall_48h": [1, 2, 3, 4, 5],
            "rainfall_72h": [1, 2, 3, 4, 5],
        }
    )
    train, test = chronological_split(df, test_fraction=0.4)
    assert train.observed_at.max() < test.observed_at.min()
    assert len(train) == 3
    assert len(test) == 2


def test_nested_chronological_split_keeps_final_test_future():
    df = pd.DataFrame(
        {
            "station_id": ["a"] * 10,
            "observed_at": pd.date_range("2025-01-01", periods=10, freq="h"),
            TARGET_COLUMN: [0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
        }
    )
    train_val, test = chronological_split(df, test_fraction=0.2)
    train, validation = chronological_split(train_val, test_fraction=0.25)
    assert train.observed_at.max() < validation.observed_at.min()
    assert validation.observed_at.max() < test.observed_at.min()
    assert len(train) == 6
    assert len(validation) == 2
    assert len(test) == 2


def test_load_training_rows_requires_core_rainfall(tmp_path):
    path = tmp_path / "training.parquet"
    df = pd.DataFrame(
        {
            "station_id": ["a", "a", "b"],
            "observed_at": pd.date_range("2025-01-01", periods=3, freq="h"),
            TARGET_COLUMN: [0, 1, 0],
            "rainfall_24h": [1.0, 2.0, None],
            "rainfall_48h": [1.0, 2.0, 3.0],
            "rainfall_72h": [1.0, 2.0, 3.0],
        }
    )
    df.to_parquet(path, index=False)
    loaded = load_training_rows(path)
    assert len(loaded) == 2
    assert loaded[TARGET_COLUMN].tolist() == [0, 1]


def test_tune_threshold_can_select_probabilities_below_one_percent():
    class DummyModel:
        def predict_proba(self, x):
            return np.column_stack(
                [
                    1.0 - np.array([0.00002, 0.00004, 0.00006, 0.00008]),
                    np.array([0.00002, 0.00004, 0.00006, 0.00008]),
                ]
            )

    validation = pd.DataFrame(
        {
            "rainfall_24h": [1, 2, 3, 4],
            TARGET_COLUMN: [0, 1, 0, 1],
        }
    )
    threshold = tune_threshold(DummyModel(), validation, ["rainfall_24h"])

    assert 0.00004 <= threshold <= 0.00006
