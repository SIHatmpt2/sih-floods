# Risk App

Layered Django/PostGIS flood-risk subsystem.

Ownership:
- FloodEvent
- RiskZone
- RiskAssessment
- RiskAlert
- HotspotSnapshot
- risk REST endpoints
- historical import
- Celery risk tasks

Boundary:
- Weather/provider API integrations are owned by Weather.
- Reusable ETL/features belong in `backend/data_processing/`.
- Specialized geospatial routines belong in `backend/geospatial/`.
- ML artifacts/inference contracts belong in `backend/ml/` when the broader project adds them.
