from unittest.mock import patch
from django.test import SimpleTestCase
from backend.services.core_service import CoreService


class CoreDashboardTests(SimpleTestCase):
    @patch("apps.core.services.dashboard.set_dashboard")
    @patch("apps.core.services.dashboard.get_dashboard", return_value=None)
    @patch("apps.core.services.dashboard.NotificationService.list", return_value=[])
    @patch("apps.core.services.dashboard.RiskService.current", return_value={"risk_score": 20, "risk_level": "low"})
    @patch("apps.core.services.dashboard.WeatherService.current", return_value={"temperature_c": 30})
    def test_dashboard_composes_weather_and_risk(self, weather, risk, notifications, get_cache, set_cache):
        user = type("User", (), {"id": 1})()
        payload = CoreService().dashboard(user, 20.0, 78.0)
        self.assertEqual(payload["summary"]["risk_score"], 20)
        self.assertEqual(payload["summary"]["temperature"], 30)
