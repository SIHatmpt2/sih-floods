from __future__ import annotations

from datetime import datetime
from typing import Any


_FIELD_ALIASES = {
    "station_id": ("station_id", "stationId", "id", "code"),
    "station_name": ("station_name", "stationName", "name"),
    "state": ("state", "state_name", "stateName"),
    "district": ("district", "district_name", "districtName"),
    "latitude": ("latitude", "lat", "Latitude"),
    "longitude": ("longitude", "lon", "lng", "Longitude"),
    "timestamp": ("timestamp", "time", "datetime", "date_time", "observed_at"),
    "rainfall_mm": ("rainfall_mm", "rainfall", "rain", "precipitation", "precipitation_mm"),
    "temperature_c": ("temperature_c", "temperature", "temp", "temp_c"),
    "humidity": ("humidity", "relative_humidity"),
    "water_level_m": ("water_level_m", "water_level", "level", "waterLevel"),
    "discharge_m3s": ("discharge_m3s", "discharge", "flow", "flow_rate"),
}


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("data", "stations", "observations", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [payload]
    return []


def _pick(row: dict[str, Any], field: str):
    for key in _FIELD_ALIASES[field]:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def _number(value, field: str):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc
    if field in {"rainfall_mm", "humidity", "water_level_m", "discharge_m3s"} and number < 0:
        raise ValueError(f"Invalid negative {field}: {number}")
    if field == "humidity" and number > 100:
        raise ValueError(f"Invalid humidity: {number}")
    return number


def _timestamp(value):
    if value in (None, ""):
        raise ValueError("Missing timestamp")
    if isinstance(value, datetime):
        return value
    text = str(value).strip().replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def normalize_weather_records(payload: Any, provider: str) -> list[dict[str, Any]]:
    normalized = []
    for row in _records(payload):
        station_id = _pick(row, "station_id")
        timestamp = _timestamp(_pick(row, "timestamp"))
        latitude = _number(_pick(row, "latitude"), "latitude")
        longitude = _number(_pick(row, "longitude"), "longitude")
        if not station_id or latitude is None or longitude is None:
            raise ValueError("Weather record requires station_id, latitude, and longitude")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("Weather record coordinates are outside valid WGS84 bounds")
        normalized.append({
            "provider": provider,
            "station_id": str(station_id),
            "station_name": str(_pick(row, "station_name") or station_id),
            "state": _pick(row, "state") or "",
            "district": _pick(row, "district") or "",
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp,
            "rainfall_mm": _number(_pick(row, "rainfall_mm"), "rainfall_mm"),
            "temperature_c": _number(_pick(row, "temperature_c"), "temperature_c"),
            "humidity": _number(_pick(row, "humidity"), "humidity"),
            "water_level_m": _number(_pick(row, "water_level_m"), "water_level_m"),
            "discharge_m3s": _number(_pick(row, "discharge_m3s"), "discharge_m3s"),
        })
    return normalized
