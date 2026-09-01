from pathlib import Path

import pandas as pd

from data_processing.rivers.pipeline import discover_csv_files, process_file, run_pipeline


def _write_fixture(path: Path, station: str, values: list[float]) -> None:
    rows = []
    for hour, value in enumerate(values):
        rows.append(
            {
                "Station": station,
                "Agency": "CWC",
                "State": "Assam",
                "District": "D",
                "Latitude": 26.5,
                "Longitude": 92.1,
                "Data Acquisition Time": f"07-05-2026 {hour:02d}:00",
                "River Water Level Telemetry Hourly (meter)": value,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def test_process_file_writes_parquet(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "parquet"
    _write_fixture(source, "A", [1.0, 2.0])

    result = process_file(source, output)
    assert result.exists()
    frame = pd.read_parquet(result)
    assert len(frame) == 2
    assert "station_id" in frame.columns
    assert "water_level_lag_1h" in frame.columns


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
