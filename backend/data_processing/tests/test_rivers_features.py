import pandas as pd

from data_processing.rivers.features import add_river_features
from data_processing.rivers.transform import transform_river_data


def test_transform_sorts_within_station():
    df = pd.DataFrame(
        {
            "station_id": ["b", "a", "a"],
            "observed_at": pd.to_datetime([
                "2026-01-01 02:00", "2026-01-01 02:00", "2026-01-01 01:00"
            ]),
            "water_level_m": [3.0, 2.0, 1.0],
        }
    )
    result = transform_river_data(df)
    a = result[result.station_id == "a"]
    assert list(a.observed_at) == list(pd.to_datetime(["2026-01-01 01:00", "2026-01-01 02:00"]))


def test_lags_and_rollings_do_not_cross_stations_or_use_future_rows():
    df = pd.DataFrame(
        {
            "station_id": ["a", "a", "a", "b", "b"],
            "observed_at": pd.to_datetime([
                "2026-01-01 00:00", "2026-01-01 01:00", "2026-01-01 02:00",
                "2026-01-01 00:00", "2026-01-01 01:00",
            ]),
            "water_level_m": [1.0, 2.0, 4.0, 100.0, 200.0],
        }
    )
    result = add_river_features(df)
    a = result[result.station_id == "a"].reset_index(drop=True)
    assert pd.isna(a.loc[0, "water_level_lag_1h"])
    assert a.loc[1, "water_level_lag_1h"] == 1.0
    assert a.loc[2, "water_level_lag_1h"] == 2.0
    assert a.loc[2, "water_level_rolling_mean_6h"] < 4.0

    b = result[result.station_id == "b"].reset_index(drop=True)
    assert pd.isna(b.loc[0, "water_level_lag_1h"])
    assert b.loc[1, "water_level_lag_1h"] == 100.0


def test_features_keep_missing_measurements_missing():
    df = pd.DataFrame(
        {
            "station_id": ["a", "a"],
            "observed_at": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 01:00"]),
            "water_level_m": [None, 2.0],
        }
    )
    result = add_river_features(df)
    assert pd.isna(result.loc[0, "water_level_m"])
    assert pd.isna(result.loc[1, "water_level_lag_1h"])
