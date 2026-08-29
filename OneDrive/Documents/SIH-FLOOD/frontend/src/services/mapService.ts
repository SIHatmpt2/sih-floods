import type { ApiResponse } from "../types/api";
import type { GeoJsonFeatureCollection } from "../types/map";
import { apiClient } from "./api";

const MAP_LAYERS_PATH = "/map/layers/";

/**
 * Fetches GeoJSON layer data (e.g., flood extent polygons, river
 * networks) for rendering on a MapLibre GL map.
 */
export async function fetchMapLayers(): Promise<
  ApiResponse<GeoJsonFeatureCollection>
> {
  const response = await apiClient.get<GeoJsonFeatureCollection>(
    MAP_LAYERS_PATH
  );
  return { data: response.data, status: response.status };
}
