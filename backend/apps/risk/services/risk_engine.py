from dataclasses import dataclass
from .normalizer import clamp, linear_score, risk_level


@dataclass
class RiskResult:
    score: float
    level: str
    breakdown: dict
    features: dict
    model_source: str
    data_quality: dict


WEIGHTS = {"rainfall": 0.40, "river": 0.30, "terrain": 0.20, "historical": 0.10}


def _rainfall_component(features):
    values = [
        linear_score(features.get("rainfall_24h_mm"), 0, 150),
        linear_score(features.get("rainfall_3d_mm"), 0, 300),
        linear_score(features.get("rainfall_7d_mm"), 0, 500),
    ]
    available = [v for v in values if v is not None]
    return sum(available) / len(available) if available else None


def _river_component(features):
    level_score = linear_score(features.get("water_level_m"), 0, 8)
    change_score = linear_score(features.get("water_level_change"), 0, 2)
    values = [v for v in (level_score, change_score) if v is not None]
    return sum(values) / len(values) if values else None


def _terrain_component(features):
    slope = features.get("slope_deg")
    elevation = features.get("elevation_m")
    if slope is None and elevation is None:
        return None
    slope_score = linear_score(30 - float(slope), 0, 30) if slope is not None else None
    low_elevation_score = linear_score(500 - float(elevation), 0, 500) if elevation is not None else None
    vals = [v for v in (slope_score, low_elevation_score) if v is not None]
    return sum(vals) / len(vals) if vals else None


def score_baseline(features):
    components = {
        "rainfall": _rainfall_component(features),
        "river": _river_component(features),
        "terrain": _terrain_component(features),
        "historical": features.get("historical_score"),
    }
    weighted = 0.0
    used_weight = 0.0
    for name, component in components.items():
        if component is not None:
            weighted += component * WEIGHTS[name]
            used_weight += WEIGHTS[name]
    score = weighted / used_weight if used_weight else 0.0
    score = clamp(score)
    missing = [name for name, value in components.items() if value is None]
    return RiskResult(
        score=score,
        level=risk_level(score),
        breakdown={k: (None if v is None else round(v, 2)) for k, v in components.items()},
        features=features,
        model_source="baseline",
        data_quality={
            "available_weight": round(used_weight, 3),
            "missing_components": missing,
            "partial": bool(missing),
        },
    )
