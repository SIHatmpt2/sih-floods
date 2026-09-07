from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def liveness(_request):
    return JsonResponse({"status": "alive"})


def readiness(_request):
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"

    try:
        cache.set("core-health", "ok", 5)
        checks["cache"] = "healthy"
    except Exception:
        checks["cache"] = "unhealthy"

    ok = all(value == "healthy" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if ok else "degraded", **checks},
        status=200 if ok else 503,
    )
