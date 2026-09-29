from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.weather.services.live import _accuweather


class LiveWeatherTests(SimpleTestCase):
    def test_accuweather_uses_hourly_and_24h_rainfall_separately(self):
        client = Mock()
        client.get.side_effect = [
            {
                "Key": "123",
                "LocalizedName": "Test",
                "GeoPosition": {"Latitude": 30.1, "Longitude": 78.2},
                "AdministrativeArea": {"LocalizedName": "Uttarakhand"},
                "SupplementalAdminAreas": [{"LocalizedName": "Dehradun"}],
            },
            [{
                "LocalObservationDateTime": "2026-09-29T10:00:00+00:00",
                "Temperature": {"Metric": {"Value": 25}},
                "RelativeHumidity": 80,
                "PrecipitationSummary": {
                    "PastHour": {"Metric": {"Value": 4}},
                    "Past24Hours": {"Metric": {"Value": 42}},
                },
            }],
        ]

        result = _accuweather(client, 30.1, 78.2, "secret")

        self.assertEqual(result["rainfall_mm"], 4.0)
        self.assertEqual(result["rainfall_24h_mm"], 42.0)
        self.assertEqual(client.get.call_args_list[0].kwargs["api_key"], "secret")
        self.assertNotIn("api_key_param", client.get.call_args_list[0].kwargs)
