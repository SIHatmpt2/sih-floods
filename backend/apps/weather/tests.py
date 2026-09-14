"""Tests for the weather Django application."""
from datetime import date
from unittest.mock import patch
from urllib.error import URLError

from django.conf import settings
from django.test import SimpleTestCase

from .apps import WeatherConfig
from .services.historical import HistoricalWeatherService


class WeatherAppTests(SimpleTestCase):
    def test_app_config_name(self):
        self.assertEqual(WeatherConfig.name, "apps.weather")

    def test_app_is_registered(self):
        self.assertIn("apps.weather", settings.INSTALLED_APPS)

    def test_frontend_origins_are_configured(self):
        self.assertIn("http://localhost:5173", settings.CORS_ALLOWED_ORIGINS)
        self.assertIn("http://127.0.0.1:5173", settings.CORS_ALLOWED_ORIGINS)

    def test_weather_provider_defaults_are_configured(self):
        self.assertEqual(settings.WEATHER_PROVIDER_PRIORITY, ["imd", "cwc"])

    def test_project_urls_import_without_backend_package(self):
        import config.urls

        self.assertTrue(config.urls.urlpatterns)

    @patch("apps.weather.services.historical.cache.set")
    @patch("apps.weather.services.historical.cache.get", return_value=None)
    @patch.object(HistoricalWeatherService, "_request")
    def test_historical_weather_falls_back_when_open_meteo_fails(
        self, request_mock, _cache_get, _cache_set
    ):
        nasa_payload = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "2026030500": 20.0,
                        "2026030501": 21.0,
                    },
                    "RH2M": {
                        "2026030500": 70.0,
                        "2026030501": 72.0,
                    },
                    "PRECTOTCORR": {
                        "2026030500": 1.5,
                        "2026030501": 2.5,
                    },
                    "WS10M": {
                        "2026030500": 2.0,
                        "2026030501": 3.0,
                    },
                    "PS": {
                        "2026030500": 101.0,
                        "2026030501": 100.8,
                    },
                }
            }
        }
        request_mock.side_effect = [
            URLError("historical forecast unavailable"),
            URLError("ERA5 unavailable"),
            nasa_payload,
        ]

        result = HistoricalWeatherService().for_date(26.2, 92.9, date(2026, 3, 5))

        self.assertEqual(result["analysis_date"], "2026-03-05")
        self.assertEqual(result["rainfall_24h_mm"], 4.0)
        self.assertEqual(result["rainfall_7d_mm"], 4.0)
        self.assertEqual(result["temperature_c"], 21.0)
        self.assertEqual(result["humidity"], 72.0)
        self.assertEqual(result["wind_speed_kmh"], 10.8)
        self.assertEqual(result["pressure_hpa"], 1008.0)
        self.assertEqual(result["data_quality"]["source"], "nasa-power")
