# Django App and Risk Data Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `main` into three Django apps under `backend/apps`, move the complete tracked data tree from `saksham/backend/data` to `backend/apps/risk/data`, remove the old backend data tree, and keep data processing pointed at the new risk-owned data location.

**Architecture:** `apps/core`, `apps/risk`, and `apps/weather` are conventional Django app packages. `apps/risk/data` owns flood-risk datasets, while `backend/data_processing` remains reusable ETL/ML infrastructure. Git tree entries from `saksham` are reused by blob SHA for the large raw datasets, avoiding content duplication; generated Parquet outputs remain runtime artifacts.

**Tech Stack:** Django 5.2, Python 3.12, pandas, PyArrow, GitHub Git Data API, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-02-django-app-risk-data-restructure-design.md`

## Global Constraints

- Target application branch is `main`.
- `backend/apps/core`, `backend/apps/risk`, and `backend/apps/weather` contain Python Django scaffolding.
- `backend/apps/risk/data` is the canonical data root.
- `backend/data` is removed entirely.
- `backend/data_processing` remains outside Django apps.
- All tracked files beneath `saksham/backend/data` are transferred without content transformation.
- Empty required directories are represented with `.gitkeep`.
- CWC Parquet outputs are generated, not committed.
- Existing rainfall/river feature engineering is not redesigned.

---

### Task 1: Create the Django app scaffold

**Files:**
- Create: `backend/apps/__init__.py`
- Create: `backend/apps/core/__init__.py`
- Create: `backend/apps/core/admin.py`
- Create: `backend/apps/core/apps.py`
- Create: `backend/apps/core/models.py`
- Create: `backend/apps/core/serializers.py`
- Create: `backend/apps/core/views.py`
- Create: `backend/apps/core/tests.py`
- Create: `backend/apps/core/migrations/__init__.py`
- Create: `backend/apps/risk/__init__.py`
- Create: `backend/apps/risk/admin.py`
- Create: `backend/apps/risk/apps.py`
- Create: `backend/apps/risk/models.py`
- Create: `backend/apps/risk/serializers.py`
- Create: `backend/apps/risk/views.py`
- Create: `backend/apps/risk/tests.py`
- Create: `backend/apps/risk/migrations/__init__.py`
- Create: `backend/apps/weather/__init__.py`
- Create: `backend/apps/weather/admin.py`
- Create: `backend/apps/weather/apps.py`
- Create: `backend/apps/weather/models.py`
- Create: `backend/apps/weather/serializers.py`
- Create: `backend/apps/weather/views.py`
- Create: `backend/apps/weather/tests.py`
- Create: `backend/apps/weather/migrations/__init__.py`
- Delete: `backend/apps/.gitkeep`

**Interfaces:**
- Produces `CoreConfig.name == "apps.core"`, `RiskConfig.name == "apps.risk"`, and `WeatherConfig.name == "apps.weather"`.
- Produces importable Django packages with conventional empty model/admin/serializer/view modules.

- [ ] **Step 1: Write the failing app import/configuration test**

Add a data-processing-independent test module under `backend/apps/risk/tests.py` that imports `RiskConfig` and asserts its Django app name is `apps.risk`; duplicate the same explicit assertion for core and weather in their own `tests.py` modules.

- [ ] **Step 2: Run the focused tests to verify they fail correctly**

Run from `backend`: `python -m pytest apps/core/tests.py apps/risk/tests.py apps/weather/tests.py -q`.
Expected: collection/import failure because the app modules do not yet exist.

- [ ] **Step 3: Write the minimal Django scaffolding**

Each `apps.py` defines one `AppConfig` subclass with `default_auto_field = "django.db.models.BigAutoField"` and the package-specific `name`. Each other module contains a module docstring and valid Python. Each migrations directory gets `__init__.py`.

- [ ] **Step 4: Run the focused tests and Django checks**

Run from `backend`: `python -m pytest apps/core/tests.py apps/risk/tests.py apps/weather/tests.py -q` and `python manage.py check`.
Expected: all focused tests pass and Django reports no system-check errors.

- [ ] **Step 5: Commit**

Commit on the isolated implementation branch with message: `feat: scaffold core risk and weather apps`.

---

### Task 2: Move the complete tracked data tree into the risk app

**Files:**
- Move/recreate: every tracked file beneath `saksham/backend/data` to `backend/apps/risk/data/<same relative path>`.
- Delete: every tracked file beneath `backend/data` from `main`.
- Preserve: empty directories from the source data tree with `.gitkeep` when they have no tracked data files.

**Interfaces:**
- Produces canonical paths such as `backend/apps/risk/data/raw/rainfall/cwc/...`, `backend/apps/risk/data/raw/river_data/cwc/...`, and the GLOF atlas path.
- Produces no `backend/data` entries.

- [ ] **Step 1: Write a structural regression test**

Add `backend/apps/risk/tests.py` assertions that `Path(__file__).resolve().parent / "data"` exists, that its `raw` and `geospatial` directories exist, and that the moved CWC rainfall/river files exist by filename.

- [ ] **Step 2: Run the structural test to verify it fails correctly**

Run from `backend`: `python -m pytest apps/risk/tests.py -q`.
Expected: failure because the risk-owned data directory does not yet exist.

- [ ] **Step 3: Rebuild the Git tree using source blob SHAs**

Fetch the recursive `saksham` tree, select all entries under `backend/data`, and add each blob at `backend/apps/risk/data/<relative path>` to a tree based on the current implementation branch. Add `sha: null` entries for the existing `backend/data` files to delete them. Do not re-upload the large dataset contents; reuse their existing blob SHAs.

- [ ] **Step 4: Add required `.gitkeep` files for empty directories**

Preserve `geospatial/.gitkeep` if the source directory is empty. If any destination directory would otherwise contain no tracked files, add a zero-byte `.gitkeep`. Do not retain `backend/data/.gitkeep`.

- [ ] **Step 5: Run the structural test and inspect the final tree**

Run `python -m pytest apps/risk/tests.py -q` and fetch the recursive implementation-branch tree. Expected: risk data tests pass; no `backend/data` paths remain; every source data blob has an equivalent risk-data path.

- [ ] **Step 6: Commit**

Commit with message: `feat: move backend data under risk app`.

---

### Task 3: Repoint data-processing paths and CI

**Files:**
- Modify: `backend/data_processing/rivers/pipeline.py`
- Modify: `backend/data_processing/rainfall/pipeline.py`
- Modify/create: `.github/workflows/build-data-parquet.yml`

**Interfaces:**
- River defaults become `backend/apps/risk/data/raw/river_data/cwc` and `backend/apps/risk/data/processed/river_data/parquet`.
- Rainfall defaults become `backend/apps/risk/data/raw/rainfall/cwc` and `backend/apps/risk/data/processed/rainfall/parquet`.
- CI builds both pipelines from `backend` and uploads `backend/apps/risk/data/processed/...` artifacts.

- [ ] **Step 1: Write failing path tests**

Extend existing pipeline tests so their default-path constants equal `Path(__file__).resolve().parents[3] / "apps" / "risk" / "data" / "raw" / ...` and corresponding processed directories.

- [ ] **Step 2: Run focused tests to verify failure**

Run from `backend`: `python -m pytest data_processing/tests/test_rivers_pipeline.py data_processing/tests/test_integration.py -q`.
Expected: path assertions fail against the old `backend/data` defaults.

- [ ] **Step 3: Update pipeline defaults**

Change only the data-root portions of the two pipelines. Keep discovery, cleaning, feature engineering, output naming, and Parquet writing unchanged.

- [ ] **Step 4: Update CI artifact paths and trigger**

Use a workflow that triggers on pushes to `main` and manual dispatch, installs `backend/requirements.txt`, runs both pipeline modules from `backend`, and uploads `backend/apps/risk/data/processed/river_data/parquet/*.parquet` and `backend/apps/risk/data/processed/rainfall/parquet/*.parquet`.

- [ ] **Step 5: Run focused tests**

Run `python -m pytest data_processing/tests -q` from `backend`.
Expected: all existing data-processing tests pass.

- [ ] **Step 6: Commit**

Commit with message: `refactor: point data pipelines at risk data root`.

---

### Task 4: Register apps and verify Django integration

**Files:**
- Modify: `backend/config/settings.py`
- Modify: `backend/config/urls.py` only if needed to keep imports clean; no API endpoints are required by this restructure.
- Modify: `README.md` only where it documents the old `backend/data` location.

**Interfaces:**
- Django `INSTALLED_APPS` contains `apps.core`, `apps.risk`, and `apps.weather`.
- No functional API behavior is added.

- [ ] **Step 1: Write failing settings test**

Add an assertion to the app test suite that `settings.INSTALLED_APPS` contains all three app package names.

- [ ] **Step 2: Run it to verify failure**

Run `python -m pytest apps/core/tests.py apps/risk/tests.py apps/weather/tests.py -q` from `backend`.
Expected: failure because settings does not register the new apps.

- [ ] **Step 3: Register the apps**

Add `apps.core`, `apps.risk`, and `apps.weather` to `INSTALLED_APPS` without changing unrelated settings.

- [ ] **Step 4: Update stale documentation references**

Search the repository for `backend/data` and replace only references that describe the canonical backend data path. Do not change historical Superpowers records that intentionally describe prior states.

- [ ] **Step 5: Run Django and Python tests**

Run `python manage.py check` and `python -m pytest data_processing/tests apps/core/tests.py apps/risk/tests.py apps/weather/tests.py -q` from `backend`.
Expected: no Django check errors and zero test failures.

- [ ] **Step 6: Commit**

Commit with message: `feat: register backend domain apps`.

---

### Task 5: Final structural and regression verification

**Files:**
- Modify only if verification exposes a defect; otherwise no source changes.

**Interfaces:**
- Final `main` tree contains the three apps, risk-owned data, and unchanged reusable data-processing package.

- [ ] **Step 1: Run the full backend test suite**

From `backend`, run `python -m pytest -q`.
Expected: zero failures.

- [ ] **Step 2: Run Django deployment checks**

From `backend`, run `python manage.py check --deploy`.
Expected: no fatal system-check errors; environment-only warnings are recorded if present.

- [ ] **Step 3: Verify structural invariants**

Fetch the recursive `main` tree and confirm: `backend/apps/__init__.py` exists; each app has the specified Python modules and migrations init; `backend/apps/risk/data` contains every tracked source-data path from `saksham/backend/data`; `backend/data` has no entries; data-processing remains at `backend/data_processing`; no stale runtime path remains in pipeline source or workflow.

- [ ] **Step 4: Verify final commit status**

Confirm `main` points to the intended final commit and that the implementation branch is an ancestor of `main` after integration.

- [ ] **Step 5: Commit any verification-only fixes**

If and only if verification required a source correction, commit it with a focused message and rerun the affected verification plus the full suite.
