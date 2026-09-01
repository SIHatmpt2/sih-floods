"""CWC river CSV -> canonical Parquet pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .clean import clean_cwc_data
from .features import add_river_features

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW_DIR = PROJECT_ROOT / "backend" / "data" / "raw" / "river_data" / "cwc"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "backend" / "data" / "processed" / "river_data" / "parquet"


def discover_csv_files(raw_dir: Path) -> list[Path]:
    """Recursively discover CSV inputs in deterministic order."""
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw river-data directory does not exist: {raw_dir}")
    if not raw_dir.is_dir():
        raise NotADirectoryError(raw_dir)
    return sorted((p for p in raw_dir.rglob("*.csv") if p.is_file()), key=lambda p: p.as_posix().lower())


def _output_name(input_path: Path) -> str:
    return f"{input_path.stem.lower().replace(' ', '_')}.parquet"


def process_file(input_path: Path, output_dir: Path) -> Path:
    """Read, clean, feature-engineer and write one CWC CSV as compressed Parquet."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(input_path, low_memory=False)
    cleaned = clean_cwc_data(frame, input_path)

    # Both measurement families are emitted for a stable schema. Current CWC
    # files primarily contain hourly water-level telemetry; discharge columns
    # remain nullable until a source actually supplies discharge observations.
    featured = add_river_features(cleaned, "water_level_m")
    discharge_features = add_river_features(cleaned, "discharge_cumecs")
    base = set(featured.columns)
    for column in discharge_features.columns:
        if column not in base:
            featured[column] = discharge_features[column].to_numpy()

    output_path = output_dir / _output_name(input_path)
    featured.to_parquet(output_path, engine="pyarrow", compression="zstd", index=False)
    LOGGER.info("Wrote %d rows to %s", len(featured), output_path)
    return output_path


def _write_combined(parquet_files: list[Path], output_path: Path) -> Path:
    """Combine Parquet fragments while retaining one source table in memory at a time."""
    import pyarrow.parquet as pq

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    try:
        for path in parquet_files:
            table = pq.read_table(path)
            if writer is None:
                writer = pq.ParquetWriter(output_path, table.schema, compression="zstd")
            elif table.schema != writer.schema:
                raise ValueError(f"Incompatible Parquet schema in {path}; canonical pipeline should produce identical schemas")
            writer.write_table(table)
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        raise ValueError("No Parquet files were available for combined output")
    return output_path


def run_pipeline(raw_dir: Path | None = None, output_dir: Path | None = None, combine: bool = True) -> dict[str, object]:
    """Process all CWC river CSVs and return generated output paths."""
    raw_dir = Path(raw_dir) if raw_dir is not None else DEFAULT_RAW_DIR
    output_dir = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    files = discover_csv_files(raw_dir)
    if not files:
        raise FileNotFoundError(f"No CSV files found under {raw_dir}")
    per_file = [process_file(path, output_dir) for path in files]
    combined = _write_combined(per_file, output_dir / "river_observations.parquet") if combine else None
    return {"per_file": per_file, "combined": combined}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    LOGGER.info("River pipeline outputs: %s", run_pipeline())
