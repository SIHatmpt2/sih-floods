# River ML Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the shared processing utilities and implement a reproducible CWC river pipeline that normalizes raw CSV observations into compressed Parquet datasets ready for leakage-safe XGBoost training.

**Architecture:** Keep raw CSVs immutable. A dataset-specific `rivers` package will normalize CWC schemas, validate station/timestamp/measurement fields, add provenance, derive strictly historical temporal features, and write per-source plus combined Parquet outputs. Shared utilities remain dataset-agnostic; future flood-event labels will be joined later through an explicit target-building step.

**Tech Stack:** Python 3, pandas, NumPy, PyArrow, scikit-learn, XGBoost, pytest.

**Spec:** `docs/superpowers/specs/2026-09-01-river-ml-data-pipeline-design.md`

## Global Constraints

- Preserve raw CWC CSVs; never overwrite or delete them.
- Unknown/malformed values remain missing unless a field has a domain-justified deterministic replacement.
- Temporal features may use only current/past observations; no future leakage.
- XGBoost does not require feature scaling; do not introduce unnecessary scaling.
- Do not invent a flood-event target from river measurements.
- Prefer PyArrow for Parquet interoperability and compression.
- Tests use small fixtures and do not depend on the large committed raw files.

---

### Task 1: Harden shared processing utilities

**Files:**
- Modify: `backend/data_processing/clean.py`
- Modify: `backend/data_processing/transform.py`
- Test: `backend/data_processing/tests/test_clean.py`
- Test: `backend/data_processing/tests/test_transform.py`

**Interfaces:**
- Preserve existing public helper names.
- `coerce_datetime` must support explicit format lists through a new optional `formats` argument without breaking current callers.
- `parse_lat_lon` and `parse_wkt_point` continue returning `Point | None`.

- [ ] **Step 1: Add tests for null handling, datetime parsing, coordinate bounds, and infinite replacement.**
- [ ] **Step 2: Run the focused tests and verify failures for the new behaviors.**
- [ ] **Step 3: Implement minimal changes: normalize null-like text before numeric coercion where appropriate, allow explicit datetime formats, keep missing numeric values missing in generic utilities, and retain defensive coordinate parsing.**
- [ ] **Step 4: Run focused tests and verify they pass.**
- [ ] **Step 5: Commit the shared utility changes.**

### Task 2: Implement CWC river cleaning

**Files:**
- Modify: `backend/data_processing/rivers/clean.py`
- Test: `backend/data_processing/tests/test_rivers_clean.py`

**Interfaces:**
- `normalize_cwc_columns(df) -> DataFrame`
- `clean_cwc_data(df, source_file) -> DataFrame`
- Canonical columns include station identity, administrative/geographic fields, timestamp, water level, discharge, and source provenance.

- [ ] **Step 1: Add fixture-based tests for the CWC header shown in the raw files, numeric conversion, timestamp conversion, `-` missing values, and duplicate observations.**
- [ ] **Step 2: Run tests and verify the expected failures.**
- [ ] **Step 3: Implement canonical renaming and type cleaning without converting unknown discharge/water-level values to zero.**
- [ ] **Step 4: Validate latitude/longitude ranges and preserve invalid measurements as missing while reporting them through logging.**
- [ ] **Step 5: Add deterministic `station_id` from stable station/location context and `source_file`.**
- [ ] **Step 6: Run tests and verify they pass.**
- [ ] **Step 7: Commit the river cleaning implementation.**

### Task 3: Implement leakage-safe river transformations and features

**Files:**
- Modify: `backend/data_processing/rivers/transform.py`
- Modify: `backend/data_processing/rivers/features.py`
- Test: `backend/data_processing/tests/test_rivers_features.py`

**Interfaces:**
- `transform_river_data(df) -> DataFrame`
- `add_river_features(df, value_column='water_level_m') -> DataFrame`

- [ ] **Step 1: Add tests proving station/time sorting and lag behavior.**
- [ ] **Step 2: Add tests proving rolling features never include future rows and do not cross station boundaries.**
- [ ] **Step 3: Implement timestamp/calendar features and station-local lags for 1h, 3h, 6h, 12h, and 24h based on observation order/timestamp.**
- [ ] **Step 4: Implement station-local rolling mean/max/std and rate-of-change features using backward-looking windows only.**
- [ ] **Step 5: Keep missing history as missing instead of fabricating zero observations.**
- [ ] **Step 6: Run focused tests and verify they pass.**
- [ ] **Step 7: Commit transformation and feature changes.**

### Task 4: Implement the river CSV → Parquet pipeline

**Files:**
- Modify: `backend/data_processing/rivers/pipeline.py`
- Modify: `backend/data_processing/rivers/__init__.py`
- Modify: `backend/data_processing/pipeline.py` only if required to expose the river pipeline cleanly.
- Modify: `backend/requirements.txt` to add `pyarrow>=18,<22` if no Parquet engine exists.
- Test: `backend/data_processing/tests/test_rivers_pipeline.py`

**Interfaces:**
- `discover_csv_files(raw_dir) -> list[Path]`
- `process_file(input_path, output_dir) -> Path`
- `run_pipeline(raw_dir=None, output_dir=None, combine=True) -> dict[str, Path]`

- [ ] **Step 1: Add tests using temporary CSV fixtures for discovery, per-file processing, Parquet round-trip, and combined output.**
- [ ] **Step 2: Run tests and verify failures.**
- [ ] **Step 3: Implement deterministic raw/output paths rooted at `backend/data`, not `backend/apps`.**
- [ ] **Step 4: Implement per-source Parquet output with compression and stable filenames.**
- [ ] **Step 5: Implement combined canonical Parquet output without loading every source twice or mutating raw files.**
- [ ] **Step 6: Emit row-count, invalid-value, duplicate, and output-path logging.**
- [ ] **Step 7: Preserve exception context rather than replacing all exceptions with generic errors.**
- [ ] **Step 8: Run the pipeline tests and verify they pass.**
- [ ] **Step 9: Commit the pipeline implementation and dependency change.**

### Task 5: Fix existing historical-event path/interface inconsistencies

**Files:**
- Modify: `backend/data_processing/past_flood_events/pipeline.py`
- Modify: `backend/data_processing/past_flood_events/transform.py` only where needed for compatibility with hardened shared helpers.
- Test: `backend/data_processing/tests/test_past_flood_events.py`

**Interfaces:**
- Preserve `past_flood_events.run_pipeline`, `clean_data`, `engineer_features`, and `transform_geospatial`.

- [ ] **Step 1: Add regression tests for the correct module path and repository-relative default data paths.**
- [ ] **Step 2: Fix documentation/CLI examples from `flood_events` to `past_flood_events`.**
- [ ] **Step 3: Fix default raw/output paths to the repository's `backend/data` layout without assuming the future historical-event file exists today.**
- [ ] **Step 4: Run regression tests and verify they pass.**
- [ ] **Step 5: Commit the compatibility fixes.**

### Task 6: Whole-package verification and ML data contract

**Files:**
- Modify: `backend/data_processing/rivers/features.py` or `backend/data_processing/rivers/pipeline.py` only if verification reveals an issue.
- Create: `backend/data_processing/tests/test_integration.py`
- Create: `backend/data_processing/README.md`

- [ ] **Step 1: Run the full data-processing test suite.**
- [ ] **Step 2: Run static compilation/import checks on every processing module.**
- [ ] **Step 3: Run the river pipeline against a small fixture set and inspect Parquet schema, null counts, station grouping, and chronological ordering.**
- [ ] **Step 4: Document the canonical schema, generated features, Parquet locations, and the future flood-label join contract.**
- [ ] **Step 5: Verify no future values are used by feature generation.**
- [ ] **Step 6: Commit final documentation and fixes.**

## Verification Commands

```bash
cd backend
python -m compileall data_processing
pytest data_processing/tests -q
python -m data_processing.rivers.pipeline
```

The full raw CWC corpus should be processed in an environment with PyArrow installed. Generated Parquet artifacts are derived data and should not be treated as source-of-truth input; if repository size policy permits them they can be committed separately, otherwise the pipeline deterministically regenerates them from the committed CSVs.
