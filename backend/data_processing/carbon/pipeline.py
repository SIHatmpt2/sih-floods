"""CAMS CO2 raw CSV -> monthly Parquet features.

The training join uses the hilly-location product first and the regional
monthly mean as a deterministic fallback. The large grid CSV is validated
and preserved as a raw source; it is not expanded into the training table.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "apps" / "risk" / "data"
DEFAULT_RAW_DIR = DEFAULT_DATA_ROOT / "raw" / "carbon_emission"
DEFAULT_OUTPUT_DIR = DEFAULT_DATA_ROOT / "processed" / "carbon_emission" / "parquet"
HILLY_NAME = "cams_co2_hilly_locations.csv"
REGIONAL_NAME = "cams_co2_monthly_regional_mean.csv"
GRID_NAME = "cams_co2_monthly_grid.csv"
CARBON_FEATURES = [
    "co2_ppm",
    "co2_monthly_change_ppm",
    "co2_yearly_change_ppm",
    "co2_regional_anomaly_ppm",
]


def _require(df: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = columns - set(df.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {sorted(missing)}")


def _clean_regional(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    _require(frame, {"date", "regional_mean_co2_ppm"}, "regional CAMS data")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["regional_mean_co2_ppm"] = pd.to_numeric(frame["regional_mean_co2_ppm"], errors="coerce")
    frame = frame.dropna(subset=["date", "regional_mean_co2_ppm"]).sort_values("date")
    frame = frame.drop_duplicates("date", keep="last")
    frame["regional_mean_co2_ppm"] = frame["regional_mean_co2_ppm"].astype("float64")
    return frame.reset_index(drop=True)


def _clean_hilly(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    _require(frame, {"location", "date", "latitude", "longitude", "co2_ppm"}, "hilly CAMS data")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in ["requested_latitude", "requested_longitude", "latitude", "longitude", "co2_ppm"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["location", "date", "latitude", "longitude", "co2_ppm"])
    frame = frame.sort_values(["location", "date"])
    frame = frame.drop_duplicates(["location", "date"], keep="last")
    frame["co2_monthly_change_ppm"] = frame.groupby("location")["co2_ppm"].diff()
    frame["co2_yearly_change_ppm"] = frame.groupby("location")["co2_ppm"].diff(12)
    return frame.reset_index(drop=True)


def _add_regional_anomaly(hilly: pd.DataFrame, regional: pd.DataFrame) -> pd.DataFrame:
    result = pd.merge_asof(
        hilly.sort_values("date"),
        regional[["date", "regional_mean_co2_ppm"]].sort_values("date"),
        on="date",
        direction="nearest",
        tolerance=pd.Timedelta(days=31),
    )
    result["co2_regional_anomaly_ppm"] = result["co2_ppm"] - result["regional_mean_co2_ppm"]
    return result


def validate_grid(path: Path) -> dict[str, object]:
    """Validate the large grid source without loading it into model memory."""
    frame = pd.read_csv(path, nrows=5, low_memory=False)
    if frame.empty:
        raise ValueError(f"Grid carbon CSV is empty: {path}")
    _require(frame, {"date", "co2_ppm"}, "grid CAMS data")
    return {"path": path.as_posix(), "columns": list(frame.columns)}


def run_pipeline(
    raw_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    raw_dir = Path(raw_dir) if raw_dir is not None else DEFAULT_RAW_DIR
    output_dir = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    hilly_path = raw_dir / HILLY_NAME
    regional_path = raw_dir / REGIONAL_NAME
    grid_path = raw_dir / GRID_NAME
    for path in (hilly_path, regional_path, grid_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing CAMS carbon source: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    regional = _clean_regional(regional_path)
    hilly = _add_regional_anomaly(_clean_hilly(hilly_path), regional)

    regional_out = output_dir / "carbon_regional_monthly.parquet"
    hilly_out = output_dir / "carbon_hilly_monthly.parquet"
    regional.to_parquet(regional_out, engine="pyarrow", compression="zstd", index=False)
    hilly.to_parquet(hilly_out, engine="pyarrow", compression="zstd", index=False)
    grid_info = validate_grid(grid_path)
    LOGGER.info("Wrote carbon Parquet: hilly=%d rows regional=%d rows", len(hilly), len(regional))
    return {"hilly": hilly_out, "regional": regional_out, "grid": grid_info}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    LOGGER.info("Carbon pipeline outputs: %s", run_pipeline())
