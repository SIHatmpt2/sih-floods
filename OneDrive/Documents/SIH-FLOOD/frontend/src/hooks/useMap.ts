import { useCallback, useState } from "react";
import type { Coordinates, MapViewState } from "../types/map";
import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM } from "../utils/constants";

interface UseMapResult {
  center: Coordinates;
  zoom: number;
  setCenter: (center: Coordinates) => void;
  setZoom: (zoom: number) => void;
  reset: () => void;
}

/**
 * Manages map viewport state (center + zoom). Contains no UI markup -
 * pair this with whichever map rendering library you choose.
 */
export function useMap(
  initialState: MapViewState = {
    center: DEFAULT_MAP_CENTER,
    zoom: DEFAULT_MAP_ZOOM,
  }
): UseMapResult {
  const [center, setCenter] = useState<Coordinates>(initialState.center);
  const [zoom, setZoom] = useState<number>(initialState.zoom);

  const reset = useCallback(() => {
    setCenter(initialState.center);
    setZoom(initialState.zoom);
  }, [initialState.center, initialState.zoom]);

  return { center, zoom, setCenter, setZoom, reset };
}
