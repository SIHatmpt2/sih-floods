/* =====================================
   FLOODINTEL
   REDIRECT PAGE
   GOOGLE MAPS + LOCATION DATA
===================================== */


/* =====================================
   GOOGLE MAPS API KEY
===================================== */

const GOOGLE_MAPS_API_KEY =
    "AIzaSyDjpeFM_t0zw1KLKi_taxZUDIyEViyzFEc";


/* =====================================
   LOCATIONS
   Same coordinates as landing page
===================================== */

const locations = {

    location1: {
        name: "Location 1",
        lat: 26.2,
        lng: 92.9
    },

    location2: {
        name: "Location 2",
        lat: 28.2,
        lng: 94.7
    },

    location3: {
        name: "Location 3",
        lat: 27.5,
        lng: 88.5
    },

    location4: {
        name: "Location 4",
        lat: 30.1,
        lng: 79.2
    },

    location5: {
        name: "Location 5",
        lat: 31.8,
        lng: 77.2
    },

    location6: {
        name: "Location 6",
        lat: 33.4,
        lng: 75.3
    },

    location7: {
        name: "Location 7",
        lat: 34.2,
        lng: 77.6
    },

    location8: {
        name: "Location 8",
        lat: 27.0,
        lng: 91.0
    },

    location9: {
        name: "Location 9",
        lat: 29.5,
        lng: 80.5
    },

    location10: {
        name: "Location 10",
        lat: 25.5,
        lng: 89.5
    }

};


/* =====================================
   GET SELECTED LOCATION
===================================== */

const params =
    new URLSearchParams(window.location.search);

const selectedKey =
    params.get("location") || "location1";

const selectedLocation =
    locations[selectedKey] || locations.location1;


/* =====================================
   MAP VARIABLE
===================================== */

let map;


/* =====================================
   UPDATE LOCATION NAME
===================================== */

const locationNameElement =
    document.getElementById("locationName");

if (locationNameElement) {

    locationNameElement.textContent =
        selectedLocation.name;

}


/* =====================================
   INITIALIZE GOOGLE MAP
===================================== */

function initMap() {

    const mapCenter = {
        lat: selectedLocation.lat,
        lng: selectedLocation.lng
    };


    map = new google.maps.Map(
        document.getElementById("map"),
        {

            center: mapCenter,

            zoom: 8,

            mapTypeId: "hybrid",

            streetViewControl: false,

            mapTypeControl: false,

            fullscreenControl: true,

            zoomControl: false,

            clickableIcons: false

        }
    );


    /* =================================
       LOCATION MARKER
    ================================= */

    new google.maps.Marker({

        position: mapCenter,

        map: map,

        title: selectedLocation.name

    });

}


/* =====================================
   MAKE INITMAP AVAILABLE GLOBALLY
===================================== */

window.initMap = initMap;


/* =====================================
   CUSTOM ZOOM IN
===================================== */

const zoomInButton =
    document.getElementById("zoomIn");

if (zoomInButton) {

    zoomInButton.addEventListener(
        "click",
        function () {

            if (!map) return;

            const currentZoom =
                map.getZoom();

            map.setZoom(currentZoom + 1);

        }
    );

}


/* =====================================
   CUSTOM ZOOM OUT
===================================== */

const zoomOutButton =
    document.getElementById("zoomOut");

if (zoomOutButton) {

    zoomOutButton.addEventListener(
        "click",
        function () {

            if (!map) return;

            const currentZoom =
                map.getZoom();

            map.setZoom(currentZoom - 1);

        }
    );

}


/* =====================================
   LOAD GOOGLE MAPS API
===================================== */

const googleMapsScript =
    document.createElement("script");


googleMapsScript.src =
    "https://maps.googleapis.com/maps/api/js?key=" +
    GOOGLE_MAPS_API_KEY +
    "&callback=initMap";


googleMapsScript.async = true;

googleMapsScript.defer = true;


document.head.appendChild(
    googleMapsScript
);