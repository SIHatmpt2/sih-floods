from __future__ import annotations

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point


class WeatherStation(models.Model):
    provider = models.CharField(max_length=32)
    station_id = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    location = models.PointField(geography=True, srid=4326)
    state = models.CharField(max_length=128, blank=True)
    district = models.CharField(max_length=128, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("provider", "station_id")]
        indexes = [
            models.Index(fields=["active", "provider"], name="ws_active_provider_idx"),
            models.Index(fields=["active", "state"], name="ws_active_state_idx"),
            models.Index(fields=["active", "district"], name="ws_active_district_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.station_id} ({self.name})"

    def coordinates(self) -> tuple[float, float]:
        point: Point = self.location
        return point.y, point.x


class WeatherObservation(models.Model):
    station = models.ForeignKey(WeatherStation, on_delete=models.CASCADE, related_name="observations")
    timestamp = models.DateTimeField()
    rainfall_mm = models.FloatField(null=True)
    temperature_c = models.FloatField(null=True)
    humidity = models.FloatField(null=True)
    water_level_m = models.FloatField(null=True)
    discharge_m3s = models.FloatField(null=True)

    class Meta:
        unique_together = [("station", "timestamp")]
        indexes = [
            models.Index(fields=["station", "-timestamp"], name="weather_obs_station_ts_idx"),
        ]
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.station.station_id} @ {self.timestamp.isoformat()}"
