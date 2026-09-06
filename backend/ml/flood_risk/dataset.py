"""Build the V1 supervised training table from processed flood, rainfall, river and glacier data."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_COLUMN = "flood_next_72h"
DEFAULT_OUTPUT = Path("backend/apps/risk/data/processed/training_v1.parquet")

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
GLACIER_FEATURES = [
    "glacier_area_km2", "glacier_area_change_1y_km2", "glacier_area_change_1y_pct",
    "glacier_cumulative_area_change_km2", "glacier_cumulative_area_change_pct",
    "glacier_elevation_m", "glacier_melting_rate_min_km_per_year", "glacier_melting_rate_max_km_per_year",
]
HISTORICAL_FEATURES = [
    "flood_count_1y", "flood_count_3y", "flood_count_5y", "days_since_last_flood",
    "historical_max_severity", "historical_mean_severity", "historical_glof_count",
]


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
    result = result.sort_values(["station_id", "observed_at"], kind="stable")
    return result[keep].drop_duplicates(["station_id", "observed_at"], keep="last")


def _nearest_rainfall_station(river: pd.DataFrame, rainfall: pd.DataFrame, max_km: float) -> pd.DataFrame:
    """Map each river station to the nearest rainfall station with coordinates."""
    cols = ["station_id", "latitude", "longitude"]
    if not set(cols).issubset(river.columns) or not set(cols).issubset(rainfall.columns):
        return pd.DataFrame(columns=["river_station_id", "rain_station_id", "distance_km"])
    r = river[cols].dropna().drop_duplicates("station_id")
    p = rainfall[cols].dropna().drop_duplicates("station_id")
    if r.empty or p.empty:
        return pd.DataFrame(columns=["river_station_id", "rain_station_id", "distance_km"])
    rlat, rlon = np.radians(r["latitude"].to_numpy()), np.radians(r["longitude"].to_numpy())
    plat, plon = np.radians(p["latitude"].to_numpy()), np.radians(p["longitude"].to_numpy())
    dlat = rlat[:, None] - plat[None, :]
    dlon = rlon[:, None] - plon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(rlat[:, None]) * np.cos(plat[None, :]) * np.sin(dlon / 2) ** 2
    distances = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    nearest = distances.argmin(axis=1)
    nearest_distance = distances[np.arange(len(r)), nearest]
    mapping = pd.DataFrame({
        "river_station_id": r["station_id"].to_numpy(),
        "rain_station_id": p.iloc[nearest]["station_id"].to_numpy(),
        "distance_km": nearest_distance,
    })
    return mapping.loc[mapping["distance_km"] <= max_km].reset_index(drop=True)


def _aggregate_rainfall(df: pd.DataFrame) -> pd.DataFrame:
    _require_columns(df, {"station_id", "observed_at", "rainfall_mm"}, "rainfall data")
    result = df.copy()
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result["rainfall_mm"] = pd.to_numeric(result["rainfall_mm"], errors="coerce")
    result = result.dropna(subset=["station_id", "observed_at"])
    result = result.sort_values(["station_id", "observed_at"], kind="stable")
    result = result.drop_duplicates(["station_id", "observed_at"], keep="last")

    pieces: list[pd.DataFrame] = []
    for station_id, group in result.groupby("station_id", sort=False):
        group = group.sort_values("observed_at").set_index("observed_at")
        features = group[["rainfall_mm"]].copy()
        for window, name in [("24h", "rainfall_24h"), ("48h", "rainfall_48h"), ("72h", "rainfall_72h"), ("7D", "rainfall_7d"), ("30D", "rainfall_30d")]:
            features[name] = group["rainfall_mm"].rolling(window, min_periods=1).sum()
        features["station_id"] = station_id
        features = features.reset_index()
        pieces.append(features)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=["station_id", "observed_at", "rainfall_mm"] + RAIN_FEATURES)


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


def _add_historical_features(rows: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Create backward-looking flood-frequency features; future events are excluded."""
    _require_columns(events, {"event_date", "location"}, "flood events")
    e = events.copy()
    e["event_date"] = pd.to_datetime(e["event_date"], errors="coerce")
    e = e.dropna(subset=["event_date", "location"]).sort_values("event_date")
    severity = pd.to_numeric(e.get("severity_index", pd.Series(index=e.index, dtype=float)), errors="coerce")
    e["severity_numeric"] = severity
    e["glof_numeric"] = e.get("glof_risk", pd.Series(index=e.index, dtype="string")).fillna("").str.lower().str.contains("high|critical|probable|suspected", regex=True).astype(int)

    output = rows.copy()
    for c in HISTORICAL_FEATURES:
        output[c] = 0.0
    for station_id, indices in output.groupby("station_id", sort=False).groups.items():
        station_rows = output.loc[indices]
        if station_rows.empty:
            continue
        station_meta = station_rows.iloc[0]
        matched = _station_event_subset(station_meta, e)
        dates = matched["event_date"].sort_values().to_numpy(dtype="datetime64[ns]")
        severity_values = matched["severity_numeric"].to_numpy(dtype=float)
        glof_values = matched["glof_numeric"].to_numpy(dtype=int)
        for idx in indices:
            ts = output.at[idx, "observed_at"]
            if pd.isna(ts):
                continue
            end = np.datetime64(ts.to_datetime64())
            prior = dates < end
            prior_dates = dates[prior]
            output.at[idx, "flood_count_1y"] = int((prior_dates >= end - np.timedelta64(365, "D")).sum())
            output.at[idx, "flood_count_3y"] = int((prior_dates >= end - np.timedelta64(1095, "D")).sum())
            output.at[idx, "flood_count_5y"] = int((prior_dates >= end - np.timedelta64(1825, "D")).sum())
            output.at[idx, "days_since_last_flood"] = float((end - prior_dates[-1]).astype("timedelta64[D]").astype(int)) if len(prior_dates) else np.nan
            prior_severity = severity_values[prior]
            output.at[idx, "historical_max_severity"] = np.nanmax(prior_severity) if np.isfinite(prior_severity).any() else np.nan
            output.at[idx, "historical_mean_severity"] = np.nanmean(prior_severity) if np.isfinite(prior_severity).any() else np.nan
            output.at[idx, "historical_glof_count"] = int(glof_values[prior].sum())
    return output


def _label_events(rows: pd.DataFrame, events: pd.DataFrame, horizon_hours: int) -> pd.Series:
    """Label each observation when a matching flood starts in the next horizon."""
    _require_columns(events, {"event_date", "location"}, "flood events")
    e = events.copy()
    e["event_date"] = pd.to_datetime(e["event_date"], errors="coerce")
    e = e.dropna(subset=["event_date", "location"])
    horizon = pd.Timedelta(hours=horizon_hours)
    labels = np.zeros(len(rows), dtype=np.int8)
    for station_id, indices in rows.groupby("station_id", sort=False).groups.items():
        station_rows = rows.loc[indices]
        matched = _station_event_subset(station_rows.iloc[0], e)
        dates = matched["event_date"].to_numpy(dtype="datetime64[ns]")
        for idx in indices:
            ts = rows.at[idx, "observed_at"]
            if pd.isna(ts) or not len(dates):
                continue
            start, end = ts.to_datetime64(), (ts + horizon).to_datetime64()
            labels[idx] = int(((dates >= start) & (dates <= end)).any())
    return pd.Series(labels, index=rows.index, name=TARGET_COLUMN)


def _add_glacier_state(rows: pd.DataFrame, glaciers: pd.DataFrame) -> pd.DataFrame:
    """Attach glacier features only when a glacier name conservatively matches station geography."""
    required = {"glacier_lake", "year", "area_km2"}
    if not required.issubset(glaciers.columns):
        return rows
    g = glaciers.copy()
    g["year"] = pd.to_numeric(g["year"], errors="coerce")
    g = g.dropna(subset=["year"]).sort_values(["glacier_lake", "year"], kind="stable")
    feature_map = {
        "area_km2": "glacier_area_km2", "area_change_1y_km2": "glacier_area_change_1y_km2",
        "area_change_1y_pct": "glacier_area_change_1y_pct", "cumulative_area_change_km2": "glacier_cumulative_area_change_km2",
        "cumulative_area_change_pct": "glacier_cumulative_area_change_pct", "elevation_m": "glacier_elevation_m",
        "melting_rate_min_km_per_year": "glacier_melting_rate_min_km_per_year", "melting_rate_max_km_per_year": "glacier_melting_rate_max_km_per_year",
    }
    available = [c for c in feature_map if c in g.columns]
    if not available:
        return rows
    g = g[["glacier_lake", "year"] + available].rename(columns=feature_map)
    g["glacier_key"] = g["glacier_lake"].map(_norm)
    geography = rows[["station_id", "station", "district", "state", "river", "basin"]].drop_duplicates("station_id").copy()
    geography["geo_text"] = geography.fillna("").astype(str).drop(columns="station_id").agg(" ".join, axis=1).map(_norm)
    pairs = []
    for _, geo in geography.iterrows():
        matched = g.loc[g["glacier_key"].map(lambda x: bool(x) and (x in geo["geo_text"] or geo["geo_text"] in x))].copy()
        if not matched.empty:
            matched["station_id"] = geo["station_id"]
            pairs.append(matched)
    if not pairs:
        return rows
    matched = pd.concat(pairs, ignore_index=True)
    result = rows.copy()
    result["year"] = result["observed_at"].dt.year
    result = result.merge(matched.drop(columns=["glacier_lake", "glacier_key"]), on=["station_id", "year"], how="left")
    return result.drop(columns=["year"], errors="ignore")


def build_training_table(river: pd.DataFrame, rainfall: pd.DataFrame, events: pd.DataFrame, glaciers: pd.DataFrame | None = None, rainfall_max_distance_km: float = 50.0, horizon_hours: int = 72) -> pd.DataFrame:
    """Build the V1 schema using river observations as the temporal backbone."""
    base = _prepare_river(river)
    rain = _aggregate_rainfall(rainfall)
    mapping = _nearest_rainfall_station(base, rain, rainfall_max_distance_km)
    if not mapping.empty:
        rain = rain.merge(mapping.rename(columns={"river_station_id": "river_station_id", "rain_station_id": "station_id"}), on="station_id", how="inner")
        rain = rain.rename(columns={"river_station_id": "river_station_id", "station_id": "rain_station_id"})
        base = pd.merge_asof(
            base.sort_values("observed_at"), rain.sort_values("observed_at"),
            left_on="observed_at", right_on="observed_at", left_by="station_id", right_by="river_station_id",
            direction="backward", tolerance=pd.Timedelta("3h"), suffixes=("", "_rain"),
        )
        base = base.drop(columns=[c for c in ("river_station_id", "latitude_rain", "longitude_rain") if c in base.columns], errors="ignore")
    else:
        for c in RAIN_FEATURES:
            base[c] = np.nan

    base = _add_historical_features(base, events)
    for c in GLACIER_FEATURES:
        if c not in base.columns:
            base[c] = np.nan
    if glaciers is not None and not glaciers.empty:
        base = _add_glacier_state(base, glaciers)
    base[TARGET_COLUMN] = _label_events(base, events, horizon_hours)
    base["month"] = base["observed_at"].dt.month.astype("Int8")
    base["day_of_year"] = base["observed_at"].dt.dayofyear.astype("Int16")
    base["is_monsoon"] = base["month"].isin([6, 7, 8, 9]).astype("Int8")
    ordered = ["station_id", "observed_at", "station", "state", "district", "river", "basin"] + RAIN_FEATURES + RIVER_FEATURES + HISTORICAL_FEATURES + GLACIER_FEATURES + ["month", "day_of_year", "is_monsoon", TARGET_COLUMN]
    return base[[c for c in ordered if c in base.columns]].sort_values(["station_id", "observed_at"], kind="stable").reset_index(drop=True)


def write_training_table(df: pd.DataFrame, output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    """Validate and write the V1 training table as compressed Parquet."""
    _require_columns(df, {"station_id", "observed_at", TARGET_COLUMN}, "training table")
    result = df.copy()
    for column in result.columns:
        if column not in {"station_id", "observed_at", "station", "state", "district", "river", "basin"}:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    result[TARGET_COLUMN] = result[TARGET_COLUMN].fillna(0).astype("int8")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, engine="pyarrow", compression="zstd", index=False)
    return output
