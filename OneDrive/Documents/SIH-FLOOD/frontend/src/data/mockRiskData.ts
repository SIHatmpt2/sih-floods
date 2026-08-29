import type { FloodEvent } from "../types/risk";

/**
 * Hand-authored mock flood events for local development and UI
 * testing. Every field on FloodEvent is populated (no nulls) so
 * components can be built and styled before the backend is wired up.
 * Locations are real flood-prone regions in the Indian Himalaya and
 * foothills; the specific figures are illustrative, not records of
 * any single real disaster.
 */
export const mockFloodEvents: FloodEvent[] = [
  {
    event_id: "FLD-2024-014",
    location: "South Lhonak Lake Basin, Mangan, Sikkim",
    date: "2024-09-18",
    time_period: 3,

    temp_change: 2.1,
    rain_3weeks: 210.5,
    wind_before: 12.4,
    wind_after: 28.7,

    glacier_impact: true,
    glof_risk: "HIGH",

    regularity: "OCC",
    interval: "5-7 years",

    snowmelt: true,
    cloudburst: false,
    steep_topography: true,
    landslide: true,
    deforestation: false,
    encroachment: true,

    major_causes:
      "Moraine-dammed lake breach following prolonged glacial melt and an upstream landslide surge, compounded by unregulated settlement in the floodplain.",

    casualties: 38,
    victims: 4200,
    peak_waterlevel: 6.8,
    severity_index: "EX",

    coordinates: { longitude: 88.1975, latitude: 27.8942 },
  },
  {
    event_id: "FLD-2023-007",
    location: "Kedarnath Valley, Rudraprayag, Uttarakhand",
    date: "2023-07-11",
    time_period: 2,

    temp_change: 1.4,
    rain_3weeks: 340.2,
    wind_before: 9.8,
    wind_after: 22.3,

    glacier_impact: false,
    glof_risk: "LOW",

    regularity: "FREQ",
    interval: "1-2 years",

    snowmelt: false,
    cloudburst: true,
    steep_topography: true,
    landslide: true,
    deforestation: true,
    encroachment: true,

    major_causes:
      "Intense cloudburst over an already saturated catchment triggered flash flooding and debris flow through a narrow valley lined with unregulated construction.",

    casualties: 22,
    victims: 1850,
    peak_waterlevel: 4.3,
    severity_index: "SV",

    coordinates: { longitude: 79.0669, latitude: 30.7346 },
  },
  {
    event_id: "FLD-2022-021",
    location: "Teesta River Basin, Kalimpong, West Bengal",
    date: "2022-08-25",
    time_period: 6,

    temp_change: 0.8,
    rain_3weeks: 495.6,
    wind_before: 15.2,
    wind_after: 19.5,

    glacier_impact: false,
    glof_risk: "UNK",

    regularity: "ANN",
    interval: "Annually, during monsoon season",

    snowmelt: false,
    cloudburst: false,
    steep_topography: false,
    landslide: false,
    deforestation: true,
    encroachment: true,

    major_causes:
      "Sustained monsoon rainfall combined with an upstream dam release and floodplain encroachment led to prolonged inundation of low-lying settlements.",

    casualties: 6,
    victims: 9700,
    peak_waterlevel: 3.1,
    severity_index: "AN",

    coordinates: { longitude: 88.4772, latitude: 27.0645 },
  },
];
