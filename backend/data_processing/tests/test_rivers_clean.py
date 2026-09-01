import pandas as pd
import pytest

from data_processing.rivers.clean import clean_cwc_data, normalize_cwc_columns


def test_normalize_cwc_columns_and_clean_measurements():
    raw = pd.DataFrame(
        {
            "SlNo": [1, 2],
            "Station": ["Station A", "Station A"],
            "Agency": ["CWC", "CWC"],
            "State LGD Code": [18, 18],
            "State": ["Assam", "Assam"],
            "District LGD Code": [283, 283],
            "District": ["DARRANG", "DARRANG"],
            "Tehsil": ["-", "-"],
            "Block": ["-", "-"],
            "Village": ["-", "-"],
            "River": ["River X", "River X"],
            "Basin": ["Basin X", "Basin X"],
            "Tributary": ["-", "-"],
            "Subtributary": ["-", "-"],
            "SubSubtributary": ["-", "-"],
            "Local River": ["-", "-"],
            "Latitude": [26.5, 26.5],
            "Longitude": [92.1, 92.1],
            "Is_DischargeDataAvailable": ["No", "Yes"],
            "RL_of_zeroGauge": [0, 0],
            "MeanSeaLevel": [0, 0],
            "Data Acquisition Time": ["07-05-2026 20:00", "07-05-2026 21:00"],
            "River Water Level Telemetry Hourly (meter)": [60.937, "-"],
        }
    )

    normalized = normalize_cwc_columns(raw)
    assert "observed_at" in normalized.columns
    assert "water_level_m" in normalized.columns
    assert "station" in normalized.columns

    cleaned = clean_cwc_data(raw, "river_data/cwc/test.csv")
    assert cleaned["observed_at"].notna().all()
    assert cleaned.loc[0, "water_level_m"] == pytest.approx(60.937)
    assert pd.isna(cleaned.loc[1, "water_level_m"])
    assert cleaned.loc[0, "source_file"] == "river_data/cwc/test.csv"
    assert cleaned["station_id"].nunique() == 1


def test_clean_removes_duplicate_station_timestamps():
    raw = pd.DataFrame(
        {
            "Station": ["A", "A"],
            "Agency": ["CWC", "CWC"],
            "State": ["Assam", "Assam"],
            "District": ["D", "D"],
            "Latitude": [26.5, 26.5],
            "Longitude": [92.1, 92.1],
            "Data Acquisition Time": ["07-05-2026 20:00", "07-05-2026 20:00"],
            "River Water Level Telemetry Hourly (meter)": [1.0, 2.0],
        }
    )
    cleaned = clean_cwc_data(raw, "x.csv")
    assert len(cleaned) == 1
    assert cleaned.loc[0, "water_level_m"] == pytest.approx(1.0)


def test_invalid_coordinates_are_missing_not_clipped():
    raw = pd.DataFrame(
        {
            "Station": ["A"],
            "Agency": ["CWC"],
            "State": ["Assam"],
            "District": ["D"],
            "Latitude": [120],
            "Longitude": [92.1],
            "Data Acquisition Time": ["07-05-2026 20:00"],
            "River Water Level Telemetry Hourly (meter)": [1.0],
        }
    )
    cleaned = clean_cwc_data(raw, "x.csv")
    assert pd.isna(cleaned.loc[0, "latitude"])
