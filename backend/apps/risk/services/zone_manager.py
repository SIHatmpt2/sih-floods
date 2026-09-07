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
from . import cache


def collect_features(latitude, longitude):
    features = {}
    features.update(rainfall_features(latitude, longitude))
    features.update(river_features(latitude, longitude))
    features.update(terrain_features(latitude, longitude))
    features.update(historical_features(latitude, longitude))
    return features


@transaction.atomic
def assess_point(latitude, longitude, zone=None, persist=False):
    features = collect_features(latitude, longitude)
    result = score_baseline(features)
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
