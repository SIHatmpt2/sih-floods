import csv
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from services.core_service import CoreService
from services.risk_service import RiskService
from services.weather_service import WeatherService
from apps.risk.services.rainfall import rainfall_features
from .serializers import CoordinateQuerySerializer, NotificationRecordSerializer, UserLocationSerializer

service = CoreService()

LOCATIONS = {
    "location1": {"name": "Bijoypur, Diyun Circle, Changlang, Arunachal Pradesh, India", "lat": 27.95, "lng": 96.15},
    "location2": {"name": "Daporijo, Upper Subansiri, Arunachal Pradesh, India", "lat": 27.9833, "lng": 94.2167},
    "location3": {"name": "Namsai, Arunachal Pradesh, India", "lat": 27.67, "lng": 95.86},
    "location4": {"name": "Pasighat, East Siang, Arunachal Pradesh, India", "lat": 28.0667, "lng": 95.3269},
    "location5": {"name": "Yazali, Keyi Panyor, Arunachal Pradesh, India", "lat": 27.40318, "lng": 93.74447},
    "location6": {"name": "Dibrugarh, Assam, India", "lat": 27.4728, "lng": 94.912},
    "location7": {"name": "Dikhowmukh, Sivasagar, Assam, India", "lat": 27.0001, "lng": 94.4647},
    "location8": {"name": "Guwahati, Kamrup Metropolitan, Assam, India", "lat": 26.1445, "lng": 91.7362},
    "location9": {"name": "Hailakandi, Assam, India", "lat": 24.6833, "lng": 92.5667},
    "location10": {"name": "Silchar, Cachar, Assam, India", "lat": 24.8333, "lng": 92.7789},
    "location11": {"name": "Sivasagar, Assam, India", "lat": 26.9843, "lng": 94.637},
    "location12": {"name": "Boh Valley, Shahpur, Kangra, Himachal Pradesh, India", "lat": 32.15, "lng": 76.18},
    "location13": {"name": "Cholling, Kinnaur, Himachal Pradesh, India", "lat": 31.5833, "lng": 78.1333},
    "location14": {"name": "Kullu, Himachal Pradesh, India", "lat": 31.9584, "lng": 77.1089},
    "location15": {"name": "Mandi, Himachal Pradesh, India", "lat": 31.5892, "lng": 76.9182},
    "location16": {"name": "Mastrang, Sangla Valley, Kinnaur, Himachal Pradesh, India", "lat": 31.35, "lng": 78.25},
    "location17": {"name": "Nahan, Sirmaur, Himachal Pradesh, India", "lat": 30.558, "lng": 77.296},
    "location18": {"name": "Samej Village, Rampur, Himachal Pradesh, India", "lat": 31.31, "lng": 77.64},
    "location19": {"name": "Chisoti, Paddar, Kishtwar, Jammu & Kashmir, India", "lat": 33.43, "lng": 76.78},
    "location20": {"name": "Kathua, Jammu & Kashmir, India", "lat": 32.3867, "lng": 75.5189},
    "location21": {"name": "Pahalgam, Anantnag, Jammu & Kashmir, India", "lat": 34.0161, "lng": 75.315},
    "location22": {"name": "Surjan Morha, Kathua, Jammu & Kashmir, India", "lat": 32.62, "lng": 75.56},
    "location23": {"name": "Imphal, Manipur, India", "lat": 24.817, "lng": 93.9368},
    "location24": {"name": "Tupul, Noney, Manipur, India", "lat": 24.805, "lng": 93.672},
    "location25": {"name": "Nongpoh, Ri-Bhoi, Meghalaya, India", "lat": 25.9, "lng": 91.88},
    "location26": {"name": "Sohra, East Khasi Hills, Meghalaya, India", "lat": 25.2677, "lng": 91.7323},
    "location27": {"name": "Tura, West Garo Hills, Meghalaya, India", "lat": 25.5144, "lng": 90.2038},
    "location28": {"name": "Aizawl, Mizoram, India", "lat": 23.7271, "lng": 92.7176},
    "location29": {"name": "Chümoukedima, Nagaland, India", "lat": 25.86, "lng": 93.72},
    "location30": {"name": "Chungthang, Mangan, Sikkim, India", "lat": 27.6037, "lng": 88.6433},
    "location31": {"name": "Gangtok, Sikkim, India", "lat": 27.3389, "lng": 88.6065},
    "location32": {"name": "Mangan, Sikkim, India", "lat": 27.5096, "lng": 88.5364},
    "location33": {"name": "Agartala, West Tripura, Tripura, India", "lat": 23.8315, "lng": 91.2868},
    "location34": {"name": "Belonia, South Tripura, Tripura, India", "lat": 23.25, "lng": 91.45},
    "location35": {"name": "Dehradun, Uttarakhand, India", "lat": 30.3165, "lng": 78.0322},
    "location36": {"name": "Dharali, Uttarkashi, Uttarakhand, India", "lat": 31.04, "lng": 78.74},
    "location37": {"name": "Gopeshwar, Chamoli, Uttarakhand, India", "lat": 30.404, "lng": 79.32},
    "location38": {"name": "Sonprayag, Rudraprayag, Uttarakhand, India", "lat": 30.64, "lng": 79.07},
    "location39": {"name": "Syanachatti, Uttarkashi, Uttarakhand, India", "lat": 30.98, "lng": 78.47},
}

MONSOON_STATUS_BY_STATE = {
    "Arunachal Pradesh": "Yes",
    "Assam": "Yes",
    "Himachal Pradesh": "Yes",
    "Jammu & Kashmir": "Yes",
    "Manipur": "Yes",
    "Meghalaya": "Yes",
    "Mizoram": "Yes",
    "Nagaland": "Yes",
    "Sikkim": "Yes",
    "Tripura": "Yes",
    "Uttarakhand": "Yes",
}


# Static historical event data used only by the non-Core/Risk intelligence tiles.
# Each website location is explicitly tied to its corresponding Event ID so that
# matching does not depend on punctuation/spelling differences in the CSV Location field.
EVENT_ID_BY_LOCATION = {
    "location1": "AR26-001", "location2": "HP26-002", "location3": "HP26-003",
    "location4": "HP26-004", "location5": "AS26-005", "location6": "AS26-006",
    "location7": "UK26-007", "location8": "AS25-008", "location9": "AR25-009",
    "location10": "MG25-010", "location11": "UK25-011", "location12": "HP25-012",
    "location13": "JK25-013", "location14": "JK25-014", "location15": "AS24-015",
    "location16": "AR24-016", "location17": "SK24-017", "location18": "MN24-018",
    "location19": "TR24-019", "location20": "UK24-020", "location21": "HP24-021",
    "location22": "AR23-022", "location23": "AS23-023", "location24": "MG23-024",
    "location25": "HP23-025", "location26": "UK23-026", "location27": "SK23-027",
    "location28": "JK23-028", "location29": "AS22-029", "location30": "AR22-030",
    "location31": "MG22-031", "location32": "MN22-032", "location33": "SK22-033",
    "location34": "HP22-034", "location35": "UK22-035", "location36": "JK22-036",
    "location37": "MZ22-037", "location38": "NL22-038", "location39": "TR22-039",
}

TILE_COLUMNS = {
    "slope": "Slope(In degrees)",
    "river_distance": "River distance(metres)",
    "soil_texture": "Soil Texture",
    "soil_status": "Soil status",
    "soil_moisture": "Soil Moisture",
    "deforestation": "Deforestation",
    "forest_cover": "Forest cover",
    "forest_density": "Estimated trees/km²",
    "carbon_emissions": "CO2 emissions in tons/year",
    "encroachment": "Enroachment",
}


@lru_cache(maxsize=1)
def load_event_tile_data():
    dataset_path = Path(settings.BASE_DIR) / "data" / "raw" / "Raw_Events_Location.csv"
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return {row["Event ID"]: row for row in csv.DictReader(csv_file)}


def get_event_tile_data(location_key):
    event_id = EVENT_ID_BY_LOCATION.get(location_key)
    row = load_event_tile_data().get(event_id, {})
    slope_value = row.get(TILE_COLUMNS["slope"], "")
    slope_text = str(slope_value).lower()
    slope_numbers = []
    import re
    for match in re.findall(r"\\d+(?:\\.\\d+)?", slope_text):
        slope_numbers.append(float(match))
    slope_high = "near-vertical" in slope_text or "near vertical" in slope_text or any(value > 65 for value in slope_numbers)

    return {
        "event_id": event_id,
        "slope": slope_value,
        "slope_high": slope_high,
        "river_distance": row.get(TILE_COLUMNS["river_distance"], ""),
        "soil_texture": row.get(TILE_COLUMNS["soil_texture"], ""),
        "soil_status": row.get(TILE_COLUMNS["soil_status"], ""),
        "soil_moisture": row.get(TILE_COLUMNS["soil_moisture"], ""),
        "deforestation": row.get(TILE_COLUMNS["deforestation"], ""),
        "forest_cover": row.get(TILE_COLUMNS["forest_cover"], ""),
        "forest_density": row.get(TILE_COLUMNS["forest_density"], ""),
        "carbon_emissions": row.get(TILE_COLUMNS["carbon_emissions"], ""),
        "encroachment": row.get(TILE_COLUMNS["encroachment"], ""),
    }


def redirect_result(request):
    location_key = request.GET.get("location", "location1")
    location = LOCATIONS.get(location_key, LOCATIONS["location1"])
    lat, lon = location["lat"], location["lng"]

    weather = WeatherService().current(lat, lon)
    weather_outputs = {
        "rainfall_mm": weather.get("rainfall_24h_mm", weather.get("rainfall_mm")),
        "rainfall_7d_mm": rainfall_features(lat, lon).get("rainfall_7d_mm"),
        "temperature_c": weather.get("temperature_c"),
        "humidity": weather.get("humidity"),
    }

    risk = RiskService().current(lat, lon, weather=weather)
    event_tile_data = get_event_tile_data(location_key)
    state = location["name"].split(",")[-2].strip()
    monsoon_status = MONSOON_STATUS_BY_STATE.get(state, "No")
    return render(request, "redirect.html", {
        "location": location,
        "location_key": location_key,
        "locations": LOCATIONS,
        "weather": weather,
        "weather_outputs": weather_outputs,
        "risk": risk,
        "event_tile_data": event_tile_data,
        "monsoon_status": monsoon_status,
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
