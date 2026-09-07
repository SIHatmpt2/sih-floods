from django.contrib.gis.db import models as gis_models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FloodEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("event_date", models.DateField()),
                ("district", models.CharField(blank=True, max_length=255)),
                ("location", gis_models.PointField(geography=True, srid=4326)),
                ("severity", models.FloatField(default=0.0)),
                ("rainfall_mm", models.FloatField(blank=True, null=True)),
                ("water_level_m", models.FloatField(blank=True, null=True)),
                ("source", models.CharField(max_length=255)),
                ("source_record_id", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"indexes": [
                models.Index(fields=["event_date"]),
                models.Index(fields=["district"]),
                models.Index(fields=["source"]),
            ]},
        ),
        migrations.CreateModel(
            name="RiskZone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("zone_code", models.CharField(max_length=100, unique=True)),
                ("geometry", gis_models.PolygonField(geography=True, srid=4326)),
                ("is_active", models.BooleanField(default=True)),
                ("latest_score", models.FloatField(default=0.0)),
                ("risk_level", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("severe", "Severe")], default="low", max_length=20)),
                ("feature_snapshot", models.JSONField(blank=True, default=dict)),
                ("last_assessed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"indexes": [models.Index(fields=["is_active", "risk_level"])]},
        ),
        migrations.CreateModel(
            name="RiskAssessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("location", gis_models.PointField(geography=True, srid=4326)),
                ("score", models.FloatField()),
                ("risk_level", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("severe", "Severe")], max_length=20)),
                ("breakdown", models.JSONField(default=dict)),
                ("features", models.JSONField(default=dict)),
                ("model_source", models.CharField(default="baseline", max_length=50)),
                ("data_quality", models.JSONField(blank=True, default=dict)),
                ("observed_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("zone", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="assessments", to="risk.riskzone")),
            ],
            options={"indexes": [models.Index(fields=["observed_at"]), models.Index(fields=["risk_level"])]},
        ),
        migrations.CreateModel(
            name="RiskAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("location", gis_models.PointField(geography=True, srid=4326)),
                ("severity", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("severe", "Severe")], max_length=20)),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("trigger_score", models.FloatField()),
                ("status", models.CharField(choices=[("open", "Open"), ("read", "Read"), ("resolved", "Resolved")], default="open", max_length=20)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("zone", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="alerts", to="risk.riskzone")),
            ],
            options={"indexes": [models.Index(fields=["status", "severity"]), models.Index(fields=["created_at"])]},
        ),
        migrations.CreateModel(
            name="HotspotSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("snapshot_at", models.DateTimeField()),
                ("centroid", gis_models.PointField(geography=True, srid=4326)),
                ("score", models.FloatField()),
                ("risk_level", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("severe", "Severe")], max_length=20)),
                ("assessment_count", models.PositiveIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={"indexes": [models.Index(fields=["snapshot_at"]), models.Index(fields=["risk_level"])]},
        ),
        migrations.AddConstraint(
            model_name="floodevent",
            constraint=models.UniqueConstraint(fields=("source", "source_record_id"), name="risk_floodevent_unique_source_record"),
        ),
    ]
