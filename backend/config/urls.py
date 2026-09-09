from __future__ import annotations

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core import health

urlpatterns = [
    path("api/core/", include("apps.core.urls")),
    path("api/risk/", include("apps.risk.urls")),
    path("api/weather/", include("apps.weather.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("health/", health.readiness, name="health"),
    path("health/ready/", health.readiness, name="health-ready"),
    path("health/live/", health.liveness, name="health-live"),
]
