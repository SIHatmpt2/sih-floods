import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, ReferenceLine } from "recharts";
import { DISCHARGE_DATA, Metrics, PRECIPITATION_DATA, TABLE_DATA } from "../../data/floodWatchData";
import { formatNumber, getRiskColor } from "../../utils/risk";
import Icon from "./Icon";

type Props = { state: string; district: string; metrics: Metrics };

const drivers = [
  ["rain", "Heavy Monsoon Rainfall", "Prolonged intense monsoon trough over Northeast region delivering record precipitation.", "Contribution Level", "driver1"],
  ["water", "River Basin Overflow", "The Brahmaputra and tributary systems experiencing heavy inflows from upstream catchment areas.", "Basin Capacity Exceeded", "driver2"],
  ["grid", "Drainage Infrastructure", "Urban channels overwhelmed due to limited outfall capacity and siltation blockages.", "Infrastructure Strain Rating", "driver3"],
] as const;

const protocols = [
  ["alert", "Evacuate Low Areas", "Move to assigned municipal shelters or higher ground immediately if located near embankments."],
  ["radio", "Monitor Channels", "Keep tuned to local DD News and official disaster management cell warning dispatches."],
  ["package", "Emergency Kit", "Pack clean drinking water, non-perishable rations, emergency light, and critical medical supplies."],
  ["alert", "Avoid Water Bodies", "Do not attempt to cross submerged streets, bridges, or culverts on foot or inside vehicles."],
];

export default function FloodWatchResults({ state, district, metrics }: Props) {
  const color = getRiskColor(metrics.risk);
  return <section id="risk-results" className="fw-results">
    <div className="fw-shell">
      <div className="fw-section-head"><div><div className="fw-eyebrow blue">Analysis complete</div><h2>Flood Risk Analysis Results</h2><p>Real-time telemetry and meteorological data for <strong>{state} — {district} District</strong></p></div><span className="fw-live-pill"><i />Model output live</span></div>
      <div className="fw-metric-grid">
        <Metric title="Risk Level" value={metrics.risk} sub={metrics.status} icon="alert" color={color} />
        <Metric title="Rainfall (24H)" value={String(metrics.rainfall)} unit="mm" icon="rain" color="#28b6ee" />
        <Metric title="River Discharge" value={formatNumber(metrics.discharge)} unit="m³/s" icon="water" color="#36d2b1" />
        <Metric title="Flood Probability" value={String(metrics.prob)} unit="%" icon="alert" color="#fb5b63" />
        <Metric title="Last Updated" value={metrics.time.split(" ")[0]} unit={metrics.time.substring(metrics.time.indexOf(" ") + 1)} icon="clock" color="#8aa0b7" />
      </div>
      <p className="fw-note">* Telemetry data is simulated for validation and disaster scenario testing.</p>

      <div className="fw-driver-section"><div className="fw-section-title"><span>01</span><div><h3>Primary Meteorological Drivers</h3><p>Signals currently contributing to the model assessment.</p></div></div><div className="fw-driver-grid">
        {drivers.map(([icon, title, text, label, key]) => <div className="fw-driver" key={title}><div className="fw-driver-title"><span><Icon name={icon} size={17}/></span><h4>{title}</h4></div><p>{text}</p><div className="fw-driver-label"><span>{label}</span><b>{metrics[key]}%</b></div><div className="fw-progress"><i style={{ width: `${metrics[key]}%` }} /></div></div>)}
      </div></div>

      <div className="fw-chart-grid">
        <ChartCard title="Precipitation Trend (7-Day)" label="Daily Millimeters"><ResponsiveContainer width="100%" height="100%"><BarChart data={PRECIPITATION_DATA}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="name" axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip contentStyle={{borderRadius:12,border:"1px solid #dce8f4"}}/><Bar dataKey="value" fill="#1b9ee0" radius={[6,6,0,0]} barSize={24}/></BarChart></ResponsiveContainer></ChartCard>
        <ChartCard title="River Discharge Rate (Brahmaputra)" label="Danger Zone Limit"><ResponsiveContainer width="100%" height="100%"><LineChart data={DISCHARGE_DATA}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="name" axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false} domain={[1000,2500]}/><Tooltip contentStyle={{borderRadius:12,border:"1px solid #dce8f4"}}/><ReferenceLine y={2000} stroke="#fb5b63" strokeDasharray="4 4"/><Line type="monotone" dataKey="value" stroke="#21b89c" strokeWidth={3} dot={{r:4}}/></LineChart></ResponsiveContainer></ChartCard>
      </div>

      <div className="fw-table-section"><div className="fw-section-title"><span>02</span><div><h3>Active Civil Risk Index per Hydrological Node</h3><p>Current status of monitored zones and telemetry freshness.</p></div></div><div className="fw-table-wrap"><table><thead><tr><th>Monitoring Zone / Block</th><th>Risk Classification</th><th>Est. Resident Impact</th><th>Telemetry Verified</th></tr></thead><tbody>{TABLE_DATA.map((row) => <tr key={row.zone}><td>{row.zone}</td><td><span className={`fw-risk-tag ${row.risk.split(" ")[0].toLowerCase()}`}>{row.risk}</span></td><td>{row.residents}</td><td>{row.telemetry}</td></tr>)}</tbody></table></div></div>

      <div className="fw-bottom-grid"><div><div className="fw-section-title"><span>03</span><div><h3>Critical Zone Alerts</h3><p>Prioritized locations requiring attention.</p></div></div><div className="fw-alert-grid">{TABLE_DATA.map((row) => <div className="fw-alert-card" key={row.zone}><div><strong>{row.zone.split(" ").slice(0,2).join(" ")}</strong><span className={`fw-risk-tag ${row.risk.split(" ")[0].toLowerCase()}`}>{row.risk.split(" ")[0]}</span></div><p>District: {district}</p><p>Est. Affected: {row.residents.split(" ")[0]}</p></div>)}</div></div>
        <div><div className="fw-section-title"><span>04</span><div><h3>Recommended Safety Protocols</h3><p>Practical actions for residents and response teams.</p></div></div><div className="fw-protocol-grid">{protocols.map(([icon,title,text]) => <div className="fw-protocol" key={title}><span><Icon name={icon} size={18}/></span><div><h4>{title}</h4><p>{text}</p></div></div>)}</div></div>
      </div>
    </div>
  </section>;
}

function Metric({ title, value, unit, sub, icon, color }: { title:string; value:string; unit?:string; sub?:string; icon:string; color:string }) {
  return <article className="fw-metric" style={{"--metric-color": color} as React.CSSProperties}><div className="fw-metric-top"><span>{title}</span><Icon name={icon} size={16}/></div><div className="fw-metric-value">{value} {unit && <small>{unit}</small>}</div>{sub ? <div className="fw-metric-sub"><i/> {sub}</div> : <div className="fw-metric-line"/>}</article>;
}

function ChartCard({ title, label, children }: {title:string; label:string; children:React.ReactNode}) { return <div className="fw-chart-card"><div className="fw-chart-head"><h3>{title}</h3><span>{label}</span></div><div className="fw-chart">{children}</div></div>; }
