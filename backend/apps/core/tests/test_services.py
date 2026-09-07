from django.test import SimpleTestCase
from unittest.mock import patch
from apps.core.services.analytics import AnalyticsService


class AnalyticsTests(SimpleTestCase):
    @patch("apps.core.services.analytics.RiskAssessment")
    def test_daily_summary_contract(self, model):
        model.objects.count.return_value = 3
        model.objects.values.return_value.annotate.return_value = []
        self.assertEqual(AnalyticsService().daily_summary()["total_assessments"], 3)
