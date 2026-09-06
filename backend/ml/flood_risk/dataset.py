"""Build the V1 supervised flood-risk training table.

V1 uses river observations as the temporal backbone and joins rainfall,
historical flood events, and glacier state. Future event information is never
used in backward-looking features.
"""
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
    "water_level_m", "water_level_delta_1h", "water_level_pct_change_1h",
    "water_level_lag_1h", "water_level_lag_3h", "water_level_lag_6h", "water_level_lag_12h", "water_level_lag_24h",
    "water_level_rolling_mean_6h", "water_level_rolling_max_6h", "water_level_rolling_std_6h",
    "water_level_rolling_mean_24h", "water_level_rolling_max_24h", "water_level_rolling_std_24h",
    "discharge_cumecs", "discharge_delta_1h", "discharge_pct_change_1h",
    "discharge_lag_1h", "discharge_lag_3h", "discharge_lag_6h", "discharge_lag_12h", "discharge_lag_24h",
    "discharge_rolling_mean_6h", "discharge_rolling_max_6h", "discharge_rolling_std_6h",
    "discharge_rolling_mean_24h", "discharge_rolling_max_24h", "discharge_rolling_std_24h",
]
HISTORICAL_FEATURES = ["flood_count_1y", "flood_count_3y", "flood_count_5y", "days_since_last_flood", "historical_max_severity", "historical_mean_severity", "historical_glof_count"]
GLACIER_FEATURES = [
    "glacier_area_km2", "glacier_area_change_1y_km2", "glacier_area_change_1y_pct",
    "glacier_cumulative_area_change_km2", "glacier_cumulative_area_change_pct",
    "glacier_elevation_m", "glacier_melting_rate_min_km_per_year", "glacier_melting_rate_max_km_per_year",
]


def _norm(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def _require(df: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = columns - set(df.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {sorted(missing)}")


def _prepare_river(df: pd.DataFrame) -> pd.DataFrame:
    _require(df, {"station_id", "observed_at"}, "river data")
    keep = ["station_id", "observed_at", "station", "state", "district", "tehsil", "block", "village", "river", "basin", "latitude", "longitude", "water_level_m", "discharge_cumecs"]
    result = df[[c for c in keep if c in df.columns]].copy()
    result["station_id"] = result["station_id"].astype("string")
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result = result.dropna(subset=["station_id", "observed_at"])
    if result.duplicated(["station_id", "observed_at"]).any():
        result = result.drop_duplicates(["station_id", "observed_at"], keep="last")
    return result.reset_index(drop=True)


def _add_river_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)
    for source, prefix in (("water_level_m", "water_level"), ("discharge_cumecs", "discharge")):
        if source not in out.columns:
            continue
        values = pd.to_numeric(out[source], errors="coerce").astype("float64")
        grouped = values.groupby(out["station_id"], sort=False)
        prev = grouped.shift(1)
        out[source] = values
        out[f"{prefix}_delta_1h"] = values - prev
        pct = (values - prev).div(prev).mul(100.0)
        out[f"{prefix}_pct_change_1h"] = pct.where(prev.notna() & prev.ne(0))
        for n in (1, 3, 6, 12, 24):
            out[f"{prefix}_lag_{n}h"] = grouped.shift(n)
        for n in (6, 24):
            rolling = grouped.rolling(n, min_periods=1)
            out[f"{prefix}_rolling_mean_{n}h"] = rolling.mean().reset_index(level=0, drop=True)
            out[f"{prefix}_rolling_max_{n}h"] = rolling.max().reset_index(level=0, drop=True)
            out[f"{prefix}_rolling_std_{n}h"] = rolling.std().reset_index(level=0, drop=True)
    return out


def _aggregate_rainfall(df: pd.DataFrame) -> pd.DataFrame:
    _require(df, {"station_id", "observed_at", "rainfall_mm"}, "rainfall data")
    keep = [c for c in ["station_id", "observed_at", "rainfall_mm", "latitude", "longitude"] if c in df.columns]
    result = df[keep].copy()
    result["station_id"] = result["station_id"].astype("string")
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result["rainfall_mm"] = pd.to_numeric(result["rainfall_mm"], errors="coerce")
    result = result.dropna(subset=["station_id", "observed_at"]).drop_duplicates(["station_id", "observed_at"], keep="last")
    result = result.sort_values(["station_id", "observed_at"], kind="stable")
    pieces = []
    for station_id, group in result.groupby("station_id", sort=False):
        group = group.set_index("observed_at").sort_index()
        features = pd.DataFrame(index=group.index)
        for window, name in [("24h", "rainfall_24h"), ("48h", "rainfall_48h"), ("72h", "rainfall_72h"), ("7D", "rainfall_7d"), ("30D", "rainfall_30d")]:
            features[name] = group["rainfall_mm"].rolling(window, min_periods=1).sum()
        features["station_id"] = station_id
        for coordinate in ("latitude", "longitude"):
            if coordinate in group:
                features[coordinate] = group[coordinate].iloc[0]
        pieces.append(features.reset_index())
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=["station_id", "observed_at"] + RAIN_FEATURES + ["latitude", "longitude"])


def _nearest_rainfall_station(river: pd.DataFrame, rainfall: pd.DataFrame, max_km: float) -> pd.DataFrame:
    cols = ["station_id", "latitude", "longitude"]
    if not set(cols).issubset(river.columns) or not set(cols).issubset(rainfall.columns):
        return pd.DataFrame(columns=["river_station_id", "rain_station_id", "distance_km"])
    r = river[cols].dropna().drop_duplicates("station_id")
    p = rainfall[cols].dropna().drop_duplicates("station_id")
    if r.empty or p.empty:
        return pd.DataFrame(columns=["river_station_id", "rain_station_id", "distance_km"])
    rlat, rlon = np.radians(r["latitude"].to_numpy()), np.radians(r["longitude"].to_numpy())
    plat, plon = np.radians(p["latitude"].to_numpy()), np.radians(p["longitude"].to_numpy())
    dlat, dlon = rlat[:, None] - plat[None, :], rlon[:, None] - plon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(rlat[:, None]) * np.cos(plat[None, :]) * np.sin(dlon / 2) ** 2
    distances = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    nearest = distances.argmin(axis=1)
    distance = distances[np.arange(len(r)), nearest]
    return pd.DataFrame({"river_station_id": r["station_id"].astype("string").to_numpy(), "rain_station_id": p.iloc[nearest]["station_id"].astype("string").to_numpy(), "distance_km": distance}).loc[lambda x: x.distance_km <= max_km].reset_index(drop=True)


def _event_map(rows: pd.DataFrame, events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if events.empty:
        return {}
    loc = events["location"].map(_norm)
    cols = [c for c in ("station", "district", "tehsil", "block", "village", "river", "state", "basin") if c in rows.columns]
    stations = rows[["station_id"] + cols].drop_duplicates("station_id")
    mapping = {}
    for row in stations.itertuples(index=False):
        candidates = [_norm(getattr(row, c, "")) for c in cols]
        candidates = [x for x in candidates if x]
        mask = pd.Series(False, index=events.index)
        for candidate in candidates:
            mask |= loc.eq(candidate) | loc.str.contains(re.escape(candidate), regex=True, na=False)
        matched = events.loc[mask]
        if not matched.empty:
            mapping[str(row.station_id)] = matched
    return mapping


def _add_historical_features(rows: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    _require(events, {"event_date", "location"}, "flood events")
    e = events.copy()
    e["event_date"] = pd.to_datetime(e["event_date"], errors="coerce")
    e = e.dropna(subset=["event_date", "location"]).sort_values("event_date", kind="stable")
    out = rows.copy()
    for column in HISTORICAL_FEATURES:
        out[column] = 0.0
    mapping = _event_map(out, e)
    for station_id, idx in out.groupby("station_id", sort=False).groups.items():
        matched = mapping.get(str(station_id))
        if matched is None:
            continue
        dates = matched["event_date"].to_numpy(dtype="datetime64[ns]")
        severity = pd.to_numeric(matched.get("severity_index", pd.Series(np.nan, index=matched.index)), errors="coerce").to_numpy(dtype=float)
        glof = matched.get("glof_risk", pd.Series("", index=matched.index)).fillna("").astype(str).str.lower().str.contains("high|critical|probable|suspected", regex=True).to_numpy(dtype=np.int8)
        ts = out.loc[idx, "observed_at"].to_numpy(dtype="datetime64[ns]")
        pos = np.searchsorted(dates, ts, side="left")
        for days, name in ((365, "flood_count_1y"), (1095, "flood_count_3y"), (1825, "flood_count_5y")):
            left = np.searchsorted(dates, ts - np.timedelta64(days, "D"), side="left")
            out.loc[idx, name] = pos - left
        prior = pos - 1
        valid = prior >= 0
        since = np.full(len(ts), np.nan)
        since[valid] = (ts[valid] - dates[prior[valid]]).astype("timedelta64[D]").astype(float)
        out.loc[idx, "days_since_last_flood"] = since
        max_values = np.full(len(ts), np.nan)
        mean_values = np.full(len(ts), np.nan)
        glof_values = np.zeros(len(ts))
        for j, p in enumerate(pos):
            if p:
                vals = severity[:p][np.isfinite(severity[:p])]
                if len(vals):
                    max_values[j] = vals.max()
                    mean_values[j] = vals.mean()
                glof_values[j] = glof[:p].sum()
        out.loc[idx, "historical_max_severity"] = max_values
        out.loc[idx, "historical_mean_severity"] = mean_values
        out.loc[idx, "historical_glof_count"] = glof_values
    return out


def _label_events(rows: pd.DataFrame, events: pd.DataFrame, horizon_hours: int) -> pd.Series:
    _require(events, {"event_date", "location"}, "flood events")
    e = events.copy()
    e["event_date"] = pd.to_datetime(e["event_date"], errors="coerce")
    e = e.dropna(subset=["event_date", "location"]).sort_values("event_date", kind="stable")
    labels = pd.Series(np.zeros(len(rows), dtype=np.int8), index=rows.index, name=TARGET_COLUMN)
    mapping = _event_map(rows, e)
    horizon = np.timedelta64(horizon_hours, "h")
    for station_id, idx in rows.groupby("station_id", sort=False).groups.items():
        matched = mapping.get(str(station_id))
        if matched is None:
            continue
        dates = matched["event_date"].to_numpy(dtype="datetime64[ns]")
        ts = rows.loc[idx, "observed_at"].to_numpy(dtype="datetime64[ns]")
        left = np.searchsorted(dates, ts, side="left")
        right = np.searchsorted(dates, ts + horizon, side="right")
        labels.loc[idx] = (right > left).astype(np.int8)
    return labels


def _add_glacier_state(rows: pd.DataFrame, glaciers: pd.DataFrame) -> pd.DataFrame:
    required = {"glacier_lake", "year", "area_km2"}
    if not required.issubset(glaciers.columns):
        return rows
    g = glaciers.copy()
    g["year"] = pd.to_numeric(g["year"], errors="coerce")
    g = g.dropna(subset=["year"]).sort_values(["glacier_lake", "year"], kind="stable")
    mapping = {"area_km2": "glacier_area_km2", "area_change_1y_km2": "glacier_area_change_1y_km2", "area_change_1y_pct": "glacier_area_change_1y_pct", "cumulative_area_change_km2": "glacier_cumulative_area_change_km2", "cumulative_area_change_pct": "glacier_cumulative_area_change_pct", "elevation_m": "glacier_elevation_m", "melting_rate_min_km_per_year": "glacier_melting_rate_min_km_per_year", "melting_rate_max_km_per_year": "glacier_melting_rate_max_km_per_year"}
    available = [c for c in mapping if c in g.columns]
    if not available:
        return rows
    g = g[["glacier_lake", "year"] + available].rename(columns=mapping)
    g["glacier_key"] = g["glacier_lake"].map(_norm)
    geo_cols = [c for c in ("station", "district", "state", "river", "basin") if c in rows.columns]
    stations = rows[["station_id"] + geo_cols].drop_duplicates("station_id")
    stations["geo_text"] = stations[geo_cols].fillna("").astype(str).agg(" ".join, axis=1).map(_norm)
    pairs = []
    for row in stations.itertuples(index=False):
        matched = g.loc[g["glacier_key"].map(lambda x: bool(x) and (x in row.geo_text or row.geo_text in x))].copy()
        if not matched.empty:
            matched["station_id"] = row.station_id
            pairs.append(matched)
    if not pairs:
        return rows
    matched = pd.concat(pairs, ignore_index=True)
    out = rows.copy()
    out["_year"] = out["observed_at"].dt.year
    out = out.merge(matched.drop(columns=["glacier_lake", "glacier_key"]), left_on=["station_id", "_year"], right_on=["station_id", "year"], how="left")
    return out.drop(columns=["_year", "year"], errors="ignore")


def _add_rainfall_features(base: pd.DataFrame, rain: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Join mapped rainfall features without a large all-stations merge.

    The mapping has a river station ID and a rainfall station ID. Joining on
    the two original station IDs under the same merge key prevents rainfall
    from matching when those IDs differ. We instead use a common temporary key
    while joining one mapped station at a time to keep peak memory bounded.
    """
    out = base.copy()
    for column in RAIN_FEATURES:
        out[column] = np.nan

    rain_by_station = {str(k): g for k, g in rain.groupby("station_id", sort=False)}
    base_groups = out.groupby("station_id", sort=False).groups
    matched_rows = 0

    for row in mapping.itertuples(index=False):
        river_id = str(row.river_station_id)
        rain_id = str(row.rain_station_id)
        indices = base_groups.get(row.river_station_id)
        rain_group = rain_by_station.get(rain_id)
        if indices is None or rain_group is None:
            continue

        left = out.loc[indices, ["observed_at"]].copy()
        left["_join_station_id"] = river_id
        right = rain_group[["observed_at"] + RAIN_FEATURES].copy()
        right["_join_station_id"] = river_id
        left = left.sort_values("observed_at", kind="stable")
        right = right.sort_values("observed_at", kind="stable")
        joined = pd.merge_asof(
            left,
            right,
            on="observed_at",
            by="_join_station_id",
            direction="backward",
            tolerance=pd.Timedelta(hours=3),
        )
        left_positions = left.index.to_numpy()
        for column in RAIN_FEATURES:
            values = joined[column].to_numpy()
            out.loc[left_positions, column] = values
            matched_rows += int(pd.notna(values).sum())
        del left, right, joined

    LOGGER.info("Rainfall join populated %d feature values", matched_rows)
    return out


def build_training_table(river: pd.DataFrame, rainfall: pd.DataFrame, events: pd.DataFrame, glaciers: pd.DataFrame | None = None, rainfall_max_distance_km: float = 50.0, horizon_hours: int = 72) -> pd.DataFrame:
    LOGGER.info("Preparing river observations")
    base = _prepare_river(river)
    LOGGER.info("River observations prepared: %d rows, %d stations", len(base), base.station_id.nunique())
    LOGGER.info("Deriving river features")
    base = _add_river_features(base)
    LOGGER.info("Aggregating rainfall observations")
    rain = _aggregate_rainfall(rainfall)
    LOGGER.info("Mapping rainfall stations to river stations")
    mapping = _nearest_rainfall_station(base, rain, rainfall_max_distance_km)
    if mapping.empty:
        LOGGER.warning("No rainfall stations within %.1f km", rainfall_max_distance_km)
    else:
        LOGGER.info("Joining rainfall: %d station mappings", len(mapping))
        base = _add_rainfall_features(base, rain, mapping)
    del rain
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
    base["month"] = base.observed_at.dt.month.astype("int8")
    base["day_of_year"] = base.observed_at.dt.dayofyear.astype("int16")
    base["is_monsoon"] = base.month.isin([6, 7, 8, 9]).astype("int8")
    ordered = ["station_id", "observed_at", "station", "state", "district", "river", "basin"] + RAIN_FEATURES + RIVER_FEATURES + HISTORICAL_FEATURES + GLACIER_FEATURES + ["month", "day_of_year", "is_monsoon", TARGET_COLUMN]
    return base[[c for c in ordered if c in base.columns]].sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)


def write_training_table(df: pd.DataFrame, output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    _require(df, {"station_id", "observed_at", TARGET_COLUMN}, "training table")
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


def _read_processed(root: Path, relative: str, name: str, columns: list[str] | None = None) -> pd.DataFrame:
    path = root / "processed" / relative
    if not path.exists():
        raise FileNotFoundError(f"Missing processed {name}: {path}. Run its corresponding data-processing pipeline first.")
    LOGGER.info("Reading %s: %s", name, path)
    return pd.read_parquet(path, columns=columns) if columns else pd.read_parquet(path)


def load_processed_inputs(data_root: str | Path = DEFAULT_DATA_ROOT):
    root = Path(data_root)
    river = _read_processed(root, "river_data/parquet/river_observations.parquet", "river data", ["station_id", "station", "state", "district", "tehsil", "block", "village", "river", "basin", "latitude", "longitude", "observed_at", "water_level_m", "discharge_cumecs"])
    rainfall = _read_processed(root, "rainfall/parquet/rainfall_observations.parquet", "rainfall data", ["station_id", "station", "latitude", "longitude", "observed_at", "rainfall_mm"])
    events = _read_processed(root, "past_events/parquet/past_flood_events.parquet", "past flood events")
    glacier_path = root / "processed" / "glaciers_data" / "parquet" / "glacier_changes.parquet"
    glaciers = pd.read_parquet(glacier_path) if glacier_path.exists() else None
    if glaciers is None:
        LOGGER.warning("No combined glacier Parquet found: %s", glacier_path)
    else:
        LOGGER.info("Reading glacier data: %s", glacier_path)
    return river, rainfall, events, glaciers


def build_training_dataset(data_root: str | Path = DEFAULT_DATA_ROOT, output_path: str | Path | None = None, rainfall_max_distance_km: float = 50.0, horizon_hours: int = 72) -> Path:
    root = Path(data_root)
    output = Path(output_path) if output_path is not None else root / "processed" / "training_v1.parquet"
    river, rainfall, events, glaciers = load_processed_inputs(root)
    LOGGER.info("Input sizes: river=%d rainfall=%d events=%d glaciers=%s", len(river), len(rainfall), len(events), len(glaciers) if glaciers is not None else "none")
    table = build_training_table(river, rainfall, events, glaciers, rainfall_max_distance_km, horizon_hours)
    if table.empty:
        raise ValueError("V1 training table is empty")
    positives = int(table[TARGET_COLUMN].sum())
    LOGGER.info("V1 training table: rows=%d columns=%d positives=%d negatives=%d", len(table), len(table.columns), positives, len(table) - positives)
    LOGGER.info("V1 date range: %s -> %s", table.observed_at.min(), table.observed_at.max())
    LOGGER.info("V1 missingness (top 10): %s", table.isna().mean().sort_values(ascending=False).head(10).to_dict())
    return write_training_table(table, output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the V1 flood-risk training Parquet")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--rainfall-max-distance-km", type=float, default=50.0)
    parser.add_argument("--horizon-hours", type=int, default=72)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    output = build_training_dataset(args.data_root, args.output, args.rainfall_max_distance_km, args.horizon_hours)
    LOGGER.info("V1 training dataset written to %s", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())