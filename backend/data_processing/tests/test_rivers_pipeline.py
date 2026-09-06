from pathlib import Path

import pandas as pd

from data_processing.rivers.clean import clean_cwc_data
from data_processing.rivers.pipeline import DEFAULT_OUTPUT_DIR, DEFAULT_RAW_DIR, discover_csv_files, process_file, run_pipeline


def test_default_paths_are_owned_by_risk_app():
    backend_root = Path(__file__).resolve().parents[2]
    expected = backend_root / "apps" / "risk" / "data"
    assert DEFAULT_RAW_DIR == expected / "raw" / "river_data" / "cwc"
    assert DEFAULT_OUTPUT_DIR == expected / "processed" / "river_data" / "parquet"


def _write_fixture(path: Path, station: str, values: list[float], discharge: list[float] | None = None) -> None:
    rows = []
    for hour, value in enumerate(values):
        row = {
            "Station": station,
            "Agency": "CWC",
            "State": "Assam",
            "District": "D",
            "Latitude": 26.5,
            "Longitude": 92.1,
            "Data Acquisition Time": f"07-05-2026 {hour:02d}:00",
            "River Water Level Telemetry Hourly (meter)": value,
        }
        if discharge is not None:
            row["Telemetry Hourly River Water Discharge (m3/sec)"] = discharge[hour]
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def test_discharge_header_is_normalized_and_numeric():
    frame = pd.DataFrame({
        "Station": ["A"],
        "Agency": ["CWC"],
        "State": ["Assam"],
        "District": ["D"],
        "Latitude": [26.5],
        "Longitude": [92.1],
        "Data Acquisition Time": ["07-05-2026 00:00"],
        "Telemetry Hourly River Water Discharge (m3/sec)": ["12.5"],
    })
    cleaned = clean_cwc_data(frame, "input.csv")
    assert cleaned["discharge_cumecs"].notna().all()
    assert cleaned["discharge_cumecs"].iloc[0] == 12.5


def test_process_file_writes_parquet():
    source = Path("input.csv")
    output = Path("parquet")
    # Existing test intentionally exercises the historical water-level fixture.
    _write_fixture(source, "A", [1.0, 2.0])
    result = process_file(source, output)
    assert result.exists()
    frame = pd.read_parquet(result)
    assert len(frame) == 2
    assert "station_id" in frame.columns
    assert "water_level_lag_1h" in frame.columns


def test_process_file_preserves_discharge_features(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "parquet"
    _write_fixture(source, "A", [1.0, 2.0, 3.0], [10.0, 20.0, 30.0])
    result = process_file(source, output)
    frame = pd.read_parquet(result)
    assert frame["discharge_cumecs"].notna().all()
    assert frame["discharge_cumecs"].tolist() == [10.0, 20.0, 30.0]
    assert frame["discharge_delta_1h"].iloc[1] == 10.0
    assert frame["discharge_lag_1h"].iloc[1] == 10.0


def test_discovery_is_recursive_and_sorted(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "a").mkdir()
    _write_fixture(tmp_path / "b" / "z.csv", "B", [1.0])
    _write_fixture(tmp_path / "a" / "a.csv", "A", [1.0])
    assert [p.name for p in discover_csv_files(tmp_path)] == ["a.csv", "z.csv"]


def test_run_pipeline_creates_per_file_and_combined_outputs(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _write_fixture(raw / "a.csv", "A", [1.0, 2.0])
    _write_fixture(raw / "b.csv", "B", [3.0, 4.0])
    outputs = run_pipeline(raw_dir=raw, output_dir=tmp_path / "out", combine=True)
    assert len(outputs["per_file"]) == 2
    assert outputs["combined"].exists()
    combined = pd.read_parquet(outputs["combined"])
    assert len(combined) == 4
    assert set(combined["station"].dropna()) == {"A", "B"}
