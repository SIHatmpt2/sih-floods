import os
from pathlib import Path


class ModelUnavailable(Exception):
    pass


class RiskModel:
    """Provider-neutral pretrained XGBoost adapter; training is offline."""

    def __init__(self, model_path=None):
        self.model_path = Path(model_path or os.getenv("RISK_XGBOOST_MODEL_PATH", ""))
        self._model = None

    def load(self):
        if not self.model_path:
            raise ModelUnavailable("No XGBoost model path configured")
        if not self.model_path.exists():
            raise ModelUnavailable(f"Model artifact not found: {self.model_path}")
        try:
            import joblib
            self._model = joblib.load(self.model_path)
        except Exception as exc:
            raise ModelUnavailable(str(exc)) from exc
        return self._model

    def predict(self, features, feature_order=None):
        if self._model is None:
            self.load()
        order = feature_order or sorted(features)
        vector = [[features.get(name) if features.get(name) is not None else 0.0 for name in order]]
        prediction = self._model.predict(vector)[0]
        return float(prediction)
