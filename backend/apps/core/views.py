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
    "location1": {"name": "Yazali, Keyi Panyor, Arunachal Pradesh, India", "lat": 27.40318, "lng": 93.74447},
    "location2": {"name": "Cholling, Kinnaur, Himachal Pradesh, India", "lat": 31.5833, "lng": 78.1333},
    "location3": {"name": "Mastrang, Sangla Valley, Kinnaur, Himachal Pradesh, India", "lat": 31.35, "lng": 78.25},
    "location4": {"name": "Boh Valley, Shahpur, Kangra, Himachal Pradesh, India", "lat": 32.15, "lng": 76.18},
    "location5": {"name": "Sivasagar, Assam, India", "lat": 26.9843, "lng": 94.6370},
    "location6": {"name": "Dikhowmukh, Sivasagar, Assam, India", "lat": 27.0001, "lng": 94.4647},
    "location7": {"name": "Syanachatti, Uttarkashi, Uttarakhand, India", "lat": 30.98, "lng": 78.47},
    "location8": {"name": "Hailakandi, Assam, India", "lat": 24.6833, "lng": 92.5667},
    "location9": {"name": "Daporijo, Upper Subansiri, Arunachal Pradesh, India", "lat": 27.9833, "lng": 94.2167},
    "location10": {"name": "Sohra, East Khasi Hills, Meghalaya, India", "lat": 25.2677, "lng": 91.7323},
    "location11": {"name": "Dharali, Uttarkashi, Uttarakhand, India", "lat": 31.04, "lng": 78.74},
    "location12": {"name": "Mandi, Himachal Pradesh, India", "lat": 31.5892, "lng": 76.9182},
    "location13": {"name": "Chisoti, Paddar, Kishtwar, Jammu & Kashmir, India", "lat": 33.43, "lng": 76.78},
    "location14": {"name": "Kathua, Jammu & Kashmir, India", "lat": 32.3867, "lng": 75.5189},
    "location15": {"name": "Guwahati, Kamrup Metropolitan, Assam, India", "lat": 26.1445, "lng": 91.7362},
    "location16": {"name": "Bijoypur, Diyun Circle, Changlang, Arunachal Pradesh, India", "lat": 27.95, "lng": 96.15},
    "location17": {"name": "Mangan, Sikkim, India", "lat": 27.5096, "lng": 88.5364},
    "location18": {"name": "Imphal, Manipur, India", "lat": 24.8170, "lng": 93.9368},
    "location19": {"name": "Agartala, West Tripura, Tripura, India", "lat": 23.8315, "lng": 91.2868},
    "location20": {"name": "Sonprayag, Rudraprayag, Uttarakhand, India", "lat": 30.64, "lng": 79.07},
    "location21": {"name": "Samej Village, Rampur, Himachal Pradesh, India", "lat": 31.31, "lng": 77.64},
    "location22": {"name": "Pasighat, East Siang, Arunachal Pradesh, India", "lat": 28.0667, "lng": 95.3269},
    "location23": {"name": "Dibrugarh, Assam, India", "lat": 27.4728, "lng": 94.9120},
    "location24": {"name": "Tura, West Garo Hills, Meghalaya, India", "lat": 25.5144, "lng": 90.2038},
    "location25": {"name": "Kullu, Himachal Pradesh, India", "lat": 31.9584, "lng": 77.1089},
    "location26": {"name": "Dehradun, Uttarakhand, India", "lat": 30.3165, "lng": 78.0322},
    "location27": {"name": "Gangtok, Sikkim, India", "lat": 27.3389, "lng": 88.6065},
    "location28": {"name": "Surjan Morha, Kathua, Jammu & Kashmir, India", "lat": 32.62, "lng": 75.56},
    "location29": {"name": "Silchar, Cachar, Assam, India", "lat": 24.8333, "lng": 92.7789},
    "location30": {"name": "Namsai, Arunachal Pradesh, India", "lat": 27.67, "lng": 95.86},
    "location31": {"name": "Nongpoh, Ri-Bhoi, Meghalaya, India", "lat": 25.9, "lng": 91.88},
    "location32": {"name": "Tupul, Noney, Manipur, India", "lat": 24.8050, "lng": 93.6720},
    "location33": {"name": "Chungthang, Mangan, Sikkim, India", "lat": 27.6037, "lng": 88.6433},
    "location34": {"name": "Nahan, Sirmaur, Himachal Pradesh, India", "lat": 30.558, "lng": 77.296},
    "location35": {"name": "Gopeshwar, Chamoli, Uttarakhand, India", "lat": 30.4040, "lng": 79.3200},
    "location36": {"name": "Pahalgam, Anantnag, Jammu & Kashmir, India", "lat": 34.0161, "lng": 75.3150},
    "location37": {"name": "Aizawl, Mizoram, India", "lat": 23.7271, "lng": 92.7176},
    "location38": {"name": "Chümoukedima, Nagaland, India", "lat": 25.86, "lng": 93.72},
    "location39": {"name": "Belonia, South Tripura, Tripura, India", "lat": 23.25, "lng": 91.45},
}


def _parse_analysis_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Http404("Invalid date. Use YYYY-MM-DD.") from exc


def _render_analysis_error(request, location, location_key, analysis_date, message, current=False):
    return render(request, "redirect.html", {
        "location": location,
        "location_key": location_key,
        "analysis_date": analysis_date,
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
    analysis_date = _parse_analysis_date(request.GET.get("date"))
    lat, lon = location["lat"], location["lng"]
    today = date.today()

    if analysis_date > today:
        raise Http404("Analysis only accepts today or earlier dates.")

    # Today uses live AccuWeather conditions. A separate historical request
    # supplies the rolling seven-day rainfall total because the live provider
    # does not reliably expose that aggregate.
    if analysis_date == today:
        try:
            weather = WeatherService().current(lat, lon)
        except Exception as exc:
            return _render_analysis_error(
                request, location, location_key, analysis_date,
                f"Live weather service failed: {exc}", current=True,
            )

        source = weather.get("data_quality", {}).get("source") or weather.get("station", {}).get("provider")
        if not weather.get("data_quality", {}).get("available") or source not in {"accuweather", "imd"}:
            return _render_analysis_error(
                request, location, location_key, analysis_date,
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
            # Keep the live analysis usable if the separate aggregate request
            # is unavailable; the field remains explicitly unavailable.
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
            "locations": LOCATIONS,
            "weather": weather,
            "weather_outputs": weather_outputs,
            "risk": risk,
            "historical_event": event,
            "analysis_error": None,
            "current_mode": True,
        })

    try:
        weather = HistoricalWeatherService().for_date(lat, lon, analysis_date)
        risk = RiskService().historical(lat, lon, analysis_date, weather)
    except HistoricalWeatherError as exc:
        return _render_analysis_error(
            request, location, location_key, analysis_date, str(exc), current=False,
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
