import { LOCATION_DATA } from "../../data/floodWatchData";
import { useFloodWatch } from "../../hooks/useFloodWatch";
import CustomIndiaMap from "../../components/floodwatch/CustomIndiaMap";
import FloodWatchHeader from "../../components/floodwatch/FloodWatchHeader";
import FloodWatchResults from "../../components/floodwatch/FloodWatchResults";
import Icon from "../../components/floodwatch/Icon";
import "./floodwatch.css";

const features = [
  ["rain", "Rainfall Analysis", "Continuous precipitation monitoring using IMD and satellite data.", "blue"],
  ["water", "River Discharge", "Real-time river discharge and water-level tracking across major basins.", "teal"],
  ["satellite", "Satellite Imagery", "Multi-spectral imagery for flood extent mapping and situational awareness.", "red"],
  ["map", "Geographic Intel", "Elevation, soil saturation and drainage-basin signals for predictive assessment.", "amber"],
];

export default function FloodWatchPage() {
  const fw = useFloodWatch();
  return <div className="floodwatch-app">
    <FloodWatchHeader mobileOpen={fw.isMobileMenuOpen} onMobileToggle={() => fw.setIsMobileMenuOpen(!fw.isMobileMenuOpen)} />
    <main>
      <section className="fw-hero">
        <div className="fw-hero-glow"/><div className="fw-river-art"/>
        <div className="fw-shell fw-hero-content">
          <div className="fw-status"><i/>Live disaster intelligence · civic control</div>
          <h1>Know the Risk.<br/><em>Stay Safe.</em></h1>
          <p>Real-time critical flood monitoring, telemetry updates, and local authority alerts designed to protect Indian communities before disaster strikes.</p>
          <div className="fw-hero-actions"><a className="fw-button fw-button-primary" href="#risk-selector">Check Flood Risk <Icon name="search" size={16}/></a><a className="fw-button fw-button-outline" href="#live-map">Explore Map <Icon name="map" size={16}/></a></div>
          <div className="fw-hero-stats"><span><b>24/7</b> monitoring</span><span><b>5 min</b> telemetry cadence</span><span><b>43</b> ML features</span></div>
        </div>
      </section>

      <section className="fw-feature-wrap"><div className="fw-shell fw-feature-grid">{features.map(([icon,title,text,accent]) => <article className="fw-feature" key={title}><div className={`fw-feature-icon ${accent}`}><Icon name={icon} size={19}/></div><div><h3>{title}</h3><p>{text}</p></div></article>)}</div></section>

      <section id="risk-selector" className="fw-selector"><div className="fw-shell"><div className="fw-selector-card glass-card"><div className="fw-selector-copy"><span className="fw-number">01</span><div><div className="fw-eyebrow blue">Local assessment</div><h2>Check Flood Risk</h2><p>Select a state and district to analyze current flood risk conditions.</p></div></div><div className="fw-selector-form"><label>State<select value={fw.selectedState} onChange={(e) => fw.selectState(e.target.value)}><option value="" disabled>Select State</option>{Object.keys(LOCATION_DATA).map((state)=><option key={state}>{state}</option>)}</select><Icon name="chevron" size={17}/></label><label>District<select value={fw.selectedDistrict} disabled={!fw.selectedState} onChange={(e)=>fw.selectDistrict(e.target.value)}><option value="" disabled>Select District</option>{fw.districts.map((district)=><option key={district}>{district}</option>)}</select><Icon name="chevron" size={17}/></label><button className="fw-button fw-button-primary fw-analyze" disabled={!fw.selectedState || !fw.selectedDistrict} onClick={fw.analyze}>Analyze Risk <Icon name="arrow" size={16}/></button></div></div></div></section>

      <section id="live-map" className="fw-map-section"><div className="fw-shell"><div className="fw-map-header"><div><div className="fw-eyebrow">Situation room</div><h2>Live Hydrological Map</h2><p>Explore current risk layers across monitored regions.</p></div><div className="fw-tabs">{[["risk","Flood Risk"],["rain","Rainfall"],["river","River Levels"],["sat","Satellite"]].map(([id,label])=><button key={id} className={fw.activeTab===id?"active":""} onClick={()=>fw.setActiveTab(id)}>{label}</button>)}</div></div><div className="fw-map-frame"><CustomIndiaMap activeTab={fw.activeTab}/></div></div></section>

      {fw.isAnalyzed && <FloodWatchResults state={fw.selectedState} district={fw.selectedDistrict} metrics={fw.metrics}/>} 

      <section id="about" className="fw-about"><div className="fw-shell fw-about-grid"><div><div className="fw-eyebrow blue">About FloodWatch</div><h2>Flood intelligence built for earlier decisions.</h2><p>FloodWatch combines real-time rainfall data, river discharge monitoring, satellite imagery analysis, and machine learning to help identify emerging flood risk.</p><p>By bringing civic-tech resources and critical telemetry together, the platform gives authorities and communities a clearer window to prepare before conditions become dangerous.</p></div><div className="fw-about-stats"><div><b>5</b><span>States monitored</span></div><div><b>150+</b><span>Districts covered</span></div><div><b>5 min</b><span>Update cadence</span></div><div><b>24/7</b><span>Active alerts</span></div></div></div></section>
    </main>
    <footer className="fw-footer"><div className="fw-shell fw-footer-grid"><div><div className="fw-brand"><span className="fw-brand-mark"><Icon name="activity" size={18}/></span><span>FloodWatch</span></div><p>Empowering communities with flood intelligence and real-time civic disaster defense resources.</p></div><div><h4>Quick Links</h4><a href="#risk-selector">Risk Analysis</a><a href="#live-map">Live Map</a><a href="#about">About Us</a></div><div><h4>Resources</h4><a href="#about">Data Sources</a><a href="#live-map">Telemetry</a><a href="#risk-selector">Risk Assessment</a></div><div><h4 className="emergency">Emergency Channels</h4><span>National Disaster Helpline</span><a className="hotline" href="tel:1078">1078</a><span>NDRF Emergency Call</span><a className="hotline" href="tel:01124363200">011-24363200</a></div></div><div className="fw-footer-bottom fw-shell"><span>© 2026 FloodWatch · Built for India</span><span>Powered by Open Data & ML</span></div></footer>
  </div>;
}
