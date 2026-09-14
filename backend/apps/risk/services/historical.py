from datetime import date, timedelta

from django.utils import timezone

from .normalizer import clamp
from ..selectors import recent_flood_events


def historical_features(latitude, longitude, analysis_date: date | None = None):
    """Build historical-event features using the requested analysis date."""
    analysis_date = analysis_date or timezone.now().date()
    events = list(recent_flood_events(latitude, longitude, radius_km=50, days=3650, end_date=analysis_date))
    if not events:
        return {
            "event_count": 0,
            "recent_event_count": 0,
            "max_severity": 0.0,
            "historical_score": 0.0,
            "days_since_last_flood": 0,
        }

    recent_cutoff = analysis_date - timedelta(days=365)
    recent_event_count = sum(event.event_date >= recent_cutoff for event in events)
    max_severity = max((event.severity or 0.0) for event in events)
    event_score = clamp(len(events) * 10.0)
    severity_score = clamp(max_severity)
    recent_score = clamp(recent_event_count * 15.0)
    days_since_last_flood = max(0, (analysis_date - events[0].event_date).days)
    return {
        "event_count": len(events),
        "recent_event_count": recent_event_count,
        "max_severity": severity_score,
        "historical_score": clamp(event_score * 0.4 + severity_score * 0.3 + recent_score * 0.3),
        "days_since_last_flood": days_since_last_flood,
    }
