from celery import shared_task
from django.db import close_old_connections

from .models import RiskZone
from .services.zone_manager import assess_point
from .services.hotspot import refresh_hotspots


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=3)
def refresh_active_zones(self):
    close_old_connections()
    updated = 0
    for zone in RiskZone.objects.filter(is_active=True).iterator():
        assess_point(
            zone.geometry.centroid.y,
            zone.geometry.centroid.x,
            zone=zone,
            persist=True,
        )
        updated += 1
    return {"updated": updated}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=3)
def refresh_hotspot_snapshots(self):
    close_old_connections()
    return {"created": refresh_hotspots()}


@shared_task
def refresh_risk_pipeline():
    return {
        "zones": refresh_active_zones.delay().id,
        "hotspots": refresh_hotspot_snapshots.delay().id,
    }
