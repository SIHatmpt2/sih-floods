from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.utils import timezone

from apps.weather.models import WeatherStation


def _stations(point):
    """
    Return up to five nearest stations with usable river observations.

    CWC stations are preferred when available; otherwise stations from
    other providers are returned.
    """
    base = (
        WeatherStation.objects.filter(
            Q(observations__discharge_m3s__isnull=False)
            | Q(observations__water_level_m__isnull=False),
            active=True,
            location__distance_lte=(point, 75_000),
        )
        .distinct()
    )

    cwc = (
        base.filter(provider="cwc")
        .annotate(distance=Distance("location", point))
        .order_by("distance")
    )

    stations = list(cwc[:5])
    if stations:
        return stations

    return list(
        base.annotate(distance=Distance("location", point))
        .order_by("distance")[:5]
    )


from functools import lru_cache
from pathlib import Path

RIVER_DATASET = Path(__file__).resolve().parents[2] / 'risk' / 'data' / 'processed' / 'river_data' / 'parquet' / 'river_observations.parquet'

@lru_cache(maxsize=1)
def _parquet_snapshot():
    if not RIVER_DATASET.is_file():
        return None
    try:
        import pyarrow.dataset as ds
        table = ds.dataset(RIVER_DATASET, format='parquet').to_table(columns=['station_id','station','latitude','longitude','observed_at','water_level_m','discharge_cumecs'])
        return table.to_pandas()
    except Exception:
        return None

def _river_features_from_parquet(latitude, longitude, now):
    frame = _parquet_snapshot()
    if frame is None or frame.empty:
        return None
    import math
    import pandas as pd
    frame['observed_at'] = pd.to_datetime(frame['observed_at'], errors='coerce', utc=True)
    for column in ('latitude','longitude','water_level_m','discharge_cumecs'):
        frame[column] = pd.to_numeric(frame[column], errors='coerce')
    frame = frame.dropna(subset=['station_id','latitude','longitude','observed_at'])
    now_utc = pd.Timestamp(now).tz_convert('UTC')
    frame = frame[(frame['observed_at'] <= now_utc) & (frame['observed_at'] >= now_utc - pd.Timedelta(days=7))]
    if frame.empty:
        return None
    lat_delta = frame['latitude'] - float(latitude)
    lon_delta = (frame['longitude'] - float(longitude)) * math.cos(math.radians(float(latitude)))
    frame['_distance2'] = lat_delta * lat_delta + lon_delta * lon_delta
    nearest = frame.sort_values('_distance2').groupby('station_id', sort=False).head(1).sort_values('_distance2').head(5)
    if nearest.empty:
        return None
    station_id = nearest.iloc[0]['station_id']
    station_rows = frame[frame['station_id'] == station_id].sort_values('observed_at')
    latest = station_rows.iloc[-1]
    previous_rows = station_rows[station_rows['observed_at'] < latest['observed_at']]
    previous = previous_rows.iloc[-1] if not previous_rows.empty else None
    level = None if pd.isna(latest['water_level_m']) else float(latest['water_level_m'])
    discharge = None if pd.isna(latest['discharge_cumecs']) else float(latest['discharge_cumecs'])
    previous_level = None if previous is None or pd.isna(previous['water_level_m']) else float(previous['water_level_m'])
    previous_discharge = None if previous is None or pd.isna(previous['discharge_cumecs']) else float(previous['discharge_cumecs'])
    return {
        'water_level_m': level,
        'discharge_m3s': discharge,
        'water_level_change': level - previous_level if level is not None and previous_level is not None else None,
        'discharge_change': discharge - previous_discharge if discharge is not None and previous_discharge is not None else None,
        'station_id': str(station_id),
        'station_name': str(latest.get('station') or station_id),
        'observed_at': latest['observed_at'].to_pydatetime(),
        'source': 'cwc_parquet',
    }
def river_features(latitude, longitude):
    point = Point(float(longitude), float(latitude), srid=4326)
    stations = _stations(point)

    empty = {
        "water_level_m": None,
        "discharge_m3s": None,
        "water_level_change": None,
        "discharge_change": None,
    }

    now = timezone.now()
    if not stations:
        return _river_features_from_parquet(latitude, longitude, now) or empty
    latest = None
    station = None

    for candidate in stations:
        observation = (
            candidate.observations.filter(timestamp__lte=now)
            .filter()
            .order_by("-timestamp")
            .first()
        )
        if observation is not None:
            latest = observation
            station = candidate
            break

    if latest is None:
        return empty

    previous = None
    if isinstance(latest.timestamp, datetime):
        previous = (
            station.observations.filter(timestamp__lt=latest.timestamp)
            .filter(
                timestamp__gte=latest.timestamp - timedelta(hours=24)
            )
            .order_by("-timestamp")
            .first()
        )

    return {
        "water_level_m": latest.water_level_m,
        "discharge_m3s": latest.discharge_m3s,
        "water_level_change": (
            latest.water_level_m - previous.water_level_m
            if previous
            and latest.water_level_m is not None
            and previous.water_level_m is not None
            else None
        ),
        "discharge_change": (
            latest.discharge_m3s - previous.discharge_m3s
            if previous
            and latest.discharge_m3s is not None
            and previous.discharge_m3s is not None
            else None
        ),
    }
