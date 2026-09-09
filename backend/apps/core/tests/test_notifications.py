from django.test import TestCase
from services.core_service import CoreService


class NotificationTests(TestCase):
    def test_service_exists(self):
        self.assertIsNotNone(CoreService)
