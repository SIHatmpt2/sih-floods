from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.risk.services.river import river_features


class RiverFeatureTests(SimpleTestCase):
    @patch("apps.risk.services.river._stations")
    def test_river_features_accepts_water_level_only_station(self, stations):
        latest = SimpleNamespace(
            timestamp=SimpleNamespace(),
            water_level_m=5.0,
            discharge_m3s=None,
        )
        observations = SimpleNamespace(
            filter=lambda **kwargs: SimpleNamespace(
                order_by=lambda *args: SimpleNamespace(first=lambda: latest)
            )
        )
        station = SimpleNamespace(
            provider="cwc",
            distance=SimpleNamespace(m=1000),
            observations=observations,
        )
        stations.return_value = [station]

        result = river_features(30.1, 78.2)

        self.assertEqual(result["water_level_m"], 5.0)
        self.assertIsNone(result["discharge_m3s"])
