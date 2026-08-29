import type { Coordinates } from "./map";

/**
 * Value sets mirrored from the Django backend's TextChoices.
 * Keep in sync with backend/flood/models.py (PastFloodEvent).
 */
export type GlofRiskLevel = "LOW" | "MOD" | "HIGH" | "UNK";
export type RegularityLevel = "RARE" | "OCC" | "FREQ" | "ANN";
export type SeverityLevel = "AN" | "SV" | "EX";

/**
 * Shape of a single historical flood event as returned by
 * GET /api/risk/events/
 */
export interface FloodEvent {
  event_id: string;
  location: string;
  date: string; // ISO 8601 date string, e.g. "2026-07-14"
  time_period: number | null;

  temp_change: number | null;
  rain_3weeks: number | null;
  wind_before: number | null;
  wind_after: number | null;

  glacier_impact: boolean;
  glof_risk: GlofRiskLevel | null;

  regularity: RegularityLevel | null;
  interval: string | null;

  snowmelt: boolean;
  cloudburst: boolean;
  steep_topography: boolean;
  landslide: boolean;
  deforestation: boolean;
  encroachment: boolean;

  major_causes: string | null;

  casualties: number | null;
  victims: number | null;
  peak_waterlevel: number | null;
  severity_index: SeverityLevel | null;

  coordinates: Coordinates | null;
}
