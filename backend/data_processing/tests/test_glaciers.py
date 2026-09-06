"""Unit tests for glacier/lake cleaning and temporal features."""

import pandas as pd

from backend.data_processing.glaciers.clean import clean_glacier_data
from backend.data_processing.glaciers.features import add_glacier_features


def test_clean_and_feature_glacier_data(tmp_path):
    source = tmp_path / "glaciers.csv"
    df = pd.DataFrame({
        "Glacier/Lake": ["Bokhar Chu", "Bokhar Chu", "Bokhar Chu"],
        "Year": [2024, 2025, 2026],
        "Area(Km2)": [149.29, 146.6, 144.0],
        "Elevation(metre)": ["4,164", "4,164", "4,164"],
        "Melting rate(Vertical thinning)": ["~0.3km-0.6km horizontal retreat/year"] * 3,
        "flood cause": ["NO", "NO", "NO"],
        "River Originating": ["Indus"] * 3,
    })
    cleaned = clean_glacier_data(df, source)
    featured = add_glacier_features(cleaned)
    assert len(featured) == 3
    assert featured.loc[0, "elevation_m"] == 4164
    assert featured.loc[1, "area_change_1y_km2"] < 0
    assert featured.loc[2, "is_area_declining"] == 1
