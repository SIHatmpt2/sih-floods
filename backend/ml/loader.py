"""Lazy loader for a Risk model artifact.

The loader deliberately does not train models at request time. A model artifact
must already exist on disk; callers may configure its path through settings.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RiskModelLoader:
    _cache: dict[str, Any] = {}

    @classmethod
    def load_json(cls, path: str | Path) -> dict[str, Any]:
        resolved = str(Path(path).expanduser().resolve())
        if resolved not in cls._cache:
            with open(resolved, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                raise ValueError("Risk model artifact must contain a JSON object")
            cls._cache[resolved] = payload
        return cls._cache[resolved]
