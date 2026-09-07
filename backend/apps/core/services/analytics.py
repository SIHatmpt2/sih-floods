from django.db.models import Count
from apps.risk.models import RiskAssessment


class AnalyticsService:
    """Read-only application analytics over persisted risk assessments."""

    def daily_summary(self) -> dict:
        distribution = {
            row["risk_level"]: row["count"]
            for row in RiskAssessment.objects.values("risk_level").annotate(count=Count("id"))
        }
        return {"total_assessments": RiskAssessment.objects.count(), "risk_distribution": distribution}

    def state_summary(self, state: str | None = None) -> dict:
        queryset = RiskAssessment.objects.select_related("zone")
        if state:
            queryset = queryset.filter(zone__state__iexact=state)
        distribution = {
            row["risk_level"]: row["count"]
            for row in queryset.values("risk_level").annotate(count=Count("id"))
        }
        return {"state": state, "risk_distribution": distribution}
