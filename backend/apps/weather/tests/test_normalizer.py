from django.test import SimpleTestCase

from apps.weather.services.normalizer import normalize_weather_records


class WeatherNormalizerTests(SimpleTestCase):
    def test_normalizes_common_station_payload(self):
        rows = normalize_weather_records(
            {
                "data": [
                    {
                        "station_id": "IMD-1",
                        "station_name": "Station A",
                        "lat": 30.1,
                        "lon": 78.2,
                        "timestamp": "2026-09-07T10:00:00Z",
                        "rainfall": 12.5,
                        "temperature": 29.0,
                        "humidity": 80,
                    }
                ]
            },
            provider="imd",
        )
        self.assertEqual(rows[0]["station_id"], "IMD-1")
        self.assertEqual(rows[0]["rainfall_mm"], 12.5)
        self.assertEqual(rows[0]["latitude"], 30.1)
        self.assertEqual(rows[0]["longitude"], 78.2)
        self.assertEqual(rows[0]["provider"], "imd")

    def test_rejects_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            normalize_weather_records(
                [{"station_id": "bad", "lat": 95, "lon": 78, "timestamp": "2026-09-07T10:00:00Z"}],
                provider="imd",
            )
