from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase

from apps.weather.services.ingestion import WeatherIngestionService


class WeatherIngestionTests(SimpleTestCase):
    @patch("apps.weather.services.ingestion.fetch_current")
    @patch("apps.weather.services.ingestion.WeatherObservation.objects")
    @patch("apps.weather.services.ingestion.WeatherStation.objects")
    def test_refresh_location_preserves_existing_station_metadata(self, stations, observations, fetch_current):
        existing = SimpleNamespace(state="Uttarakhand", district="Dehradun")
        stations.filter.return_value.first.return_value = existing
        stations.update_or_create.return_value = (existing, False)
        observations.update_or_create.return_value = (SimpleNamespace(id=1), True)
        fetch_current.return_value = {
            "provider": "imd",
            "station_id": "IMD-1",
            "station_name": "Station A",
            "latitude": 30.1,
            "longitude": 78.2,
            "timestamp": __import__("datetime").datetime.fromisoformat("2026-09-07T10:00:00+00:00"),
            "rainfall_mm": 5.0,
            "temperature_c": 29.0,
            "humidity": 80.0,
            "water_level_m": None,
            "discharge_m3s": None,
        }

        WeatherIngestionService().refresh_location(30.1, 78.2)

        defaults = stations.update_or_create.call_args.kwargs["defaults"]
        self.assertEqual(defaults["state"], "Uttarakhand")
        self.assertEqual(defaults["district"], "Dehradun")
