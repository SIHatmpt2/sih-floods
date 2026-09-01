# River ML Data Pipeline Design

**Goal:** Harden `backend/data_processing` and build a reproducible CWC river-data pipeline that converts raw CSV observations into canonical, compressed Parquet datasets suitable for leakage-safe XGBoost training.

## Scope

- Fix shared data-processing correctness issues that affect the river pipeline.
- Implement `backend/data_processing/rivers/{clean,transform,features,pipeline}.py`.
- Preserve raw CWC CSVs as source data.
- Produce normalized per-source Parquet plus a combined canonical Parquet dataset.
- Preserve provenance and station identity.
- Add temporal and lag/rolling features only from current/past observations.
- Do not invent a flood-event target; expose a clean interface for joining a future historical flood-event label dataset.
- Add tests for parsing, normalization, deduplication, feature generation, and pipeline behavior.

## Canonical River Schema

Each normalized observation should have, where available:

- `station_id` — stable deterministic station key derived from agency/station/location context.
- `station` — source station name.
- `agency`, `state`, `district`, `tehsil`, `block`, `village`.
- `river`, `basin`, `tributary`, `subtributary`, `subsubtributary`, `local_river`.
- `latitude`, `longitude`.
- `is_discharge_data_available`.
- `rl_of_zero_gauge`, `mean_sea_level`.
- `observed_at` — parsed timestamp.
- `water_level_m` — numeric water level where present.
- `discharge_cumecs` — numeric discharge where present.
- `source_file` — relative raw source path.

Unknown values remain missing rather than being silently interpreted as zero. Raw source values are not overwritten.

## Feature Contract

Derived features may include:

- calendar features: year, month, day-of-year, day-of-week, hour, monsoon/season indicator;
- station-relative water-level features where the required reference is present;
- lag features such as 1h, 3h, 6h, 12h, 24h;
- rolling statistics such as 6h/24h mean, max, and standard deviation;
- rate-of-change features.

All temporal features must be computed after sorting by station and timestamp. Features may only use observations at or before the prediction timestamp. No future-window or centered rolling calculation is permitted.

## Parquet Strategy

1. Discover all CWC CSVs under `backend/data/raw/river_data/cwc/`.
2. Read each source without loading all files into memory simultaneously.
3. Normalize each source to the canonical schema.
4. Clean types, nulls, timestamps, coordinates, and duplicates.
5. Add provenance.
6. Write compressed Parquet for each source under `backend/data/processed/river_data/parquet/`.
7. Write a combined canonical Parquet dataset under `backend/data/processed/river_data/river_observations.parquet` when feasible.
8. Never modify or delete the raw CSVs.

## ML Readiness

- Parquet is the storage/interchange format, not the target itself.
- XGBoost inputs must be numeric or explicitly encoded; raw free-text station fields are retained for traceability but excluded from the numeric feature matrix unless encoded through a defined feature step.
- Train/validation/test splitting must be chronological or grouped chronologically by station to prevent temporal leakage.
- Any learned imputation/scaling parameters must be fit on training data only. XGBoost itself does not require feature scaling.
- The future flood-event dataset will provide the supervised target and should be joined using explicit station/location/time rules rather than inferred from discharge magnitude alone.

## Error Handling

- Fail loudly on structurally invalid input (missing required timestamp/station information).
- Coerce malformed individual measurements to missing and report counts.
- Reject invalid coordinates rather than silently clipping them.
- Log source file, row counts, dropped duplicates, invalid measurements, and output paths.
- Pipeline errors must retain the original exception context.

## Dependencies

Use the existing pandas/NumPy/scikit-learn/XGBoost/joblib stack declared in `backend/requirements.txt`. Add a Parquet engine dependency only if the repository does not already provide one; prefer `pyarrow` for interoperability and efficient columnar storage.

## Testing

Tests should cover representative CWC schemas, alternate/missing values, timestamp parsing, coordinate validation, duplicate removal, station grouping, lag/rolling leakage behavior, Parquet round-trip, and multi-file pipeline execution. Tests must use small fixtures rather than the committed multi-megabyte raw files.
