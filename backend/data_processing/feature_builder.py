"""Build the feature contract consumed by the trained Risk model."""
from __future__ import annotations

from datetime import datetime


def build_risk_features(weather: dict) -> dict:
    """Map normalized weather data into the V1.5 model feature names."""
    now = datetime.now().astimezone()
    rainfall_24h = weather.get("rainfall_24h_mm", weather.get("rainfall_mm"))
    rainfall_3d = weather.get("rainfall_3d_mm")
    rainfall_7d = weather.get("rainfall_7d_mm")
    rainfall_30d = weather.get("rainfall_30d_mm")
    water_level = weather.get("water_level_m")
    discharge = weather.get("discharge_m3s")
    water_change = weather.get("water_level_change")
    discharge_change = weather.get("discharge_change")

    return {
        "rainfall_24h": rainfall_24h,
        "rainfall_48h": weather.get("rainfall_48h_mm", rainfall_3d),
        "rainfall_72h": rainfall_3d,
        "rainfall_7d": rainfall_7d,
        "rainfall_30d": rainfall_30d,
        "water_level_m": water_level,
        "water_level_delta_1h": water_change,
        "water_level_pct_change_1h": weather.get("water_level_pct_change_1h"),
        "water_level_lag_1h": weather.get("water_level_lag_1h", water_level),
        "water_level_lag_3h": weather.get("water_level_lag_3h", water_level),
        "water_level_lag_6h": weather.get("water_level_lag_6h", water_level),
        "water_level_lag_12h": weather.get("water_level_lag_12h", water_level),
        "water_level_lag_24h": weather.get("water_level_lag_24h", water_level),
        "water_level_rolling_mean_6h": weather.get("water_level_rolling_mean_6h", water_level),
        "water_level_rolling_max_6h": weather.get("water_level_rolling_max_6h", water_level),
        "water_level_rolling_std_6h": weather.get("water_level_rolling_std_6h"),
        "water_level_rolling_mean_24h": weather.get("water_level_rolling_mean_24h", water_level),
        "water_level_rolling_max_24h": weather.get("water_level_rolling_max_24h", water_level),
        "water_level_rolling_std_24h": weather.get("water_level_rolling_std_24h"),
        "discharge_cumecs": discharge,
        "discharge_delta_1h": discharge_change,
        "discharge_pct_change_1h": weather.get("discharge_pct_change_1h"),
        "discharge_lag_1h": weather.get("discharge_lag_1h", discharge),
        "discharge_lag_3h": weather.get("discharge_lag_3h", discharge),
        "discharge_lag_6h": weather.get("discharge_lag_6h", discharge),
        "discharge_lag_12h": weather.get("discharge_lag_12h", discharge),
        "discharge_lag_24h": weather.get("discharge_lag_24h", discharge),
        "discharge_rolling_mean_6h": weather.get("discharge_rolling_mean_6h", discharge),
        "discharge_rolling_max_6h": weather.get("discharge_rolling_max_6h", discharge),
        "discharge_rolling_std_6h": weather.get("discharge_rolling_std_6h"),
        "discharge_rolling_mean_24h": weather.get("discharge_rolling_mean_24h", discharge),
        "discharge_rolling_max_24h": weather.get("discharge_rolling_max_24h", discharge),
        "discharge_rolling_std_24h": weather.get("discharge_rolling_std_24h"),
        "flood_count_1y": weather.get("flood_count_1y", weather.get("recent_event_count", 0)),
        "flood_count_3y": weather.get("flood_count_3y", weather.get("event_count", 0)),
        "flood_count_5y": weather.get("flood_count_5y", weather.get("event_count", 0)),
        "days_since_last_flood": weather.get("days_since_last_flood"),
        "historical_max_severity": weather.get("historical_max_severity", weather.get("max_severity", 0.0)),
        "historical_mean_severity": weather.get("historical_mean_severity", weather.get("max_severity", 0.0)),
        "historical_glof_count": weather.get("historical_glof_count", 0),
        "month": now.month,
        "day_of_year": now.timetuple().tm_yday,
        "is_monsoon": int(now.month in (6, 7, 8, 9)),
        "temperature_c": weather.get("temperature_c"),
        "humidity": weather.get("humidity"),
        "slope_deg": weather.get("slope_deg"),
        "elevation_m": weather.get("elevation_m"),
        "historical_score": weather.get("historical_score"),
    }
