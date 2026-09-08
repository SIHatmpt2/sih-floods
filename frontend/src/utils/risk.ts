import { RiskLevel, riskColors } from "../data/floodWatchData";

export function getRiskColor(level: RiskLevel) {
  return riskColors[level];
}

export function getRiskLabel(level: RiskLevel) {
  return level === "HIGH" ? "HIGH RISK" : level;
}

export function formatNumber(value: number) {
  return value.toLocaleString("en-IN");
}
