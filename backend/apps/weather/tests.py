"""Tests for the weather Django application."""
from django.conf import settings
from django.test import SimpleTestCase

from .apps import WeatherConfig


class WeatherAppTests(SimpleTestCase):
    def test_app_config_name(self):
        self.assertEqual(WeatherConfig.name, "apps.weather")

    def test_app_is_registered(self):
        self.assertIn("apps.weather", settings.INSTALLED_APPS)
