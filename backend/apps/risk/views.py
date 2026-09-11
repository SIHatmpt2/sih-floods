from pathlib import Path

from django.http import FileResponse, Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from services.risk_service import RiskService
from .permissions import RiskAPIPermission
from .models import FloodEvent, RiskZone, RiskAlert, HotspotSnapshot
from .serializers import CoordinateQuerySerializer, DaysQuerySerializer, FloodEventSerializer, RiskZoneSerializer, RiskAlertSerializer, HotspotSnapshotSerializer
from .pagination import RiskPagination
from .selectors import nearby_zones, active_zones
from .services.analytics import assessment_summary, risk_distribution
from .services.model_artifacts import list_model_artifacts, resolve_model_artifact


class FloodEventListView(ListAPIView):
    permission_classes = [RiskAPIPermission]
    queryset = FloodEvent.objects.all()
    serializer_class = FloodEventSerializer
    pagination_class = RiskPagination


class FloodEventDetailView(RetrieveAPIView):
    permission_classes = [RiskAPIPermission]
    queryset = FloodEvent.objects.all()
    serializer_class = FloodEventSerializer


class RiskZoneListView(ListAPIView):
    permission_classes = [RiskAPIPermission]
    queryset = active_zones()
    serializer_class = RiskZoneSerializer
    pagination_class = RiskPagination


class RiskZoneNearbyView(APIView):
    permission_classes = [RiskAPIPermission]
    def get(self, request):
        params = CoordinateQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        return Response(RiskZoneSerializer(nearby_zones(**params.validated_data), many=True).data)


class RiskCurrentView(APIView):
    permission_classes = [RiskAPIPermission]
    def get(self, request):
        params = CoordinateQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        return Response(RiskService().current(params.validated_data["lat"], params.validated_data["lon"]))


class RiskBreakdownView(RiskCurrentView):
    pass


class RiskSummaryView(APIView):
    permission_classes = [RiskAPIPermission]
    def get(self, request):
        params = DaysQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        return Response(assessment_summary(days=params.validated_data["days"]))


class HighRiskView(APIView):
    permission_classes = [RiskAPIPermission]
    def get(self, request):
        zones = active_zones().filter(risk_level__in=["high", "severe"])
        return Response(RiskZoneSerializer(zones[:200], many=True).data)


class RiskHistoryView(APIView):
    permission_classes = [RiskAPIPermission]
    def get(self, request):
        coords = CoordinateQuerySerializer(data=request.query_params)
        coords.is_valid(raise_exception=True)
        days = DaysQuerySerializer(data=request.query_params)
        days.is_valid(raise_exception=True)
        rows = RiskService().history(coords.validated_data["lat"], coords.validated_data["lon"], days=days.validated_data["days"])
        return Response([{"score": row.score, "level": row.risk_level, "breakdown": row.breakdown, "observed_at": row.observed_at} for row in rows])


class RiskAlertListView(ListAPIView):
    permission_classes = [RiskAPIPermission]
    queryset = RiskAlert.objects.filter(status__in=["open", "read"])
    serializer_class = RiskAlertSerializer
    pagination_class = RiskPagination


class HotspotListView(ListAPIView):
    permission_classes = [RiskAPIPermission]
    queryset = HotspotSnapshot.objects.all()
    serializer_class = HotspotSnapshotSerializer
    pagination_class = RiskPagination


class RiskAnalyticsView(APIView):
    permission_classes = [RiskAPIPermission]
    def get(self, request):
        return Response({"distribution": risk_distribution(), "summary": assessment_summary(days=7)})


class RiskModelListView(APIView):
    permission_classes = [RiskAPIPermission]

    def get(self, request):
        artifacts = list_model_artifacts()
        return Response({
            "models": [
                {
                    "name": artifact.name,
                    "url": request.build_absolute_uri(f"/api/risk/models/{artifact.name}"),
                    "size": artifact.stat().st_size,
                }
                for artifact in artifacts
            ]
        })


class RiskModelArtifactView(APIView):
    permission_classes = [RiskAPIPermission]

    def get(self, request, filename):
        artifact = resolve_model_artifact(filename)
        if artifact.suffix.lower() != ".json":
            raise Http404("Model artifact not found")
        return FileResponse(
            artifact.open("rb"),
            content_type="application/json",
            as_attachment=False,
            filename=Path(filename).name,
        )
