from django.test import TestCase
from unittest.mock import patch
from backend.services.core_service import CoreService


class DashboardTests(TestCase):
    @patch("backend.services.weather_service.WeatherService.current", return_value={"temperature_c": 28})
    @patch("backend.services.risk_service.RiskService.assess", return_value={"risk_score": 78, "risk_level": "Severe"})
    def test_dashboard_aggregation(self, *_):
        result = CoreService().dashboard(None, 30.3165, 78.0322)
        self.assertEqual(result["risk"]["risk_level"], "Severe")
        self.assertEqual(result["summary"]["temperature"], 28)
