import Icon from "./Icon";

type Props = { activeTab: string };

export default function CustomIndiaMap({ activeTab }: Props) {
  return <div className="fw-map">
    <div className="fw-map-grid" />
    <div className="fw-map-legend">
      <div className="fw-eyebrow">Hydrological Risk</div>
      {[['CRITICAL','risk-critical'],['HIGH','risk-high'],['MODERATE','risk-moderate'],['LOW','risk-low']].map(([label, cls]) => <div className="fw-legend-item" key={label}><span className={`fw-dot ${cls}`} />{label === 'CRITICAL' ? 'Critical Risk' : `${label[0]}${label.slice(1).toLowerCase()} Risk`}</div>)}
    </div>
    <div className="fw-map-live"><Icon name="clock" size={15} />24:00 <span>LIVE</span></div>
    <div className="fw-map-controls"><button aria-label="Zoom in"><span>+</span></button><button aria-label="Zoom out"><span>−</span></button></div>
    <div className="fw-map-art" aria-label={`${activeTab} risk map of India`}>
      <svg viewBox="0 0 1000 800" role="img">
        <defs><filter id="mapShadow"><feDropShadow dx="0" dy="12" stdDeviation="12" floodOpacity=".25" /></filter></defs>
        <path className="india-base" d="M350 150 400 100 450 120 500 200 600 250 650 220 750 280 800 250 850 300 950 280 900 350 850 400 800 450 750 420 700 500 650 550 600 700 550 750 500 700 450 600 400 550 350 500 300 450 200 400 150 350 200 300 250 250 300 200Z" filter="url(#mapShadow)" />
        <path className="river" d="M450 120 Q500 150 550 200 T650 250 T750 280 T850 350" />
        <path className="river river-secondary" d="M350 150 Q400 200 450 250 T550 300 T650 350 T700 500" />
        <path className="zone low" d="M350 150 400 100 450 120 420 180Z" />
        <path className="zone critical" d="M420 180 500 200 600 250 550 350 400 300Z" />
        <path className="zone high" d="M400 300 550 350 500 450 350 400Z" />
        <path className="zone critical" d="M600 250 750 280 800 250 850 300 750 350 650 300Z" />
        <path className="zone high" d="M550 350 650 300 700 400 650 500 500 450Z" />
        <path className="zone moderate" d="M650 300 750 350 800 400 700 400Z" />
        <path className="zone moderate" d="M400 550 450 600 500 700 450 720 380 600Z" />
        <g className="map-label"><rect x="675" y="196" width="126" height="30" rx="7"/><text x="738" y="216">ASSAM · CRITICAL</text></g>
        <g className="map-label map-label-light"><rect x="472" y="216" width="112" height="30" rx="7"/><text x="528" y="236">BIHAR · HIGH</text></g>
        <g className="map-label"><rect x="548" y="318" width="148" height="30" rx="7"/><text x="622" y="338">WEST BENGAL · HIGH</text></g>
        <g className="map-label map-label-light"><rect x="292" y="596" width="150" height="30" rx="7"/><text x="367" y="616">KERALA · MODERATE</text></g>
      </svg>
    </div>
    <div className="fw-map-footer"><span><i />Data layers synchronized</span><span>Source: IMD · CWC · Satellite</span></div>
  </div>;
}
