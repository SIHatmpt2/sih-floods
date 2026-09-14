from datetime import date

from django.test import SimpleTestCase

from .feature_builder import build_risk_features


class HistoricalFeatureBuilderTests(SimpleTestCase):
    def test_calendar_features_use_analysis_date(self):
        features = build_risk_features(
            {"rainfall_24h_mm": 120, "rainfall_3d_mm": 200, "rainfall_7d_mm": 300},
            analysis_datetime=date(2023, 6, 13),
        )
        self.assertEqual(features["month"], 6)
        self.assertEqual(features["day_of_year"], 164)
        self.assertEqual(features["is_monsoon"], 1)
