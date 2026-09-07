from django.test import SimpleTestCase
from backend.apps.risk.services.normalizer import linear_score, risk_level
from backend.apps.risk.services.risk_engine import score_baseline


class RiskEngineTests(SimpleTestCase):
    def test_level_boundaries(self):
        self.assertEqual(risk_level(0), "low")
        self.assertEqual(risk_level(25), "moderate")
        self.assertEqual(risk_level(50), "high")
        self.assertEqual(risk_level(75), "severe")

    def test_linear_score(self):
        self.assertEqual(linear_score(50, 0, 100), 50)
        self.assertEqual(linear_score(200, 0, 100), 100)

    def test_partial_baseline_does_not_fabricate_missing_values(self):
        result = score_baseline({
            "rainfall_24h_mm": 100,
            "rainfall_3d_mm": 0,
            "rainfall_7d_mm": 0,
            "water_level_m": None,
            "water_level_change": None,
            "slope_deg": None,
            "elevation_m": None,
            "historical_score": 20,
        })
        self.assertEqual(result.model_source, "baseline")
        self.assertIn("river", result.data_quality["missing_components"])
        self.assertIsNone(result.breakdown["river"])
