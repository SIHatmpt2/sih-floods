"""Historical flood-event processing pipeline.

Run from the repository root with::

    python -m backend.data_processing.past_flood_events.pipeline
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from ..ingest import load_csv, save_geodata
from .clean import clean_data
from .features import engineer_features
from .transform import transform_geospatial

LOGGER = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = REPO_ROOT / "backend" / "data" / "raw" / "flood_events" / "flood_events.csv"
DEFAULT_OUTPUT = REPO_ROOT / "backend" / "data" / "processed" / "flood_events" / "flood_events.geojson"


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def run_pipeline(input_path: str | Path = DEFAULT_INPUT, output_path: str | Path = DEFAULT_OUTPUT):
    """Execute ingest -> clean -> geospatial/temporal transform -> features -> GeoJSON."""
    raw_df = load_csv(str(input_path))
    clean_df = clean_data(raw_df)
    gdf = transform_geospatial(clean_df, crs="EPSG:4326")
    LOGGER.info("Non-null geometries: %d/%d", int(gdf.geometry.notna().sum()), len(gdf))
    LOGGER.info("Valid geometries: %d/%d", int(gdf.geometry.is_valid.sum()), len(gdf))
    featured_gdf = engineer_features(gdf)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    save_geodata(featured_gdf, str(output_file))
    LOGGER.info("Flood-event pipeline completed successfully: %s", output_file)
    return featured_gdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process historical flood-event data.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to flood_events.csv")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output GeoJSON path")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.log_level)
    try:
        run_pipeline(args.input, args.output)
    except Exception:
        LOGGER.exception("Flood-event pipeline failed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
