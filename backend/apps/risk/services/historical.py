from .normalizer import clamp
from ..selectors import recent_flood_events


def historical_features(latitude, longitude):
    events = list(recent_flood_events(latitude, longitude, radius_km=50, days=3650))
    if not events:
        return {"event_count": 0, "recent_event_count": 0, "max_severity": 0.0, "historical_score": 0.0}
    max_severity = max((event.severity or 0.0) for event in events)
    event_score = clamp(len(events) * 10.0)
    severity_score = clamp(max_severity)
    return {
        "event_count": len(events),
        "recent_event_count": min(len(events), 10),
        "max_severity": severity_score,
        "historical_score": clamp(event_score * 0.6 + severity_score * 0.4),
    }
