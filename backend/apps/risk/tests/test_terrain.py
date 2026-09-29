from django.test import SimpleTestCase

from apps.risk.services.terrain import terrain_features


class TerrainFeatureTests(SimpleTestCase):
    def test_verified_location_dataset_provides_slope(self):
        result = terrain_features(27.95, 96.15)
        self.assertEqual(result["event_id"], "AR24-016")
        self.assertIsNotNone(result["slope_deg"])
        self.assertEqual(result["source"], "verified_location_event_dataset")

    def test_distant_location_does_not_invent_terrain(self):
        result = terrain_features(0.0, 0.0)
        self.assertIsNone(result["slope_deg"])
        self.assertIsNone(result["elevation_m"])
