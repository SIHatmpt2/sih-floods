from datetime import date

from apps.risk.services.zone_manager import assess_point
from apps.risk.services.analytics import assessment_summary, risk_distribution
from apps.risk.selectors import assessment_history, high_risk_zones, nearest_zone
from apps.risk.services import cache


class RiskService:
    """Stable application-facing facade used by Core and other domains."""

    def current(self, latitude: float, longitude: float, weather=None) -> dict:
        if weather is None:
            cached = cache.get_current(latitude, longitude)
            if cached:
                return cached

        zone = nearest_zone(latitude, longitude)
        result = assess_point(latitude, longitude, zone=zone, persist=False, weather=weather)
        payload = {
            "risk_score": result.score,
            "risk_level": result.level,
            "breakdown": result.breakdown,
            "features": result.features,
            "model_source": result.model_source,
            "data_quality": result.data_quality,
        }

        if weather is None:
            cache.set_current(latitude, longitude, payload)
        return payload

    def historical(self, latitude: float, longitude: float, analysis_date: date, weather: dict) -> dict:
        """Run the risk model against reconstructed conditions for a past date."""
        zone = nearest_zone(latitude, longitude)
        result = assess_point(
            latitude,
            longitude,
            zone=zone,
            persist=False,
            weather=weather,
            analysis_date=analysis_date,
        )
        return {
            "risk_score": result.score,
            "risk_level": result.level,
            "breakdown": result.breakdown,
            "features": result.features,
            "model_source": result.model_source,
            "data_quality": result.data_quality,
        }

    def breakdown(self, latitude: float, longitude: float) -> dict:
        result = self.current(latitude, longitude)
        return {
            "risk_score": result.get("risk_score"),
            "risk_level": result.get("risk_level"),
            "breakdown": result.get("breakdown", {}),
            "data_quality": result.get("data_quality", {}),
            "model_source": result.get("model_source", "baseline"),
        }

    def refresh_zone(self, zone_id: int):
        from apps.risk.models import RiskZone
        zone = RiskZone.objects.get(pk=zone_id)
        centroid = zone.geometry.centroid
        return assess_point(centroid.y, centroid.x, zone=zone, persist=True)

    def history(self, latitude: float, longitude: float, days=7):
        return assessment_history(latitude, longitude, days=days)

    def get_summary(self, days=7):
        return assessment_summary(days=days)

    def get_distribution(self):
        return risk_distribution()

    def high_risk_zones(self, limit=100):
        return high_risk_zones()[:limit]
