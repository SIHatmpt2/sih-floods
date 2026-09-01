from pathlib import Path

from data_processing.past_flood_events.pipeline import DEFAULT_INPUT, DEFAULT_OUTPUT


def test_historical_pipeline_defaults_use_backend_data_tree():
    assert Path(DEFAULT_INPUT).as_posix().endswith("backend/data/raw/flood_events/flood_events.csv")
    assert Path(DEFAULT_OUTPUT).as_posix().endswith("backend/data/processed/flood_events/flood_events.geojson")
