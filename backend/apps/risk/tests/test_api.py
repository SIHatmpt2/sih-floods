from rest_framework.test import APITestCase
from rest_framework import status


class RiskApiTests(APITestCase):
    def test_invalid_coordinates_are_rejected(self):
        response = self.client.get("/api/risk/current/?lat=999&lon=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
