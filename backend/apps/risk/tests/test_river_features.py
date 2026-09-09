from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.risk.services.river import river_features


class RiverFeatureTests(SimpleTestCase):
    @patch("apps.risk.services.river.WeatherStation.objects")
    def test_river_features_accepts_water_level_only_station(self, stations):
        station = SimpleNamespace(
            provider="cwc",
            distance=SimpleNamespace(m=1000),
            observations=MagicMock(),
        )
        stations.filter.return_value.distinct.return_value.filter.return_value.annotate.return_value.order_by.return_value.__getitem__.return_value = [station]
        stations.filter.return_value.distinct.return_value.annotate.return_value.order_by.return_value.__getitem__.return_value = [station]
        latest = SimpleNamespace(
            timestamp=SimpleNamespace(),
            water_level_m=5.0,
            discharge_m3s=None,
        )
        station.observations.filter.return_value.filter.return_value.order_by.return_value.first.return_value = latest
        station.observations.filter.return_value.order_by.return_value.first.return_value = latest
        station.observations.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = latest
        self.assertEqual(river_features(30.1, 78.2)["water_level_m"], 5.0)
