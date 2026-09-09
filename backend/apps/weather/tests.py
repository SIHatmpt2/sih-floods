"""Tests for the weather Django application."""
from django.conf import settings
from django.test import SimpleTestCase

from .apps import WeatherConfig


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
