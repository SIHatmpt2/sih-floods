from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from services.core_service import CoreService
from services.risk_service import RiskService
from services.weather_service import WeatherService
from .serializers import CoordinateQuerySerializer, NotificationRecordSerializer, UserLocationSerializer

service = CoreService()

LOCATIONS = {
    "location1": {"name": "Assam Floodplain", "lat": 26.2, "lng": 92.9},
    "location2": {"name": "Arunachal Pradesh", "lat": 28.2, "lng": 94.7},
    "location3": {"name": "Sikkim", "lat": 27.5, "lng": 88.5},
    "location4": {"name": "Nainital, Uttarakhand", "lat": 29.3919, "lng": 79.4542},
    "location5": {"name": "Himachal Pradesh", "lat": 31.8, "lng": 77.2},
    "location6": {"name": "Jammu & Kashmir", "lat": 33.4, "lng": 75.3},
    "location7": {"name": "Ladakh", "lat": 34.2, "lng": 77.6},
    "location8": {"name": "Northeast Hills", "lat": 27.0, "lng": 91.0},
    "location9": {"name": "Terai Region", "lat": 29.5, "lng": 80.5},
}


def home(request):
    return render(request, "index.html", {"locations": LOCATIONS})


def redirect_result(request):
    location_key = request.GET.get("location", "location1")
    location = LOCATIONS.get(location_key, LOCATIONS["location1"])
    lat, lon = location["lat"], location["lng"]

    weather = WeatherService().current(lat, lon)
    risk = RiskService().current(lat, lon)

    return render(request, "redirect.html", {
        "location": location,
        "location_key": location_key,
        "weather": weather,
        "risk": risk,
    })


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = CoordinateQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(service.dashboard(request.user, query.validated_data["lat"], query.validated_data["lon"]))


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(service.analytics(request.query_params.get("state")))


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        unread = request.query_params.get("unread") == "true"
        return Response(NotificationRecordSerializer(service.notifications(request.user, unread_only=unread), many=True).data)


class SafeZoneView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = CoordinateQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = service.safe_zone(query.validated_data["lat"], query.validated_data["lon"])
        return Response(result or {"detail": "No suitable safe zone found"}, status=200 if result else 404)


class UserLocationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        rows = request.user.saved_locations.order_by("-is_primary", "name")
        return Response(UserLocationSerializer(rows, many=True).data)

    def post(self, request):
        serializer = UserLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = service.save_location(
            request.user,
            serializer.validated_data["name"],
            serializer.validated_data["latitude"],
            serializer.validated_data["longitude"],
            serializer.validated_data.get("is_primary", False),
        )
        return Response(UserLocationSerializer(location).data, status=201)


class NearbyUserLocationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = CoordinateQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        location = service.nearby_location(request.user, query.validated_data["lat"], query.validated_data["lon"])
        return Response(UserLocationSerializer(location).data if location else {"detail": "No saved location found"}, status=200 if location else 404)
