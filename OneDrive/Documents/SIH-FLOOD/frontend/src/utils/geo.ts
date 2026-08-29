import type { Coordinates } from "../types/map";

export interface BoundingBox {
  minLongitude: number;
  minLatitude: number;
  maxLongitude: number;
  maxLatitude: number;
}

/**
 * Computes the bounding box that contains every coordinate in the
 * given list. Returns null for an empty list.
 */
export function getBoundingBox(points: Coordinates[]): BoundingBox | null {
  if (points.length === 0) {
    return null;
  }

  return points.reduce<BoundingBox>(
    (box, point) => ({
      minLongitude: Math.min(box.minLongitude, point.longitude),
      minLatitude: Math.min(box.minLatitude, point.latitude),
      maxLongitude: Math.max(box.maxLongitude, point.longitude),
      maxLatitude: Math.max(box.maxLatitude, point.latitude),
    }),
    {
      minLongitude: points[0].longitude,
      minLatitude: points[0].latitude,
      maxLongitude: points[0].longitude,
      maxLatitude: points[0].latitude,
    }
  );
}

/**
 * Formats a coordinate pair for display, e.g. "20.5937°N, 78.9629°E".
 */
export function formatCoordinates(
  coordinates: Coordinates,
  precision: number = 4
): string {
  const latDirection = coordinates.latitude >= 0 ? "N" : "S";
  const lonDirection = coordinates.longitude >= 0 ? "E" : "W";
  const lat = Math.abs(coordinates.latitude).toFixed(precision);
  const lon = Math.abs(coordinates.longitude).toFixed(precision);
  return `${lat}°${latDirection}, ${lon}°${lonDirection}`;
}
