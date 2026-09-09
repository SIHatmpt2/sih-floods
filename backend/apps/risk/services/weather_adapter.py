"""Risk-side adapter for consuming normalized WeatherService data."""
from __future__ import annotations

from services.weather_service import WeatherService
from data_processing.feature_builder import build_risk_features


class WeatherRiskAdapter:
    def __init__(self, weather_service: WeatherService | None = None):
        self.weather_service = weather_service or WeatherService()

    def current_features(self, lat: float, lon: float) -> dict:
        weather = self.weather_service.current(lat, lon)
        return build_risk_features(weather)
