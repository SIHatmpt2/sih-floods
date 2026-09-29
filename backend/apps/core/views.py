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
    if any(word in text for word in (
        "saturated", "waterlogged", "high", "severe", "heavy",
        "significant", "major", "poor",
    )):
        return "negative"
    if any(word in text for word in (
        "low", "minimal", "normal", "good", "stable", "healthy", "dense",
    )):
        return "positive"
    return "neutral"


def _impact_tone(value, negative_terms, positive_terms=()):
    text = str(value or "").lower()
    if any(term in text for term in negative_terms):
        return "negative"
    if any(term in text for term in positive_terms):
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
    soil_texture = str(row.get(TILE_COLUMNS["soil_texture"], "")).strip()
    soil_status = str(row.get(TILE_COLUMNS["soil_status"], "")).strip()
    deforestation = str(row.get(TILE_COLUMNS["deforestation"], "")).strip()
    encroachment = str(row.get(TILE_COLUMNS["encroachment"], "")).strip()

    soil_texture_text = soil_texture.lower()
    if "rocky" in soil_texture_text or "very shallow" in soil_texture_text:
        soil_texture_comment = "Shallow rocky soil has limited storage capacity, so intense rain can shift quickly to runoff."
    elif "clay" in soil_texture_text:
        soil_texture_comment = "Clay-rich soil can slow infiltration as it wets, increasing runoff once storage fills."
    elif "silt" in soil_texture_text:
        soil_texture_comment = "Silt-rich soil can become runoff-prone once rainfall exceeds its infiltration capacity."
    elif "sand" in soil_texture_text:
        soil_texture_comment = "Sandy soil can infiltrate quickly, but intense rain can exceed its infiltration capacity."
    elif soil_texture:
        soil_texture_comment = "The soil can absorb rainfall, but runoff increases once rainfall exceeds infiltration capacity."
    else:
        soil_texture_comment = "Soil texture information is unavailable."

    soil_status_text = soil_status.lower()
    if "waterlogged" in soil_status_text:
        soil_status_comment = "Waterlogged ground has little infiltration capacity, increasing standing water and runoff persistence."
    elif "saturated" in soil_status_text:
        soil_status_comment = "Saturated soil has little remaining storage, so additional rain is more likely to become runoff."
    elif "wet" in soil_status_text:
        soil_status_comment = "Wet topsoil retains some storage, but intense rain can quickly increase runoff."
    else:
        soil_status_comment = "The recorded soil condition provides limited evidence about current runoff response."

    deforestation_tone = _impact_tone(
        deforestation,
        negative_terms=(
            "clearing", "cutting", "fragmentation", "blasting", "logging", "degraded",
            "thinning", "removal", "slicing", "mining", "quarrying", "felling",
            "human-induced", "loss of", "stripped", "contributing factor",
            "compounding factor", "accelerating factor", "amplifying", "runoff velocities",
            "vegetation", "tree-clearing",
        ),
        positive_terms=("retained", "restored", "reforestation", "regenerated", "intact"),
    )
    encroachment_tone = _impact_tone(
        encroachment,
        negative_terms=(
            "high", "critical", "extreme", "directly", "adjacent", "built", "constructed",
            "encroached", "settlements", "structures", "expansion", "floodplain",
            "riverbank", "drainage", "channel", "stream", "corridor", "camp", "hotels",
        ),
        positive_terms=("limited", "minimal", "none", "absent", "setback"),
    )

    comments = {
        "slope": _comment(
            "This very steep terrain can accelerate runoff and increase slope-failure susceptibility during intense rain."
            if slope_high
            else "This steep terrain can accelerate runoff during intense rain."
            if slope_medium
            else "This terrain generally produces slower surface runoff.",
            "negative" if slope_high or slope_medium else "positive",
        ),
        "river_distance": _comment(
            "Close river proximity increases exposure to overbank flooding and rapid channel response."
            if river_numeric is not None and river_numeric < 500
            else "Greater separation generally reduces direct river-flood exposure."
            if river_numeric is not None
            else "River proximity information is unavailable.",
            "negative" if river_numeric is not None and river_numeric < 500 else "positive" if river_numeric is not None else "neutral",
        ),
        "soil_texture": _comment(
            soil_texture_comment,
            "negative" if ("rocky" in soil_texture_text or "very shallow" in soil_texture_text or "clay" in soil_texture_text) else "positive" if "sand" in soil_texture_text else "neutral",
        ),
        "soil_status": _comment(
            soil_status_comment,
            "negative" if any(term in soil_status_text for term in ("saturated", "waterlogged")) else "neutral",
        ),
        "soil_moisture": _comment(
            "High soil moisture leaves less pore space for incoming rainfall, increasing rapid runoff potential."
            if soil_moisture_very_very_high or soil_moisture_very_high or soil_moisture_high
            else "Lower soil moisture leaves more capacity to absorb additional rainfall."
            if str(soil_moisture_range).strip()
            else "Soil moisture information is unavailable.",
            "negative" if soil_moisture_very_very_high or soil_moisture_very_high or soil_moisture_high else "positive",
        ),
        "carbon_emissions": _comment(
            "Higher carbon emissions indicate greater long-term environmental pressure in this area."
            if carbon_high
            else "Moderate carbon emissions indicate some long-term environmental pressure in this area."
            if carbon_medium
            else "Lower carbon emissions indicate lower long-term environmental pressure in this area."
            if carbon_numeric is not None
            else "Carbon-emissions information is unavailable.",
            "negative" if carbon_high or carbon_medium else "positive" if carbon_numeric is not None else "neutral",
        ),
        "forest_cover": _comment(
            "Higher forest cover can intercept rainfall and reinforce slopes, helping buffer runoff."
            if forest_cover_numeric is not None and forest_cover_numeric >= 50
            else "Lower forest cover provides less interception and slope reinforcement, allowing faster runoff."
            if forest_cover_numeric is not None
            else "Forest-cover information is unavailable.",
            "positive" if forest_cover_numeric is not None and forest_cover_numeric >= 50 else "negative" if forest_cover_numeric is not None else "neutral",
        ),
        "forest_density": _comment(
            "Dense tree cover can improve slope stability and slow surface runoff."
            if forest_density_numeric is not None and forest_density_numeric >= 30000
            else "Lower tree density provides less root reinforcement and rainfall interception."
            if forest_density_numeric is not None
            else "Forest-density information is unavailable.",
            "positive" if forest_density_numeric is not None and forest_density_numeric >= 30000 else "negative" if forest_density_numeric is not None else "neutral",
        ),
        "deforestation": _comment(
            "Vegetation loss can reduce root reinforcement and increase surface runoff."
            if deforestation_tone == "negative"
            else "Better vegetation retention can improve slope protection and runoff buffering."
            if deforestation_tone == "positive"
            else "The observation does not quantify a clear flood-response effect."
            if deforestation
            else "Deforestation information is unavailable.",
            deforestation_tone,
        ),
        "encroachment": _comment(
            "Construction within natural drainage corridors can obstruct flow and increase local flood exposure."
            if encroachment_tone == "negative"
            else "Limited encroachment leaves more natural drainage capacity."
            if encroachment_tone == "positive"
            else "The observation does not clearly quantify drainage obstruction."
            if encroachment
            else "Encroachment information is unavailable.",
            encroachment_tone,
        ),
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
    risk_comment = _comment(
        "There is a higher risk of flooding at this location."
        if risk_score is not None and risk_score >= 70
        else "There is a lower risk of flooding at this location."
        if risk_score is not None and risk_score < 40
        else "There is a moderate risk of flooding at this location."
        if risk_score is not None
        else "Risk score information is unavailable.",
        "negative" if risk_score is not None and risk_score >= 70 else "positive" if risk_score is not None and risk_score < 40 else "neutral",
    )
    risk_level_comment = _comment(
        "The current flood-risk level is high at this location."
        if any(word in risk_level_text for word in ("high", "severe", "very high"))
        else "The current flood-risk level is low at this location."
        if any(word in risk_level_text for word in ("low", "safe"))
        else "The current flood-risk level is moderate at this location."
        if risk.get("risk_level")
        else "Risk-level information is unavailable.",
        "negative" if any(word in risk_level_text for word in ("high", "severe", "very high")) else "positive" if any(word in risk_level_text for word in ("low", "safe")) else "neutral",
    )
    rainfall_numeric = _numeric_value(weather_outputs["rainfall_mm"])
    humidity_numeric = _numeric_value(weather_outputs["humidity"])
    rainfall_comment = _comment(
        "Recent rainfall can rapidly increase runoff and flash-flood potential."
        if rainfall_numeric is not None and rainfall_numeric >= 50
        else "Recent rainfall adds short-term runoff pressure; further accumulation could increase risk."
        if rainfall_numeric is not None and rainfall_numeric >= 20
        else "Recent rainfall is contributing little to immediate runoff pressure."
        if rainfall_numeric is not None
        else "Rainfall information is unavailable.",
        "negative" if rainfall_numeric is not None and rainfall_numeric >= 50 else "neutral" if rainfall_numeric is not None and rainfall_numeric >= 20 else "positive" if rainfall_numeric is not None else "neutral",
    )
    temperature_numeric = _numeric_value(weather_outputs["temperature_c"])
    temperature_comment = _comment(
        "Current temperature can influence atmospheric instability, but rainfall remains the stronger immediate flood driver."
        if temperature_numeric is not None
        else "Temperature information is unavailable.",
        "neutral" if temperature_numeric is not None else "neutral",
    )
    humidity_comment = _comment(
        "High atmospheric moisture can support heavy-rainfall development."
        if humidity_numeric is not None and humidity_numeric > 80
        else "Moist atmospheric conditions can support rainfall, but humidity alone does not indicate flooding."
        if humidity_numeric is not None and humidity_numeric >= 60
        else "Humidity alone provides limited evidence of immediate heavy-rainfall development."
        if humidity_numeric is not None
        else "Humidity information is unavailable.",
        "negative" if humidity_numeric is not None and humidity_numeric > 80 else "neutral" if humidity_numeric is not None and humidity_numeric >= 60 else "positive" if humidity_numeric is not None else "neutral",
    )
    state = location["name"].split(",")[-2].strip()
    monsoon_status = MONSOON_STATUS_BY_STATE.get(state, "No")
    monsoon_comment = _comment(
        "Active monsoon conditions provide a persistent moisture source for heavy rainfall."
        if monsoon_status == "Yes"
        else "Outside the active monsoon season, seasonal moisture contribution is generally lower.",
        "negative" if monsoon_status == "Yes" else "positive",
    )
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
