from django.urls import path
from .views import (
    AnalyticsView, DashboardView, NotificationListView, SafeZoneView,
    UserLocationListCreateView, NearbyUserLocationView,
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("safe-zone/", SafeZoneView.as_view(), name="safe-zone"),
    path("locations/", UserLocationListCreateView.as_view(), name="locations"),
    path("locations/nearby/", NearbyUserLocationView.as_view(), name="locations-nearby"),
]
