export type RiskLevel = "CRITICAL" | "HIGH" | "MODERATE" | "LOW";

export type Metrics = {
  risk: RiskLevel;
  rainfall: number;
  discharge: number;
  prob: number;
  time: string;
  status: string;
  driver1: number;
  driver2: number;
  driver3: number;
};

export const LOCATION_DATA: Record<string, string[]> = {
  Assam: ["Kamrup", "Nagaon", "Barpeta", "Dhubri"],
  Bihar: ["Patna", "Muzaffarpur", "Darbhanga", "Supaul"],
  "West Bengal": ["Malda", "Murshidabad", "Howrah", "Nadia"],
  Kerala: ["Alappuzha", "Ernakulam", "Kottayam", "Thrissur"],
};

export const MOCK_METRICS: Record<string, Metrics> = {
  Kamrup: { risk: "HIGH", rainfall: 127, discharge: 2450, prob: 84, time: "15 min ago", status: "CRITICAL MONITORING", driver1: 85, driver2: 92, driver3: 78 },
  Nagaon: { risk: "HIGH", rainfall: 95, discharge: 1900, prob: 72, time: "1 hour ago", status: "HIGH ALERT", driver1: 65, driver2: 75, driver3: 60 },
  Barpeta: { risk: "HIGH", rainfall: 110, discharge: 2100, prob: 78, time: "2 hours ago", status: "HIGH ALERT", driver1: 75, driver2: 85, driver3: 65 },
  Dhubri: { risk: "MODERATE", rainfall: 65, discharge: 1500, prob: 45, time: "3 hours ago", status: "ELEVATED RISK", driver1: 45, driver2: 55, driver3: 40 },
  default: { risk: "MODERATE", rainfall: 50, discharge: 1200, prob: 30, time: "10 min ago", status: "WATCH", driver1: 30, driver2: 40, driver3: 35 },
};

export const PRECIPITATION_DATA = [
  { name: "Mon", value: 45 }, { name: "Tue", value: 55 }, { name: "Wed", value: 72 },
  { name: "Thu", value: 105 }, { name: "Fri", value: 100 }, { name: "Sat", value: 75 }, { name: "Sun", value: 62 },
];

export const DISCHARGE_DATA = [
  { name: "Mon", value: 1500 }, { name: "Tue", value: 1400 }, { name: "Wed", value: 1550 },
  { name: "Thu", value: 2200 }, { name: "Fri", value: 2050 }, { name: "Sat", value: 1750 }, { name: "Sun", value: 1900 },
];

export const TABLE_DATA = [
  { zone: "Kamrup Metro (Guwahati Basin)", risk: "CRITICAL", residents: "142,500 Residents", telemetry: "15 mins ago · Live Telemetry" },
  { zone: "Nagaon Central Block", risk: "HIGH RISK", residents: "89,200 Residents", telemetry: "1 hour ago" },
  { zone: "Barpeta Outer Embankment", risk: "HIGH RISK", residents: "115,000 Residents", telemetry: "2 hours ago" },
  { zone: "Dhubri Border Corridor", risk: "MODERATE", residents: "64,000 Residents", telemetry: "3 hours ago" },
];

export const riskColors: Record<RiskLevel, string> = {
  CRITICAL: "#fb5b63",
  HIGH: "#ff9b54",
  MODERATE: "#e9c75f",
  LOW: "#36d2b1",
};
