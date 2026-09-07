from backend.apps.risk.services.zone_manager import assess_point
from backend.apps.risk.services.analytics import assessment_summary, risk_distribution
from backend.apps.risk.selectors import nearby_zones, nearest_zone, assessment_history
from backend.apps.risk.services import cache


class RiskService:
    """Application-facing risk facade used by Core and other backend modules."""

    @staticmethod
    def get_current_risk(latitude, longitude):
        cached = cache.get_current(latitude, longitude)
        if cached:
            return cached
        zone = nearest_zone(latitude, longitude)
        result = assess_point(latitude, longitude, zone=zone, persist=False)
        return {
            "score": result.score,
            "level": result.level,
            "breakdown": result.breakdown,
            "features": result.features,
            "model_source": result.model_source,
            "data_quality": result.data_quality,
        }

    @staticmethod
    def get_risk_breakdown(latitude, longitude):
        return RiskService.get_current_risk(latitude, longitude)

    @staticmethod
    def list_high_risk_zones(limit=100):
        from backend.apps.risk.models import RiskZone
        return RiskZone.objects.filter(
            is_active=True, risk_level__in=["high", "severe"]
        ).order_by("-latest_score")[:limit]

    @staticmethod
    def refresh_zone(zone_id):
        from backend.apps.risk.models import RiskZone
        zone = RiskZone.objects.get(pk=zone_id)
        centroid = zone.geometry.centroid
        return assess_point(centroid.y, centroid.x, zone=zone, persist=True)

    @staticmethod
    def get_summary(days=7):
        return assessment_summary(days=days)

    @staticmethod
    def get_distribution():
        return risk_distribution()

    @staticmethod
    def get_history(latitude, longitude, days=7):
        return assessment_history(latitude, longitude, days=days)
