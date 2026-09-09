from unittest.mock import patch
from django.test import SimpleTestCase
from apps.risk.services.risk_engine import RiskResult
from services.risk_service import RiskService


class RiskServiceContractTests(SimpleTestCase):
    @patch("services.risk_service.nearest_zone", return_value=None)
    @patch("services.risk_service.assess_point")
    @patch("services.risk_service.cache.get_current", return_value=None)
    @patch("services.risk_service.cache.set_current")
    def test_current_contract(self, set_cache, get_cache, assess, nearest):
        assess.return_value = RiskResult(63, "high", {"rainfall": 70}, {"rainfall_24h_mm": 100}, "baseline", {"partial": False})
        data = RiskService().current(20, 78)
        self.assertEqual(data["risk_score"], 63)
        self.assertEqual(data["risk_level"], "high")
        set_cache.assert_called_once()
