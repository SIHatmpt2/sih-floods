const locations = window.FLOODINTEL_LOCATIONS || {};
const params = new URLSearchParams(window.location.search);
const selectedKey = params.get("location") || "location1";
const selectedLocation = locations[selectedKey] || Object.values(locations)[0] || null;

const riskData = window.FLOODINTEL_RISK || {};

let map;
let marker;
let riskCircle;

const locationNameElement = document.getElementById("locationName");

if (locationNameElement && selectedLocation) {
    locationNameElement.textContent = selectedLocation.name;
}

function getRiskColor(level) {
    switch ((level || "").toLowerCase()) {
        case "low":
            return "#1f8a4c";
        case "moderate":
            return "#d97706";
        case "high":
            return "#dc2626";
        case "severe":
        case "very high":
            return "#6b1111";
        default:
            return "#61758d";
    }
}

function createSelectedMarker(center, name) {
    const icon = L.divIcon({
        className: "selected-location-marker",
        html: '<div class="marker-pulse"><div class="marker-dot"></div></div>',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
        popupAnchor: [0, -15]
    });

    marker = L.marker(center, { icon }).addTo(map);

    const data = window.FLOODINTEL_RISK || {};

    const popupContent = `
        <strong>${name}</strong><br>
        Risk Score: ${data.score ? Number(data.score).toFixed(1) + "/100" : "—"}<br>
        Risk Level: ${data.level || "—"}<br>
        Rainfall (24h): ${data.rainfall24h ? data.rainfall24h + " mm" : "—"}<br>
        Rainfall (7d): ${data.rainfall7d ? data.rainfall7d + " mm" : "—"}
    `;

    marker.bindPopup(popupContent).openPopup();
}

function createRiskCircle(center) {
    const riskColor = getRiskColor(riskData.level);

    if (riskCircle) {
        riskCircle.remove();
    }

    riskCircle = L.circle(center, {
        radius: 1500,
        color: riskColor,
        fillColor: riskColor,
        fillOpacity: 0.18,
        weight: 2
    }).addTo(map);
}

function addRiskLegend() {
    const legend = L.control({ position: "bottomright" });

    legend.onAdd = function () {
        const div = L.DomUtil.create("div", "risk-legend");

        div.innerHTML = `
            <div class="risk-legend-title">Risk Level</div>
            <div><span class="risk-dot low"></span> Low</div>
            <div><span class="risk-dot moderate"></span> Moderate</div>
            <div><span class="risk-dot high"></span> High</div>
            <div><span class="risk-dot severe"></span> Severe</div>
        `;

        return div;
    };

    legend.addTo(map);
}

function initMap() {
    const mapElement = document.getElementById("map");

    if (!mapElement || !selectedLocation || typeof L === "undefined") {
        return;
    }

    if (map) {
        map.remove();
        marker = null;
        riskCircle = null;
    }

    const center = [
        Number(selectedLocation.lat),
        Number(selectedLocation.lng)
    ];

    map = L.map(mapElement, {
        zoomControl: false,
        attributionControl: true,
        scrollWheelZoom: true
    }).setView(center, 11);

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        {
            maxZoom: 19,
            attribution: "Tiles &copy; Esri"
        }
    ).addTo(map);

    createRiskCircle(center);
    createSelectedMarker(center, selectedLocation.name);
    addRiskLegend();

    window.setTimeout(() => map?.invalidateSize(), 0);
}

window.initFloodIntelMap = initMap;

document.getElementById("zoomIn")?.addEventListener("click", () => map?.zoomIn());
document.getElementById("zoomOut")?.addEventListener("click", () => map?.zoomOut());
document.addEventListener("DOMContentLoaded", initMap);
