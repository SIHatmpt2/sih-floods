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
from .location_data import EVENT_ID_BY_LOCATION, LOCATIONS

service = CoreService()


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


def _comment(text, tone="neutral"):
    return {"text": text, "tone": tone}


def _numeric_value(value):
    import re
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else None


def _text_tone(value):
    text = str(value or "").lower()
    if any(word in text for word in ("high", "severe", "heavy", "significant", "major", "poor")):
        return "negative"
    if any(word in text for word in ("low", "minimal", "normal", "good", "stable", "healthy", "dense")):
        return "positive"
    return "neutral"


def get_event_tile_data(location_key):
    event_id = EVENT_ID_BY_LOCATION.get(location_key)
    row = load_event_tile_data().get(event_id, {})
    slope_value = row.get(TILE_COLUMNS["slope"], "")
    slope_text = str(slope_value).lower()
    slope_numbers = []
    import re
    for match in re.findall(r"\d+(?:\.\d+)?", slope_text):
        slope_numbers.append(float(match))
    # 40–65° = orange; >65° or any near-vertical wording = red.
    slope_high = "near-vertical" in slope_text or "near vertical" in slope_text or any(value > 65 for value in slope_numbers)
    slope_medium = not slope_high and any(value >= 40 for value in slope_numbers)

    soil_moisture_value = row.get(TILE_COLUMNS["soil_moisture"], "")
    moisture_text = str(soil_moisture_value)
    moisture_match = re.search(r"^(.*?)\s*\(([^)]+)\)", moisture_text)
    soil_moisture_range = moisture_match.group(1).strip() if moisture_match else moisture_text
    soil_moisture_status = moisture_match.group(2).strip() if moisture_match else ""
    moisture_status_text = soil_moisture_status.lower()
    soil_moisture_very_very_high = "very very high" in moisture_status_text
    soil_moisture_very_high = not soil_moisture_very_very_high and "very high" in moisture_status_text
    soil_moisture_high = not soil_moisture_very_high and not soil_moisture_very_very_high and moisture_status_text == "high"

    carbon_value = row.get(TILE_COLUMNS["carbon_emissions"], "")
    carbon_digits = re.sub(r"[^0-9.]", "", str(carbon_value))
    try:
        carbon_numeric = float(carbon_digits) if carbon_digits else None
    except ValueError:
        carbon_numeric = None
    carbon_high = carbon_numeric is not None and carbon_numeric >= 30000
    carbon_medium = carbon_numeric is not None and 10000 < carbon_numeric < 30000

    river_numeric = _numeric_value(row.get(TILE_COLUMNS["river_distance"], ""))
    forest_cover_numeric = _numeric_value(row.get(TILE_COLUMNS["forest_cover"], ""))
    forest_density_numeric = _numeric_value(row.get(TILE_COLUMNS["forest_density"], ""))
    soil_status = row.get(TILE_COLUMNS["soil_status"], "")
    deforestation = row.get(TILE_COLUMNS["deforestation"], "")
    encroachment = row.get(TILE_COLUMNS["encroachment"], "")
    comments = {
        "slope": _comment(f"{slope_value} slope — steep terrain can rapidly increase surface runoff" if slope_high else f"{slope_value} slope — terrain can increase runoff during heavy rain" if slope_medium else f"{slope_value} slope — lower slope-driven runoff potential", "negative" if slope_high or slope_medium else "positive"),
        "river_distance": _comment(f"{river_numeric:g} m from river — direct flood exposure is elevated" if river_numeric is not None and river_numeric < 500 else f"{river_numeric:g} m from river — direct river exposure is lower" if river_numeric is not None else "River proximity unavailable", "negative" if river_numeric is not None and river_numeric < 500 else "positive" if river_numeric is not None else "neutral"),
        "soil_texture": _comment(f"{str(row.get(TILE_COLUMNS['soil_texture'], '')).strip()} soil texture — influences how quickly rainfall infiltrates versus becomes runoff" if str(row.get(TILE_COLUMNS["soil_texture"], "")).strip() else "Soil texture unavailable"),
        "soil_status": _comment(f"{str(soil_status).strip()} soil status — current condition can influence runoff response" if str(soil_status).strip() else "Soil status unavailable", _text_tone(soil_status)),
        "soil_moisture": _comment(f"{soil_moisture_range} ({soil_moisture_status}) — soil saturation can limit further rainfall infiltration" if soil_moisture_very_very_high or soil_moisture_very_high or soil_moisture_high else f"{soil_moisture_range} ({soil_moisture_status}) — greater infiltration capacity remains" if str(soil_moisture_range).strip() else "Soil moisture unavailable", "negative" if soil_moisture_very_very_high or soil_moisture_very_high or soil_moisture_high else "positive"),
        "carbon_emissions": _comment(f"{carbon_numeric:g} tons/year — indicates higher environmental pressure but is not a direct short-term flood trigger" if carbon_high or carbon_medium else f"{carbon_numeric:g} tons/year — lower environmental pressure; not a direct short-term flood trigger" if carbon_numeric is not None else "Carbon-emissions value unavailable", "negative" if carbon_high or carbon_medium else "positive"),
        "forest_cover": _comment(f"{forest_cover_numeric:g}% forest cover — provides stronger natural runoff buffering" if forest_cover_numeric is not None and forest_cover_numeric >= 50 else f"{forest_cover_numeric:g}% forest cover — reduced vegetation may increase surface runoff" if forest_cover_numeric is not None else "Forest-cover value unavailable", "positive" if forest_cover_numeric is not None and forest_cover_numeric >= 50 else "negative" if forest_cover_numeric is not None else "neutral"),
        "forest_density": _comment(f"{forest_density_numeric:g} trees/km² — dense vegetation provides stronger slope protection" if forest_density_numeric is not None and forest_density_numeric >= 30000 else f"{forest_density_numeric:g} trees/km² — lower vegetation density provides less slope protection" if forest_density_numeric is not None else "Forest-density value unavailable", "positive" if forest_density_numeric is not None and forest_density_numeric >= 30000 else "negative" if forest_density_numeric is not None else "neutral"),
        "deforestation": _comment(f"{str(deforestation).strip()} deforestation — vegetation loss can increase surface runoff" if _text_tone(deforestation) == "negative" else f"{str(deforestation).strip()} deforestation — natural vegetation cover is better retained" if _text_tone(deforestation) == "positive" else f"{str(deforestation).strip()} deforestation — runoff impact needs additional context" if str(deforestation).strip() else "Deforestation value unavailable", _text_tone(deforestation)),
        "encroachment": _comment(f"{str(encroachment).strip()} encroachment — drainage obstruction may worsen local flooding" if _text_tone(encroachment) == "negative" else f"{str(encroachment).strip()} encroachment — drainage obstruction is likely limited" if _text_tone(encroachment) == "positive" else f"{str(encroachment).strip()} encroachment — drainage impact needs additional context" if str(encroachment).strip() else "Encroachment value unavailable", _text_tone(encroachment)),
    }

    return {
        "event_id": event_id,
        "slope": slope_value,
        "slope_high": slope_high,
        "slope_medium": slope_medium,
        "river_distance": row.get(TILE_COLUMNS["river_distance"], ""),
        "soil_texture": row.get(TILE_COLUMNS["soil_texture"], ""),
        "soil_status": row.get(TILE_COLUMNS["soil_status"], ""),
        "soil_moisture": soil_moisture_value,
        "soil_moisture_range": soil_moisture_range,
        "soil_moisture_status": soil_moisture_status,
        "soil_moisture_high": soil_moisture_high,
        "soil_moisture_very_high": soil_moisture_very_high,
        "soil_moisture_very_very_high": soil_moisture_very_very_high,
        "carbon_emissions": carbon_value,
        "carbon_medium": carbon_medium,
        "carbon_high": carbon_high,
        "deforestation": row.get(TILE_COLUMNS["deforestation"], ""),
        "forest_cover": row.get(TILE_COLUMNS["forest_cover"], ""),
        "forest_density": row.get(TILE_COLUMNS["forest_density"], ""),
        "encroachment": row.get(TILE_COLUMNS["encroachment"], ""),
        "comments": comments,
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
    risk_score = _numeric_value(risk.get("risk_score"))
    risk_level_text = str(risk.get("risk_level") or "").lower()
    risk_comment = _comment(f"Risk score {risk_score:g}/100 — current conditions indicate elevated flood potential" if risk_score is not None and risk_score >= 70 else f"Risk score {risk_score:g}/100 — current conditions indicate lower flood potential" if risk_score is not None and risk_score < 40 else f"Risk score {risk_score:g}/100 — current conditions indicate moderate flood potential" if risk_score is not None else "Risk score unavailable", "negative" if risk_score is not None and risk_score >= 70 else "positive" if risk_score is not None and risk_score < 40 else "neutral")
    risk_level_comment = _comment(f"Risk level: {risk.get('risk_level')} — classification reflects the current flood-risk state" if risk.get("risk_level") else "Risk level unavailable", "negative" if any(word in risk_level_text for word in ("high", "severe", "very high")) else "positive" if any(word in risk_level_text for word in ("low", "safe")) else "neutral")
    rainfall_numeric = _numeric_value(weather_outputs["rainfall_mm"])
    humidity_numeric = _numeric_value(weather_outputs["humidity"])
    rainfall_comment = _comment(f"{rainfall_numeric:g} mm rainfall — heavy precipitation can rapidly increase flash-flood potential" if rainfall_numeric is not None and rainfall_numeric >= 50 else f"{rainfall_numeric:g} mm rainfall — lower immediate rainfall-driven flood pressure" if rainfall_numeric is not None and rainfall_numeric < 20 else f"{rainfall_numeric:g} mm rainfall — moderate precipitation warrants continued monitoring" if rainfall_numeric is not None else "Rainfall data unavailable", "negative" if rainfall_numeric is not None and rainfall_numeric >= 50 else "positive" if rainfall_numeric is not None and rainfall_numeric < 20 else "neutral")
    temperature_comment = _comment(f"{_numeric_value(weather_outputs['temperature_c']):g}°C — temperature has limited direct influence on immediate flood risk" if _numeric_value(weather_outputs["temperature_c"]) is not None else "Temperature data unavailable")
    humidity_comment = _comment(f"{humidity_numeric:g}% humidity — elevated atmospheric moisture can support heavy-rainfall conditions" if humidity_numeric is not None and humidity_numeric > 80 else f"{humidity_numeric:g}% humidity — lower atmospheric moisture contribution to immediate flood risk" if humidity_numeric is not None else "Humidity data unavailable", "negative" if humidity_numeric is not None and humidity_numeric > 80 else "positive" if humidity_numeric is not None else "neutral")
    state = location["name"].split(",")[-2].strip()
    monsoon_status = MONSOON_STATUS_BY_STATE.get(state, "No")
    monsoon_comment = _comment(f"Monsoon active in {state} — persistent moisture can support heavy rainfall" if monsoon_status == "Yes" else f"Monsoon influence is lower in {state} — this factor contributes less to current rainfall potential")
    return render(request, "redirect.html", {
        "location": location,
        "location_key": location_key,
        "locations": LOCATIONS,
        "weather": weather,
        "weather_outputs": weather_outputs,
        "risk": risk,
        "event_tile_data": event_tile_data,
        "monsoon_status": monsoon_status,
        "risk_comment": risk_comment,
        "risk_level_comment": risk_level_comment,
        "rainfall_comment": rainfall_comment,
        "temperature_comment": temperature_comment,
        "humidity_comment": humidity_comment,
        "monsoon_comment": monsoon_comment,
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
