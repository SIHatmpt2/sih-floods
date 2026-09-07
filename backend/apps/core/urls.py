from django.urls import path
from .views import AnalyticsView, DashboardView, NotificationListView, SafeZoneView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("safe-zone/", SafeZoneView.as_view(), name="safe-zone"),
]
