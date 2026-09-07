from django.test import SimpleTestCase
from apps.core.tasks import refresh_dashboard_cache


class TaskTests(SimpleTestCase):
    def test_task_name(self):
        self.assertEqual(refresh_dashboard_cache.name, "apps.core.tasks.refresh_dashboard_cache")
