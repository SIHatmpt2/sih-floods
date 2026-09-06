"""Tests for the V1 supervised training-table schema and pipeline."""

from pathlib import Path

import pandas as pd

from ml.flood_risk.dataset import (
    TARGET_COLUMN,
    build_training_table,
    build_training_dataset,
)


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


def test_build_training_dataset_loads_processed_inputs_and_writes_output(tmp_path: Path):
    data_root = tmp_path / "data"
    processed = data_root / "processed"
    for directory in (
        processed / "river_data" / "parquet",
        processed / "rainfall" / "parquet",
        processed / "past_events" / "parquet",
    ):
        directory.mkdir(parents=True)

    timestamps = pd.date_range("2025-07-01", periods=4, freq="h")
    pd.DataFrame({
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
    }).to_parquet(processed / "river_data" / "parquet" / "river_observations.parquet", index=False)
    pd.DataFrame({
        "station_id": ["rain-1"] * 4,
        "station": ["Rain A"] * 4,
        "latitude": [31.01] * 4,
        "longitude": [78.01] * 4,
        "observed_at": timestamps,
        "rainfall_mm": [5.0, 10.0, 20.0, 30.0],
    }).to_parquet(processed / "rainfall" / "parquet" / "rainfall_observations.parquet", index=False)
    pd.DataFrame({
        "event_date": [pd.Timestamp("2025-07-03")],
        "location": ["Kinnaur"],
        "severity_index": [8.0],
        "glof_risk": ["NO"],
    }).to_parquet(processed / "past_events" / "parquet" / "past_flood_events.parquet", index=False)

    output = build_training_dataset(data_root=data_root)

    assert output == data_root / "processed" / "training_v1.parquet"
    assert output.exists()
    written = pd.read_parquet(output)
    assert len(written) == 4
    assert TARGET_COLUMN in written.columns
