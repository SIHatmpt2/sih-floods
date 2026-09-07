from django.contrib import admin
from .models import FloodEvent, RiskZone, RiskAssessment, RiskAlert


@admin.register(FloodEvent)
class FloodEventAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "event_date", "district", "severity", "source")
    list_filter = ("severity", "source")
    search_fields = ("name", "district", "source")


@admin.register(RiskZone)
class RiskZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "risk_level", "latest_score", "is_active", "updated_at")
    list_filter = ("risk_level", "is_active")
    search_fields = ("name",)


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ("id", "risk_level", "score", "observed_at", "model_source")
    list_filter = ("risk_level", "model_source")


@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "status", "created_at", "resolved_at")
    list_filter = ("severity", "status")
    search_fields = ("title", "message")
