from backend.services.weather_service import WeatherService
from backend.services.risk_service import RiskService
from .cache import get_dashboard, set_dashboard
from .notification import NotificationService


class DashboardService:
    """Composes Weather + Risk data for the application dashboard."""

    def __init__(self):
        self.weather = WeatherService()
        self.risk = RiskService()
        self.notifications = NotificationService()

    def build(self, user, latitude: float, longitude: float) -> dict:
        user_id = getattr(user, "id", 0)
        cached = get_dashboard(user_id, latitude, longitude)
        if cached is not None:
            return cached

        weather = self.weather.current(latitude, longitude)
        risk = self.risk.assess(latitude, longitude)
        payload = {
            "weather": weather,
            "risk": risk,
            "alerts": [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "status": n.status,
                }
                for n in self.notifications.list(user)[:10]
            ],
            "summary": {
                "temperature": weather.get("temperature_c"),
                "risk_score": risk.get("risk_score"),
                "risk_level": risk.get("risk_level"),
            },
        }
        set_dashboard(user_id, latitude, longitude, payload)
        return payload
