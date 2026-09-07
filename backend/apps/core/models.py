from django.conf import settings
from django.contrib.gis.db import models


class UserLocation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    location = models.PointField(geography=True)
    is_primary = models.BooleanField(default=False)


class DashboardSnapshot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    weather_summary = models.JSONField(default=dict)
    risk_summary = models.JSONField(default=dict)
    alerts_count = models.PositiveIntegerField(default=0)


class NotificationRecord(models.Model):
    CHANNELS = (
        ("app", "App"),
        ("sms", "SMS"),
        ("email", "Email"),
        ("push", "Push"),
    )
    STATUS = (
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("read", "Read"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNELS, default="app")
    status = models.CharField(max_length=20, choices=STATUS, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
