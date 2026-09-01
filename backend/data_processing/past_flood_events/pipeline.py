```python
"""
Historical flood-event processing pipeline.

Run from the project root with:

    python -m backend.data_processing.flood_events.pipeline
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


DEFAULT_INPUT = (
    "backend/apps/risk/data/raw/"
    "flood_events/flood_events.csv"
)

DEFAULT_OUTPUT = (
    "backend/apps/risk/data/processed/"
    "flood_events/flood_events.geojson"
)


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


def run_pipeline(
    input_path: str = DEFAULT_INPUT,
    output_path: str = DEFAULT_OUTPUT,
):
    """
    Execute the complete historical flood-event pipeline.

    Processing sequence:

        CSV
          ↓
        ingest
          ↓
        clean
          ↓
        geospatial/temporal transformation
          ↓
        feature engineering
          ↓
        GeoJSON output
    """
    LOGGER.info(
        "Starting flood-event processing pipeline."
    )
    LOGGER.info("Input: %s", input_path)
    LOGGER.info("Output: %s", output_path)

    # ---------------------------------------------------------
    # 1. INGEST
    # ---------------------------------------------------------

    raw_df = load_csv(input_path)

    LOGGER.info(
        "Raw records: %d",
        len(raw_df),
    )

    # ---------------------------------------------------------
    # 2. CLEAN
    # ---------------------------------------------------------

    clean_df = clean_data(raw_df)

    LOGGER.info(
        "Records after cleaning: %d",
        len(clean_df),
    )

    # ---------------------------------------------------------
    # 3. TRANSFORM
    # ---------------------------------------------------------

    gdf = transform_geospatial(
        clean_df,
        crs="EPSG:4326",
    )

    non_null_geometry = int(
        gdf.geometry.notna().sum()
    )

    valid_geometry = int(
        gdf.geometry.is_valid.sum()
    )

    LOGGER.info(
        "Non-null geometries: %d/%d",
        non_null_geometry,
        len(gdf),
    )

    LOGGER.info(
        "Valid geometries: %d/%d",
        valid_geometry,
        len(gdf),
    )

    # ---------------------------------------------------------
    # 4. FEATURES
    # ---------------------------------------------------------

    featured_gdf = engineer_features(gdf)

    LOGGER.info(
        "Feature engineering complete."
    )

    LOGGER.info(
        "Final rows: %d",
        len(featured_gdf),
    )

    LOGGER.info(
        "Final columns: %d",
        len(featured_gdf.columns),
    )

    # ---------------------------------------------------------
    # 5. SAVE
    # ---------------------------------------------------------

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_geodata(
        featured_gdf,
        str(output_file),
    )

    LOGGER.info(
        "Flood-event pipeline completed successfully."
    )

    return featured_gdf


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Process historical flood-event data."
    )

    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Path to flood_events.csv.",
    )

    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=(
            "Output path. Supported formats depend on "
            "save_geodata()."
        ),
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=[
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
        ],
        help="Logging level.",
    )

    return parser


def main() -> int:
    """Command-line entry point."""
    parser = build_parser()
    args = parser.parse_args()

    configure_logging(args.log_level)

    try:
        run_pipeline(
            input_path=args.input,
            output_path=args.output,
        )
    except Exception:
        LOGGER.exception(
            "Flood-event pipeline failed."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
