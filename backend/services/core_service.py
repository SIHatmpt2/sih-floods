from apps.core.services.analytics import AnalyticsService
from apps.core.services.dashboard import DashboardService
from apps.core.services.notification import NotificationService
from apps.core.services.safe_zone import SafeZoneService


class CoreService:
    """Application facade for cross-domain Core operations."""

    def __init__(self):
        self._dashboard = DashboardService()
        self._analytics = AnalyticsService()
        self._notifications = NotificationService()
        self._safe_zone = SafeZoneService()

    def dashboard(self, user, latitude: float, longitude: float) -> dict:
        return self._dashboard.build(user, latitude, longitude)

    def analytics(self, state=None) -> dict:
        return self._analytics.state_summary(state) if state else self._analytics.daily_summary()

    def notifications(self, user, unread_only: bool = False):
        return self._notifications.list(user, unread_only=unread_only)

    def safe_zone(self, latitude: float, longitude: float):
        return self._safe_zone.nearest_safe_zone(latitude, longitude)
