from django.core.cache import cache

KEY_PREFIX = "risk:current"
TTL_SECONDS = 300


def _key(latitude, longitude):
    return f"{KEY_PREFIX}:{float(latitude):.5f}:{float(longitude):.5f}"


def get_current(latitude, longitude):
    return cache.get(_key(latitude, longitude))


def set_current(latitude, longitude, value, timeout=TTL_SECONDS):
    cache.set(_key(latitude, longitude), value, timeout=timeout)


def clear_current(latitude, longitude):
    cache.delete(_key(latitude, longitude))
