from __future__ import annotations

from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt

from django.conf import settings

from .client import WeatherProviderClient

ACCUWEATHER_BASE = "https://dataservice.accuweather.com"
IMD_CURRENT_URL = "https://api.imd.gov.in/api/v1/current_wx"


def _number(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _parse_time(value):
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _distance_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def _accuweather(client, latitude, longitude, api_key):
    location = client.get(
        f"{ACCUWEATHER_BASE}/locations/v1/cities/geoposition/search",
        params={
            "q": f"{latitude:.4f},{longitude:.4f}",
            "language": "en-us",
            "toplevel": "true",
            "apikey": api_key,
        },
    )
    key = location.get("Key") if isinstance(location, dict) else None
    if not key:
        raise ValueError("AccuWeather did not return a location key")

    rows = client.get(
        f"{ACCUWEATHER_BASE}/currentconditions/v1/{key}",
        params={"language": "en-us", "details": "true", "apikey": api_key},
    )
    if not isinstance(rows, list) or not rows:
        raise ValueError("AccuWeather returned no current conditions")
    row = rows[0]
    metric = (row.get("Temperature") or {}).get("Metric") or {}
    rain = (((row.get("PrecipitationSummary") or {}).get("Past24Hours") or {}).get("Metric") or {}).get("Value")
    position = location.get("GeoPosition") or {}
    return {
        "provider": "accuweather",
        "station_id": f"accuweather:{key}",
        "station_name": location.get("LocalizedName") or location.get("EnglishName") or f"{latitude:.4f},{longitude:.4f}",
        "state": ((location.get("AdministrativeArea") or {}).get("LocalizedName") or ""),
        "district": ((location.get("SupplementalAdminAreas") or [{}])[0].get("LocalizedName") if location.get("SupplementalAdminAreas") else "") or "",
        "latitude": _number(position.get("Latitude")) or latitude,
        "longitude": _number(position.get("Longitude")) or longitude,
        "timestamp": _parse_time(row.get("LocalObservationDateTime")),
        "rainfall_mm": _number(rain),
        "temperature_c": _number(metric.get("Value")),
        "humidity": _number(row.get("RelativeHumidity")),
        "water_level_m": None,
        "discharge_m3s": None,
    }


def _imd(client, latitude, longitude, api_key):
    payload = client.get(IMD_CURRENT_URL, api_key=api_key)
    if isinstance(payload, dict):
        rows = payload.get("data") or payload.get("stations") or payload.get("observations") or []
    else:
        rows = payload
    if not isinstance(rows, list) or not rows:
        raise ValueError("IMD returned no current weather stations")

    candidates = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        lat = _number(row.get("latitude") or row.get("lat") or row.get("Latitude"))
        lon = _number(row.get("longitude") or row.get("lon") or row.get("Longitude"))
        if lat is not None and lon is not None:
            candidates.append((_distance_km(latitude, longitude, lat, lon), row, lat, lon))
    if not candidates:
        raise ValueError("IMD returned stations without coordinates")
    _, row, lat, lon = min(candidates, key=lambda item: item[0])

    date = row.get("date") or row.get("Date of Observation") or row.get("observation_date")
    time = row.get("time") or row.get("Time of Observation") or row.get("observation_time")
    timestamp = f"{date}T{time}+00:00" if date and time else row.get("timestamp")
    return {
        "provider": "imd",
        "station_id": str(row.get("stationId") or row.get("station_id") or row.get("Station Id") or row.get("id")),
        "station_name": str(row.get("station") or row.get("Station") or row.get("station_name") or "IMD station"),
        "state": str(row.get("state") or row.get("state_name") or ""),
        "district": str(row.get("district") or row.get("district_name") or ""),
        "latitude": lat,
        "longitude": lon,
        "timestamp": _parse_time(timestamp),
        "rainfall_mm": _number(row.get("rainfall") or row.get("Last 24 hrs Rainfall")),
        "temperature_c": _number(row.get("temperature") or row.get("Temperature")),
        "humidity": _number(row.get("humidity") or row.get("Humidity")),
        "water_level_m": None,
        "discharge_m3s": None,
    }


def fetch_current(latitude: float, longitude: float) -> dict:
    client = WeatherProviderClient(timeout=getattr(settings, "STATE_API_TIMEOUT", 30))
    errors = []
    for provider in ("accuweather", "imd"):
        key = getattr(settings, f"{provider.upper()}_API_KEY", None)
        if not key:
            continue
        try:
            if provider == "accuweather":
                return _accuweather(client, latitude, longitude, key)
            return _imd(client, latitude, longitude, key)
        except Exception as exc:
            errors.append(f"{provider}: {exc}")
    raise RuntimeError("No live weather provider succeeded: " + "; ".join(errors))
