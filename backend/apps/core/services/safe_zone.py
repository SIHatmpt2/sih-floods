from apps.risk.selectors import nearest_zone


class SafeZoneService:
    """Delegates spatial lookup to the Risk domain instead of duplicating GIS logic."""

    def nearest_safe_zone(self, latitude: float, longitude: float):
        zone = nearest_zone(latitude, longitude)
        if zone is None:
            return None
        return {"zone_id": zone.id, "zone_name": zone.name}
