from django.utils import timezone
from ..models import HotspotSnapshot, RiskAssessment


def refresh_hotspots(limit=50):
    rows = RiskAssessment.objects.filter(score__gte=50).order_by("-score", "-observed_at")[:limit]
    created = 0
    now = timezone.now()
    for assessment in rows:
        if assessment.location is None:
            continue
        HotspotSnapshot.objects.create(
            snapshot_at=now,
            centroid=assessment.location,
            score=float(assessment.score),
            risk_level=assessment.risk_level,
            assessment_count=1,
            metadata={"assessment_id": assessment.id, "aggregation": "top_assessments"},
        )
        created += 1
    return created
