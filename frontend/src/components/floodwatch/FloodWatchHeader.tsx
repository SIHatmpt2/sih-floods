import Icon from "./Icon";

type Props = { mobileOpen: boolean; onMobileToggle: () => void };

const links = [
  ["Home", "#"], ["Information", "#about"], ["Risk Analysis", "#risk-selector"], ["Live Map", "#live-map"], ["About Us", "#about"],
];

export default function FloodWatchHeader({ mobileOpen, onMobileToggle }: Props) {
  return <header className="fw-nav">
    <div className="fw-shell fw-nav-inner">
      <a className="fw-brand" href="#" aria-label="FloodWatch home">
        <span className="fw-brand-mark"><Icon name="activity" size={19} /></span>
        <span>FloodWatch</span><Icon name="rain" size={17} />
      </a>
      <nav className="fw-desktop-nav">{links.map(([label, href]) => <a key={label} href={href}>{label}</a>)}</nav>
      <a className="fw-button fw-button-primary fw-nav-cta" href="#risk-selector">Check Risk <Icon name="arrow" size={16} /></a>
      <button className="fw-icon-button fw-mobile-toggle" onClick={onMobileToggle} aria-label="Toggle navigation"><Icon name={mobileOpen ? "close" : "menu"} /></button>
    </div>
    {mobileOpen && <nav className="fw-mobile-nav">{links.map(([label, href]) => <a key={label} href={href} onClick={onMobileToggle}>{label}</a>)}</nav>}
  </header>;
}
