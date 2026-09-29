from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("weather", "0002_rename_station_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="weatherobservation",
            name="rainfall_24h_mm",
            field=models.FloatField(null=True),
        ),
    ]
