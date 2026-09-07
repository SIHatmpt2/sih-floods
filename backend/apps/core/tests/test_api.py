from unittest.mock import patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from apps.core.views import DashboardView


class DashboardApiTests(SimpleTestCase):
    @patch("apps.core.views.service.dashboard", return_value={"risk": {"risk_level": "low"}})
    def test_dashboard_uses_service(self, dashboard):
        request = APIRequestFactory().get("/api/core/dashboard/?lat=30&lon=78")
        request.user = type("User", (), {"is_authenticated": True, "id": 1})()
        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        dashboard.assert_called_once()
