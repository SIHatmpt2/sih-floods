from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.risk.services.river import river_features


class RiverFeatureTests(SimpleTestCase):
    @patch("apps.risk.services.river._stations")
    def test_river_features_accepts_water_level_only_station(self, stations):
        latest = SimpleNamespace(
            timestamp=datetime(2026, 1, 2, 12, tzinfo=timezone.utc),
            water_level_m=5.0,
            discharge_m3s=None,
        )
        previous = SimpleNamespace(
            timestamp=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
            water_level_m=4.5,
            discharge_m3s=None,
        )
        observations = MagicMock()
        observations.filter.return_value.order_by.return_value.first.side_effect = [latest, previous]
        station = SimpleNamespace(observations=observations)
        stations.return_value = [station]

        result = river_features(30.1, 78.2)

        self.assertEqual(result["water_level_m"], 5.0)
        self.assertIsNone(result["discharge_m3s"])
        self.assertEqual(result["water_level_change"], 0.5)
        self.assertIsNone(result["discharge_change"])
