# Rebuilt Risk API

This package replaces `backend/apps/risk/` with a layered Django/PostGIS flood-risk subsystem.

## Architecture

External/weather data stays outside Risk provider adapters. Risk consumes normalized observations through the Weather service/app boundary. Historical flood data enters through the `import_floods` management command. Risk scoring is deterministic by default and can use a pretrained model artifact through `services/ml.py`.

No request path trains models or performs Pandas/GeoPandas ETL.

## API

When mounted under `/api/risk/`:

- `GET /events/`
- `GET /events/<id>/`
- `GET /zones/`
- `GET /zones/nearby/?lat=&lon=&radius_km=`
- `GET /current/?lat=&lon=`
- `GET /breakdown/?lat=&lon=`
- `GET /summary/?days=`
- `GET /high-risk/`
- `GET /history/?lat=&lon=&days=`
- `GET /alerts/`
- `GET /hotspots/`
- `GET /analytics/`

## Baseline scoring

- rainfall: 40%
- river: 30%
- terrain: 20%
- historical: 10%

Levels:

- 0-24 Low
- 25-49 Moderate
- 50-74 High
- 75-100 Severe

When a feature source is unavailable, the result reports missing components rather than fabricating data.

## Integration

Add the app to `INSTALLED_APPS`:

```python
"backend.apps.risk",
```

Mount URLs:

```python
path("api/risk/", include("backend.apps.risk.urls")),
```

Apply:

```bash
python manage.py migrate
```

For Celery discovery, ensure the project already autodiscovers tasks.

## Historical import

CSV columns:

```text
name,event_date,latitude,longitude,severity,source,district
```

Optional: `id,rainfall_mm,water_level_m`.

Run:

```bash
python manage.py import_floods data/raw/floods.csv
```

## Model artifact

Set `RISK_XGBOOST_MODEL_PATH=/path/to/pretrained/model.joblib`.
Training is offline. Do not commit model weights or large raster/satellite artifacts to Git.
