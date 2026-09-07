from apps.core.services.analytics import AnalyticsService
from apps.core.services.dashboard import DashboardService
from apps.core.services.notification import NotificationService
from apps.core.services.safe_zone import SafeZoneService
from apps.core.services.location import LocationService


class CoreService:
    """Cross-domain orchestration entry point for Core APIs."""

    def __init__(self):
        self.dashboard_service = DashboardService()
        self.analytics_service = AnalyticsService()
        self.notification_service = NotificationService()
        self.safe_zone_service = SafeZoneService()
        self.location_service = LocationService()

    def dashboard(self, user, latitude: float, longitude: float) -> dict:
        return self.dashboard_service.build(user, latitude, longitude)

    def analytics(self, state: str | None = None) -> dict:
        return self.analytics_service.state_summary(state) if state else self.analytics_service.daily_summary()

    def notifications(self, user, unread_only: bool = False):
        return self.notification_service.list(user, unread_only=unread_only)

    def safe_zone(self, latitude: float, longitude: float):
        return self.safe_zone_service.nearest_safe_zone(latitude, longitude)

    def save_location(self, user, name, latitude, longitude, is_primary=False):
        return self.location_service.save(user, name, latitude, longitude, is_primary)

    def nearby_location(self, user, latitude, longitude):
        return self.location_service.nearby(user, latitude, longitude)
