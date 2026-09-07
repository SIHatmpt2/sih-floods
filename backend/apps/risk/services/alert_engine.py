from django.contrib.gis.geos import Point
from ..models import RiskAlert

THRESHOLDS = {"moderate": 25, "high": 50, "severe": 75}


def _should_alert(score):
    return score >= THRESHOLDS["high"]


def create_or_update_alert(zone, score, level, breakdown):
    if not _should_alert(score):
        return None
    location = zone.geometry.centroid
    title = f"{level.title()} flood-risk alert for {zone.name}"
    message = f"Current risk score is {score:.1f}/100. Review the risk breakdown and local conditions."
    alert = RiskAlert.objects.filter(zone=zone, status__in=["open", "read"]).first()
    if alert:
        alert.trigger_score = score
        alert.severity = level
        alert.message = message
        alert.metadata = {"breakdown": breakdown}
        alert.save(update_fields=["trigger_score", "severity", "message", "metadata"])
        return alert
    return RiskAlert.objects.create(
        zone=zone,
        location=Point(location.x, location.y, srid=4326),
        severity=level,
        title=title,
        message=message,
        trigger_score=score,
        metadata={"breakdown": breakdown},
    )
