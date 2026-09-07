# Risk API Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing Risk scaffold with a testable Django/PostGIS flood-risk subsystem that imports historical events, derives transparent risk features from normalized data, persists risk state, exposes REST APIs, and runs refresh/alert work through Celery without provider calls, ETL, or model training in HTTP requests.

**Architecture:** Risk owns its flood-event, risk-assessment, risk-zone, and alert domain models. It consumes normalized weather/hydrology through stable service boundaries, uses focused domain services and PostGIS selectors for calculations, and exposes `backend/services/risk_service.py` as the application-facing facade. A deterministic 0–100 baseline score is always available; a configured pretrained model may replace the baseline only when its artifact and feature contract are valid.

**Tech Stack:** Django, Django REST Framework, GeoDjango/PostGIS, Celery, Redis/Django cache, PostgreSQL, pytest/Django TestCase, optional XGBoost inference artifact.

**Spec:** `docs/superpowers/specs/2026-09-07-risk-api-rebuild-design.md`

## Global Constraints

- Risk must not contain AccuWeather, IMD, CWC, or state-provider HTTP clients.
- Historical cleansing/normalization and reusable feature engineering must not be embedded in Django views or the management command.
- All spatial locations use PostGIS geometry with explicit SRID and database-backed spatial lookups.
- Baseline risk weights are rainfall 40%, river 30%, terrain 20%, historical 10%.
- Risk levels are 0–24 Low, 25–49 Moderate, 50–74 High, 75–100 Severe.
- Missing inputs must be reported as missing/partial data rather than fabricated values.
- XGBoost/U-Net training never runs in HTTP requests; only pretrained inference is allowed at runtime.
- Large datasets, rasters, satellite imagery, and model weights are not committed to Git.
- Celery tasks use Redis and are retryable/idempotent where practical.
- Views remain thin and delegate business logic to services/selectors.

---

### Task 1: Map the existing backend and lock Risk integration points

**Files:**
- Read: `backend/apps/weather/**`
- Read: `backend/apps/core/**`
- Read: `backend/config/**`
- Read: `backend/services/**`
- Modify: only files required to register the rebuilt Risk app after implementation
- Test: existing backend test suite

**Interfaces:**
- Consumes: existing Weather/Core service contracts and Django project URL/settings conventions.
- Produces: a concrete list of integration points for Risk without changing Weather/Core ownership.

- [ ] **Step 1: Inspect the current project structure and existing service imports.**

```bash
git status --short
git log -5 --oneline
find backend -maxdepth 3 -type f | sort
```

Read the existing Weather service facade, Core service facade, project settings, root URL configuration, Celery setup, dependency file, and current Risk files before modifying them.

- [ ] **Step 2: Write a failing integration test that confirms the Risk app can be imported without importing any provider client.**

```python
def test_risk_module_does_not_import_provider_clients():
    import importlib
    module = importlib.import_module("backend.apps.risk")
    assert module is not None
```

- [ ] **Step 3: Run the test.**

```bash
pytest -q
```

Expected: the new test passes against the scaffold; the purpose is to establish the import boundary before deeper implementation.

- [ ] **Step 4: Record the exact existing integration points in the implementation branch notes.**

The implementer must identify the existing WeatherService import path and project URL/settings paths from the repository rather than inventing alternate locations.

- [ ] **Step 5: Commit the baseline discovery-only changes, if any.**

```bash
git add docs/superpowers/plans/2026-09-07-risk-api-rebuild.md
git commit -m "docs: map risk integration boundaries"
```

---

### Task 2: Implement the Risk domain models and migrations

**Files:**
- Replace: `backend/apps/risk/models.py`
- Create: `backend/apps/risk/constants.py`
- Create: `backend/apps/risk/managers.py`
- Create: `backend/apps/risk/migrations/0001_initial.py`
- Modify: `backend/apps/risk/admin.py`
- Test: `backend/apps/risk/tests/test_models.py`

**Interfaces:**
- Consumes: Django settings `AUTH_USER_MODEL`; GeoDjango `PointField`/`PolygonField`; PostGIS.
- Produces: `FloodEvent`, `RiskZone`, `RiskAssessment`, `RiskAlert` with stable field names used by serializers/services.

- [ ] **Step 1: Write model tests before implementation.**

```python
from django.contrib.gis.geos import Point, Polygon
from django.test import TestCase

from backend.apps.risk.models import FloodEvent, RiskAssessment, RiskAlert, RiskZone


class RiskModelTests(TestCase):
    def test_flood_event_persists_provenance_and_location(self):
        event = FloodEvent.objects.create(
            name="Test Flood",
            event_date="2024-07-01",
            district="Pune",
            location=Point(73.8567, 18.5204, srid=4326),
            severity="high",
            rainfall_mm=180,
            water_level_m=4.2,
            source="test",
        )
        assert event.pk is not None
        assert event.location.srid == 4326
        assert event.source == "test"

    def test_risk_assessment_score_is_bounded(self):
        zone = RiskZone.objects.create(
            name="Zone A",
            geometry=Polygon((
                (73.85, 18.51), (73.87, 18.51),
                (73.87, 18.53), (73.85, 18.53),
                (73.85, 18.51),
            ), srid=4326),
            latest_score=40,
            latest_level="moderate",
        )
        assessment = RiskAssessment.objects.create(
            zone=zone,
            location=Point(73.8567, 18.5204, srid=4326),
            score=40,
            level="moderate",
            breakdown={"rainfall": 40},
            features={"rainfall_24h_mm": 20},
            model_source="baseline",
        )
        assert 0 <= assessment.score <= 100

    def test_alert_defaults_to_open(self):
        alert = RiskAlert.objects.create(
            title="High flood risk",
            message="Risk threshold exceeded",
            severity="high",
            status="open",
            trigger_score=76,
        )
        assert alert.status == "open"
```

- [ ] **Step 2: Run the model tests to verify the scaffold fails.**

```bash
pytest -q backend/apps/risk/tests/test_models.py
```

Expected: FAIL because the concrete model fields do not yet exist.

- [ ] **Step 3: Implement the models.**

Use one consistent `PointField(geography=True, srid=4326)` for `FloodEvent.location` and `RiskAssessment.location`, and `PolygonField(geography=True, srid=4326)` for `RiskZone.geometry`.

`FloodEvent` fields:

```python
name = models.CharField(max_length=255)
event_date = models.DateField(db_index=True)
district = models.CharField(max_length=120, db_index=True)
location = gis_models.PointField(geography=True, srid=4326)
severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, db_index=True)
rainfall_mm = models.FloatField(null=True, blank=True)
water_level_m = models.FloatField(null=True, blank=True)
source = models.CharField(max_length=255)
source_record_id = models.CharField(max_length=255, null=True, blank=True)
metadata = models.JSONField(default=dict, blank=True)
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

`RiskZone` fields:

```python
name = models.CharField(max_length=255)
geometry = gis_models.PolygonField(geography=True, srid=4326)
is_active = models.BooleanField(default=True, db_index=True)
latest_score = models.FloatField(default=0)
latest_level = models.CharField(max_length=16, choices=RISK_LEVEL_CHOICES, default="low", db_index=True)
last_calculated_at = models.DateTimeField(null=True, blank=True, db_index=True)
metadata = models.JSONField(default=dict, blank=True)
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

`RiskAssessment` fields:

```python
zone = models.ForeignKey(RiskZone, null=True, blank=True, on_delete=models.CASCADE, related_name="assessments")
location = gis_models.PointField(geography=True, srid=4326)
assessed_at = models.DateTimeField(auto_now_add=True, db_index=True)
score = models.FloatField()
level = models.CharField(max_length=16, choices=RISK_LEVEL_CHOICES, db_index=True)
breakdown = models.JSONField(default=dict)
features = models.JSONField(default=dict)
data_quality = models.JSONField(default=dict)
model_source = models.CharField(max_length=64, default="baseline")
metadata = models.JSONField(default=dict, blank=True)
```

`RiskAlert` fields:

```python
zone = models.ForeignKey(RiskZone, null=True, blank=True, on_delete=models.SET_NULL, related_name="alerts")
location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
severity = models.CharField(max_length=16, choices=ALERT_SEVERITY_CHOICES)
title = models.CharField(max_length=255)
message = models.TextField()
status = models.CharField(max_length=16, choices=ALERT_STATUS_CHOICES, default="open", db_index=True)
trigger_score = models.FloatField(null=True, blank=True)
created_at = models.DateTimeField(auto_now_add=True, db_index=True)
read_at = models.DateTimeField(null=True, blank=True)
resolved_at = models.DateTimeField(null=True, blank=True)
metadata = models.JSONField(default=dict, blank=True)
```

Add spatial indexes through the model fields and a uniqueness constraint for flood events on `(source, source_record_id)` when `source_record_id` is non-null through a conditional constraint.

- [ ] **Step 4: Generate and inspect the migration.**

```bash
python manage.py makemigrations risk
python manage.py sqlmigrate risk 0001
```

Confirm PostGIS geometry fields and indexes are represented.

- [ ] **Step 5: Run tests.**

```bash
pytest -q backend/apps/risk/tests/test_models.py
```

Expected: PASS.

- [ ] **Step 6: Commit.**

```bash
git add backend/apps/risk/models.py backend/apps/risk/constants.py backend/apps/risk/managers.py backend/apps/risk/migrations backend/apps/risk/admin.py backend/apps/risk/tests/test_models.py
git commit -m "feat: add risk domain models"
```

---

### Task 3: Build normalization, feature services, and deterministic risk engine

**Files:**
- Create: `backend/apps/risk/services/__init__.py`
- Create: `backend/apps/risk/services/normalizer.py`
- Create: `backend/apps/risk/services/rainfall.py`
- Create: `backend/apps/risk/services/river.py`
- Create: `backend/apps/risk/services/terrain.py`
- Create: `backend/apps/risk/services/historical.py`
- Create: `backend/apps/risk/services/risk_engine.py`
- Test: `backend/apps/risk/tests/test_engine.py`
- Test: `backend/apps/risk/tests/test_features.py`

**Interfaces:**
- Consumes: normalized observation/service outputs plus Risk-owned historical events.
- Produces: a `RiskFeatureVector` dictionary, deterministic component scores, total score, level, and explicit missing-data metadata.

- [ ] **Step 1: Write failing tests for normalization and level thresholds.**

```python
from backend.apps.risk.services.normalizer import clamp01, normalize_range
from backend.apps.risk.services.risk_engine import calculate_risk


def test_normalize_range_clamps_outside_bounds():
    assert normalize_range(-1, 0, 100) == 0
    assert normalize_range(50, 0, 100) == 0.5
    assert normalize_range(101, 0, 100) == 1


def test_level_boundaries_are_stable():
    assert calculate_risk({"rainfall_score": 24, "river_score": 0, "terrain_score": 0, "historical_score": 0})["level"] == "low"
    assert calculate_risk({"rainfall_score": 25, "river_score": 0, "terrain_score": 0, "historical_score": 0})["level"] == "moderate"
    assert calculate_risk({"rainfall_score": 50, "river_score": 0, "terrain_score": 0, "historical_score": 0})["level"] == "high"
    assert calculate_risk({"rainfall_score": 75, "river_score": 0, "terrain_score": 0, "historical_score": 0})["level"] == "severe"
```

- [ ] **Step 2: Run tests to verify failure.**

```bash
pytest -q backend/apps/risk/tests/test_engine.py
```

Expected: FAIL because the service modules do not yet exist.

- [ ] **Step 3: Implement `normalizer.py`.**

```python
def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize_range(value: float, low: float, high: float) -> float:
    if high <= low:
        raise ValueError("high must be greater than low")
    return clamp01((float(value) - low) / (high - low))
```

Add helpers for missing-safe numeric conversion and score clamping.

- [ ] **Step 4: Implement rainfall feature extraction.**

Expose:

```python
def rainfall_features(observations) -> dict[str, float | None]:
    """Return rainfall_24h_mm, rainfall_3d_mm, rainfall_7d_mm, rainfall_30d_mm and rainfall_score."""
```

The implementation must operate on already normalized observation objects/querysets and calculate window sums from timestamps. It must not make external HTTP requests.

- [ ] **Step 5: Implement river feature extraction.**

Expose:

```python
def river_features(observations) -> dict[str, float | None]:
    """Return current level/discharge, change and a normalized river_score."""
```

Use the latest valid observation and a prior comparison point where available; missing values remain `None` and lower the completeness metadata rather than becoming zero without explanation.

- [ ] **Step 6: Implement terrain feature interface.**

Expose:

```python
def terrain_features(latitude: float, longitude: float) -> dict[str, float | None]:
    """Return configured terrain attributes or explicit missing values."""
```

When no terrain source is configured, return `{"elevation_m": None, "slope_deg": None, "terrain_score": 0.0, "available": False}` and record the unavailable feature in downstream `data_quality`.

- [ ] **Step 7: Implement historical feature extraction from `FloodEvent`.**

Expose:

```python
def historical_features(point, radius_km: float = 25.0) -> dict[str, float | int | None]:
    """Return nearby event count, severity-weighted count, latest event age and historical_score."""
```

Use PostGIS distance filtering. Map severity to deterministic weights and normalize the result into 0–100.

- [ ] **Step 8: Implement the baseline risk engine.**

Expose:

```python
BASELINE_WEIGHTS = {
    "rainfall_score": 0.40,
    "river_score": 0.30,
    "terrain_score": 0.20,
    "historical_score": 0.10,
}


def calculate_risk(features: dict) -> dict:
    """Return score, level, component breakdown, and completeness metadata."""
```

The weighted score is clamped to 0–100. The output includes `model_source="baseline"` and a `missing_features` list.

- [ ] **Step 9: Run feature and engine tests.**

```bash
pytest -q backend/apps/risk/tests/test_engine.py backend/apps/risk/tests/test_features.py
```

Expected: PASS.

- [ ] **Step 10: Commit.**

```bash
git add backend/apps/risk/services backend/apps/risk/tests/test_engine.py backend/apps/risk/tests/test_features.py
git commit -m "feat: add deterministic risk feature engine"
```

---

### Task 4: Add the Risk application service facade and PostGIS selectors

**Files:**
- Create/replace: `backend/apps/risk/selectors.py`
- Create/replace: `backend/apps/risk/services/cache.py`
- Create: `backend/apps/risk/services/zone_manager.py`
- Create: `backend/apps/risk/services/risk_runtime.py`
- Create/replace: `backend/services/risk_service.py`
- Test: `backend/apps/risk/tests/test_services.py`

**Interfaces:**
- Consumes: feature services from Task 3, Risk models, existing WeatherService interface, Django cache.
- Produces: stable operations for HTTP views/Core and Celery tasks: `get_current_risk`, `get_risk_breakdown`, `list_high_risk_zones`, `refresh_zone`.

- [ ] **Step 1: Write failing service tests.**

```python
from unittest.mock import patch
from django.contrib.gis.geos import Point

from backend.services.risk_service import RiskService


def test_get_current_risk_returns_baseline_when_model_is_unavailable():
    with patch("backend.apps.risk.services.risk_runtime.load_predictor", return_value=None):
        result = RiskService().get_current_risk(18.5204, 73.8567)
    assert 0 <= result["score"] <= 100
    assert result["model_source"] == "baseline"
    assert "breakdown" in result
```

- [ ] **Step 2: Implement selectors with explicit geometry inputs.**

Use Django GIS expressions such as `Distance`, `D`, `GeometryDistance`, or equivalent supported by the project database. Expose focused functions such as:

```python
def nearby_flood_events(point, radius_km: float): ...
def nearby_active_zones(point, radius_km: float): ...
def latest_assessments_for_zone(zone_id: int, limit: int = 100): ...
def high_risk_zones(levels=("high", "severe")): ...
```

Reject negative radii and invalid coordinates before query construction.

- [ ] **Step 3: Implement cache wrappers.**

Use a versioned key such as:

```python
risk_key = f"risk:v1:{round(latitude, 4)}:{round(longitude, 4)}"
```

Cache current-risk results for a short TTL and never cache secrets or provider credentials.

- [ ] **Step 4: Implement runtime orchestration.**

`risk_runtime.py` must:
1. obtain normalized weather/hydrology data through the existing WeatherService/app interface;
2. compute rainfall, river, terrain, and historical features;
3. attempt pretrained inference through a small predictor interface;
4. fall back to the deterministic engine when inference is unavailable or the feature contract is invalid;
5. return a JSON-serializable result containing score, level, breakdown, features, data quality, and model source.

- [ ] **Step 5: Implement `backend/services/risk_service.py`.**

Provide:

```python
class RiskService:
    def get_current_risk(self, latitude: float, longitude: float) -> dict: ...
    def get_risk_breakdown(self, latitude: float, longitude: float) -> dict: ...
    def list_high_risk_zones(self, *, limit: int = 100): ...
    def refresh_zone(self, zone_id: int) -> dict: ...
```

The facade must be importable by Core without Core knowing implementation details.

- [ ] **Step 6: Run service tests.**

```bash
pytest -q backend/apps/risk/tests/test_services.py
```

Expected: PASS.

- [ ] **Step 7: Commit.**

```bash
git add backend/apps/risk/selectors.py backend/apps/risk/services backend/services/risk_service.py backend/apps/risk/tests/test_services.py
git commit -m "feat: add risk service facade and spatial selectors"
```

---

### Task 5: Implement historical flood import and data validation

**Files:**
- Create: `backend/apps/risk/management/__init__.py`
- Create: `backend/apps/risk/management/commands/__init__.py`
- Create: `backend/apps/risk/management/commands/import_floods.py`
- Create: `backend/data_processing/floods/__init__.py`
- Create: `backend/data_processing/floods/normalizer.py`
- Create: `backend/data_processing/floods/validators.py`
- Test: `backend/apps/risk/tests/test_import_floods.py`

**Interfaces:**
- Consumes: CSV/JSON flood-event source rows.
- Produces: validated `FloodEvent` records with provenance; malformed rows are rejected individually without corrupting the whole import transaction.

- [ ] **Step 1: Write failing command tests.**

```python
from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from backend.apps.risk.models import FloodEvent


class ImportFloodsTests(TestCase):
    def test_valid_row_imports(self):
        payload = "name,event_date,district,latitude,longitude,severity,rainfall_mm,water_level_m,source,source_record_id\nFlood A,2024-07-01,Pune,18.52,73.85,high,150,4.1,test,row-1\n"
        call_command("import_floods", file="-", stdin=StringIO(payload), format="csv")
        assert FloodEvent.objects.filter(source_record_id="row-1").count() == 1

    def test_duplicate_source_record_is_idempotent(self):
        payload = "name,event_date,district,latitude,longitude,severity,rainfall_mm,water_level_m,source,source_record_id\nFlood A,2024-07-01,Pune,18.52,73.85,high,150,4.1,test,row-2\n"
        call_command("import_floods", file="-", stdin=StringIO(payload), format="csv")
        call_command("import_floods", file="-", stdin=StringIO(payload), format="csv")
        assert FloodEvent.objects.filter(source_record_id="row-2").count() == 1
```

- [ ] **Step 2: Run the tests to confirm failure.**

```bash
pytest -q backend/apps/risk/tests/test_import_floods.py
```

Expected: FAIL because the command does not exist.

- [ ] **Step 3: Implement reusable row validation in `data_processing/floods/validators.py`.**

Validate required fields, latitude/longitude ranges, date format, and severity choices. Return structured validation errors rather than raising an unhandled exception for one bad row.

- [ ] **Step 4: Implement normalization in `data_processing/floods/normalizer.py`.**

Convert numeric strings to floats, normalize severity to the Risk choice values, construct `Point(lon, lat, srid=4326)`, and preserve the original source identifier.

- [ ] **Step 5: Implement the thin management command.**

`import_floods.py` parses the source format and delegates each row to the reusable validator/normalizer, then writes/upserts `FloodEvent`. It must not use Pandas/GeoPandas and must not contain reusable feature-engineering code.

- [ ] **Step 6: Run import tests.**

```bash
pytest -q backend/apps/risk/tests/test_import_floods.py
```

Expected: PASS.

- [ ] **Step 7: Commit.**

```bash
git add backend/apps/risk/management backend/data_processing/floods backend/apps/risk/tests/test_import_floods.py
git commit -m "feat: add idempotent flood event importer"
```

---

### Task 6: Implement pretrained ML inference boundary without training in requests

**Files:**
- Create: `backend/ml/__init__.py`
- Create: `backend/ml/risk/__init__.py`
- Create: `backend/ml/risk/predictor.py`
- Create: `backend/ml/risk/schema.py`
- Create: `backend/ml/risk/README.md`
- Test: `backend/apps/risk/tests/test_predictor.py`

**Interfaces:**
- Consumes: numeric feature dictionary produced by Task 3.
- Produces: `predict(features) -> float` only when a configured pretrained artifact is available and schema-compatible; otherwise raises a controlled `ModelUnavailable`/returns `None` to trigger baseline fallback.

- [ ] **Step 1: Write failing tests for feature contract and artifact fallback.**

```python
from backend.ml.risk.predictor import RiskPredictor


def test_unconfigured_predictor_is_unavailable(monkeypatch):
    monkeypatch.delenv("RISK_MODEL_PATH", raising=False)
    predictor = RiskPredictor()
    assert predictor.is_available() is False


def test_invalid_feature_vector_does_not_predict():
    predictor = RiskPredictor(model=None)
    try:
        predictor.predict({"rainfall_24h_mm": None})
    except ValueError as exc:
        assert "feature" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run the tests and verify failure.**

```bash
pytest -q backend/apps/risk/tests/test_predictor.py
```

Expected: FAIL until the predictor boundary exists.

- [ ] **Step 3: Implement schema validation.**

Define a stable ordered feature contract. Missing required model features must invalidate model inference rather than silently filling arbitrary values.

- [ ] **Step 4: Implement lazy model loading.**

Read the artifact path from environment/configuration. Do not bundle weights in Git. Load once per worker process, never per row in a request.

- [ ] **Step 5: Implement predictor scoring.**

Return a numeric score and clamp it to 0–100. Do not fit, retrain, or mutate model state.

- [ ] **Step 6: Wire runtime fallback.**

When the predictor is unavailable or invalid, use the baseline engine and record `model_source="baseline"` plus the relevant model fallback reason in metadata.

- [ ] **Step 7: Run tests.**

```bash
pytest -q backend/apps/risk/tests/test_predictor.py backend/apps/risk/tests/test_services.py
```

Expected: PASS.

- [ ] **Step 8: Commit.**

```bash
git add backend/ml backend/apps/risk/tests/test_predictor.py backend/apps/risk/services/risk_runtime.py
git commit -m "feat: add optional pretrained risk inference"
```

---

### Task 7: Add REST serializers, views, URLs, alerts, hotspots, and analytics

**Files:**
- Replace: `backend/apps/risk/serializers.py`
- Replace: `backend/apps/risk/views.py`
- Replace: `backend/apps/risk/urls.py`
- Create: `backend/apps/risk/services/alert_engine.py`
- Create: `backend/apps/risk/services/hotspot.py`
- Create: `backend/apps/risk/services/analytics.py`
- Test: `backend/apps/risk/tests/test_api.py`
- Test: `backend/apps/risk/tests/test_alerts.py`

**Interfaces:**
- Consumes: RiskService, selectors, persisted domain models.
- Produces: JSON REST endpoints with serializer-level validation and no heavy computation/provider calls in views.

- [ ] **Step 1: Write failing API tests for coordinate validation and endpoint response shape.**

```python
from rest_framework.test import APIClient
from django.urls import reverse


def test_current_risk_rejects_invalid_coordinates(db):
    response = APIClient().get(reverse("risk-current"), {"lat": 200, "lon": 73})
    assert response.status_code == 400


def test_current_risk_returns_score_and_breakdown(db, monkeypatch):
    monkeypatch.setattr("backend.services.risk_service.RiskService.get_current_risk", lambda self, lat, lon: {
        "score": 62.0,
        "level": "high",
        "breakdown": {"rainfall": 70, "river": 60, "terrain": 50, "historical": 40},
        "model_source": "baseline",
    })
    response = APIClient().get(reverse("risk-current"), {"lat": 18.52, "lon": 73.85})
    assert response.status_code == 200
    assert response.json()["score"] == 62.0
```

- [ ] **Step 2: Run API tests to confirm failure.**

```bash
pytest -q backend/apps/risk/tests/test_api.py
```

Expected: FAIL because the endpoint names/implementations do not yet exist.

- [ ] **Step 3: Implement serializers.**

Validate:
- latitude: -90 to 90
- longitude: -180 to 180
- radius_km: greater than 0 and bounded to a safe maximum
- days: positive integer with a bounded maximum
- pagination/limit: positive integer with a bounded maximum

- [ ] **Step 4: Implement thin API views.**

Create endpoints:

```text
GET /api/risk/events/
GET /api/risk/events/<id>/
GET /api/risk/zones/
GET /api/risk/zones/nearby/?lat=&lon=&radius_km=
GET /api/risk/current/?lat=&lon=
GET /api/risk/breakdown/?lat=&lon=
GET /api/risk/summary/
GET /api/risk/high-risk/
GET /api/risk/history/?lat=&lon=&days=
GET /api/risk/alerts/
GET /api/risk/hotspots/
GET /api/risk/analytics/
```

Views only validate input, call services/selectors, serialize results, and return responses.

- [ ] **Step 5: Implement alert engine.**

Expose:

```python
def evaluate_transition(previous_level: str | None, current_level: str) -> bool: ...
def create_alert_for_assessment(assessment) -> RiskAlert | None: ...
```

Create alerts on transitions into `high`/`severe`, avoid duplicate open alerts for the same zone and severity, and allow resolved/read status transitions.

- [ ] **Step 6: Implement hotspots and analytics.**

`hotspot.py` groups active high/severe zones spatially and returns concise GeoJSON-like records. `analytics.py` returns risk-level distributions and time-window summaries using persisted assessments; it does not run raw ETL.

- [ ] **Step 7: Run API/alert tests.**

```bash
pytest -q backend/apps/risk/tests/test_api.py backend/apps/risk/tests/test_alerts.py
```

Expected: PASS.

- [ ] **Step 8: Commit.**

```bash
git add backend/apps/risk/serializers.py backend/apps/risk/views.py backend/apps/risk/urls.py backend/apps/risk/services/alert_engine.py backend/apps/risk/services/hotspot.py backend/apps/risk/services/analytics.py backend/apps/risk/tests/test_api.py backend/apps/risk/tests/test_alerts.py
git commit -m "feat: expose risk REST APIs and alerts"
```

---

### Task 8: Add Celery risk refresh pipeline and dynamic zone persistence

**Files:**
- Replace: `backend/apps/risk/tasks.py`
- Create/replace: `backend/apps/risk/services/zone_manager.py`
- Create: `backend/apps/risk/services/task_helpers.py`
- Test: `backend/apps/risk/tests/test_tasks.py`

**Interfaces:**
- Consumes: RiskService, active RiskZone records, persisted observations.
- Produces: updated `RiskAssessment`, `RiskZone.latest_*`, `RiskAlert`, and cache state.

- [ ] **Step 1: Write failing Celery task tests.**

```python
from unittest.mock import patch


def test_refresh_active_zones_calls_risk_service(db):
    with patch("backend.apps.risk.tasks.RiskService.refresh_zone", return_value={"score": 80}) as refresh:
        from backend.apps.risk.tasks import refresh_active_zones
        result = refresh_active_zones()
    assert result["processed"] >= 0
```

- [ ] **Step 2: Run tests to verify failure.**

```bash
pytest -q backend/apps/risk/tests/test_tasks.py
```

Expected: FAIL until the tasks exist.

- [ ] **Step 3: Implement `refresh_zone` persistence.**

For each active zone:
1. derive a representative point or configured centroid;
2. call `RiskService.refresh_zone(zone_id)`;
3. create a new `RiskAssessment` rather than overwriting history;
4. update `RiskZone.latest_score`, `latest_level`, and `last_calculated_at` atomically;
5. evaluate alerts;
6. invalidate the zone’s risk cache.

- [ ] **Step 4: Implement retryable tasks.**

Use Celery autoretry or explicit retry handling with bounded exponential backoff and jitter. Keep tasks idempotent by deriving all writes from the current zone state and the current calculation timestamp.

Required tasks:

```python
refresh_active_zones()
refresh_zone_task(zone_id)
update_risk_alerts()
refresh_hotspots()
cleanup_resolved_alerts()
```

- [ ] **Step 5: Run task tests.**

```bash
pytest -q backend/apps/risk/tests/test_tasks.py
```

Expected: PASS.

- [ ] **Step 6: Commit.**

```bash
git add backend/apps/risk/tasks.py backend/apps/risk/services/zone_manager.py backend/apps/risk/services/task_helpers.py backend/apps/risk/tests/test_tasks.py
git commit -m "feat: add asynchronous risk refresh pipeline"
```

---

### Task 9: Integrate Django routing/settings, admin, documentation, and full verification

**Files:**
- Modify: existing project settings file containing `INSTALLED_APPS`
- Modify: existing root URL configuration
- Modify: existing Celery beat/task configuration if present
- Modify: `backend/apps/risk/admin.py`
- Create: `backend/apps/risk/README.md`
- Create: `backend/apps/risk/tests/test_integration.py`
- Modify: CI workflow only if the repository already has one and it needs Risk-specific services

**Interfaces:**
- Consumes: completed Risk app.
- Produces: a registered Django app with migrations, URLs, admin, Celery discovery, and integration tests.

- [ ] **Step 1: Write integration tests.**

```python
from django.urls import reverse


def test_risk_urls_are_registered():
    assert reverse("risk-summary")
    assert reverse("risk-current")


def test_risk_migrations_are_current():
    from django.core.management import call_command
    call_command("migrate", verbosity=0)
```

- [ ] **Step 2: Run the integration tests and full test suite before final wiring.**

```bash
pytest -q backend/apps/risk/tests/test_integration.py
```

Expected: FAIL for URL registration until project wiring is complete.

- [ ] **Step 3: Register the app and root routes.**

Add the Risk app config exactly once to `INSTALLED_APPS` and include its URLs under `/api/risk/`. Preserve the existing Weather/Core registrations.

- [ ] **Step 4: Register admin classes.**

Expose searchable/filterable admin views for `FloodEvent`, `RiskZone`, `RiskAssessment`, and `RiskAlert`. Mark derived timestamps and score fields appropriately read-only where they should not be edited manually.

- [ ] **Step 5: Add Risk README.**

Document:
- ownership boundaries;
- endpoint list;
- scoring weights and levels;
- environment/model configuration;
- import command examples;
- Celery tasks;
- explicit statement that provider API calls belong to Weather and ML training is offline.

- [ ] **Step 6: Run migrations and the complete Risk test suite.**

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
pytest -q backend/apps/risk/tests
pytest -q
```

Expected: no pending model changes; all Risk tests pass; existing project tests remain green.

- [ ] **Step 7: Run static and application checks.**

```bash
python manage.py check
python manage.py check --deploy
```

Fix only Risk-related issues introduced by this rebuild and preserve existing project conventions.

- [ ] **Step 8: Exercise representative API paths against a running PostGIS/Redis environment.**

```bash
curl -f "http://localhost:8000/api/risk/current/?lat=18.5204&lon=73.8567"
curl -f "http://localhost:8000/api/risk/summary/"
curl -f "http://localhost:8000/api/risk/zones/nearby/?lat=18.5204&lon=73.8567&radius_km=25"
```

Confirm responses are JSON, scores are 0–100, levels match thresholds, and no provider HTTP request is initiated from the web process.

- [ ] **Step 9: Verify Celery registration.**

Start a worker in the project’s supported way and inspect registered tasks. Confirm the Risk task names are present and execute one against a test zone.

- [ ] **Step 10: Review the final diff for architecture violations.**

```bash
git diff --check
rg -n "requests\.|httpx\.|urllib|AccuWeather|IMD|CWC" backend/apps/risk backend/services/risk_service.py
rg -n "fit\(|fit_predict\(|train|GeoDataFrame|pandas|geopandas" backend/apps/risk backend/services/risk_service.py
```

Expected: no provider client strings/imports in Risk, no training calls, no Pandas/GeoPandas ETL in views/command, and no whitespace errors.

- [ ] **Step 11: Commit the integrated Risk subsystem.**

```bash
git add backend/apps/risk backend/services/risk_service.py backend/ml backend/data_processing/floods <project-settings-file> <root-url-file> docs/superpowers/specs/2026-09-07-risk-api-rebuild-design.md docs/superpowers/plans/2026-09-07-risk-api-rebuild.md
git commit -m "feat: rebuild flood risk API"
```

---

## Final Acceptance Checklist

- [ ] PostGIS migrations apply cleanly.
- [ ] `FloodEvent`, `RiskZone`, `RiskAssessment`, and `RiskAlert` persist correctly.
- [ ] Historical flood import is idempotent and preserves provenance.
- [ ] Current risk returns a deterministic baseline when model data is unavailable.
- [ ] Risk breakdown exposes rainfall/river/terrain/historical contributions.
- [ ] High/severe alerts are threshold-transition based and deduplicated.
- [ ] Nearby/high-risk/history/hotspot/analytics endpoints use selectors/services.
- [ ] Celery refreshes zones and persists assessment history.
- [ ] Redis cache is used only as a derived accelerator, never as source of truth.
- [ ] Risk never calls AccuWeather/IMD/CWC/state APIs directly.
- [ ] No request path trains XGBoost/U-Net.
- [ ] No Pandas/GeoPandas ETL exists in views or the import command.
- [ ] Missing source data is explicitly surfaced in `data_quality`.
- [ ] Existing Weather and Core applications remain functional.
- [ ] Full project test suite and Django checks pass.
