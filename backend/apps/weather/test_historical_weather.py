from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.historical import HistoricalWeatherService


class HistoricalWeatherServiceTests(SimpleTestCase):
    def test_build_window_uses_previous_six_days(self):
        start, end = HistoricalWeatherService.analysis_window(date(2023, 6, 13))
        self.assertEqual(start.isoformat(), "2023-06-07")
        self.assertEqual(end.isoformat(), "2023-06-13")

    @patch("apps.weather.services.historical.urlopen")
    def test_historical_weather_uses_forecast_archive_for_recent_dates(self, urlopen):
        payload = {
            "timezone": "Asia/Kolkata",
            "hourly": {
                "time": ["2024-06-13T22:00", "2024-06-13T23:00"],
                "precipitation": [10.0, 5.0],
                "rain": [10.0, 5.0],
                "temperature_2m": [20.0, 19.0],
                "relative_humidity_2m": [90.0, 92.0],
                "wind_speed_10m": [8.0, 10.0],
                "pressure_msl": [900.0, 899.0],
            },
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                import json
                return json.dumps(payload).encode()

        urlopen.return_value = Response()
        result = HistoricalWeatherService().for_date(31.71194, 76.93273, date(2024, 6, 13))

        self.assertEqual(result["analysis_date"], "2024-06-13")
        self.assertEqual(result["rainfall_24h_mm"], 15.0)
        self.assertEqual(result["temperature_c"], 19.0)
        self.assertEqual(result["humidity"], 92.0)
        self.assertEqual(result["data_quality"]["source"], "open-meteo-historical-forecast")

    @patch("apps.weather.services.historical.urlopen")
    def test_historical_weather_falls_back_to_best_match_archive(self, urlopen):
        payload = {
            "timezone": "Asia/Kolkata",
            "hourly": {
                "time": ["2024-06-13T22:00", "2024-06-13T23:00"],
                "precipitation": [10.0, 5.0],
                "rain": [10.0, 5.0],
                "temperature_2m": [20.0, 19.0],
                "relative_humidity_2m": [90.0, 92.0],
                "wind_speed_10m": [8.0, 10.0],
                "pressure_msl": [900.0, 899.0],
            },
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                import json
                return json.dumps(payload).encode()

        urlopen.side_effect = [TimeoutError("historical forecast timeout"), Response()]
        result = HistoricalWeatherService().for_date(31.71194, 76.93273, date(2024, 6, 13))

        self.assertEqual(result["data_quality"]["source"], "open-meteo-best-match")
        self.assertEqual(result["rainfall_24h_mm"], 15.0)
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("models=best_match", urlopen.call_args.args[0].full_url)

    @patch("apps.weather.services.historical.urlopen")
    def test_historical_weather_uses_best_match_for_older_dates(self, urlopen):
        payload = {
            "timezone": "Asia/Kolkata",
            "hourly": {
                "time": ["2023-06-13T22:00", "2023-06-13T23:00"],
                "precipitation": [10.0, 5.0],
                "rain": [10.0, 5.0],
                "temperature_2m": [20.0, 19.0],
                "relative_humidity_2m": [90.0, 92.0],
                "wind_speed_10m": [8.0, 10.0],
                "pressure_msl": [900.0, 899.0],
            },
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                import json
                return json.dumps(payload).encode()

        urlopen.return_value = Response()
        result = HistoricalWeatherService().for_date(31.71194, 76.93273, date(2023, 6, 13))

        self.assertEqual(result["analysis_date"], "2023-06-13")
        self.assertEqual(result["rainfall_24h_mm"], 15.0)
        self.assertEqual(result["data_quality"]["source"], "open-meteo-best-match")

    @patch("apps.weather.services.historical.urlopen")
    def test_best_match_failure_falls_back_to_era5(self, urlopen):
        payload = {
            "timezone": "Asia/Kolkata",
            "hourly": {
                "time": ["2023-06-13T22:00", "2023-06-13T23:00"],
                "precipitation": [10.0, 5.0],
                "rain": [10.0, 5.0],
                "temperature_2m": [20.0, 19.0],
                "relative_humidity_2m": [90.0, 92.0],
                "wind_speed_10m": [8.0, 10.0],
                "pressure_msl": [900.0, 899.0],
            },
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                import json
                return json.dumps(payload).encode()

        urlopen.side_effect = [TimeoutError("best match timeout"), Response()]
        result = HistoricalWeatherService().for_date(31.71194, 76.93273, date(2023, 6, 13))

        self.assertEqual(result["data_quality"]["source"], "open-meteo-era5")
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("models=era5", urlopen.call_args.args[0].full_url)

    @patch("apps.weather.services.historical.urlopen")
    def test_all_historical_sources_failure_is_reported(self, urlopen):
        urlopen.side_effect = TimeoutError("archive timeout")

        with self.assertRaisesRegex(Exception, "Historical weather API failed"):
            HistoricalWeatherService().for_date(31.71194, 76.93273, date(2023, 6, 13))
