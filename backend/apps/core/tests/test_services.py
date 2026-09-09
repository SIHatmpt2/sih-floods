from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.services.analytics import AnalyticsService


class AnalyticsTests(SimpleTestCase):
    @patch("apps.core.services.analytics.RiskAssessment")
    def test_daily_summary_contract(self, model):
        model.objects.count.return_value = 3
        model.objects.values.return_value.annotate.return_value = []
        self.assertEqual(AnalyticsService().daily_summary()["total_assessments"], 3)

    @patch("apps.core.services.analytics.RiskAssessment")
    def test_state_summary_filters_stored_feature_state(self, model):
        queryset = model.objects.select_related.return_value
        filtered = queryset.filter.return_value
        filtered.values.return_value.annotate.return_value = []

        result = AnalyticsService().state_summary("Uttarakhand")

        queryset.filter.assert_called_once_with(features__state__iexact="Uttarakhand")
        self.assertEqual(result["state"], "Uttarakhand")
