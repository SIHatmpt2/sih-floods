from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
RISK_MODEL_DIR = BACKEND_DIR / "models"
for _path in (str(BASE_DIR), str(BACKEND_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-override-in-production")
INSTALLED_APPS = [
    "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.gis",
    "rest_framework", "corsheaders", "drf_spectacular",
    "apps.weather", "apps.core", "apps.risk",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "backend.config.urls"
WSGI_APPLICATION = "backend.config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATABASES: dict[str, Any] = {"default": {"ENGINE": "django.contrib.gis.db.backends.postgis", "NAME": os.environ.get("POSTGRES_DB", "flood_db"), "USER": os.environ.get("POSTGRES_USER", "postgres"), "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""), "HOST": os.environ.get("POSTGRES_HOST", "localhost"), "PORT": os.environ.get("POSTGRES_PORT", "5432"), "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60"))}}
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
CACHES: dict[str, Any] = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1"}}
TIME_ZONE = "Asia/Kolkata"
USE_TZ = True
LANGUAGE_CODE = "en-us"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", "")
CORS_ALLOW_CREDENTIALS = True
REST_FRAMEWORK: dict[str, Any] = {"DEFAULT_PAGINATION_CLASS": "apps.weather.pagination.WeatherPageNumberPagination", "PAGE_SIZE": 20, "DEFAULT_PERMISSION_CLASSES": ["apps.weather.permissions.WeatherAPIPermission"], "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"], "EXCEPTION_HANDLER": "apps.weather.exceptions.weather_exception_handler", "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}
SPECTACULAR_SETTINGS = {"TITLE": "SIH Flood Weather API", "DESCRIPTION": "Unified Weather, Flood Risk, and Core API.", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False, "COMPONENT_SPLIT_REQUEST": True}
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = int(os.environ.get("CELERY_TASK_TIME_LIMIT", str(int(timedelta(minutes=5).total_seconds()))))
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.environ.get("CELERY_WORKER_PREFETCH_MULTIPLIER", "1"))
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
ACCUWEATHER_API_KEY = os.environ.get("ACCUWEATHER_API_KEY") or None
IMD_API_URL = os.environ.get("IMD_API_URL") or None
IMD_API_KEY = os.environ.get("IMD_API_KEY") or None
CWC_API_URL = os.environ.get("CWC_API_URL") or None
CWC_API_KEY = os.environ.get("CWC_API_KEY") or None
STATE_API_TIMEOUT = int(os.environ.get("STATE_API_TIMEOUT", "30"))
STATE_API_ENDPOINTS = {}
WEATHER_PROVIDER_PRIORITY = env_list("WEATHER_PROVIDER_PRIORITY", "accuweather,imd,cwc")
WEATHER_MAX_AGE_MINUTES = int(os.environ.get("WEATHER_MAX_AGE_MINUTES", "180"))
WEATHER_API_REQUIRE_AUTH = env_bool("WEATHER_API_REQUIRE_AUTH", False)
RISK_API_REQUIRE_AUTH = env_bool("RISK_API_REQUIRE_AUTH", False)
RISK_XGBOOST_MODEL_PATH = os.environ.get("RISK_XGBOOST_MODEL_PATH", "") or None
RISK_JSON_MODEL_PATH = os.environ.get("RISK_JSON_MODEL_PATH", "") or str(RISK_MODEL_DIR / "flood_risk_v1.json")
RISK_TERRAIN_SOURCE = os.environ.get("RISK_TERRAIN_SOURCE", "unconfigured")
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
