from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import Http404


def model_directory() -> Path:
    return Path(settings.RISK_MODEL_DIR).resolve()


def list_model_artifacts() -> list[Path]:
    root = model_directory()
    if not root.is_dir():
        return []
    return sorted(
        (path for path in root.iterdir() if path.is_file() and path.suffix.lower() == ".json"),
        key=lambda path: path.name,
    )


def resolve_model_artifact(filename: str) -> Path:
    root = model_directory()
    candidate = (root / filename).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise Http404("Model artifact not found") from exc
    if candidate.suffix.lower() != ".json" or not candidate.is_file():
        raise Http404("Model artifact not found")
    return candidate
