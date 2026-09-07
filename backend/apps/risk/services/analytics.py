from datetime import timedelta
from django.db.models import Avg, Count
from django.utils import timezone
from ..models import RiskAssessment, RiskZone


def risk_distribution():
    rows = (
        RiskZone.objects.filter(is_active=True)
        .values("risk_level")
        .annotate(count=Count("id"), average_score=Avg("latest_score"))
        .order_by("risk_level")
    )
    return list(rows)


def assessment_summary(days=7):
    since = timezone.now() - timedelta(days=days)
    qs = RiskAssessment.objects.filter(observed_at__gte=since)
    return {
        "days": days,
        "count": qs.count(),
        "average_score": qs.aggregate(value=Avg("score"))["value"],
        "severe_count": qs.filter(risk_level="severe").count(),
        "high_count": qs.filter(risk_level="high").count(),
    }
