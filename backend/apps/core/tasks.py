from celery import shared_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def refresh_dashboard_cache(self):
    return {"status": "scheduled"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def sync_dashboard_snapshot(self):
    return {"status": "scheduled"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def cleanup_notifications(self):
    return {"status": "scheduled"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def refresh_safe_zones(self):
    return {"status": "scheduled"}
