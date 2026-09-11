const GOOGLE_MAPS_API_KEY = "AIzaSyDjpeFM_t0zw1KLKi_taxZUDIyEViyzFEc";

const locations = {
    location1: { name: "Assam Floodplain", lat: 26.2, lng: 92.9 },
    location2: { name: "Arunachal Pradesh", lat: 28.2, lng: 94.7 },
    location3: { name: "Sikkim", lat: 27.5, lng: 88.5 },
    location4: { name: "Nainital, Uttarakhand", lat: 29.3919, lng: 79.4542 },
    location5: { name: "Himachal Pradesh", lat: 31.8, lng: 77.2 },
    location6: { name: "Jammu & Kashmir", lat: 33.4, lng: 75.3 },
    location7: { name: "Ladakh", lat: 34.2, lng: 77.6 },
    location8: { name: "Northeast Hills", lat: 27.0, lng: 91.0 },
    location9: { name: "Terai Region", lat: 29.5, lng: 80.5 }
};

const params = new URLSearchParams(window.location.search);
const selectedKey = params.get("location") || "location1";
const selectedLocation = locations[selectedKey] || locations.location1;
let map;

const locationNameElement = document.getElementById("locationName");
if (locationNameElement) locationNameElement.textContent = selectedLocation.name;

function initMap() {
    const mapCenter = { lat: selectedLocation.lat, lng: selectedLocation.lng };
    map = new google.maps.Map(document.getElementById("map"), {
        center: mapCenter,
        zoom: 8,
        mapTypeId: "hybrid",
        streetViewControl: false,
        mapTypeControl: false,
        fullscreenControl: true,
        zoomControl: false,
        clickableIcons: false
    });
    new google.maps.Marker({ position: mapCenter, map, title: selectedLocation.name });
}

window.initMap = initMap;
document.getElementById("zoomIn")?.addEventListener("click", () => map && map.setZoom(map.getZoom() + 1));
document.getElementById("zoomOut")?.addEventListener("click", () => map && map.setZoom(map.getZoom() - 1));

const googleMapsScript = document.createElement("script");
googleMapsScript.src = "https://maps.googleapis.com/maps/api/js?key=" + GOOGLE_MAPS_API_KEY + "&callback=initMap";
googleMapsScript.async = true;
googleMapsScript.defer = true;
document.head.appendChild(googleMapsScript);
