const locations = window.FLOODINTEL_LOCATIONS || {};
let map;
let marker;

function getSelectedLocation() {
    const select = document.getElementById("locationSelect");
    return locations[select?.value] || Object.values(locations)[0] || null;
}

function createSelectedMarker(center, name) {
    const icon = L.divIcon({
        className: "selected-location-marker",
        html: '<div style="width:30px;height:30px;border-radius:50%;background:rgba(0,121,254,.25);display:flex;align-items:center;justify-content:center;animation:markerPulse 1.8s ease-out infinite;"><div style="width:12px;height:12px;border-radius:50%;background:#0079FE;border:3px solid #ffffff;box-shadow:0 1px 5px rgba(0,0,0,.35);"></div></div>',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
        popupAnchor: [0, -15]
    });

    if (marker) {
        marker.setLatLng(center);
        marker.setIcon(icon);
        marker.bindPopup(name);
    } else {
        marker = L.marker(center, { icon }).addTo(map);
        marker.bindPopup(name);
    }

    marker.openPopup();
}

function focusLocation(selected, animate = true) {
    if (!map || !selected) return;

    const center = [Number(selected.lat), Number(selected.lng)];

    map.setView(center, 11, {
        animate: animate,
        duration: 0.8
    });

    createSelectedMarker(center, selected.name);
}

function initMap() {
    const mapElement = document.getElementById("map");
    const selected = getSelectedLocation();

    if (!mapElement || !selected || typeof L === "undefined") return;

    if (map) {
        map.remove();
        marker = null;
    }

    const center = [Number(selected.lat), Number(selected.lng)];

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

    createSelectedMarker(center, selected.name);

    window.setTimeout(() => map?.invalidateSize(), 0);
}

window.initFloodIntelMap = initMap;

const locationSelect = document.getElementById("locationSelect");

if (locationSelect) {
    locationSelect.addEventListener("change", function () {
        const selectedLocation = locations[this.value];

        if (!selectedLocation) return;

        focusLocation(selectedLocation, true);

        const url = new URL(window.location.href);
        url.searchParams.set("location", this.value);
        window.location.assign(url.toString());
    });
}

document.getElementById("zoomIn")?.addEventListener("click", () => {
    map?.zoomIn();
});

document.getElementById("zoomOut")?.addEventListener("click", () => {
    map?.zoomOut();
});

document.addEventListener("DOMContentLoaded", initMap);

const markerStyle = document.createElement("style");
markerStyle.textContent = `@keyframes markerPulse {0%{transform:scale(.7);opacity:1}70%{transform:scale(1.25);opacity:.45}100%{transform:scale(1.4);opacity:0}}`;
document.head.appendChild(markerStyle);
