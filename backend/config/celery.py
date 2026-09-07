from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "refresh-imd-every-30-minutes": {"task": "apps.weather.tasks.refresh_imd", "schedule": crontab(minute="*/30")},
    "refresh-cwc-every-30-minutes": {"task": "apps.weather.tasks.refresh_cwc", "schedule": crontab(minute="*/30")},
    "refresh-risk-zones-every-30-minutes": {"task": "apps.risk.tasks.refresh_active_zones", "schedule": crontab(minute="*/30")},
    "refresh-risk-hotspots-hourly": {"task": "apps.risk.tasks.refresh_hotspot_snapshots", "schedule": crontab(minute=0)},
    "refresh-state-providers-hourly": {"task": "apps.weather.tasks.refresh_state_providers", "schedule": crontab(minute=0)},
}
