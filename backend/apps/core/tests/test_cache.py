from django.core.cache import cache
from django.test import SimpleTestCase
from apps.core.services.cache import dashboard_key, set_dashboard, get_dashboard


class CacheTests(SimpleTestCase):
    def test_dashboard_cache_round_trip(self):
        cache.clear()
        key = dashboard_key(1, 30.0, 78.0)
        set_dashboard(1, 30.0, 78.0, {"ok": True})
        self.assertEqual(key, dashboard_key(1, 30.0, 78.0))
        self.assertEqual(get_dashboard(1, 30.0, 78.0), {"ok": True})
