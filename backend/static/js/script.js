/* =========================
   FLOODINTEL
   GOOGLE MAPS + LOCATIONS
========================= */


/* =========================
   GOOGLE MAPS API KEY
========================= */

const GOOGLE_MAPS_API_KEY = "AIzaSyDjpeFM_t0zw1KLKi_taxZUDIyEViyzFEc";


/* =========================
   LOCATION DATA
========================= */

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


/* =========================
   MAP VARIABLES
========================= */

let map;


/* =========================
   INITIALIZE GOOGLE MAP
========================= */

function initMap() {

    const defaultCenter = {
        lat: 29.5,
        lng: 88.5
    };

    map = new google.maps.Map(
        document.getElementById("map"),
        {
            center: defaultCenter,
            zoom: 5,

            /* Satellite + map labels */
            mapTypeId: "hybrid",

            streetViewControl: false,
            mapTypeControl: false,
            fullscreenControl: true,

            /* Disable default zoom buttons */
            zoomControl: false
        }
    );

}


/* =========================
   LOCATION SELECTOR
========================= */

const locationSelect =
    document.getElementById("locationSelect");


locationSelect.addEventListener("change", function () {

    const selectedLocation =
        locations[this.value];

    if (!selectedLocation || !map) {
        return;
    }

    map.panTo({
        lat: selectedLocation.lat,
        lng: selectedLocation.lng
    });

    map.setZoom(8);

});


/* =========================
   CUSTOM ZOOM IN
========================= */

document
    .getElementById("zoomIn")
    .addEventListener("click", function () {

        if (!map) {
            return;
        }

        map.setZoom(map.getZoom() + 1);

    });


/* =========================
   CUSTOM ZOOM OUT
========================= */

document
    .getElementById("zoomOut")
    .addEventListener("click", function () {

        if (!map) {
            return;
        }

        map.setZoom(map.getZoom() - 1);

    });


/* =========================
   LOAD GOOGLE MAPS API
========================= */

const googleMapsScript =
    document.createElement("script");

googleMapsScript.src =
    "https://maps.googleapis.com/maps/api/js?key=" +
    GOOGLE_MAPS_API_KEY +
    "&callback=initMap";

googleMapsScript.async = true;
googleMapsScript.defer = true;

document.head.appendChild(googleMapsScript);