# Risk API Rebuild Design

## Goal
Rebuild `backend/apps/risk/` as a coherent Django/PostGIS risk subsystem that consumes normalized weather and hydrology data through service boundaries, imports historical flood events, exposes simple REST endpoints, and supports derived risk scoring without putting ETL, provider calls, or ML training inside HTTP views.

## Source constraints
This design follows the uploaded SIH Floods Master Architecture and Real-Time Station/API Architecture. The guide assigns `risk` ownership of `FloodEvent`, risk assessments/zones, risk APIs, historical import, and risk tasks; raw data belongs in `backend/data/raw/`; reusable transformation/feature engineering belongs in `backend/data_processing/`; specialized hydrology spatial operations belong in `backend/geospatial/`; reusable business logic belongs in `backend/services/`; and ML training/inference belongs in `backend/ml/`. The architecture requires PostgreSQL/PostGIS, Redis/Celery for background work, and MinIO for large objects/model artifacts. It explicitly forbids Pandas/GeoPandas ETL in views, storing large imagery in PostgreSQL/Git, and training XGBoost/U-Net during an HTTP request.

## Architecture

```text
Historical source files ──> data_processing ──> import_floods ──> PostGIS FloodEvent
External weather/hydrology ──> weather_service / normalized observations
                                      |
                                      v
                              risk feature services
                                      |
                       +--------------+--------------+
                       |                             |
                    PostGIS                      ML inference
                       |                       (pretrained only)
                       +--------------+--------------+
                                      v
                             services/risk_service.py
                                      |
                                      v
                              Django risk API
                                      |
                                      v
                                 React/MapLibre
```

Risk is an application/domain boundary. It must not know provider-specific API details. Current weather and hydrology are accessed through reusable service interfaces. Historical import is a thin Django command; cleansing, normalization and reusable feature calculations live outside the command. Runtime risk calculation may use a deterministic baseline when no trained model artifact is available, and may delegate to a pre-trained XGBoost predictor when one is configured. No request path trains a model.

## Domain model

### FloodEvent
Required fields from the guide: `id`, `name`, `event_date`, `district`, `location`, `severity`, `rainfall_mm`, `water_level_m`, `source`. `location` is a PostGIS geometry; the rebuild uses a consistent `PointField`.

### RiskZone
A spatial polygon representing the current derived risk footprint. It stores a stable code, geometry, active flag, latest score and latest level, plus timestamps and the latest feature snapshot.

### RiskAssessment
A timestamped evaluation for a location/zone. It stores total score, level, explanation/breakdown JSON, feature values, model/source metadata, and geometry. It provides historical risk state without overwriting prior assessments.

### RiskAlert / HotspotSnapshot
Alerts persist threshold crossings for current risk states. Hotspot snapshots persist derived high-risk aggregations for map/analytics consumers.

## Service boundaries

`backend/services/risk_service.py` is the application-facing facade. Focused services under `backend/apps/risk/services/` own normalization, feature extraction, scoring, caching, alerts, hotspots, analytics, and pretrained-model inference.

Risk may query its own models and existing Weather interfaces, but it must not call AccuWeather, IMD, CWC, or state APIs directly.

## Baseline scoring

A deterministic baseline keeps the API useful before an XGBoost artifact is available:

- rainfall: 40%
- river: 30%
- terrain: 20%
- historical: 10%

Final score is clamped to 0–100. Levels:

- 0–24: Low
- 25–49: Moderate
- 50–74: High
- 75–100: Severe

When a feature source is unavailable, the result explicitly reports missing components rather than fabricating values.

## API contract

- `GET /api/risk/events/`
- `GET /api/risk/events/<id>/`
- `GET /api/risk/zones/`
- `GET /api/risk/zones/nearby/?lat=<>&lon=<>&radius_km=<>`
- `GET /api/risk/current/?lat=<>&lon=<>`
- `GET /api/risk/breakdown/?lat=<>&lon=<>`
- `GET /api/risk/summary/`
- `GET /api/risk/high-risk/`
- `GET /api/risk/history/?lat=<>&lon=<>&days=<>`
- `GET /api/risk/alerts/`
- `GET /api/risk/hotspots/`
- `GET /api/risk/analytics/`

Coordinates and ranges are validated at the serializer layer. Spatial filtering uses PostGIS selectors; query parameters are never raw SQL.

## Background jobs

Celery/Redis handles zone refresh, derived assessment persistence, alert evaluation and hotspot refresh. Tasks are retryable with bounded retries/backoff and do not contain fixed station catalogues.

## Non-goals

No hard-coded stations, provider-specific HTTP clients in Risk, large datasets/rasters/weights in Git, request-time model training, microservice decomposition, or fabricated terrain/GLOF/satellite data.

## Acceptance criteria

Risk must migrate against PostGIS, import historical flood events, expose the documented endpoints, compute transparent baseline scores from available normalized features, persist assessments/zones, run Celery refresh/alert jobs, use spatial nearest/radius queries, integrate through `risk_service`, and have a maintainable test suite.
