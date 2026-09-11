from pathlib import Path

from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status


class RiskApiTests(APITestCase):
    def test_invalid_coordinates_are_rejected(self):
        response = self.client.get("/api/risk/current/?lat=999&lon=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_model_artifact_index_lists_json_models(self):
        response = self.client.get("/api/risk/models/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["models"])
        self.assertTrue(all(item["name"].endswith(".json") for item in response.data["models"]))
        self.assertEqual(len(response.data["models"]), len(list(Path(settings.RISK_MODEL_DIR).glob("*.json"))))

    def test_model_artifact_is_served(self):
        artifact = next(Path(settings.RISK_MODEL_DIR).glob("*.json"))
        response = self.client.get(f"/api/risk/models/{artifact.name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("{", response.content[:100].decode("utf-8", errors="ignore"))

    def test_model_artifact_path_traversal_is_rejected(self):
        response = self.client.get("/api/risk/models/../settings.py")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
