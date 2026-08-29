/**
 * A single geographic coordinate pair used for map markers and
 * viewport state. Longitude/latitude order matches GeoJSON convention
 * (and the PostGIS PointField on the backend).
 */
export interface Coordinates {
  longitude: number;
  latitude: number;
}

/**
 * The full viewport state for the map: where it's centered and how
 * far zoomed in it is.
 */
export interface MapViewState {
  center: Coordinates;
  zoom: number;
}

/**
 * Minimal GeoJSON Feature Collection shape, sufficient for MapLibre
 * GL JS source data. Tighten geometry/property typing as your layer
 * definitions solidify.
 */
export interface GeoJsonFeature {
  type: "Feature";
  geometry: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  properties: Record<string, unknown>;
}

export interface GeoJsonFeatureCollection {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}
