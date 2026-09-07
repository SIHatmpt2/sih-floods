from apps.risk.selectors import nearest_safe_zone


class SafeZoneService:
    """Delegates safe-zone selection to the Risk domain."""

    def nearest_safe_zone(self, latitude: float, longitude: float):
        zone = nearest_safe_zone(latitude, longitude)
        if zone is None:
            return None
        return {"zone_id": zone.id, "zone_name": zone.name, "risk_level": zone.risk_level}
