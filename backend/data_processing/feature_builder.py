"""Build the stable feature contract consumed by Risk inference."""
from __future__ import annotations


def build_risk_features(weather: dict) -> dict:
    """Map normalized WeatherService output into Risk feature names."""
    station = weather.get("station") or {}
    return {
        "rainfall_24h_mm": weather.get("rainfall_24h_mm", weather.get("rainfall_mm")),
        "rainfall_3d_mm": weather.get("rainfall_3d_mm"),
        "rainfall_7d_mm": weather.get("rainfall_7d_mm"),
        "water_level_m": weather.get("water_level_m"),
        "discharge_m3s": weather.get("discharge_m3s"),
        "water_level_change": weather.get("water_level_change"),
        "temperature_c": weather.get("temperature_c"),
        "humidity": weather.get("humidity"),
        "slope_deg": weather.get("slope_deg"),
        "elevation_m": weather.get("elevation_m"),
        "historical_score": weather.get("historical_score"),
        "state": station.get("state"),
        "district": station.get("district"),
    }
