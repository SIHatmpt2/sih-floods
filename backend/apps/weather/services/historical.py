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
    """Fetch historical hourly weather for a requested date/time."""

    @staticmethod
    def analysis_window(analysis_date: date) -> tuple[date, date]:
        return analysis_date - timedelta(days=6), analysis_date

    def for_date(
        self,
        latitude: float,
        longitude: float,
        analysis_date: date,
        analysis_datetime: datetime | None = None,
    ) -> dict:
        if analysis_datetime is not None:
            if analysis_datetime.tzinfo is None:
                analysis_datetime = analysis_datetime.replace(tzinfo=IST)
            else:
                analysis_datetime = analysis_datetime.astimezone(IST)
            analysis_date = analysis_datetime.date()
            start_date = (analysis_datetime - timedelta(days=7)).date()
        else:
            start_date, _ = self.analysis_window(analysis_date)

        cache_suffix = (
            analysis_datetime.isoformat() if analysis_datetime is not None else analysis_date.isoformat()
        )
        cache_key = (
            f"floodintel:historical-weather:{float(latitude):.4f}:"
            f"{float(longitude):.4f}:{cache_suffix}"
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        end_date = analysis_date
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

        if analysis_date.year >= 2022:
            try:
                payload = self._request(HISTORICAL_FORECAST_API, common)
                result = self._build_result(
                    payload,
                    analysis_date,
                    source="open-meteo-historical-forecast",
                    dataset="Open-Meteo Historical Forecast",
                    analysis_datetime=analysis_datetime,
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

        try:
            payload = self._request(ARCHIVE_API, {**common, "models": "era5"})
            result = self._build_result(
                payload,
                analysis_date,
                source="open-meteo-era5",
                dataset="ERA5 reanalysis",
                analysis_datetime=analysis_datetime,
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
            result = self._build_nasa_result(
                payload,
                analysis_date,
                start_date,
                end_date,
                analysis_datetime=analysis_datetime,
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
        analysis_datetime: datetime | None = None,
    ) -> dict:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        precipitation = hourly.get("precipitation") or []
        rainfall = hourly.get("rain") or precipitation
        temperatures = hourly.get("temperature_2m") or []
        humidity = hourly.get("relative_humidity_2m") or []
        wind = hourly.get("wind_speed_10m") or []
        pressure = hourly.get("pressure_msl") or []

        if analysis_datetime is None:
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
            selected_rain = [row["precipitation"] for row in rows if row["precipitation"] is not None]
            recent_rain = all_rain[-72:] if all_rain else []
            last = rows[-1]
            return self._result_payload(
                analysis_date,
                analysis_datetime,
                rows,
                selected_rain,
                all_rain[-48:],
                recent_rain,
                last,
                source,
                dataset,
            )

        cutoff = analysis_datetime.astimezone(IST) if analysis_datetime.tzinfo else analysis_datetime.replace(tzinfo=IST)
        window_start = cutoff - timedelta(days=7)
        parsed_rows = []
        for index, timestamp in enumerate(times):
            local_time = self._local_datetime(timestamp)
            if window_start < local_time <= cutoff:
                parsed_rows.append((local_time, {
                    "time": local_time.isoformat(),
                    "precipitation": self._number(precipitation, index),
                    "rain": self._number(rainfall, index),
                    "temperature_c": self._number(temperatures, index),
                    "humidity": self._number(humidity, index),
                    "wind_speed_kmh": self._number(wind, index),
                    "pressure_hpa": self._number(pressure, index),
                }))

        if not parsed_rows:
            raise HistoricalWeatherError(
                f"No hourly observations were returned through {cutoff.isoformat()}."
            )

        parsed_rows.sort(key=lambda item: item[0])
        rows = [row for local_time, row in parsed_rows if local_time.date() == analysis_date]
        available = [(local_time, row["precipitation"]) for local_time, row in parsed_rows if row["precipitation"] is not None]
        if not rows:
            raise HistoricalWeatherError(
                f"No hourly observations were returned for {analysis_date.isoformat()}."
            )

        def window_sum(hours: int) -> list[float]:
            start = cutoff - timedelta(hours=hours)
            return [value for local_time, value in available if start < local_time <= cutoff]

        rain_24 = window_sum(24)
        rain_48 = window_sum(48)
        rain_72 = window_sum(72)
        rain_168 = window_sum(168)
        last = parsed_rows[-1][1]
        return self._result_payload(
            analysis_date,
            cutoff,
            rows,
            rain_24,
            rain_48,
            rain_72,
            last,
            source,
            dataset,
            rainfall_7d=rain_168,
            selected_observations=len(available),
        )

    def _result_payload(
        self,
        analysis_date,
        analysis_datetime,
        rows,
        rain_24,
        rain_48,
        rain_72,
        last,
        source,
        dataset,
        *,
        rainfall_7d=None,
        selected_observations=None,
    ):
        return {
            "analysis_date": analysis_date.isoformat(),
            "analysis_datetime": analysis_datetime.isoformat() if analysis_datetime else None,
            "rainfall_24h_mm": round(sum(rain_24), 2),
            "rainfall_3d_mm": round(sum(rain_72), 2),
            "rainfall_7d_mm": round(sum(rainfall_7d if rainfall_7d is not None else rain_72), 2),
            "rainfall_48h_mm": round(sum(rain_48), 2),
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
                "selected_window_observations": selected_observations,
                "resolution": "hourly",
                "partial": len(rows) < 24,
            },
        }

    def _build_nasa_result(
        self,
        payload: dict,
        analysis_date: date,
        start_date: date,
        end_date: date,
        analysis_datetime: datetime | None = None,
    ) -> dict:
        parameters = ((payload.get("properties") or {}).get("parameter") or {})
        temperature = parameters.get("T2M") or {}
        humidity = parameters.get("RH2M") or {}
        precipitation = parameters.get("PRECTOTCORR") or {}
        wind = parameters.get("WS10M") or {}
        pressure = parameters.get("PS") or {}

        timestamps = sorted(set(temperature) | set(humidity) | set(precipitation) | set(wind) | set(pressure))
        if not timestamps:
            raise HistoricalWeatherError(
                f"NASA POWER returned no hourly observations for {analysis_date.isoformat()}."
            )

        rows = []
        window_rain = []
        cutoff = None
        if analysis_datetime is not None:
            cutoff = analysis_datetime.astimezone(IST) if analysis_datetime.tzinfo else analysis_datetime.replace(tzinfo=IST)
            window_start = cutoff - timedelta(days=7)

        for timestamp in timestamps:
            utc_time = datetime.strptime(timestamp, "%Y%m%d%H").replace(tzinfo=timezone.utc)
            local_time = utc_time.astimezone(IST)
            local_date = local_time.date()
            rain_value = self._nasa_number(precipitation.get(timestamp))

            if cutoff is not None:
                in_window = window_start < local_time <= cutoff
            else:
                in_window = start_date <= local_date <= end_date
            if in_window and rain_value is not None:
                window_rain.append((local_time, rain_value))

            if local_date != analysis_date or (cutoff is not None and local_time > cutoff):
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
        if cutoff is None:
            rain_24 = [row["precipitation"] for row in rows if row["precipitation"] is not None]
            rain_48 = all_rain[-48:]
            rain_72 = all_rain[-72:]
            rain_7d = all_rain
        else:
            rain_24 = [value for local_time, value in window_rain if cutoff - timedelta(hours=24) < local_time <= cutoff]
            rain_48 = [value for local_time, value in window_rain if cutoff - timedelta(hours=48) < local_time <= cutoff]
            rain_72 = [value for local_time, value in window_rain if cutoff - timedelta(hours=72) < local_time <= cutoff]
            rain_7d = all_rain

        last = rows[-1]
        return self._result_payload(
            analysis_date,
            cutoff,
            rows,
            rain_24,
            rain_48,
            rain_72,
            last,
            "nasa-power",
            "NASA POWER MERRA-2",
            rainfall_7d=rain_7d,
            selected_observations=len(window_rain),
        )

    @staticmethod
    def _local_datetime(timestamp: str) -> datetime:
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=IST)
        return parsed.astimezone(IST)

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
