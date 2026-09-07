from django.contrib.gis.db import models


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MODERATE = "moderate", "Moderate"
    HIGH = "high", "High"
    SEVERE = "severe", "Severe"


class AlertStatus(models.TextChoices):
    OPEN = "open", "Open"
    READ = "read", "Read"
    RESOLVED = "resolved", "Resolved"


class FloodEvent(models.Model):
    name = models.CharField(max_length=255)
    event_date = models.DateField()
    district = models.CharField(max_length=255, blank=True)
    location = models.PointField(geography=True, srid=4326)
    severity = models.FloatField(default=0.0)
    rainfall_mm = models.FloatField(null=True, blank=True)
    water_level_m = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=255)
    source_record_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["event_date"]),
            models.Index(fields=["district"]),
            models.Index(fields=["source"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_record_id"],
                name="risk_floodevent_unique_source_record",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.event_date})"


class RiskZone(models.Model):
    name = models.CharField(max_length=255)
    zone_code = models.CharField(max_length=100, unique=True)
    geometry = models.PolygonField(geography=True, srid=4326)
    is_active = models.BooleanField(default=True)
    latest_score = models.FloatField(default=0.0)
    risk_level = models.CharField(
        max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW
    )
    feature_snapshot = models.JSONField(default=dict, blank=True)
    last_assessed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["is_active", "risk_level"])]

    def __str__(self):
        return self.name


class RiskAssessment(models.Model):
    zone = models.ForeignKey(
        RiskZone, null=True, blank=True, on_delete=models.SET_NULL, related_name="assessments"
    )
    location = models.PointField(geography=True, srid=4326)
    score = models.FloatField()
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices)
    breakdown = models.JSONField(default=dict)
    features = models.JSONField(default=dict)
    model_source = models.CharField(max_length=50, default="baseline")
    data_quality = models.JSONField(default=dict, blank=True)
    observed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["observed_at"]),
            models.Index(fields=["risk_level"]),
        ]
        ordering = ["-observed_at"]

    def __str__(self):
        return f"{self.risk_level}: {self.score:.2f}"


class RiskAlert(models.Model):
    zone = models.ForeignKey(
        RiskZone, null=True, blank=True, on_delete=models.SET_NULL, related_name="alerts"
    )
    location = models.PointField(geography=True, srid=4326)
    severity = models.CharField(max_length=20, choices=RiskLevel.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    trigger_score = models.FloatField()
    status = models.CharField(
        max_length=20, choices=AlertStatus.choices, default=AlertStatus.OPEN
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class HotspotSnapshot(models.Model):
    snapshot_at = models.DateTimeField()
    centroid = models.PointField(geography=True, srid=4326)
    score = models.FloatField()
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices)
    assessment_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["snapshot_at"]),
            models.Index(fields=["risk_level"]),
        ]
        ordering = ["-snapshot_at"]
