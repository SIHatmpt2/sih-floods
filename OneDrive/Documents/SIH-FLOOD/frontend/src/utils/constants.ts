import type { Variants } from "framer-motion";
import type { Coordinates } from "../types/map";

/* ------------------------------------------------------------------ */
/* API                                                                 */
/* ------------------------------------------------------------------ */
export const API_BASE_URL = "http://localhost:8000/api";
export const RISK_EVENTS_ENDPOINT = `${API_BASE_URL}/risk/events/`;

/* ------------------------------------------------------------------ */
/* Map defaults                                                        */
/* ------------------------------------------------------------------ */
export const DEFAULT_MAP_ZOOM = 5;

export const DEFAULT_MAP_CENTER: Coordinates = {
  longitude: 78.9629,
  latitude: 20.5937,
}; // Roughly centered on India; adjust to your region of interest

/* ------------------------------------------------------------------ */
/* Severity styling                                                    */
/* ------------------------------------------------------------------ */
export const SEVERITY_COLORS: Record<string, string> = {
  AN: "#facc15", // Above Normal
  SV: "#f97316", // Severe
  EX: "#dc2626", // Extreme
};

/* ------------------------------------------------------------------ */
/* Framer Motion variants                                              */
/* ------------------------------------------------------------------ */
export const cardFadeIn: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" },
  },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

export const pulseAlert: Variants = {
  initial: { scale: 1, opacity: 1 },
  animate: {
    scale: [1, 1.08, 1],
    opacity: [1, 0.7, 1],
    transition: {
      duration: 1.4,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
};
