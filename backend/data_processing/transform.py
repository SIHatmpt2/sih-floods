"""Generic geospatial and temporal transformations."""

from __future__ import annotations

import re
from typing import Final

import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.errors import GEOSException
from shapely.geometry import Point

_LAT_LON_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*[\(\[]?(-?(?:\d+(?:\.\d*)?|\.\d+))\s*[,;]\s*(-?(?:\d+(?:\.\d*)?|\.\d+))[\)\]]?\s*$"
)


def parse_lat_lon(value: object) -> Point | None:
    """Parse ``latitude, longitude`` text into a WGS84 Shapely point."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None
    match = _LAT_LON_PATTERN.fullmatch(str(value).strip())
    if match is None:
        return None
    latitude, longitude = float(match.group(1)), float(match.group(2))
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None
    return Point(longitude, latitude)


def parse_wkt_point(value: object) -> Point | None:
    """Parse a WKT Point and reject invalid coordinate ranges."""
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
    if not geometry.is_valid or not (-180 <= geometry.x <= 180 and -90 <= geometry.y <= 90):
        return None
    return geometry


def add_temporal_features(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
    """Add calendar fields from a datetime column."""
    if date_column not in df.columns:
        raise ValueError(f"Missing date column: {date_column!r}")
    result = df.copy()
    dates = pd.to_datetime(result[date_column], errors="coerce", format="mixed")
    result["year"] = dates.dt.year.astype("Int64")
    result["month"] = dates.dt.month.astype("Int64")
    result["quarter"] = dates.dt.quarter.astype("Int64")
    result["day_of_year"] = dates.dt.dayofyear.astype("Int64")
    result["day_of_week"] = dates.dt.dayofweek.astype("Int64")
    result["day"] = dates.dt.day.astype("Int64")
    result["week"] = dates.dt.isocalendar().week.astype("Int64")
    result["is_weekend"] = (dates.dt.dayofweek >= 5).where(dates.notna(), pd.NA)
    return result


def make_geodataframe(df: pd.DataFrame, geometry_column: str = "geometry", crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Convert a DataFrame containing Shapely geometries to a GeoDataFrame."""
    if geometry_column not in df.columns:
        raise ValueError(f"Missing geometry column: {geometry_column!r}")
    return gpd.GeoDataFrame(df.copy(), geometry=geometry_column, crs=crs)


def reproject(gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame; require an explicit source CRS."""
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS. Set the source CRS before reprojecting.")
    return gdf.to_crs(target_crs)
