from django.contrib.gis.db.models import PointField
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    operations = [
        migrations.CreateModel(
            name="WeatherStation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(max_length=32)),
                ("station_id", models.CharField(max_length=128)),
                ("name", models.CharField(max_length=255)),
                ("location", PointField(geography=True, srid=4326)),
                ("state", models.CharField(blank=True, max_length=128)),
                ("district", models.CharField(blank=True, max_length=128)),
                ("active", models.BooleanField(default=True)),
            ],
            options={"unique_together": {("provider", "station_id")}},
        ),
        migrations.CreateModel(
            name="WeatherObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField()),
                ("rainfall_mm", models.FloatField(null=True)),
                ("temperature_c", models.FloatField(null=True)),
                ("humidity", models.FloatField(null=True)),
                ("water_level_m", models.FloatField(null=True)),
                ("discharge_m3s", models.FloatField(null=True)),
                ("station", models.ForeignKey(on_delete=models.CASCADE, related_name="observations", to="weather.weatherstation")),
            ],
            options={"ordering": ["-timestamp"], "unique_together": {("station", "timestamp")}},
        ),
        migrations.AddIndex(
            model_name="weatherstation",
            index=models.Index(fields=["active", "provider"], name="weather_station_active_provider_idx"),
        ),
        migrations.AddIndex(
            model_name="weatherstation",
            index=models.Index(fields=["active", "state"], name="weather_station_active_state_idx"),
        ),
        migrations.AddIndex(
            model_name="weatherstation",
            index=models.Index(fields=["active", "district"], name="weather_station_active_district_idx"),
        ),
        migrations.AddIndex(
            model_name="weatherobservation",
            index=models.Index(fields=["station", "-timestamp"], name="weather_obs_station_ts_idx"),
        ),
    ]
