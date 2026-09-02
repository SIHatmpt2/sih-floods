"""Tests for the core Django application."""
from django.conf import settings
from django.test import SimpleTestCase

from .apps import CoreConfig


class CoreAppTests(SimpleTestCase):
    def test_app_config_name(self):
        self.assertEqual(CoreConfig.name, "apps.core")

    def test_app_is_registered(self):
        self.assertIn("apps.core", settings.INSTALLED_APPS)
