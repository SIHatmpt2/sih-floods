"""Run a wider V1.5 alert-policy experiment without changing the training pipeline."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from xgboost import XGBClassifier

from ml.flood_risk.train import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    chronological_split,
    load_training_rows,
    tune_threshold_event_aware,
    tune_alert_policy_event_aware,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_DATASET = Path("apps/risk/data/processed/training_v1.parquet")
DEFAULT_MODEL = Path("models/flood_risk_v1.json")
DEFAULT_METADATA = Path("models/flood_risk_v1.metadata.json")
DEFAULT_OUTPUT = Path("models/flood_risk_v1.policy_experiment.json")
DEFAULT_POLICY_SWEEP = (
    (1, 24.0), (2, 24.0), (3, 24.0), (6, 24.0), (12, 24.0),
    (1, 48.0), (2, 48.0), (3, 48.0), (6, 48.0), (12, 48.0), (18, 48.0), (24, 48.0),
    (6, 72.0), (12, 72.0), (18, 72.0), (24, 72.0),
)


def run_experiment(
    dataset_path: Path = DEFAULT_DATASET,
    model_path: Path = DEFAULT_MODEL,
    metadata_path: Path = DEFAULT_METADATA,
    output_path: Path = DEFAULT_OUTPUT,
    target_event_recall: float = 0.8,
) -> dict[str, object]:
    df = load_training_rows(dataset_path)
    train_val, _ = chronological_split(df, test_fraction=0.2)
    _, validation = chronological_split(train_val, test_fraction=0.25)
    feature_columns = [c for c in FEATURE_COLUMNS if c in df.columns and df[c].notna().any()]
    if not feature_columns:
        raise ValueError("No supported features available")

    model = XGBClassifier()
    model.load_model(model_path)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    configured_threshold = float(metadata.get("threshold", 0.5))
    threshold = configured_threshold
    if metadata.get("threshold_source") != "validation_event_recall_alert_policy":
        threshold = tune_threshold_event_aware(model, validation, feature_columns, target_event_recall)

    result = tune_alert_policy_event_aware(
        model,
        validation,
        feature_columns,
        threshold,
        target_event_recall=target_event_recall,
        policy_candidates=DEFAULT_POLICY_SWEEP,
    )
    result.update({
        "dataset": str(dataset_path),
        "model": str(model_path),
        "target_event_recall": target_event_recall,
        "validation_rows": int(len(validation)),
        "validation_positive_count": int(validation[TARGET_COLUMN].sum()),
        "policy_candidates": [
            {"min_consecutive_alerts": int(consecutive), "alert_cooldown_hours": float(cooldown)}
            for consecutive, cooldown in DEFAULT_POLICY_SWEEP
        ],
    })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    LOGGER.info(
        "Selected policy: consecutive=%d cooldown_hours=%.1f threshold=%.8g event_recall=%.4f false_alarms_per_station_day=%.4f",
        int(result["min_consecutive_alerts"]),
        float(result["alert_cooldown_hours"]),
        float(result["threshold"]),
        float(result["event_recall"] or 0.0),
        float(result["false_alarms_per_station_day"] or 0.0),
    )
    LOGGER.info("Experiment written to %s", output_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a wider V1.5 flood alert-policy experiment")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target-event-recall", type=float, default=0.8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_experiment(args.dataset, args.model, args.metadata, args.output, args.target_event_recall)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
