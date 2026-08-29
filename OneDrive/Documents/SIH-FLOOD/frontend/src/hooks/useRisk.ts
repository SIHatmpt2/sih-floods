import { useEffect, useState } from "react";
import type { FloodEvent } from "../types/risk";
import { RISK_EVENTS_ENDPOINT } from "../utils/constants";

interface UseRiskResult {
  events: FloodEvent[];
  isLoading: boolean;
  error: string | null;
}

/**
 * Fetches historical flood events from the Django backend.
 * Contains no UI markup - consumers decide how to render the data.
 */
export function useRisk(): UseRiskResult {
  const [events, setEvents] = useState<FloodEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchEvents() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(RISK_EVENTS_ENDPOINT, {
          signal: controller.signal,
          headers: { Accept: "application/json" },
        });

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const data: FloodEvent[] = await response.json();
        setEvents(data);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError(
          err instanceof Error ? err.message : "Failed to fetch flood events"
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchEvents();

    return () => controller.abort();
  }, []);

  return { events, isLoading, error };
}
