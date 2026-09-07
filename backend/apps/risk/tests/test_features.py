from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.risk.services.historical import historical_features
from apps.risk.services.risk_engine import score_baseline


class RiskFeatureTests(SimpleTestCase):
    @patch("apps.risk.services.historical.timezone.now")
    @patch("apps.risk.services.historical.recent_flood_events")
    def test_historical_recent_event_count_is_a_real_recent_count(self, recent_events, now):
        now.return_value = SimpleNamespace(date=lambda: date(2026, 9, 7))
        recent_events.return_value = [
            SimpleNamespace(event_date=date(2026, 8, 1), severity=10),
            SimpleNamespace(event_date=date(2026, 1, 1), severity=20),
            SimpleNamespace(event_date=date(2024, 1, 1), severity=30),
        ]
        result = historical_features(30.1, 78.2)
        self.assertEqual(result["event_count"], 3)
        self.assertEqual(result["recent_event_count"], 2)

    def test_baseline_exposes_missing_components_without_fabrication(self):
        result = score_baseline({"rainfall_24h_mm": None, "rainfall_3d_mm": None, "rainfall_7d_mm": None, "rainfall_30d_mm": None,
                                 "water_level_m": None, "water_level_change": None, "historical_score": 0.0,
                                 "elevation_m": None, "slope_deg": None})
        self.assertIn("rainfall", result.data_quality["missing_components"])
        self.assertIn("river", result.data_quality["missing_components"])
