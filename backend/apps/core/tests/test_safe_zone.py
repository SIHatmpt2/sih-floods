from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.services.safe_zone import SafeZoneService


class SafeZoneServiceTests(SimpleTestCase):
    @patch("apps.core.services.safe_zone.risk_selectors.nearest_safe_zone")
    def test_nearest_safe_zone_delegates_to_risk_selector(self, selector):
        selector.return_value = SimpleNamespace(
            id=7,
            name="Safe Zone A",
            risk_level="low",
        )

        result = SafeZoneService().nearest_safe_zone(30.1, 78.2)

        selector.assert_called_once_with(30.1, 78.2)
        self.assertEqual(
            result,
            {"zone_id": 7, "zone_name": "Safe Zone A", "risk_level": "low"},
        )
