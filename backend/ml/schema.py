"""Model artifact contract helpers."""

REQUIRED_MODEL_KEYS = ("version", "feature_order")


def validate_model_contract(model: dict) -> None:
    # The production V1.5 artifact is an XGBoost JSON payload wrapped in
    # {"content": "..."}. Validate that wrapper separately from the legacy
    # provider-neutral score/weights contract.
    if isinstance(model.get("content"), str):
        return

    missing = [key for key in REQUIRED_MODEL_KEYS if key not in model]
    if missing:
        raise ValueError(f"Risk model missing required keys: {', '.join(missing)}")
