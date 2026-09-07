from django.db.models import Avg, Count
from django.contrib.gis.db.models.functions import Centroid
from django.utils import timezone
from ..models import RiskAssessment, HotspotSnapshot


def refresh_hotspots(limit=50):
    qs = (
        RiskAssessment.objects.filter(score__gte=50)
        .values("risk_level")
        .annotate(score=Avg("score"), assessment_count=Count("id"), centroid=Centroid("location"))
        .order_by("-score")[:limit]
    )
    created = 0
    for row in qs:
        if row["centroid"] is None:
            continue
        HotspotSnapshot.objects.create(
            snapshot_at=timezone.now(),
            centroid=row["centroid"],
            score=float(row["score"]),
            risk_level=row["risk_level"],
            assessment_count=row["assessment_count"],
            metadata={"aggregation": "risk_level"},
        )
        created += 1
    return created
