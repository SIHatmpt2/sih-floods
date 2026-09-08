# Integration test plan

Verify the following in a repository environment with PostGIS and Redis available:

1. Weather provider configuration and normalized observations.
2. `WeatherService.current()` returns provider/database-backed normalized data.
3. `WeatherRiskAdapter.current_features()` maps that data into the Risk feature contract.
4. Risk assessment uses Weather-derived values while retaining deterministic fallback behavior when providers are unavailable.
5. Core dashboard exposes the RiskService contract without direct provider calls.
6. Celery tasks can refresh Weather/Risk data without request-time training.
7. PostGIS nearest-station/zone queries behave correctly.
