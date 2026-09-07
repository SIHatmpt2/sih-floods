from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.services.weather_service import WeatherService
from .models import WeatherStation
from .permissions import WeatherAPIPermission
from .serializers import (
    WeatherCoordinateQuerySerializer,
    WeatherCurrentSerializer,
    WeatherHistoryItemSerializer,
    WeatherHistoryQuerySerializer,
)


class WeatherCurrentView(APIView):
    permission_classes = [WeatherAPIPermission]

    def get(self, request):
        params = WeatherCoordinateQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        payload = WeatherService().current(params.validated_data["lat"], params.validated_data["lon"])
        return Response(WeatherCurrentSerializer(payload).data)


class WeatherHistoryView(APIView):
    permission_classes = [WeatherAPIPermission]

    def get(self, request):
        params = WeatherHistoryQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        rows = WeatherService().history(
            params.validated_data["lat"], params.validated_data["lon"], params.validated_data["days"]
        )
        return Response(WeatherHistoryItemSerializer(rows, many=True).data)


class WeatherStationListView(ListAPIView):
    permission_classes = [WeatherAPIPermission]
    queryset = WeatherStation.objects.filter(active=True).order_by("provider", "name")

    def list(self, request, *args, **kwargs):
        return Response(list(self.get_queryset().values(
            "id", "provider", "station_id", "name", "state", "district", "location"
        )))
