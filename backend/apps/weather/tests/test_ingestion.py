from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.weather.services.ingestion import WeatherIngestionService


class WeatherIngestionTests(SimpleTestCase):
    @patch("apps.weather.services.ingestion.WeatherProviderClient")
    @patch("apps.weather.services.ingestion.WeatherObservation.objects")
    @patch("apps.weather.services.ingestion.WeatherStation.objects")
    def test_store_does_not_erase_existing_station_metadata(self, stations, observations, client):
        station = SimpleNamespace(state="Uttarakhand", district="Dehradun")
        stations.update_or_create.return_value = (station, False)
        observations.update_or_create.return_value = (SimpleNamespace(), True)

        WeatherIngestionService().store([{
            "provider": "imd",
            "station_id": "IMD-1",
            "station_name": "Station A",
            "latitude": 30.1,
            "longitude": 78.2,
            "timestamp": "2026-09-07T10:00:00+00:00",
            "rainfall_mm": 5.0,
            "temperature_c": 29.0,
            "humidity": 80.0,
            "water_level_m": None,
            "discharge_m3s": None,
        }])

        self.assertNotIn("state", stations.update_or_create.call_args.kwargs["defaults"])
        self.assertNotIn("district", stations.update_or_create.call_args.kwargs["defaults"])

    @patch("apps.weather.services.ingestion.WeatherProviderClient")
    def test_uses_weather_api_timeout_setting(self, client):
        with self.settings(WEATHER_API_TIMEOUT=11):
            WeatherIngestionService()
        client.assert_called_once_with(timeout=11)
