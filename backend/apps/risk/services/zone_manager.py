from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.utils import timezone
from ..models import RiskAssessment
from .rainfall import rainfall_features
from .river import river_features
from .terrain import terrain_features
from .historical import historical_features
from .risk_engine import score_baseline
from .alert_engine import create_or_update_alert
from .weather_adapter import WeatherRiskAdapter
from ml.predictor import RiskModelPredictor
from . import cache


def collect_features(latitude, longitude, weather=None, analysis_date=None):
    features = {}
    if weather is None:
        try:
            features.update(WeatherRiskAdapter().current_features(latitude, longitude))
        except Exception:
            pass
        features.update(rainfall_features(latitude, longitude))
        features.update(river_features(latitude, longitude))
    else:
        from data_processing.feature_builder import build_risk_features
        features.update(build_risk_features(weather, analysis_datetime=analysis_date))
        # The baseline engine and the trained model use different naming
        # contracts. Keep aliases so the historical baseline uses the same
        # reconstructed rainfall values instead of today's database values.
        features["rainfall_24h_mm"] = weather.get("rainfall_24h_mm")
        features["rainfall_3d_mm"] = weather.get("rainfall_3d_mm")
        features["rainfall_7d_mm"] = weather.get("rainfall_7d_mm")
        features["water_level_m"] = weather.get("water_level_m")
        features["water_level_change"] = weather.get("water_level_change")

    features.update(terrain_features(latitude, longitude))
    features.update(historical_features(latitude, longitude, analysis_date=analysis_date))
    return features


def score_features(features):
    baseline = score_baseline(features)
    model_path = getattr(settings, "RISK_JSON_MODEL_PATH", None)
    if not model_path:
        return baseline
    try:
        prediction = RiskModelPredictor(model_path).predict(features)
        from .normalizer import risk_level
        score = prediction["score"]
        return baseline.__class__(
            score=score,
            level=risk_level(score),
            breakdown=baseline.breakdown,
            features=features,
            model_source=f"json:{prediction['model_version']}",
            data_quality={"model": "json", "partial": False},
        )
    except (OSError, ValueError, TypeError, KeyError):
        return baseline


@transaction.atomic
def assess_point(latitude, longitude, zone=None, persist=False, weather=None, analysis_date=None):
    features = collect_features(latitude, longitude, weather=weather, analysis_date=analysis_date)
    result = score_features(features)
    if not persist:
        return result
    now = timezone.now()
    location = GEOSGeometry(f"POINT ({float(longitude)} {float(latitude)})", srid=4326)
    assessment = RiskAssessment.objects.create(
        zone=zone,
        location=location,
        score=result.score,
        risk_level=result.level,
        breakdown=result.breakdown,
        features=result.features,
        model_source=result.model_source,
        data_quality=result.data_quality,
        observed_at=now,
    )
    if zone:
        zone.latest_score = result.score
        zone.risk_level = result.level
        zone.feature_snapshot = result.features
        zone.last_assessed_at = now
        zone.save(update_fields=["latest_score", "risk_level", "feature_snapshot", "last_assessed_at", "updated_at"])
        create_or_update_alert(zone, result.score, result.level, result.breakdown)
    cache.set_current(latitude, longitude, {
        "risk_score": result.score,
        "risk_level": result.level,
        "breakdown": result.breakdown,
        "features": result.features,
        "model_source": result.model_source,
        "data_quality": result.data_quality,
        "observed_at": now.isoformat(),
    })
    return assessment
