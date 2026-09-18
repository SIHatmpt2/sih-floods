"""Tests for CAMS carbon preprocessing and temporal features."""

import pandas as pd

from data_processing.carbon.pipeline import _add_regional_anomaly, _clean_hilly, _clean_regional


def test_cams_monthly_features(tmp_path):
    hilly = tmp_path / "hilly.csv"
    regional = tmp_path / "regional.csv"
    pd.DataFrame({
        "location": ["Dehradun"] * 13,
        "date": pd.date_range("2025-01-01", periods=13, freq="MS"),
        "requested_latitude": [30.3165] * 13,
        "requested_longitude": [78.0322] * 13,
        "latitude": [30.0] * 13,
        "longitude": [78.0] * 13,
        "co2_ppm": list(range(400, 413)),
    }).to_csv(hilly, index=False)
    pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=13, freq="MS"),
        "regional_mean_co2_ppm": [390.0] * 13,
    }).to_csv(regional, index=False)
    local = _clean_hilly(hilly)
    region = _clean_regional(regional)
    result = _add_regional_anomaly(local, region)
    assert result.loc[1, "co2_monthly_change_ppm"] == 1.0
    assert result.loc[12, "co2_yearly_change_ppm"] == 12.0
    assert result.loc[0, "co2_regional_anomaly_ppm"] == 10.0
