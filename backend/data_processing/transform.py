"""
Generic geospatial and temporal transformations.
"""

from __future__ import annotations

import re
from typing import Final

import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.errors import GEOSException
from shapely.geometry import Point


_LAT_LON_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*[\(\[]?"
    r"(-?(?:\d+(?:\.\d*)?|\.\d+))"
    r"\s*[,;]\s*"
    r"(-?(?:\d+(?:\.\d*)?|\.\d+))"
    r"[\)\]]?\s*$"
)


def parse_lat_lon(value: object) -> Point | None:
    """
    Parse a latitude/longitude value into a Shapely Point.

    Supported formats include:

        "27.7172, 85.3240"
        "(27.7172, 85.3240)"
        "[27.7172; 85.3240]"

    Input values are interpreted as:

        latitude, longitude

    The returned Shapely Point follows the standard GIS convention:

        Point(longitude, latitude)

    Returns None when the value is missing, malformed, or outside
    valid latitude/longitude ranges.
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None

    text = str(value).strip()

    match = _LAT_LON_PATTERN.fullmatch(text)
    if match is None:
        return None

    try:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
    except (TypeError, ValueError):
        return None

    if not -90.0 <= latitude <= 90.0:
        return None

    if not -180.0 <= longitude <= 180.0:
        return None

    return Point(longitude, latitude)


def parse_wkt_point(value: object) -> Point | None:
    """
    Parse a WKT Point into a Shapely Point.

    Example:

        "POINT (85.3240 27.7172)"

    Returns None when the value is missing, invalid WKT, or
    represents a geometry other than a Point.
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None

    try:
        geometry = wkt.loads(str(value))
    except (TypeError, ValueError, GEOSException):
        return None

    if not isinstance(geometry, Point):
        return None

    return geometry


def add_temporal_features(
    df: pd.DataFrame,
    date_column: str,
) -> pd.DataFrame:
    """
    Add common calendar and temporal features to a DataFrame.

    Added columns:

        year
        month
        quarter
        day_of_year
        day_of_week
        day
        week
        is_weekend

    Invalid or missing dates are converted to NaT and therefore
    produce missing temporal features.
    """
    if date_column not in df.columns:
        raise ValueError(
            f"Missing date column: {date_column!r}"
        )

    result = df.copy()

    dates = pd.to_datetime(
        result[date_column],
        errors="coerce",
    )

    result["year"] = dates.dt.year.astype("Int64")
    result["month"] = dates.dt.month.astype("Int64")
    result["quarter"] = dates.dt.quarter.astype("Int64")
    result["day_of_year"] = dates.dt.dayofyear.astype("Int64")
    result["day_of_week"] = dates.dt.dayofweek.astype("Int64")
    result["day"] = dates.dt.day.astype("Int64")

    result["week"] = (
        dates.dt.isocalendar()
        .week
        .astype("Int64")
    )

    result["is_weekend"] = (
        dates.dt.dayofweek >= 5
    ).where(
        dates.notna(),
        pd.NA,
    )

    return result


def make_geodataframe(
    df: pd.DataFrame,
    geometry_column: str = "geometry",
    crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """
    Convert a DataFrame containing Shapely geometries into a
    GeoDataFrame.

    The geometry column must already contain valid Shapely
    geometry objects or missing values.

    Parameters
    ----------
    df:
        Source DataFrame.
    geometry_column:
        Name of the column containing geometries.
    crs:
        Coordinate reference system assigned to the geometries.

    Returns
    -------
    geopandas.GeoDataFrame
        A copy of the input DataFrame as a GeoDataFrame.
    """
    if geometry_column not in df.columns:
        raise ValueError(
            f"Missing geometry column: {geometry_column!r}"
        )

    return gpd.GeoDataFrame(
        df.copy(),
        geometry=geometry_column,
        crs=crs,
    )


def reproject(
    gdf: gpd.GeoDataFrame,
    target_crs: str,
) -> gpd.GeoDataFrame:
    """
    Reproject a GeoDataFrame to a target coordinate reference system.

    Parameters
    ----------
    gdf:
        Input GeoDataFrame with a defined CRS.
    target_crs:
        Target CRS, such as "EPSG:3857".

    Returns
    -------
    geopandas.GeoDataFrame
        A reprojected copy of the GeoDataFrame.

    Raises
    ------
    ValueError
        If the input GeoDataFrame has no CRS.
    """
    if gdf.crs is None:
        raise ValueError(
            "GeoDataFrame has no CRS. "
            "Set the source CRS before reprojecting."
        )

    return gdf.to_crs(target_crs)
