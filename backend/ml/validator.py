"""Validate the minimal, provider-independent Risk model artifact contract."""
from .schema import validate_model_contract


def validate(model: dict) -> bool:
    validate_model_contract(model)
    return True
