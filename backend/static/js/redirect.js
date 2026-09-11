const locations = window.FLOODINTEL_LOCATIONS || {};
const params = new URLSearchParams(window.location.search);
const selectedKey = params.get("location") || "location1";
const selectedLocation = locations[selectedKey] || Object.values(locations)[0] || null;
let map;

const locationNameElement = document.getElementById("locationName");
if (locationNameElement && selectedLocation) {
    locationNameElement.textContent = selectedLocation.name;
}

function initMap() {
    const mapElement = document.getElementById("map");
    if (!mapElement || !selectedLocation || typeof L === "undefined") return;

    if (map) map.remove();

    const center = [Number(selectedLocation.lat), Number(selectedLocation.lng)];
    map = L.map(mapElement, {
        zoomControl: false,
        attributionControl: true,
        scrollWheelZoom: true
    }).setView(center, 8);

    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
        maxZoom: 19,
        attribution: "Tiles &copy; Esri"
    }).addTo(map);

    L.marker(center).addTo(map).bindPopup(selectedLocation.name).openPopup();
    window.setTimeout(() => map?.invalidateSize(), 0);
}

window.initFloodIntelMap = initMap;

document.getElementById("zoomIn")?.addEventListener("click", () => map?.zoomIn());
document.getElementById("zoomOut")?.addEventListener("click", () => map?.zoomOut());
document.addEventListener("DOMContentLoaded", initMap);
