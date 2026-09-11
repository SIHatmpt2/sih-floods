from unittest.mock import patch
from django.test import SimpleTestCase


class RiskTaskTests(SimpleTestCase):
    @patch("apps.risk.tasks.assess_point")
    @patch("apps.risk.tasks.RiskZone.objects.filter")
    def test_refresh_active_zones_is_callable(self, zones_filter, assess_point):
        zones_filter.return_value.iterator.return_value = []
        from apps.risk.tasks import refresh_active_zones
        result = refresh_active_zones()
        self.assertEqual(result["updated"], 0)
