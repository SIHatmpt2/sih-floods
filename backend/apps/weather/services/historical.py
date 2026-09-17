from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from django.core.cache import cache


HISTORICAL_FORECAST_API = "https://historical-forecast-api.open-meteo.com/v1/forecast"
ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
NASA_POWER_API = "https://power.larc.nasa.gov/api/temporal/hourly/point"
IST = ZoneInfo("Asia/Kolkata")


class HistoricalWeatherError(RuntimeError):
    """Raised when historical weather cannot be reconstructed."""


class HistoricalWeatherService:
    """Fetch historical hourly weather for a requested date.

    Open-Meteo is preferred because its historical forecast/archive data uses
    the same normalized variables as the live weather pipeline. NASA POWER is
    the final fallback because it provides globally available hourly historical
    meteorology without an API key.
    """

    @staticmethod
    def analysis_window(analysis_date: date) -> tuple[date, date]:
        return analysis_date - timedelta(days=6), analysis_date

    def for_date(self, latitude: float, longitude: float, analysis_date: date) -> dict:
        cache_key = (
            f"floodintel:historical-weather:{float(latitude):.4f}:"
            f"{float(longitude):.4f}:{analysis_date.isoformat()}"
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        start_date, end_date = self.analysis_window(analysis_date)
        common = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": (
                "temperature_2m,relative_humidity_2m,precipitation,rain,"
                "wind_speed_10m,pressure_msl"
            ),
            "timezone": "Asia/Kolkata",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }
        errors = []

        # Recent dates use the historical forecast archive first.
        if analysis_date.year >= 2022:
            try:
                payload = self._request(HISTORICAL_FORECAST_API, common)
                result = self._build_result(
                    payload,
                    analysis_date,
                    source="open-meteo-historical-forecast",
                    dataset="Open-Meteo Historical Forecast",
                )
                cache.set(cache_key, result, timeout=60 * 60 * 24 * 30)
                return result
            except (
                HTTPError,
                URLError,
                TimeoutError,
                OSError,
                ValueError,
                HistoricalWeatherError,
            ) as exc:
                errors.append(f"Open-Meteo Historical Forecast: {exc}")

        # ERA5 provides long-range historical coverage and is also useful as
        # a fallback when the historical forecast host is unavailable.
        try:
            payload = self._request(ARCHIVE_API, {**common, "models": "era5"})
            result = self._build_result(
                payload,
                analysis_date,
                source="open-meteo-era5",
                dataset="ERA5 reanalysis",
            )
            cache.set(cache_key, result, timeout=60 * 60 * 24 * 30)
            return result
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            HistoricalWeatherError,
        ) as exc:
            errors.append(f"Open-Meteo ERA5: {exc}")

        # Final fallback. NASA POWER has global hourly meteorological data
        # from 2001 onward, so it covers every date supported by this feature.
        # POWER timestamps are UTC here; request one extra UTC day on each side
        # so the requested Asia/Kolkata calendar window is complete after
        # timezone conversion.
        try:
            nasa_start = start_date - timedelta(days=1)
            nasa_end = end_date + timedelta(days=1)
            payload = self._request(
                NASA_POWER_API,
                {
                    "parameters": "T2M,RH2M,PRECTOTCORR,WS10M,PS",
                    "community": "RE",
                    "longitude": longitude,
                    "latitude": latitude,
                    "start": nasa_start.strftime("%Y%m%d"),
                    "end": nasa_end.strftime("%Y%m%d"),
                    "format": "JSON",
                    "time-standard": "UTC",
                },
            )
            result = self._build_nasa_result(payload, analysis_date, start_date, end_date)
            cache.set(cache_key, result, timeout=60 * 60 * 24 * 30)
            return result
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            HistoricalWeatherError,
        ) as exc:
            errors.append(f"NASA POWER: {exc}")
            raise HistoricalWeatherError(
                f"Historical weather API failed for {analysis_date.isoformat()}: "
                + " | ".join(errors)
            ) from exc

    def _build_result(
        self,
        payload: dict,
        analysis_date: date,
        *,
        source: str,
        dataset: str,
    ) -> dict:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        precipitation = hourly.get("precipitation") or []
        rainfall = hourly.get("rain") or precipitation
        temperatures = hourly.get("temperature_2m") or []
        humidity = hourly.get("relative_humidity_2m") or []
        wind = hourly.get("wind_speed_10m") or []
        pressure = hourly.get("pressure_msl") or []

        rows = []
        for index, timestamp in enumerate(times):
            if not timestamp.startswith(analysis_date.isoformat()):
                continue
            rows.append({
                "time": timestamp,
                "precipitation": self._number(precipitation, index),
                "rain": self._number(rainfall, index),
                "temperature_c": self._number(temperatures, index),
                "humidity": self._number(humidity, index),
                "wind_speed_kmh": self._number(wind, index),
                "pressure_hpa": self._number(pressure, index),
            })

        if not rows:
            raise HistoricalWeatherError(
                f"No hourly observations were returned for {analysis_date.isoformat()}."
            )

        all_rain = [self._number(value) for value in precipitation if self._number(value) is not None]
        selected_rain = [
            row["precipitation"] for row in rows if row["precipitation"] is not None
        ]
        recent_rain = all_rain[-72:] if all_rain else []
        last = rows[-1]
        return {
            "analysis_date": analysis_date.isoformat(),
            "rainfall_24h_mm": round(sum(selected_rain), 2),
            "rainfall_3d_mm": round(sum(recent_rain), 2),
            "rainfall_7d_mm": round(sum(all_rain), 2),
            "rainfall_48h_mm": round(sum(all_rain[-48:]), 2),
            "temperature_c": last.get("temperature_c"),
            "humidity": last.get("humidity"),
            "wind_speed_kmh": last.get("wind_speed_kmh"),
            "pressure_hpa": last.get("pressure_hpa"),
            "hourly": rows,
            "data_quality": {
                "available": True,
                "source": source,
                "dataset": dataset,
                "selected_date_observations": len(rows),
                "partial": len(rows) < 24,
            },
        }

    def _build_nasa_result(
        self,
        payload: dict,
        analysis_date: date,
        start_date: date,
        end_date: date,
    ) -> dict:
        parameters = ((payload.get("properties") or {}).get("parameter") or {})
        temperature = parameters.get("T2M") or {}
        humidity = parameters.get("RH2M") or {}
        precipitation = parameters.get("PRECTOTCORR") or {}
        wind = parameters.get("WS10M") or {}
        pressure = parameters.get("PS") or {}

        timestamps = sorted(
            set(temperature)
            | set(humidity)
            | set(precipitation)
            | set(wind)
            | set(pressure)
        )
        if not timestamps:
            raise HistoricalWeatherError(
                f"NASA POWER returned no hourly observations for {analysis_date.isoformat()}."
            )

        rows = []
        window_rain = []
        for timestamp in timestamps:
            utc_time = datetime.strptime(timestamp, "%Y%m%d%H").replace(tzinfo=timezone.utc)
            local_time = utc_time.astimezone(IST)
            local_date = local_time.date()

            rain_value = self._nasa_number(precipitation.get(timestamp))
            if start_date <= local_date <= end_date and rain_value is not None:
                window_rain.append((local_time, rain_value))

            if local_date != analysis_date:
                continue
            rows.append({
                "time": local_time.isoformat(),
                "precipitation": rain_value,
                "rain": rain_value,
                "temperature_c": self._nasa_number(temperature.get(timestamp)),
                "humidity": self._nasa_number(humidity.get(timestamp)),
                "wind_speed_kmh": self._nasa_number(wind.get(timestamp), multiplier=3.6),
                "pressure_hpa": self._nasa_number(pressure.get(timestamp), multiplier=10.0),
            })

        if not rows:
            raise HistoricalWeatherError(
                f"NASA POWER returned no observations for {analysis_date.isoformat()}."
            )

        rows.sort(key=lambda row: row["time"])
        window_rain.sort(key=lambda item: item[0])
        all_rain = [value for _, value in window_rain]
        selected_rain = [row["precipitation"] for row in rows if row["precipitation"] is not None]
        recent_rain = all_rain[-72:]
        last = rows[-1]
        return {
            "analysis_date": analysis_date.isoformat(),
            "rainfall_24h_mm": round(sum(selected_rain), 2),
            "rainfall_3d_mm": round(sum(recent_rain), 2),
            "rainfall_7d_mm": round(sum(all_rain), 2),
            "rainfall_48h_mm": round(sum(all_rain[-48:]), 2),
            "temperature_c": last.get("temperature_c"),
            "humidity": last.get("humidity"),
            "wind_speed_kmh": last.get("wind_speed_kmh"),
            "pressure_hpa": last.get("pressure_hpa"),
            "hourly": rows,
            "data_quality": {
                "available": True,
                "source": "nasa-power",
                "dataset": "NASA POWER MERRA-2",
                "selected_date_observations": len(rows),
                "partial": len(rows) < 24,
            },
        }

    @staticmethod
    def _request(endpoint: str, params: dict) -> dict:
        query = urlencode(params)
        request = Request(
            f"{endpoint}?{query}",
            headers={"Accept": "application/json", "User-Agent": "FloodIntel/1.0"},
        )
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("error"):
            raise ValueError(payload.get("reason", "Unknown weather API error"))
        return payload

    @staticmethod
    def _number(values, index=None):
        if index is None:
            value = values
        elif index >= len(values):
            return None
        else:
            value = values[index]
        return float(value) if value is not None else None

    @staticmethod
    def _nasa_number(value, multiplier=1.0):
        if value is None:
            return None
        numeric = float(value)
        if numeric <= -900:
            return None
        return numeric * multiplier
