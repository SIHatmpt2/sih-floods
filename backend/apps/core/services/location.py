from django.contrib.gis.geos import Point
from django.db import transaction
from apps.core.models import UserLocation
from apps.core.selectors import nearest_location


class LocationService:
    def save(self, user, name: str, latitude: float, longitude: float, is_primary=False):
        with transaction.atomic():
            if is_primary:
                UserLocation.objects.filter(user=user).update(is_primary=False)
            return UserLocation.objects.create(
                user=user,
                name=name,
                location=Point(float(longitude), float(latitude), srid=4326),
                is_primary=is_primary,
            )

    def nearby(self, user, latitude: float, longitude: float):
        return nearest_location(user, latitude, longitude)
