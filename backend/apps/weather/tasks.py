from celery import shared_task
from django.db import close_old_connections

from .services.ingestion import WeatherIngestionService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, max_retries=3)
def refresh_weather_data(self):
    close_old_connections()
    return WeatherIngestionService().refresh()
