from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("weather", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="weatherstation",
            new_name="ws_active_provider_idx",
            old_name="weather_station_active_provider_idx",
        ),
        migrations.RenameIndex(
            model_name="weatherstation",
            new_name="ws_active_state_idx",
            old_name="weather_station_active_state_idx",
        ),
        migrations.RenameIndex(
            model_name="weatherstation",
            new_name="ws_active_district_idx",
            old_name="weather_station_active_district_idx",
        ),
    ]
