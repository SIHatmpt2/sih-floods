import type { ApiResponse } from "../types/api";
import type { FloodEvent } from "../types/risk";
import { apiClient } from "./api";

const RISK_EVENTS_PATH = "/risk/events/";

/**
 * Fetches all historical flood events.
 */
export async function fetchRiskEvents(): Promise<ApiResponse<FloodEvent[]>> {
  const response = await apiClient.get<FloodEvent[]>(RISK_EVENTS_PATH);
  return { data: response.data, status: response.status };
}

/**
 * Fetches a single flood event by its event_id.
 */
export async function fetchRiskEventById(
  eventId: string
): Promise<ApiResponse<FloodEvent>> {
  const response = await apiClient.get<FloodEvent>(
    `${RISK_EVENTS_PATH}${eventId}/`
  );
  return { data: response.data, status: response.status };
}
