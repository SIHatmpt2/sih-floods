"""Tests for the flood-risk Django application."""
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from .apps import RiskConfig


class RiskAppTests(SimpleTestCase):
    def test_app_config_name(self):
        self.assertEqual(RiskConfig.name, "apps.risk")

    def test_app_is_registered(self):
        self.assertIn("apps.risk", settings.INSTALLED_APPS)

    def test_risk_data_root_exists(self):
        data_root = Path(__file__).resolve().parent / "data"
        self.assertTrue(data_root.is_dir())
        self.assertTrue((data_root / "raw").is_dir())
        self.assertTrue((data_root / "geospatial").is_dir())

    def test_cwc_source_files_exist(self):
        data_root = Path(__file__).resolve().parent / "data"
        self.assertTrue((data_root / "raw/rainfall/cwc/Arunachal 2021-2025.csv").is_file())
        self.assertTrue((data_root / "raw/river_data/cwc/ar_26-30.csv").is_file())
