import React from "react";

type Props = { name: string; size?: number; strokeWidth?: number };

const paths: Record<string, React.ReactNode> = {
  activity: <><path d="M3 12h4l3-8 4 16 3-8h4" /></>,
  rain: <><path d="M7 16a4 4 0 1 1 1-7.9A5 5 0 0 1 18 10a3 3 0 0 1-1 5.8H7Z" /><path d="M8 20h.01M12 20h.01M16 20h.01" /></>,
  water: <><path d="M12 3S6 10 6 14a6 6 0 0 0 12 0c0-4-6-11-6-11Z" /><path d="M9 15a3 3 0 0 0 3 3" /></>,
  map: <><path d="M9 18 3 21V6l6-3 6 3 6-3v15l-6 3-6-3Z" /><path d="M9 3v15M15 6v15" /></>,
  pin: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
  alert: <><path d="m12 3 9 16H3L12 3Z" /><path d="M12 9v4M12 16h.01" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  close: <><path d="m6 6 12 12M18 6 6 18" /></>,
  search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 5 5" /></>,
  chevron: <path d="m7 10 5 5 5-5" />,
  arrow: <><path d="M5 12h14M13 6l6 6-6 6" /></>,
  radio: <><circle cx="12" cy="12" r="3" /><path d="M5.6 5.6a9 9 0 0 0 0 12.8M18.4 5.6a9 9 0 0 1 0 12.8" /></>,
  package: <><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m4.5 7.5 7.5 4 7.5-4M12 21v-9.5" /></>,
  grid: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" /></>,
  satellite: <><path d="m14 10 4-4M10 14l-4 4M7 7l10 10" /><path d="M5 5h5v5H5zM14 14h5v5h-5z" /></>,
};

export default function Icon({ name, size = 20, strokeWidth = 1.8 }: Props) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}
