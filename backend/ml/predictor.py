"""Prediction adapter for an offline-trained Risk artifact."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np

from .loader import RiskModelLoader
from .validator import validate


class RiskModelPredictor:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def predict(self, features: Mapping[str, float]) -> dict:
        model = RiskModelLoader.load_json(self.model_path)
        validate(model)

        # V1.5 stores the XGBoost JSON payload inside a small JSON wrapper.
        # Keep the legacy score/weights contract supported for older artifacts.
        content = model.get("content")
        if isinstance(content, str):
            payload = json.loads(content)
            learner = payload.get("learner", {})
            feature_order = learner.get("feature_names", [])
            if not feature_order:
                raise ValueError("XGBoost Risk model has no feature names")

            vector = [features.get(name) for name in feature_order]
            if any(value is None for value in vector):
                raise ValueError("Required prediction feature is missing")

            try:
                import xgboost as xgb
            except ImportError as exc:
                raise ValueError("xgboost is required to load the Risk model") from exc

            booster = xgb.Booster()
            booster.load_model(bytearray(content.encode("utf-8")))
            matrix = xgb.DMatrix(
                np.asarray([vector], dtype=float),
                feature_names=list(feature_order),
            )
            probability = float(booster.predict(matrix)[0])

            metadata_path = Path(self.model_path).with_suffix(".metadata.json")
            model_version = "v1"
            if metadata_path.exists():
                metadata = RiskModelLoader.load_json(metadata_path)
                model_version = str(metadata.get("model_version", model_version))

            return {
                "score": max(0.0, min(100.0, probability * 100.0)),
                "probability": probability,
                "model_version": model_version,
            }

        feature_order = model.get("feature_order", [])
        vector = [features.get(name) for name in feature_order]
        if any(value is None for value in vector):
            raise ValueError("Required prediction feature is missing")

        if "score" in model:
            score = float(model["score"])
        elif isinstance(model.get("weights"), dict):
            score = sum(
                float(features.get(name, 0.0)) * float(weight)
                for name, weight in model["weights"].items()
            )
        else:
            raise ValueError("Unsupported Risk model artifact: no score, weights, or XGBoost content")

        return {
            "score": max(0.0, min(100.0, score)),
            "model_version": str(model["version"]),
        }
