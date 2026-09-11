const locations = window.FLOODINTEL_LOCATIONS || {};
let map;
let marker;

function getSelectedLocation() {
    const select = document.getElementById("locationSelect");
    return locations[select?.value] || Object.values(locations)[0] || null;
}

function initMap() {
    const mapElement = document.getElementById("map");
    const selected = getSelectedLocation();
    if (!mapElement || !selected || typeof L === "undefined") return;

    if (map) map.remove();

    const center = [Number(selected.lat), Number(selected.lng)];
    map = L.map(mapElement, {
        zoomControl: false,
        attributionControl: true,
        scrollWheelZoom: true
    }).setView(center, 8);

    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
        maxZoom: 19,
        attribution: "Tiles &copy; Esri"
    }).addTo(map);

    marker = L.marker(center).addTo(map).bindPopup(selected.name);
    marker.openPopup();
    window.setTimeout(() => map?.invalidateSize(), 0);
}

window.initFloodIntelMap = initMap;

const locationSelect = document.getElementById("locationSelect");
if (locationSelect) {
    locationSelect.addEventListener("change", function () {
        const selectedLocation = locations[this.value];
        if (!selectedLocation) return;

        if (map) {
            const center = [Number(selectedLocation.lat), Number(selectedLocation.lng)];
            map.setView(center, 8, { animate: true });
            marker?.setLatLng(center).bindPopup(selectedLocation.name).openPopup();
        }

        const url = new URL(window.location.href);
        url.searchParams.set("location", this.value);
        window.location.assign(url.toString());
    });
}

document.getElementById("zoomIn")?.addEventListener("click", () => map?.zoomIn());
document.getElementById("zoomOut")?.addEventListener("click", () => map?.zoomOut());

document.addEventListener("DOMContentLoaded", initMap);
