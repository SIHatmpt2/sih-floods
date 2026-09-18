from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
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
IST = ZoneInfo("Asia/Kolkata")
LOCATIONS = {
    "location1": {"name": "Mandi, Himachal Pradesh, India", "lat": 31.5892, "lng": 76.9182},
    "location2": {"name": "Dibrugarh, Assam, India", "lat": 27.4728, "lng": 94.912},
    "location3": {"name": "Mangan, Sikkim, India", "lat": 27.5096, "lng": 88.5364},
    "location4": {"name": "Karimganj, Assam, India", "lat": 24.8692, "lng": 92.3555},
    "location5": {"name": "East Siang, Arunachal Pradesh, India", "lat": 28.0667, "lng": 95.3333},
    "location6": {"name": "Tupul, Noney district, Manipur, India", "lat": 24.805, "lng": 93.672},
    "location7": {"name": "Dehradun, Uttarakhand, India", "lat": 30.3165, "lng": 78.0322},
    "location8": {"name": "Kathua, Jammu & Kashmir, India", "lat": 32.3867, "lng": 75.5189},
    "location9": {"name": "Aizawl, Mizoram, India", "lat": 23.7271, "lng": 92.7176},
    "location10": {"name": "Dimapur, Nagaland, India", "lat": 25.8629, "lng": 93.7537},
    "location11": {"name": "Kullu, Himachal Pradesh, India", "lat": 31.9584, "lng": 77.1089},
    "location12": {"name": "Shimla, Himachal Pradesh, India", "lat": 31.1048, "lng": 77.1734},
    "location13": {"name": "Kangra, Himachal Pradesh, India", "lat": 32.0998, "lng": 76.2691},
    "location14": {"name": "Kinnaur, Himachal Pradesh, India", "lat": 31.5833, "lng": 78.4167},
    "location15": {"name": "Sangla Valley, Himachal Pradesh, India", "lat": 31.4239, "lng": 78.2661},
    "location16": {"name": "Cholling / Miru Nallah, Kinnaur, Himachal Pradesh, India", "lat": 31.57, "lng": 78.4},
    "location17": {"name": "Mastrang / Garge Nallah, Kinnaur, Himachal Pradesh, India", "lat": 31.35, "lng": 78.25},
    "location18": {"name": "Boh Valley, Kangra, Himachal Pradesh, India", "lat": 32.15, "lng": 76.18},
    "location19": {"name": "Samej Village, Rampur, Himachal Pradesh, India", "lat": 31.31, "lng": 77.64},
    "location20": {"name": "Dharali–Harsil, Uttarkashi, Uttarakhand, India", "lat": 31.04, "lng": 78.74},
    "location21": {"name": "Syanachatti, Uttarkashi, Uttarakhand, India", "lat": 30.98, "lng": 78.47},
    "location22": {"name": "Sonprayag, Rudraprayag, Uttarakhand, India", "lat": 30.64, "lng": 79.07},
    "location23": {"name": "Chisoti (Chashoti), Kishtwar, Jammu & Kashmir, India", "lat": 33.43, "lng": 76.78},
    "location24": {"name": "Pahalgam, Jammu & Kashmir, India", "lat": 34.0161, "lng": 75.315},
    "location25": {"name": "Amarnath Cave, Jammu & Kashmir, India", "lat": 34.2139, "lng": 75.5019},
    "location26": {"name": "Pasighat, East Siang, Arunachal Pradesh, India", "lat": 28.0667, "lng": 95.3269},
    "location27": {"name": "Upper Subansiri, Arunachal Pradesh, India", "lat": 28, "lng": 94.2},
    "location28": {"name": "Bijoypur Village, Diyun Circle, Changlang, Arunachal Pradesh, India", "lat": 27.95, "lng": 96.15},
    "location29": {"name": "Sohra (Cherrapunji), Meghalaya, India", "lat": 25.2677, "lng": 91.7323},
    "location30": {"name": "Silchar, Cachar, Assam, India", "lat": 24.8333, "lng": 92.7789},
    "location31": {"name": "Sivasagar, Assam, India", "lat": 26.9843, "lng": 94.637},
    "location32": {"name": "Jorhat, Assam, India", "lat": 26.7509, "lng": 94.2037},
    "location33": {"name": "Hailakandi, Assam, India", "lat": 24.6833, "lng": 92.5667},
    "location34": {"name": "Namsai, Arunachal Pradesh, India", "lat": 27.67, "lng": 95.86},
    "location35": {"name": "Changlang, Arunachal Pradesh, India", "lat": 27.12, "lng": 96.72},
    "location36": {"name": "Gangtok, Sikkim, India", "lat": 27.3389, "lng": 88.6065},
    "location37": {"name": "Imphal, Manipur, India", "lat": 24.817, "lng": 93.9368},
    "location38": {"name": "West Tripura, Tripura, India", "lat": 23.8315, "lng": 91.2868},
    "location39": {"name": "Chümoukedima, Nagaland, India", "lat": 25.86, "lng": 93.72},
    "location40": {"name": "Sirmaur, Himachal Pradesh, India", "lat": 30.68, "lng": 77.42},
}


def _parse_analysis_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Http404("Invalid date. Use YYYY-MM-DD.") from exc


def _parse_analysis_datetime(date_value: str | None, time_value: str | None):
    analysis_date = _parse_analysis_date(date_value)
    if not time_value:
        return analysis_date, None
    try:
        analysis_time = datetime.strptime(time_value, "%H:%M").time()
    except ValueError as exc:
        raise Http404("Invalid time. Use HH:MM.") from exc
    return analysis_date, datetime.combine(analysis_date, analysis_time, tzinfo=IST)


def _render_analysis_error(request, location, location_key, analysis_date, analysis_datetime, message, current=False):
    return render(request, "redirect.html", {
        "location": location,
        "location_key": location_key,
        "analysis_date": analysis_date,
        "analysis_datetime": analysis_datetime,
        "locations": LOCATIONS,
        "weather": {},
        "weather_outputs": {},
        "risk": {},
        "historical_event": None,
        "analysis_error": message,
        "current_mode": current,
    }, status=502)


def redirect_result(request):
    location_key = request.GET.get("location", "location1")
    location = LOCATIONS.get(location_key, LOCATIONS["location1"])
    analysis_date, analysis_datetime = _parse_analysis_datetime(
        request.GET.get("date"), request.GET.get("time")
    )
    lat, lon = location["lat"], location["lng"]
    now_ist = timezone.localtime(timezone.now(), IST)

    if analysis_datetime is not None and analysis_datetime > now_ist:
        raise Http404("Analysis only accepts a date/time at or before the current time.")

    # A timestamped request is always historical, even when it is today.
    # Omitting time preserves the existing live-today behavior.
    if analysis_datetime is None and analysis_date == now_ist.date():
        try:
            weather = WeatherService().current(lat, lon)
        except Exception as exc:
            return _render_analysis_error(
                request, location, location_key, analysis_date, analysis_datetime,
                f"Live weather service failed: {exc}", current=True,
            )

        source = weather.get("data_quality", {}).get("source") or weather.get("station", {}).get("provider")
        if not weather.get("data_quality", {}).get("available") or source not in {"accuweather", "imd"}:
            return _render_analysis_error(
                request, location, location_key, analysis_date, analysis_datetime,
                "No live weather provider returned usable conditions. Configure ACCUWEATHER_API_KEY and try again.",
                current=True,
            )

        risk = RiskService().current(lat, lon, weather=weather)
        events = list(recent_flood_events(lat, lon, radius_km=50, days=3650))
        event = events[0] if events else None

        rainfall_7d_mm = weather.get("rainfall_7d_mm")
        try:
            historical_today = HistoricalWeatherService().for_date(lat, lon, analysis_date)
            rainfall_7d_mm = historical_today.get("rainfall_7d_mm")
        except HistoricalWeatherError:
            pass

        weather_outputs = {
            "rainfall_mm": weather.get("rainfall_24h_mm", weather.get("rainfall_mm")),
            "rainfall_7d_mm": rainfall_7d_mm,
            "temperature_c": weather.get("temperature_c"),
            "humidity": weather.get("humidity"),
            "wind_speed_kmh": weather.get("wind_speed_kmh"),
            "pressure_hpa": weather.get("pressure_hpa"),
            "observed_at": weather.get("observed_at"),
            "provider": source,
        }
        return render(request, "redirect.html", {
            "location": location,
            "location_key": location_key,
            "analysis_date": analysis_date,
            "analysis_datetime": analysis_datetime,
            "locations": LOCATIONS,
            "weather": weather,
            "weather_outputs": weather_outputs,
            "risk": risk,
            "historical_event": event,
            "analysis_error": None,
            "current_mode": True,
        })

    try:
        weather = HistoricalWeatherService().for_date(
            lat, lon, analysis_date, analysis_datetime=analysis_datetime
        )
        risk = RiskService().historical(lat, lon, analysis_date, weather)
    except HistoricalWeatherError as exc:
        return _render_analysis_error(
            request, location, location_key, analysis_date, analysis_datetime, str(exc), current=False,
        )

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
        "rainfall_7d_mm": weather.get("rainfall_7d_mm"),
        "temperature_c": weather.get("temperature_c"),
        "humidity": weather.get("humidity"),
        "wind_speed_kmh": weather.get("wind_speed_kmh"),
        "pressure_hpa": weather.get("pressure_hpa"),
        "provider": weather.get("data_quality", {}).get("dataset"),
    }
    return render(request, "redirect.html", {
        "location": location,
        "location_key": location_key,
        "analysis_date": analysis_date,
        "analysis_datetime": analysis_datetime,
        "locations": LOCATIONS,
        "weather": weather,
        "weather_outputs": weather_outputs,
        "risk": risk,
        "historical_event": event,
        "analysis_error": None,
        "current_mode": False,
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
