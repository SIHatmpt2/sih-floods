```python
"""
Geospatial and temporal transformation for historical flood events.
"""

from __future__ import annotations

import logging

import geopandas as gpd
import pandas as pd

from ..transform import (
    add_temporal_features,
    parse_lat_lon,
    parse_wkt_point,
)

LOGGER = logging.getLogger(__name__)


def _parse_location(value: object):
    """
    Parse a location represented as either:

    - WKT: "POINT (85.3240 27.7172)"
    - Latitude/longitude text: "27.7172, 85.3240"

    Returns
    -------
    shapely.geometry.Point | None
        Parsed point geometry, or None if the value cannot be parsed.
    """
    if value is None or pd.isna(value):
        return None

    geometry = parse_wkt_point(value)

    if geometry is not None:
        return geometry

    return parse_lat_lon(value)


def transform_geospatial(
    df: pd.DataFrame,
    crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """
    Convert cleaned flood-event records to a GeoDataFrame.

    Supported location formats include:

        "27.7172, 85.3240"
        "POINT (85.3240 27.7172)"

    Temporal features are extracted from the ``date`` column:

        year
        month
        quarter
        day_of_year
        day_of_week
        season
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    if "location" not in df.columns:
        raise ValueError("Missing required column: location")

    if "date" not in df.columns:
        raise ValueError("Missing required column: date")

    result = df.copy()

    # Parse locations into Shapely geometries.
    result["geometry"] = result["location"].apply(_parse_location)

    valid_geometry_count = int(result["geometry"].notna().sum())

    LOGGER.info(
        "Parsed %d/%d locations successfully.",
        valid_geometry_count,
        len(result),
    )

    # Create GeoDataFrame using WGS84 by default.
    gdf = gpd.GeoDataFrame(
        result,
        geometry="geometry",
        crs=crs,
    )

    # Add temporal features.
    gdf = add_temporal_features(gdf, "date")

    # Ensure season exists and is consistently represented.
    if "month" not in gdf.columns:
        raise ValueError(
            "add_temporal_features() must create a 'month' column."
        )

    gdf["season"] = (
        gdf["month"]
        .map(
            {
                12: "winter",
                1: "winter",
                2: "winter",
                3: "spring",
                4: "spring",
                5: "spring",
                6: "summer",
                7: "summer",
                8: "summer",
                9: "autumn",
                10: "autumn",
                11: "autumn",
            }
        )
        .fillna("unknown")
    )

    LOGGER.info(
        "Geospatial transformation completed for %d records.",
        len(gdf),
    )

    return gdf
