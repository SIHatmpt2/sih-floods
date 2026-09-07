from django.conf import settings


def terrain_features(latitude, longitude):
    return {
        "elevation_m": None,
        "slope_deg": None,
        "drainage_index": None,
        "source": getattr(settings, "RISK_TERRAIN_SOURCE", "unconfigured"),
    }
