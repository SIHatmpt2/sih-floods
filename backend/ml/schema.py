"""Model artifact contract helpers."""

REQUIRED_MODEL_KEYS = ("version", "feature_order")


def validate_model_contract(model: dict) -> None:
    missing = [key for key in REQUIRED_MODEL_KEYS if key not in model]
    if missing:
        raise ValueError(f"Risk model missing required keys: {', '.join(missing)}")
