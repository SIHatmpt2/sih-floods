"""Prediction adapter for an offline-trained Risk artifact.

No fitting/retraining is performed here. The exact artifact schema remains
owned by the training pipeline; this adapter accepts a compatible feature
mapping and returns a normalized score when a score/weights contract exists.
"""
from __future__ import annotations

from typing import Mapping

from .loader import RiskModelLoader
from .validator import validate


class RiskModelPredictor:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def predict(self, features: Mapping[str, float]) -> dict:
        model = RiskModelLoader.load_json(self.model_path)
        validate(model)

        feature_order = model.get("feature_order", [])
        vector = [features.get(name) for name in feature_order]
        if any(value is None for value in vector):
            raise ValueError("Required prediction feature is missing")

        if "score" in model:
            score = float(model["score"])
        elif isinstance(model.get("weights"), dict):
            score = sum(float(features.get(name, 0.0)) * float(weight)
                        for name, weight in model["weights"].items())
        else:
            raise ValueError("Unsupported Risk model artifact: no score or weights contract")

        return {
            "score": max(0.0, min(100.0, score)),
            "model_version": str(model["version"]),
        }
