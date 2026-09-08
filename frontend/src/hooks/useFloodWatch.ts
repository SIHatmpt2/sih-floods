import { useMemo, useState } from "react";
import { LOCATION_DATA, MOCK_METRICS, Metrics } from "../data/floodWatchData";

export function useFloodWatch() {
  const [selectedState, setSelectedState] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [activeTab, setActiveTab] = useState("risk");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const metrics: Metrics = useMemo(
    () => MOCK_METRICS[selectedDistrict] ?? MOCK_METRICS.default,
    [selectedDistrict],
  );

  const districts = selectedState ? LOCATION_DATA[selectedState] ?? [] : [];

  function selectState(state: string) {
    setSelectedState(state);
    setSelectedDistrict("");
    setIsAnalyzed(false);
  }

  function selectDistrict(district: string) {
    setSelectedDistrict(district);
    setIsAnalyzed(false);
  }

  function analyze() {
    if (!selectedState || !selectedDistrict) return;
    setIsAnalyzed(true);
    window.setTimeout(() => document.getElementById("risk-results")?.scrollIntoView({ behavior: "smooth" }), 80);
  }

  return {
    selectedState, selectedDistrict, districts, metrics, isAnalyzed, activeTab, isMobileMenuOpen,
    setActiveTab, setIsMobileMenuOpen, selectState, selectDistrict, analyze,
  };
}
