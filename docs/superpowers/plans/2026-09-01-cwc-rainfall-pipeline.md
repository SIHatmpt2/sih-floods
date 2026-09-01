# CWC Rainfall Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a robust CWC rainfall CSV -> canonical compressed Parquet pipeline with leakage-safe rainfall features while preserving the existing river pipeline.

**Architecture:** Add a dataset-specific `backend/data_processing/rainfall/` package following the existing river clean/transform/features/pipeline separation. The rainfall pipeline discovers all CWC rainfall CSVs, normalizes their common CWC station schema plus the rainfall measurement column, writes per-source Parquet and a combined canonical Parquet, and exposes XGBoost-safe numeric features without fabricating missing rainfall.

**Tech Stack:** Python 3.12, pandas, NumPy, PyArrow/Parquet, existing Docker Compose backend.

**Spec:** `docs/superpowers/specs/2026-09-01-river-ml-data-pipeline-design.md`

## Global Constraints

- Preserve raw CWC CSVs; generated Parquet remains a derived artifact.
- Unknown/missing measurements remain missing; never coerce missing rainfall to zero.
- Validate timestamps, stations, and coordinates; drop structurally unusable rows with logged counts.
- Temporal features must use current/past observations only and be calculated after sorting within station.
- Do not invent a flood target or join rainfall to river observations in this change.
- Use existing pandas/NumPy/pyarrow stack; do not add pytest solely for this pipeline.

---

### Task 1: Canonical rainfall cleaning

**Files:**
- Create: `backend/data_processing/rainfall/__init__.py`
- Create: `backend/data_processing/rainfall/clean.py`

**Interfaces:**
- Consumes: raw pandas DataFrames from CWC rainfall CSVs.
- Produces: `normalize_cwc_rainfall_columns(df) -> DataFrame` and `clean_cwc_rainfall_data(df, source_file) -> DataFrame`.

- [ ] **Step 1: Define canonical rainfall columns and CWC header aliases.**
- [ ] **Step 2: Normalize text sentinels (`-`, blank, NA-like values) without changing valid zero rainfall.**
- [ ] **Step 3: Parse timestamp, latitude, longitude and rainfall as nullable numeric types.**
- [ ] **Step 4: Create deterministic `station_id` from stable station metadata.**
- [ ] **Step 5: Drop rows missing timestamp/station, validate coordinate bounds, sort by station/time, and deduplicate station+timestamp.**
- [ ] **Step 6: Log invalid rows and duplicate counts and return a stable column order.**

### Task 2: Rainfall temporal transformation and features

**Files:**
- Create: `backend/data_processing/rainfall/transform.py`
- Create: `backend/data_processing/rainfall/features.py`

**Interfaces:**
- Consumes: cleaned canonical rainfall DataFrame.
- Produces: `transform_rainfall_data(df)`, `add_rainfall_features(df)`, `select_xgboost_features(df, target_column=None)`.

- [ ] **Step 1: Normalize/sort timestamps and add calendar fields.**
- [ ] **Step 2: Add station-local lag features for 1, 3, 6, 12 and 24 observations/hours.**
- [ ] **Step 3: Add backward-looking cumulative rainfall windows (3, 6, 12, 24, 72 observations) using only current/past rows.**
- [ ] **Step 4: Add rolling mean/max for 24 observations and rainfall rate/change features without future leakage.**
- [ ] **Step 5: Exclude identifiers/text/timestamp fields from the XGBoost numeric feature selector.**

### Task 3: Rainfall CSV -> Parquet pipeline

**Files:**
- Create: `backend/data_processing/rainfall/pipeline.py`
- Modify: `backend/data_processing/rainfall/__init__.py`

**Interfaces:**
- Consumes: `backend/data/raw/rainfall/cwc/*.csv`.
- Produces: per-source `.parquet` files and `rainfall_observations.parquet` under `backend/data/processed/rainfall/parquet/`.

- [ ] **Step 1: Discover all rainfall CSV files recursively in deterministic order.**
- [ ] **Step 2: Process each CSV one at a time to avoid loading the full corpus simultaneously.**
- [ ] **Step 3: Add provenance and write Zstandard-compressed Parquet with PyArrow.**
- [ ] **Step 4: Combine per-source Parquet fragments with schema validation.**
- [ ] **Step 5: Provide a module entry point: `python -m data_processing.rainfall.pipeline`.**

### Task 4: Repository integration

**Files:**
- Modify: `.gitignore`
- Modify: `.github/workflows/build-river-parquet.yml`

- [ ] **Step 1: Ignore generated rainfall Parquet output.**
- [ ] **Step 2: Update the data-build workflow to generate both river and rainfall Parquet artifacts.**
- [ ] **Step 3: Preserve existing river workflow behavior.**

### Task 5: Verification

**Files:**
- Modify: `backend/data_processing/rivers/__init__.py` if needed to remove the `runpy` warning caused by eager pipeline import.

- [ ] **Step 1: Run lightweight syntax/import checks.**
- [ ] **Step 2: Run the rainfall pipeline in Docker against the committed CWC CSVs.**
- [ ] **Step 3: Verify per-source and combined Parquet output exists and has consistent schema.**
- [ ] **Step 4: Inspect row counts, timestamp ranges, unique stations, missing rainfall, and rainfall value ranges.**
- [ ] **Step 5: Report verification evidence without claiming tests that were not run.**
