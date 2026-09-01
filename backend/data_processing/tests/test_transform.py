import pandas as pd

from data_processing.transform import parse_lat_lon, parse_wkt_point


def test_parse_lat_lon_uses_latitude_longitude_order():
    point = parse_lat_lon("27.7172, 85.3240")
    assert point.x == 85.3240
    assert point.y == 27.7172


def test_parse_lat_lon_rejects_invalid_ranges():
    assert parse_lat_lon("91, 85") is None
    assert parse_lat_lon("27, 181") is None


def test_parse_wkt_point_rejects_non_point_and_invalid_range():
    assert parse_wkt_point("LINESTRING (85 27, 86 28)") is None
    assert parse_wkt_point("POINT (181 27)") is None
