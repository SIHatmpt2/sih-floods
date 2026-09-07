"""Tests for the V1.5 XGBoost training helpers."""

import numpy as np
import pandas as pd

from ml.flood_risk.dataset import TARGET_COLUMN
from ml.flood_risk.train import (
    apply_alert_policy,
    chronological_split,
    evaluate_event_level,
    load_training_rows,
    select_best_alert_policy_result,
    select_best_weight_result,
    train_model,
    tune_threshold,
    tune_threshold_event_aware,
)


def test_chronological_split_preserves_time_order():
    df = pd.DataFrame({"station_id": ["a"] * 5, "observed_at": pd.date_range("2025-01-01", periods=5, freq="h"), TARGET_COLUMN: [0, 1, 0, 0, 1], "rainfall_24h": [1, 2, 3, 4, 5], "rainfall_48h": [1, 2, 3, 4, 5], "rainfall_72h": [1, 2, 3, 4, 5]})
    train, test = chronological_split(df, test_fraction=0.4)
    assert train.observed_at.max() < test.observed_at.min()
    assert len(train) == 3
    assert len(test) == 2


def test_nested_chronological_split_keeps_final_test_future():
    df = pd.DataFrame({"station_id": ["a"] * 10, "observed_at": pd.date_range("2025-01-01", periods=10, freq="h"), TARGET_COLUMN: [0, 0, 1, 0, 0, 0, 1, 0, 0, 1]})
    train_val, test = chronological_split(df, test_fraction=0.2)
    train, validation = chronological_split(train_val, test_fraction=0.25)
    assert train.observed_at.max() < validation.observed_at.min()
    assert validation.observed_at.max() < test.observed_at.min()
    assert len(train) == 6
    assert len(validation) == 2
    assert len(test) == 2


def test_load_training_rows_requires_core_rainfall(tmp_path):
    path = tmp_path / "training.parquet"
    df = pd.DataFrame({"station_id": ["a", "a", "b"], "observed_at": pd.date_range("2025-01-01", periods=3, freq="h"), TARGET_COLUMN: [0, 1, 0], "rainfall_24h": [1.0, 2.0, None], "rainfall_48h": [1.0, 2.0, 3.0], "rainfall_72h": [1.0, 2.0, 3.0]})
    df.to_parquet(path, index=False)
    loaded = load_training_rows(path)
    assert len(loaded) == 2
    assert loaded[TARGET_COLUMN].tolist() == [0, 1]


def test_tune_threshold_can_select_probabilities_below_one_percent():
    class DummyModel:
        def predict_proba(self, x):
            values = np.array([0.00002, 0.00004, 0.00006, 0.00008])
            return np.column_stack([1.0 - values, values])

    validation = pd.DataFrame({"rainfall_24h": [1, 2, 3, 4], TARGET_COLUMN: [0, 1, 0, 1]})
    threshold = tune_threshold(DummyModel(), validation, ["rainfall_24h"])
    assert 0.00004 <= threshold <= 0.00006


def test_train_model_uses_ratio_based_class_weight():
    train = pd.DataFrame({"rainfall_24h": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], TARGET_COLUMN: [0, 0, 0, 0, 1, 1]})
    validation = train.copy()
    model, weight = train_model(train, validation, ["rainfall_24h"])
    assert weight == 2.0
    assert model.get_params()["scale_pos_weight"] == 2.0
    assert model.get_params()["max_delta_step"] == 1


def test_select_best_weight_result_uses_validation_pr_auc():
    results = [{"weight_multiplier": 0.25, "validation_pr_auc": 0.031}, {"weight_multiplier": 0.5, "validation_pr_auc": 0.047}, {"weight_multiplier": 1.0, "validation_pr_auc": 0.044}, {"weight_multiplier": 2.0, "validation_pr_auc": 0.039}]
    best = select_best_weight_result(results)
    assert best["weight_multiplier"] == 0.5
    assert best["validation_pr_auc"] == 0.047


def test_evaluate_event_level_groups_positive_windows_and_counts_false_alarm_days():
    df = pd.DataFrame({"station_id": ["a", "a", "a", "a", "a", "b"], "observed_at": pd.to_datetime(["2025-01-01 00:00", "2025-01-01 00:15", "2025-01-01 00:30", "2025-01-02 00:00", "2025-01-05 00:00", "2025-01-01 00:00"]), TARGET_COLUMN: [1, 1, 1, 0, 1, 1], "probability": [0.1, 0.2, 0.01, 0.9, 0.3, 0.4]})
    metrics = evaluate_event_level(df, threshold=0.05, min_consecutive_alerts=1, cooldown_hours=0)
    assert metrics["event_count"] == 3
    assert metrics["detected_event_count"] == 3
    assert metrics["event_recall"] == 1.0
    assert metrics["false_alarm_rows"] == 1
    assert metrics["false_alarm_station_days"] == 1
    assert metrics["mean_lead_time_to_window_end_hours"] == 0.16666666666666666


def test_tune_threshold_event_aware_prefers_fewer_false_alarm_days_at_target_recall():
    class DummyModel:
        def predict_proba(self, x):
            values = x["probability"].to_numpy()
            return np.column_stack([1.0 - values, values])

    validation = pd.DataFrame({"station_id": ["a"] * 8 + ["b"] * 4, "observed_at": pd.to_datetime(["2025-06-01 00:00", "2025-06-01 00:15", "2025-06-01 00:30", "2025-06-01 00:45", "2025-06-03 00:00", "2025-06-03 00:15", "2025-06-03 00:30", "2025-06-03 00:45", "2025-06-01 00:00", "2025-06-01 00:15", "2025-06-01 00:30", "2025-06-01 00:45"]), TARGET_COLUMN: [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0], "probability": [0.20, 0.19, 0.18, 0.17, 0.11, 0.10, 0.09, 0.08, 0.10, 0.02, 0.02, 0.02]})
    threshold = tune_threshold_event_aware(DummyModel(), validation, ["probability"], target_event_recall=1.0, min_consecutive_alerts=1, cooldown_hours=0)
    assert 0.10 < threshold <= 0.11


def test_apply_alert_policy_requires_consecutive_predictions_and_applies_cooldown():
    evaluation = pd.DataFrame({"station_id": ["a"] * 8, "observed_at": pd.date_range("2025-01-01", periods=8, freq="15min"), "probability": [0.2, 0.2, 0.2, 0.2, 0.01, 0.2, 0.2, 0.2]})
    alerted = apply_alert_policy(evaluation, threshold=0.1, min_consecutive_alerts=3, cooldown_hours=2.0)
    assert alerted["alert"].tolist() == [False, False, True, False, False, False, False, False]


def test_apply_alert_policy_does_not_count_nonconsecutive_rows_as_confirmation():
    evaluation = pd.DataFrame({"station_id": ["a"] * 4, "observed_at": pd.date_range("2025-01-01", periods=4, freq="15min"), "probability": [0.2, 0.01, 0.2, 0.2]})
    alerted = apply_alert_policy(evaluation, threshold=0.1, min_consecutive_alerts=2, cooldown_hours=1.0)
    assert alerted["alert"].tolist() == [False, False, False, True]


def test_select_best_alert_policy_result_minimizes_false_alarm_days_at_target_recall():
    results = [
        {"min_consecutive_alerts": 3, "alert_cooldown_hours": 24.0, "threshold": 0.01, "event_recall": 0.9, "false_alarm_station_days": 10, "false_alarm_rows": 20},
        {"min_consecutive_alerts": 6, "alert_cooldown_hours": 48.0, "threshold": 0.008, "event_recall": 0.8, "false_alarm_station_days": 4, "false_alarm_rows": 9},
        {"min_consecutive_alerts": 12, "alert_cooldown_hours": 72.0, "threshold": 0.02, "event_recall": 0.7, "false_alarm_station_days": 1, "false_alarm_rows": 2},
    ]
    best = select_best_alert_policy_result(results, target_event_recall=0.8)
    assert best["min_consecutive_alerts"] == 6
    assert best["alert_cooldown_hours"] == 48.0
