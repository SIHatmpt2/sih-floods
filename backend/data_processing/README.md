# Data processing

## River CWC pipeline

From the repository root, install backend dependencies and run:

```bash
cd backend
python -m data_processing.rivers.pipeline
```

The default input is `backend/data/raw/river_data/cwc/` and outputs are written to `backend/data/processed/river_data/parquet/`.

For every source CSV, the pipeline:

1. normalizes CWC headers;
2. converts timestamps and numeric measurements safely;
3. treats `-`, blank, and malformed measurements as missing;
4. validates latitude/longitude ranges;
5. creates a deterministic `station_id`;
6. removes duplicate station/timestamp observations while keeping the first source row;
7. adds calendar fields;
8. adds station-local backward-looking lag/rolling features;
9. writes Zstandard-compressed Parquet.

It also creates `river_observations.parquet` from the per-file outputs. Raw CSVs are never modified.

### Measurement semantics

The current CWC files include a column named `River Water Level Telemetry Hourly (meter)`, so its canonical field is `water_level_m`. A real discharge measurement is represented as `discharge_cumecs` when a source contains a recognized discharge column. The pipeline does not fabricate discharge from water level.

### XGBoost preparation

The Parquet output is a feature store, not a labeled training set. XGBoost can consume the numeric temporal, lag, rolling, and measurement features after the future historical-flood dataset supplies the supervised target. Any train/validation/test split must be chronological (or otherwise grouped by station and time) so future observations cannot leak into training.

No min-max scaling is required for XGBoost. If imputation or learned encoding is introduced later, fit those parameters on the training split only.

## Tests

```bash
cd backend
python -m compileall data_processing
pytest data_processing/tests -q
```
