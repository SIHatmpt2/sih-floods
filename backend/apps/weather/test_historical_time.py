from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .services.historical import HistoricalWeatherService


class HistoricalWeatherTimeTests(SimpleTestCase):
    def test_historical_weather_uses_rolling_window_from_analysis_time(self):
        ist = ZoneInfo("Asia/Kolkata")
        start = datetime(2026, 3, 5, 0, tzinfo=ist)
        times = []
        precipitation = []
        for index in range(48):
            timestamp = start + timedelta(hours=index)
            times.append(timestamp.isoformat())
            precipitation.append(1.0)

        payload = {
            "hourly": {
                "time": times,
                "temperature_2m": [20.0] * 48,
                "relative_humidity_2m": [70.0] * 48,
                "precipitation": precipitation,
                "rain": precipitation,
                "wind_speed_10m": [2.0] * 48,
                "pressure_msl": [1000.0] * 48,
            }
        }

        result = HistoricalWeatherService()._build_result(
            payload,
            date(2026, 3, 6),
            source="open-meteo-historical-forecast",
            dataset="Open-Meteo Historical Forecast",
            analysis_datetime=datetime(2026, 3, 6, 12, 30, tzinfo=ist),
        )

        self.assertEqual(result["analysis_datetime"], "2026-03-06T12:30:00+05:30")
        self.assertEqual(result["rainfall_24h_mm"], 24.0)
        self.assertEqual(result["rainfall_48h_mm"], 48.0)
