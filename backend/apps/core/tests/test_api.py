from unittest.mock import patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from apps.core.views import DashboardView


class DashboardApiTests(SimpleTestCase):
    @patch("apps.core.views.service.dashboard")
    def test_dashboard_uses_service(self, dashboard):
        dashboard.return_value = {"risk": {"risk_level": "High"}}
        request = APIRequestFactory().get("/api/core/dashboard/?lat=30&lon=78")
        request.user = type("User", (), {"is_authenticated": True, "id": 1})()
        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["risk"]["risk_level"], "High")
