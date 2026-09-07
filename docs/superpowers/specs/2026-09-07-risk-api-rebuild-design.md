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
Required fields from the guide: `id`, `name`, `event_date`, `district`, `location`, `severity`, `rainfall_mm`, `water_level_m`, `source`. `location` is a PostGIS geometry; point or polygon is accepted at the domain boundary, but one concrete model field will be used consistently in the implementation. Records retain source provenance and timestamps for auditability.

### RiskZone
A spatial polygon representing the current derived risk footprint. It stores a stable name/identifier, geometry, active flag, latest score and latest level, plus timestamps. Dynamic zones are recalculated by Celery rather than on every list request.

### RiskAssessment
A timestamped evaluation for a location/zone. It stores total score, level, explanation/breakdown JSON, feature values, model/source metadata, and geometry. It provides historical risk state without overwriting prior assessments.

### RiskAlert
A generated alert tied to a location or risk zone, with severity, title/message, status, trigger score, created/read/resolved timestamps. Alerts are produced by background risk refreshes and are queryable through the API.

### Optional later-domain records
GLOFEvent, GlacialLake, SatelliteObservation, exposure/construction entities remain out of the first rebuild unless existing project data requires them. The guide explicitly recommends starting with the minimum useful models and expanding when a feature requires it.

## Service boundaries

`backend/services/risk_service.py` is the application-facing facade. It exposes stable operations such as:

- `get_current_risk(latitude, longitude)`
- `get_risk_breakdown(latitude, longitude)`
- `list_high_risk_zones(...)`
- `refresh_zone(zone_id)`

`backend/apps/risk/services/` contains focused domain services:

- `risk_engine.py`: score calculation, normalization and level mapping.
- `rainfall.py`: rainfall-window features obtained from weather observations/service layer.
- `river.py`: discharge/water-level features and change statistics when observation data is available.
- `terrain.py`: interface for terrain-derived values; safe defaults when no terrain raster is configured.
- `historical.py`: event-count/severity/distance features from `FloodEvent`.
- `normalizer.py`: common bounds, units and score normalization.
- `zone_manager.py`: zone selection/recalculation.
- `cache.py`: Redis/Django-cache wrappers for current risk results.
- `alert_engine.py`: threshold transitions and alert creation.
- `hotspot.py`: high-risk spatial aggregation.
- `analytics.py`: distributions/time-window summaries.
- `notification.py`: delivery abstraction; persistence is separate from any external channel.

The risk app may query its own models and use `WeatherService`/weather app interfaces, but it must not call AccuWeather, IMD, CWC, or state APIs directly.

## Baseline scoring

A deterministic baseline keeps the API useful before the XGBoost artifact is available:

- rainfall: 40%
- river: 30%
- terrain: 20%
- historical: 10%

The final score is clamped to 0–100. Risk levels are mapped as:

- 0–24: Low
- 25–49: Moderate
- 50–74: High
- 75–100: Severe

The breakdown is returned to clients so the frontend can explain the score. Model-backed inference replaces the score only when an explicitly configured pretrained artifact is loadable and its feature contract is satisfied.

## Data flow

1. `import_floods` validates and imports historical events into PostGIS.
2. Weather/river ingestion remains owned by the weather subsystem and writes normalized observations.
3. A risk Celery task selects relevant observations using PostGIS spatial queries and computes rainfall/river/historical/terrain features.
4. Risk engine produces baseline or pretrained-model score.
5. RiskAssessment/RiskZone state is persisted.
6. Alert engine compares current state with thresholds and records alerts.
7. REST views read persisted/current service results; they do not run heavy ETL or ML training.

## API contract

Initial endpoints:

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

Coordinates are validated at the serializer layer. Spatial filtering and nearest/radius lookup are implemented in selectors using PostGIS functions. Query parameters never become raw SQL fragments.

## Background jobs

Risk tasks use Celery with Redis as broker. Tasks are retryable and idempotent where possible:

- refresh current risk for active zones
- recompute derived assessments
- update alerts
- refresh hotspot snapshots/cache
- optional cleanup of resolved alerts/history according to retention settings

No scheduled task embeds a fixed station list or provider-specific station variables.

## Error handling

- Invalid coordinates/ranges return structured 400 responses.
- Missing weather/hydrology data produces a partial-feature assessment with explicit `data_quality`/`missing_features` metadata, not a fabricated precise value.
- Unavailable ML artifact falls back to deterministic baseline and records `model_source=baseline`.
- External service failures are isolated from HTTP requests; background tasks retry with bounded backoff.
- Spatial queries require valid geometry input and use database indexes.

## Testing

The rebuilt app must include unit tests for risk normalization, score/level mapping, historical feature derivation, service fallbacks, and alert threshold transitions; API tests for validation and representative endpoint responses; and database tests for PostGIS nearest/radius filtering and model constraints. Management-command tests must cover valid import, malformed rows, duplicate handling, and provenance preservation. Celery tasks must be tested as callable functions with external dependencies mocked.

## Non-goals for this rebuild

- No hard-coded station catalogue.
- No provider-specific HTTP clients in Risk.
- No giant raw datasets, rasters, satellite imagery, or model weights in Git.
- No model training in web requests.
- No microservice decomposition.
- No complex global event ontology.
- No fabricated terrain/GLOF/satellite data when source layers are absent.

## Acceptance criteria

The implementation is complete when Risk can be migrated against PostGIS, import historical flood events, expose event/zone/current/breakdown/summary APIs, compute a transparent baseline score from available normalized features, persist assessments/zones, run Celery refresh/alert tasks using Redis, use spatial nearest/radius queries, integrate through `risk_service`, and pass the Risk test suite without embedding ETL/provider calls/training in views.
