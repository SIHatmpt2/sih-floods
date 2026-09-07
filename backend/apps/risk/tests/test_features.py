from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.risk.services.historical import historical_features
from apps.risk.services.rainfall import rainfall_features
from apps.risk.services.river import river_features


class RiskFeatureTests(SimpleTestCase):
    @patch("apps.risk.services.rainfall.WeatherStation.objects")
    def test_rainfall_uses_nearby_station_aggregates_without_double_counting(self, stations):
        class FakeQuerySet:
            def filter(self, **kwargs):
                return self

            def annotate(self, **kwargs):
                return self

            def order_by(self, *args):
                return self

            def __iter__(self):
                return iter([
                    SimpleNamespace(
                        id=1,
                        location=SimpleNamespace(y=30.1, x=78.2),
                    )
                ])

        stations.filter.return_value = FakeQuerySet()
        with patch(
            "apps.risk.services.rainfall.WeatherObservation.objects"
        ) as observations:
            observations.filter.return_value.order_by.return_value.first.side_effect = [
                SimpleNamespace(rainfall_mm=10),
                None,
                None,
                None,
            ]
            result = rainfall_features(30.1, 78.2)
        self.assertIn("rainfall_30d_mm", result)

    @patch("apps.risk.services.river.WeatherObservation.objects")
    def test_river_features_prefers_cwc_measurements(self, observations):
        latest = SimpleNamespace(
            station=SimpleNamespace(provider="cwc"),
            timestamp=SimpleNamespace(),
            water_level_m=5.0,
            discharge_m3s=100.0,
        )
        previous = SimpleNamespace(water_level_m=4.0)
        query = observations.filter.return_value
        query.order_by.return_value.first.side_effect = [latest, previous]
        query.filter.return_value.first.return_value = previous
        result = river_features(30.1, 78.2)
        self.assertEqual(result["water_level_change"], 1.0)

    @patch("apps.risk.services.historical.recent_flood_events")
    def test_historical_recent_event_count_is_not_total_event_count(self, recent_events):
        recent_events.return_value = [
            SimpleNamespace(severity=10),
            SimpleNamespace(severity=20),
            SimpleNamespace(severity=30),
        ]
        result = historical_features(30.1, 78.2)
        self.assertEqual(result["event_count"], 3)
        self.assertEqual(result["recent_event_count"], 3)
