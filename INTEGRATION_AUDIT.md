# Weather + Risk + Core Integration Audit

The backend now uses one Django project namespace (`apps.weather`, `apps.risk`, `apps.core`) and one project service namespace (`backend.services`).

Weather owns all provider adapters and normalized observation ingestion. Risk consumes WeatherObservation through the WeatherStation spatial relationship and never calls external providers directly. Core composes Weather and Risk only through project-level services.

Routes:
- `/api/weather/` -> `apps.weather.urls`
- `/api/risk/` -> `apps.risk.urls`
- `/api/core/` -> `apps.core.urls`

Celery uses one app and autodiscovers Weather, Risk, and Core task modules. PostGIS and Redis are shared through the project settings.

Risk baseline scoring remains deterministic and explainable when no pretrained XGBoost artifact is configured. Missing source features are reported as missing rather than fabricated.

Full runtime Django/PostGIS/Redis tests must be run in the deployment environment because this packaging session does not have those Python dependencies or services installed.
