from django.conf import settings
from rest_framework.permissions import BasePermission


class WeatherAPIPermission(BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "WEATHER_API_REQUIRE_AUTH", False):
            return True
        return bool(request.user and request.user.is_authenticated)
