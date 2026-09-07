# Integrated Weather + Risk + Core Backend

This release aligns the three backend domains with the approved SIH architecture.

## Key fixes
- canonical Django app imports use `apps.weather`, `apps.risk`, and `apps.core`
- Core dashboard calls `RiskService.current()` and consumes `risk_score` / `risk_level`
- Risk consumes WeatherObservation via `station__location`
- Risk uses `rainfall_mm`, `water_level_m`, and `discharge_m3s`
- Risk updates RiskZone state whenever a persisted assessment is created
- Core notification timestamps match the model and service contract
- Core locations are persisted and exposed through authenticated API endpoints
- Core safe-zone lookup returns only active low/moderate-risk zones
- one Celery application schedules Weather ingestion and Risk refresh jobs
- project settings register all three applications and project URLs expose all three API namespaces
- no provider HTTP clients exist in Risk/Core
- no training or heavy ETL occurs in request handlers

## Verification
Python compilation and static contract audits passed in the packaging environment. Full Django integration tests require installed project dependencies plus PostGIS and Redis.
