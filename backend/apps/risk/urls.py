from django.urls import path
from .views import (
    FloodEventListView, FloodEventDetailView,
    RiskZoneListView, RiskZoneNearbyView,
    RiskCurrentView, RiskBreakdownView, RiskSummaryView,
    HighRiskView, RiskHistoryView, RiskAlertListView,
    HotspotListView, RiskAnalyticsView,
)

urlpatterns = [
    path("events/", FloodEventListView.as_view(), name="risk-events"),
    path("events/<int:pk>/", FloodEventDetailView.as_view(), name="risk-event-detail"),
    path("zones/", RiskZoneListView.as_view(), name="risk-zones"),
    path("zones/nearby/", RiskZoneNearbyView.as_view(), name="risk-zones-nearby"),
    path("current/", RiskCurrentView.as_view(), name="risk-current"),
    path("breakdown/", RiskBreakdownView.as_view(), name="risk-breakdown"),
    path("summary/", RiskSummaryView.as_view(), name="risk-summary"),
    path("high-risk/", HighRiskView.as_view(), name="risk-high"),
    path("history/", RiskHistoryView.as_view(), name="risk-history"),
    path("alerts/", RiskAlertListView.as_view(), name="risk-alerts"),
    path("hotspots/", HotspotListView.as_view(), name="risk-hotspots"),
    path("analytics/", RiskAnalyticsView.as_view(), name="risk-analytics"),
]
