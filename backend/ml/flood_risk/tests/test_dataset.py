"""Tests for the V1 supervised training-table schema and leakage-safe labels."""

import pandas as pd

from ml.flood_risk.dataset import TARGET_COLUMN, build_training_table


def test_build_training_table_has_stable_schema_and_future_label():
    timestamps = pd.date_range("2025-07-01", periods=4, freq="h")
    river = pd.DataFrame({
        "station_id": ["river-1"] * 4,
        "station": ["Station A"] * 4,
        "state": ["Himachal Pradesh"] * 4,
        "district": ["Kinnaur"] * 4,
        "river": ["Sutlej"] * 4,
        "basin": ["Indus"] * 4,
        "latitude": [31.0] * 4,
        "longitude": [78.0] * 4,
        "observed_at": timestamps,
        "water_level_m": [3.0, 3.5, 4.0, 4.5],
        "discharge_cumecs": [100, 110, 120, 130],
    })
    rainfall = pd.DataFrame({
        "station_id": ["rain-1"] * 4,
        "station": ["Rain A"] * 4,
        "latitude": [31.01] * 4,
        "longitude": [78.01] * 4,
        "observed_at": timestamps,
        "rainfall_mm": [5.0, 10.0, 20.0, 30.0],
    })
    events = pd.DataFrame({
        "event_date": [pd.Timestamp("2025-07-03")],
        "location": ["Kinnaur"],
        "severity_index": [8.0],
        "glof_risk": ["NO"],
    })

    result = build_training_table(river, rainfall, events, rainfall_max_distance_km=50)

    assert TARGET_COLUMN in result.columns
    assert "rainfall_24h" in result.columns
    assert "water_level_lag_1h" in result.columns
    assert "flood_count_1y" in result.columns
    assert list(result["flood_next_72h"]) == [1, 1, 1, 1]
    assert result["station_id"].isna().sum() == 0
