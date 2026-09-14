from datetime import date

from django.http import Http404
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from services.core_service import CoreService
from services.risk_service import RiskService
from services.weather_service import WeatherService
from apps.risk.selectors import recent_flood_events
from apps.weather.services.historical import HistoricalWeatherError, HistoricalWeatherService
from .serializers import CoordinateQuerySerializer, NotificationRecordSerializer, UserLocationSerializer

service = CoreService()

LOCATIONS = {
    "location1": {"name": "Assam Floodplain", "lat": 26.2, "lng": 92.9},
    "location2": {"name": "Arunachal Pradesh", "lat": 28.2, "lng": 94.7},
    "location3": {"name": "Sikkim", "lat": 27.5, "lng": 88.5},
    "location4": {"name": "Nainital, Uttarakhand", "lat": 29.3919, "lng": 79.4542},
    "location5": {"name": "Mandi, Himachal Pradesh", "lat": 31.7119, "lng": 76.9327},
    "location6": {"name": "Jammu & Kashmir", "lat": 33.4, "lng": 75.3},
    "location7": {"name": "Ladakh", "lat": 34.2, "lng": 77.6},
    "location8": {"name": "Northeast Hills", "lat": 27.0, "lng": 91.0},
    "location9": {"name": "Terai Region", "lat": 29.5, "lng": 80.5},
    "location10": {"name": "Hamirpur, Himachal Pradesh", "lat": 31.6908, "lng": 76.5177},
}


def _parse_analysis_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Http404("Invalid date. Use YYYY-MM-DD.") from exc


def redirect_result(request):
    location_key = request.GET.get("location", "location1")
    location = LOCATIONS.get(location_key, LOCATIONS["location1"])
    analysis_date = _parse_analysis_date(request.GET.get("date"))
    lat, lon = location["lat"], location["lng"]

    if analysis_date > date.today():
        raise Http404("Historical analysis only accepts today or earlier dates.")

    try:
        weather = HistoricalWeatherService().for_date(lat, lon, analysis_date)
        risk = RiskService().historical(lat, lon, analysis_date, weather)
    except HistoricalWeatherError as exc:
        return render(request, "redirect.html", {
            "location": location,
            "location_key": location_key,
            "analysis_date": analysis_date,
            "locations": LOCATIONS,
            "weather": {},
            "weather_outputs": {},
            "risk": {},
            "historical_event": None,
            "analysis_error": str(exc),
        }, status=502)

    events = list(recent_flood_events(
        lat,
        lon,
        radius_km=50,
        days=3650,
        end_date=analysis_date,
    ))
    event = events[0] if events else None

    weather_outputs = {
        "rainfall_mm": weather.get("rainfall_24h_mm"),
        "temperature_c": weather.get("temperature_c"),
        "humidity": weather.get("humidity"),
    }
    return render(request, "redirect.html", {
        "location": location,
        "location_key": location_key,
        "analysis_date": analysis_date,
        "locations": LOCATIONS,
        "weather": weather,
        "weather_outputs": weather_outputs,
        "risk": risk,
        "historical_event": event,
        "analysis_error": None,
    })


def home(request):
    if request.GET.get("location"):
        return redirect_result(request)
    return render(request, "index.html", {"locations": LOCATIONS})


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
