"""Build the V1 supervised training table from processed flood, rainfall, river and glacier data."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "apps" / "risk" / "data"
DEFAULT_OUTPUT = DEFAULT_DATA_ROOT / "processed" / "training_v1.parquet"
TARGET_COLUMN = "flood_next_72h"
RAIN_FEATURES = ["rainfall_24h", "rainfall_48h", "rainfall_72h", "rainfall_7d", "rainfall_30d"]
RIVER_FEATURES = [
    "water_level_m", "water_level_delta_1h", "water_level_pct_change_1h", "water_level_lag_1h", "water_level_lag_3h", "water_level_lag_6h", "water_level_lag_12h", "water_level_lag_24h",
    "water_level_rolling_mean_6h", "water_level_rolling_max_6h", "water_level_rolling_std_6h", "water_level_rolling_mean_24h", "water_level_rolling_max_24h", "water_level_rolling_std_24h",
    "discharge_cumecs", "discharge_delta_1h", "discharge_pct_change_1h", "discharge_lag_1h", "discharge_lag_3h", "discharge_lag_6h", "discharge_lag_12h", "discharge_lag_24h",
    "discharge_rolling_mean_6h", "discharge_rolling_max_6h", "discharge_rolling_std_6h", "discharge_rolling_mean_24h", "discharge_rolling_max_24h", "discharge_rolling_std_24h",
]
GLACIER_FEATURES = [
    "glacier_area_km2", "glacier_area_change_1y_km2", "glacier_area_change_1y_pct", "glacier_cumulative_area_change_km2", "glacier_cumulative_area_change_pct",
    "glacier_elevation_m", "glacier_melting_rate_min_km_per_year", "glacier_melting_rate_max_km_per_year",
]
HISTORICAL_FEATURES = ["flood_count_1y", "flood_count_3y", "flood_count_5y", "days_since_last_flood", "historical_max_severity", "historical_mean_severity", "historical_glof_count"]


def _norm(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def _require_columns(df: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = columns - set(df.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {sorted(missing)}")


def _prepare_river(df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(df, {"station_id", "observed_at"}, "river data")
    result = df.copy()
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result = result.dropna(subset=["station_id", "observed_at"])
    keep = ["station_id", "observed_at", "station", "state", "district", "tehsil", "block", "village", "river", "basin", "latitude", "longitude"] + RIVER_FEATURES
    keep = [c for c in keep if c in result.columns]
    return result.sort_values(["station_id", "observed_at"], kind="stable")[keep].drop_duplicates(["station_id", "observed_at"], keep="last")


def _nearest_rainfall_station(river: pd.DataFrame, rainfall: pd.DataFrame, max_km: float) -> pd.DataFrame:
    cols = ["station_id", "latitude", "longitude"]
    if not set(cols).issubset(river.columns) or not set(cols).issubset(rainfall.columns):
        return pd.DataFrame(columns=["river_station_id", "rain_station_id", "distance_km"])
    r = river[cols].dropna().drop_duplicates("station_id")
    p = rainfall[cols].dropna().drop_duplicates("station_id")
    if r.empty or p.empty:
        return pd.DataFrame(columns=["river_station_id", "rain_station_id", "distance_km"])
    rlat, rlon = np.radians(r.latitude.to_numpy()), np.radians(r.longitude.to_numpy())
    plat, plon = np.radians(p.latitude.to_numpy()), np.radians(p.longitude.to_numpy())
    dlat, dlon = rlat[:, None] - plat[None, :], rlon[:, None] - plon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(rlat[:, None]) * np.cos(plat[None, :]) * np.sin(dlon / 2) ** 2
    distances = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    nearest = distances.argmin(axis=1)
    nearest_distance = distances[np.arange(len(r)), nearest]
    return pd.DataFrame({"river_station_id": r.station_id.to_numpy(), "rain_station_id": p.iloc[nearest].station_id.to_numpy(), "distance_km": nearest_distance}).loc[lambda x: x.distance_km <= max_km].reset_index(drop=True)


def _aggregate_rainfall(df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(df, {"station_id", "observed_at", "rainfall_mm"}, "rainfall data")
    result = df.copy()
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result["rainfall_mm"] = pd.to_numeric(result["rainfall_mm"], errors="coerce")
    result = result.dropna(subset=["station_id", "observed_at"]).sort_values(["station_id", "observed_at"], kind="stable")
    result = result.drop_duplicates(["station_id", "observed_at"], keep="last")
    pieces = []
    for station_id, group in result.groupby("station_id", sort=False):
        group = group.set_index("observed_at").sort_index()
        features = pd.DataFrame(index=group.index)
        features["rainfall_mm"] = group["rainfall_mm"]
        for window, name in [("24h", "rainfall_24h"), ("48h", "rainfall_48h"), ("72h", "rainfall_72h"), ("7D", "rainfall_7d"), ("30D", "rainfall_30d")]:
            features[name] = group.rainfall_mm.rolling(window, min_periods=1).sum()
        for coordinate in ("latitude", "longitude"):
            if coordinate in group:
                features[coordinate] = group[coordinate].iloc[0]
        features["station_id"] = station_id
        pieces.append(features.reset_index())
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=["station_id", "observed_at", "rainfall_mm"] + RAIN_FEATURES + ["latitude", "longitude"])


def _station_event_subset(station_row: pd.Series, events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events
    location = events["location"].map(_norm)
    candidates = [_norm(station_row.get(c)) for c in ("station", "district", "tehsil", "block", "village", "river", "state", "basin")]
    candidates = [c for c in candidates if c]
    mask = pd.Series(False, index=events.index)
    for candidate in candidates:
        mask |= location.eq(candidate) | location.str.contains(re.escape(candidate), regex=True, na=False) | location.map(lambda x: bool(x) and candidate in x)
    return events.loc[mask]


def _event_arrays(station_row: pd.Series, events: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    matched = _station_event_subset(station_row, events)
    if matched.empty:
        return np.array([], dtype="datetime64[ns]"), np.array([], dtype=float), np.array([], dtype=int)
    dates = pd.to_datetime(matched.event_date, errors="coerce").dropna().sort_values().to_numpy(dtype="datetime64[ns]")
    severity = pd.to_numeric(matched.set_index(matched.index).reindex(matched.index).get("severity_index"), errors="coerce").to_numpy(dtype=float)
    glof = matched.get("glof_risk", pd.Series("", index=matched.index)).fillna("").astype(str).str.lower().str.contains("high|critical|probable|suspected", regex=True).to_numpy(dtype=int)
    order = np.argsort(pd.to_datetime(matched.event_date, errors="coerce").fillna(pd.Timestamp("1900-01-01")).to_numpy())
    return dates, severity[order][-len(dates):], glof[order][-len(dates):]


def _add_historical_features(rows: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Add backward-looking event features without per-row Python loops."""
    _require_columns(events, {"event_date", "location"}, "flood events")
    e = events.copy()
    e["event_date"] = pd.to_datetime(e["event_date"], errors="coerce")
    e = e.dropna(subset=["event_date", "location"])
    out = rows.copy()
    for c in HISTORICAL_FEATURES:
        out[c] = np.nan
    for station_id, idx in out.groupby("station_id", sort=False).groups.items():
        station = out.loc[idx].iloc[0]
        dates, severity, glof = _event_arrays(station, e)
        if not len(dates):
            out.loc[idx, "flood_count_1y"] = 0
            out.loc[idx, "flood_count_3y"] = 0
            out.loc[idx, "flood_count_5y"] = 0
            out.loc[idx, "historical_glof_count"] = 0
            continue
        ts = out.loc[idx, "observed_at"].to_numpy(dtype="datetime64[ns]")
        pos = np.searchsorted(dates, ts, side="left")
        def count_before(days: int) -> np.ndarray:
            return pos - np.searchsorted(dates, ts - np.timedelta64(days, "D"), side="left")
        out.loc[idx, "flood_count_1y"] = count_before(365)
        out.loc[idx, "flood_count_3y"] = count_before(1095)
        out.loc[idx, "flood_count_5y"] = count_before(1825)
        prior_idx = pos - 1
        out.loc[idx, "days_since_last_flood"] = np.where(prior_idx >= 0, (ts - dates[np.maximum(prior_idx, 0)]).astype("timedelta64[D]").astype(float), np.nan)
        valid = np.isfinite(severity)
        severity_prefix = np.where(valid, severity, 0.0).cumsum()
        severity_count = valid.cumsum()
        end_idx = np.maximum(pos - 1, 0)
        sums = severity_prefix[end_idx] - np.where(pos > 0, np.where(pos > 0, severity_prefix[np.maximum(pos - 1, 0)], 0), 0)
        # With only 35 events, a vectorized prefix isn't worth complicating the windowed severity calculation;
        # use searchsorted boundaries per station rather than per observation.
        max_values, mean_values = np.full(len(ts), np.nan), np.full(len(ts), np.nan)
        for j, p in enumerate(pos):
            vals = severity[:p][np.isfinite(severity[:p])]
            if len(vals):
                max_values[j] = vals.max()
                mean_values[j] = vals.mean()
        out.loc[idx, "historical_max_severity"] = max_values
        out.loc[idx, "historical_mean_severity"] = mean_values
        glof_prefix = np.concatenate(([0], np.cumsum(glof)))
        out.loc[idx, "historical_glof_count"] = glof_prefix[pos]
    return out


def _label_events(rows: pd.DataFrame, events: pd.DataFrame, horizon_hours: int) -> pd.Series:
    """Label observations when a matching flood starts in the next horizon."""
    _require_columns(events, {"event_date", "location"}, "flood events")
    e = events.copy()
    e["event_date"] = pd.to_datetime(e["event_date"], errors="coerce")
    e = e.dropna(subset=["event_date", "location"])
    labels = np.zeros(len(rows), dtype=np.int8)
    horizon = np.timedelta64(horizon_hours, "h")
    for _, idx in rows.groupby("station_id", sort=False).groups.items():
        dates, _, _ = _event_arrays(rows.loc[idx].iloc[0], e)
        if not len(dates):
            continue
        ts = rows.loc[idx, "observed_at"].to_numpy(dtype="datetime64[ns]")
        left = np.searchsorted(dates, ts, side="left")
        right = np.searchsorted(dates, ts + horizon, side="right")
        labels[np.asarray(idx)] = (right > left).astype(np.int8)
    return pd.Series(labels, index=rows.index, name=TARGET_COLUMN)


def _add_glacier_state(rows: pd.DataFrame, glaciers: pd.DataFrame) -> pd.DataFrame:
    required = {"glacier_lake", "year", "area_km2"}
    if not required.issubset(glaciers.columns):
        return rows
    g = glaciers.copy()
    g["year"] = pd.to_numeric(g.year, errors="coerce")
    g = g.dropna(subset=["year"]).sort_values(["glacier_lake", "year"], kind="stable")
    feature_map = {"area_km2": "glacier_area_km2", "area_change_1y_km2": "glacier_area_change_1y_km2", "area_change_1y_pct": "glacier_area_change_1y_pct", "cumulative_area_change_km2": "glacier_cumulative_area_change_km2", "cumulative_area_change_pct": "glacier_cumulative_area_change_pct", "elevation_m": "glacier_elevation_m", "melting_rate_min_km_per_year": "glacier_melting_rate_min_km_per_year", "melting_rate_max_km_per_year": "glacier_melting_rate_max_km_per_year"}
    available = [c for c in feature_map if c in g.columns]
    if not available:
        return rows
    g = g[["glacier_lake", "year"] + available].rename(columns=feature_map)
    g["glacier_key"] = g.glacier_lake.map(_norm)
    geo_cols = [c for c in ("station", "district", "state", "river", "basin") if c in rows.columns]
    geography = rows[["station_id"] + geo_cols].drop_duplicates("station_id").copy()
    geography["geo_text"] = geography[geo_cols].fillna("").astype(str).agg(" ".join, axis=1).map(_norm)
    pairs = []
    for _, geo in geography.iterrows():
        matched = g.loc[g.glacier_key.map(lambda x: bool(x) and (x in geo.geo_text or geo.geo_text in x))].copy()
        if not matched.empty:
            matched["station_id"] = geo.station_id
            pairs.append(matched)
    if not pairs:
        return rows
    matched = pd.concat(pairs, ignore_index=True)
    result = rows.copy()
    result["year"] = result.observed_at.dt.year
    result = result.merge(matched.drop(columns=["glacier_lake", "glacier_key"]), on=["station_id", "year"], how="left")
    return result.drop(columns="year")


def build_training_table(river: pd.DataFrame, rainfall: pd.DataFrame, events: pd.DataFrame, glaciers: pd.DataFrame | None = None, rainfall_max_distance_km: float = 50.0, horizon_hours: int = 72) -> pd.DataFrame:
    """Build the V1 schema using river observations as the temporal backbone."""
    LOGGER.info("Preparing river observations")
    base = _prepare_river(river)
    LOGGER.info("Aggregating rainfall observations")
    rain = _aggregate_rainfall(rainfall)
    LOGGER.info("Mapping rainfall stations to river stations")
    mapping = _nearest_rainfall_station(base, rain, rainfall_max_distance_km)
    if not mapping.empty:
        rain = rain.merge(mapping, left_on="station_id", right_on="rain_station_id", how="inner")
        LOGGER.info("Joining rainfall to river observations: %d station mappings", len(mapping))
        base = pd.merge_asof(base.sort_values(["station_id", "observed_at"]), rain.sort_values(["river_station_id", "observed_at"]), left_on="observed_at", right_on="observed_at", left_by="station_id", right_by="river_station_id", direction="backward", tolerance=pd.Timedelta("3h"), suffixes=("", "_rain"))
        base = base.drop(columns=[c for c in ("river_station_id", "rain_station_id", "distance_km", "latitude_rain", "longitude_rain") if c in base.columns], errors="ignore")
    else:
        LOGGER.warning("No rainfall stations within %.1f km; rainfall features will be null", rainfall_max_distance_km)
        for c in RAIN_FEATURES:
            base[c] = np.nan
    LOGGER.info("Adding historical flood features")
    base = _add_historical_features(base, events)
    for c in GLACIER_FEATURES:
        if c not in base.columns:
            base[c] = np.nan
    if glaciers is not None and not glaciers.empty:
        LOGGER.info("Adding glacier state features")
        base = _add_glacier_state(base, glaciers)
    LOGGER.info("Generating %d-hour future flood labels", horizon_hours)
    base[TARGET_COLUMN] = _label_events(base, events, horizon_hours)
    base["month"] = base.observed_at.dt.month.astype("Int8")
    base["day_of_year"] = base.observed_at.dt.dayofyear.astype("Int16")
    base["is_monsoon"] = base.month.isin([6, 7, 8, 9]).astype("Int8")
    ordered = ["station_id", "observed_at", "station", "state", "district", "river", "basin"] + RAIN_FEATURES + RIVER_FEATURES + HISTORICAL_FEATURES + GLACIER_FEATURES + ["month", "day_of_year", "is_monsoon", TARGET_COLUMN]
    return base[[c for c in ordered if c in base.columns]].sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)


def write_training_table(df: pd.DataFrame, output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    _require_columns(df, {"station_id", "observed_at", TARGET_COLUMN}, "training table")
    result = df.copy()
    protected = {"station_id", "observed_at", "station", "state", "district", "river", "basin"}
    for column in result.columns:
        if column not in protected:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    result[TARGET_COLUMN] = result[TARGET_COLUMN].fillna(0).astype("int8")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, engine="pyarrow", compression="zstd", index=False)
    return output


def _read_processed(data_root: Path, relative: str, name: str) -> pd.DataFrame:
    path = data_root / "processed" / relative
    if not path.exists():
        raise FileNotFoundError(f"Missing processed {name}: {path}. Run the corresponding data-processing pipeline first.")
    LOGGER.info("Reading %s: %s", name, path)
    return pd.read_parquet(path)


def load_processed_inputs(data_root: str | Path = DEFAULT_DATA_ROOT) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
    root = Path(data_root)
    river = _read_processed(root, "river_data/parquet/river_observations.parquet", "river data")
    rainfall = _read_processed(root, "rainfall/parquet/rainfall_observations.parquet", "rainfall data")
    events = _read_processed(root, "past_events/parquet/past_flood_events.parquet", "past flood events")
    glacier_path = root / "processed" / "glaciers_data" / "parquet" / "glacier_changes.parquet"
    glaciers = pd.read_parquet(glacier_path) if glacier_path.exists() else None
    if glaciers is None:
        LOGGER.warning("No combined glacier Parquet found at %s; glacier features will remain null", glacier_path)
    else:
        LOGGER.info("Reading glacier data: %s", glacier_path)
    return river, rainfall, events, glaciers


def build_training_dataset(data_root: str | Path = DEFAULT_DATA_ROOT, output_path: str | Path | None = None, rainfall_max_distance_km: float = 50.0, horizon_hours: int = 72) -> Path:
    root = Path(data_root)
    output = Path(output_path) if output_path is not None else root / "processed" / "training_v1.parquet"
    river, rainfall, events, glaciers = load_processed_inputs(root)
    LOGGER.info("Input sizes: river=%d rainfall=%d events=%d glaciers=%s", len(river), len(rainfall), len(events), len(glaciers) if glaciers is not None else "none")
    table = build_training_table(river, rainfall, events, glaciers=glaciers, rainfall_max_distance_km=rainfall_max_distance_km, horizon_hours=horizon_hours)
    if table.empty:
        raise ValueError("V1 training table is empty")
    positives = int(table[TARGET_COLUMN].sum())
    LOGGER.info("V1 training table: rows=%d columns=%d positives=%d negatives=%d", len(table), len(table.columns), positives, len(table) - positives)
    LOGGER.info("V1 date range: %s -> %s", table.observed_at.min(), table.observed_at.max())
    LOGGER.info("V1 missingness (top 10): %s", table.isna().mean().sort_values(ascending=False).head(10).to_dict())
    return write_training_table(table, output)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the V1 flood-risk training Parquet from processed data")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--rainfall-max-distance-km", type=float, default=50.0)
    parser.add_argument("--horizon-hours", type=int, default=72)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    output = build_training_dataset(args.data_root, args.output, args.rainfall_max_distance_km, args.horizon_hours)
    LOGGER.info("V1 training dataset written to %s", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
