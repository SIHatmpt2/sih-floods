from django.db.models import Q
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FloodEvent, RiskZone, RiskAlert, HotspotSnapshot
from .serializers import (
    CoordinateQuerySerializer,
    DaysQuerySerializer,
    FloodEventSerializer,
    RiskZoneSerializer,
    RiskAlertSerializer,
    HotspotSnapshotSerializer,
)
from .pagination import RiskPagination
from .selectors import nearby_zones, nearest_zone, assessment_history, active_zones
from .services.analytics import assessment_summary, risk_distribution
from .services.zone_manager import assess_point
from .services import cache


class FloodEventListView(ListAPIView):
    queryset = FloodEvent.objects.all()
    serializer_class = FloodEventSerializer
    pagination_class = RiskPagination


class FloodEventDetailView(RetrieveAPIView):
    queryset = FloodEvent.objects.all()
    serializer_class = FloodEventSerializer


class RiskZoneListView(ListAPIView):
    queryset = active_zones()
    serializer_class = RiskZoneSerializer
    pagination_class = RiskPagination


class RiskZoneNearbyView(APIView):
    def get(self, request):
        params = CoordinateQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = RiskZoneSerializer(
            nearby_zones(
                params.validated_data["lat"],
                params.validated_data["lon"],
                params.validated_data["radius_km"],
            ),
            many=True,
        ).data
        return Response(data)


class RiskCurrentView(APIView):
    def get(self, request):
        params = CoordinateQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        lat = params.validated_data["lat"]
        lon = params.validated_data["lon"]

        cached = cache.get_current(lat, lon)
        if cached:
            return Response(cached)

        zone = nearest_zone(lat, lon)
        result = assess_point(lat, lon, zone=zone, persist=False)
        return Response({
            "score": result.score,
            "level": result.level,
            "breakdown": result.breakdown,
            "features": result.features,
            "model_source": result.model_source,
            "data_quality": result.data_quality,
        })


class RiskBreakdownView(RiskCurrentView):
    pass


class RiskSummaryView(APIView):
    def get(self, request):
        params = DaysQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        return Response(assessment_summary(days=params.validated_data["days"]))


class HighRiskView(APIView):
    def get(self, request):
        zones = active_zones().filter(Q(risk_level="high") | Q(risk_level="severe"))
        return Response(RiskZoneSerializer(zones[:200], many=True).data)


class RiskHistoryView(APIView):
    def get(self, request):
        coords = CoordinateQuerySerializer(data=request.query_params)
        coords.is_valid(raise_exception=True)
        days = DaysQuerySerializer(data=request.query_params)
        days.is_valid(raise_exception=True)
        rows = assessment_history(
            coords.validated_data["lat"],
            coords.validated_data["lon"],
            days=days.validated_data["days"],
        )
        return Response([
            {
                "score": row.score,
                "level": row.risk_level,
                "breakdown": row.breakdown,
                "observed_at": row.observed_at,
            }
            for row in rows
        ])


class RiskAlertListView(ListAPIView):
    queryset = RiskAlert.objects.filter(status__in=["open", "read"])
    serializer_class = RiskAlertSerializer
    pagination_class = RiskPagination


class HotspotListView(ListAPIView):
    queryset = HotspotSnapshot.objects.all()
    serializer_class = HotspotSnapshotSerializer
    pagination_class = RiskPagination


class RiskAnalyticsView(APIView):
    def get(self, request):
        return Response({
            "distribution": risk_distribution(),
            "summary": assessment_summary(days=7),
        })
