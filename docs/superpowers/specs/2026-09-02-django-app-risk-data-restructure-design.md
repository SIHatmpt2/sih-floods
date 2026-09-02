# Django App and Risk Data Restructure Design

**Date:** 2026-09-02
**Target branch:** `main`

## Goal
Restructure the backend into three Django apps (`core`, `risk`, `weather`) under `backend/apps`, move the complete tracked `backend/data` payload from `saksham` into `backend/apps/risk/data`, remove the old `backend/data` tree, and keep the CWC data-processing pipeline functional against the new location.

## Architecture
- `backend/apps/core` contains shared Django application scaffolding.
- `backend/apps/risk` is the flood-risk Django application and owns its data at `backend/apps/risk/data`.
- `backend/apps/weather` contains weather/rainfall application scaffolding.
- `backend/data_processing` remains outside Django apps because it is reusable ETL/ML data infrastructure rather than request/domain application code.
- Existing CWC raw data is moved by reusing the source Git blobs from `saksham`; generated Parquet outputs remain runtime artifacts and are not committed.

## Required Structure
```text
backend/
├── apps/
│   ├── __init__.py
│   ├── core/
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   ├── migrations/__init__.py
│   │   └── data/
│   │       ├── raw/
│   │       ├── processed/
│   │       └── geospatial/
│   └── weather/
├── data_processing/
├── config/
└── manage.py
```
Empty directories are represented with `.gitkeep`. `backend/data` is removed entirely.

## Data Migration
All tracked files beneath `saksham/backend/data` are placed at the equivalent path beneath `main/backend/apps/risk/data`. This includes the CWC river/rainfall raw datasets and the GLOF atlas. Existing empty directories are preserved with `.gitkeep` where needed.

## Pipeline Changes
Update all hard-coded/default data paths in `backend/data_processing` and CI from `backend/data/...` to `backend/apps/risk/data/...`. The processing package remains at `backend/data_processing`.

## Django Changes
Register `apps.core`, `apps.risk`, and `apps.weather` in Django settings. Ensure the `apps` package is importable and each app has conventional Django Python modules. Do not introduce application models or API behavior beyond scaffolding.

## CI and Verification
The CWC Parquet workflow is retained on `main` and updated for the new data location. Verification must cover the final Git tree, absence of `backend/data`, presence of the three Django apps, import/configuration correctness, and the existing data-processing tests/pipeline path assumptions.

## Non-Goals
- No deletion or transformation of source datasets.
- No redesign of the existing rainfall/river feature engineering.
- No new ML model implementation.
- No frontend restructuring.
