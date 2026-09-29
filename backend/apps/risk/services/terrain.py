from __future__ import annotations

import csv
import math
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from apps.core.location_data import EVENT_ID_BY_LOCATION, LOCATIONS


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


@lru_cache(maxsize=1)
def _event_rows() -> dict[str, dict]:
    dataset_path = Path(settings.BASE_DIR) / "data" / "raw" / "Raw_Events_Location.csv"
    if not dataset_path.is_file():
        return {}
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["Event ID"]: row for row in csv.DictReader(handle)}


def _numeric_slope(value: str) -> float | None:
    text = str(value or "").lower()
    if "near-vertical" in text or "near vertical" in text:
        return 75.0
    values = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", text)]
    if not values:
        return None
    return sum(values) / len(values)


def _numeric_distance(value: str) -> float | None:
    values = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", str(value or ""))]
    return min(values) if values else None


def terrain_features(latitude: float, longitude: float) -> dict:
    nearest_key = None
    nearest_distance = None
    for key, location in LOCATIONS.items():
        distance = _distance_km(latitude, longitude, location["lat"], location["lng"])
        if nearest_distance is None or distance < nearest_distance:
            nearest_key = key
            nearest_distance = distance

    if nearest_key is None or nearest_distance is None or nearest_distance > 75.0:
        return {
            "elevation_m": None,
            "slope_deg": None,
            "drainage_index": None,
            "source": getattr(settings, "RISK_TERRAIN_SOURCE", "unconfigured"),
        }

    event_id = EVENT_ID_BY_LOCATION.get(nearest_key)
    row = _event_rows().get(event_id, {})
    slope = _numeric_slope(row.get("Slope(In degrees)", ""))
    river_distance = _numeric_distance(row.get("River distance(metres)", ""))
    drainage_index = None
    if river_distance is not None:
        drainage_index = max(0.0, min(100.0, 100.0 - (river_distance / 1500.0) * 100.0))

    return {
        "elevation_m": None,
        "slope_deg": slope,
        "drainage_index": drainage_index,
        "source": "verified_location_event_dataset",
        "reference_location": LOCATIONS[nearest_key]["name"],
        "reference_distance_km": round(nearest_distance, 2),
        "event_id": event_id,
    }
