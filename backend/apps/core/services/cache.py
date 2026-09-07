from __future__ import annotations
from typing import Any
from django.core.cache import cache

DASHBOARD_CACHE_TTL = 900


def dashboard_key(user_id: int, latitude: float, longitude: float) -> str:
    return f"dashboard:{user_id}:{latitude:.5f}:{longitude:.5f}"


def get_dashboard(user_id: int, latitude: float, longitude: float) -> Any:
    return cache.get(dashboard_key(user_id, latitude, longitude))


def set_dashboard(
    user_id: int, latitude: float, longitude: float, value: Any,
    timeout: int = DASHBOARD_CACHE_TTL,
) -> None:
    cache.set(dashboard_key(user_id, latitude, longitude), value, timeout)


def clear_dashboard(user_id: int, latitude: float, longitude: float) -> None:
    cache.delete(dashboard_key(user_id, latitude, longitude))
