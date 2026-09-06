"""Smoke tests for the historical flood-event pipeline helpers."""

import pandas as pd

from data_processing.past_events.clean import clean_past_events_data
from data_processing.past_events.features import add_event_features


def test_clean_and_feature_event_data(tmp_path):
    source = tmp_path / "events.csv"
    df = pd.DataFrame({
        "Event_ID": ["A-1", "A-1", "B-2"],
        "Location": ["Kinnaur", "Kinnaur", "Assam"],
        "Date": ["03-07-2026", "03-07-2026", "18-07-2026"],
        "Peak_waterlevel": ["1.2-1.8 metres", "1.2-1.8 metres", "94.26 metres"],
        "Severity_index": ["2.0/10", "2.0/10", "8.2/10"],
        "GLOF_risk": ["NO", "NO", "NO"],
    })
    cleaned = clean_past_events_data(df, source)
    featured = add_event_features(cleaned)
    assert len(featured) == 2
    assert featured.loc[0, "event_id"] == "A-1"
    assert featured.loc[0, "peak_waterlevel_m"] == 1.2
    assert featured.loc[0, "severity_index"] == 2.0
    assert featured.loc[0, "is_monsoon"] == 1
