from django.contrib.gis.geos import Point
from apps.core.models import UserLocation
from apps.risk.selectors import nearest_zone


class LocationService:
    def save(self, user, name, latitude, longitude, is_primary=False):
        point = Point(longitude, latitude, srid=4326)
        if is_primary:
            UserLocation.objects.filter(user=user, is_primary=True).update(is_primary=False)
        return UserLocation.objects.create(
            user=user,
            name=name,
            location=point,
            is_primary=is_primary,
        )

    def nearest_risk_zone(self, latitude, longitude):
        return nearest_zone(latitude, longitude)
