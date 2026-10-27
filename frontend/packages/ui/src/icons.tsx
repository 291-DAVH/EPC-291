/** The line icons of the interface: 24 px, square caps and one stroke width, so they read like the symbols of a drawing. They take the colour of the text around them. */
const PATHS: Record<string, string> = {
  projects: "M4 4h7v7H4z M13 4h7v7h-7z M4 13h7v7H4z M13 13h7v7h-7z",
  new: "M4 4h16v16H4z M12 8v8 M8 12h8",
  data: "M5 6c0-1.7 3.1-3 7-3s7 1.3 7 3-3.1 3-7 3-7-1.3-7-3z M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6 M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6",
  norms: "M6 3h9l4 4v14H6z M14 3v5h5 M9 12h7 M9 16h7",
  dashboard: "M4 18a8 8 0 1 1 16 0 M12 18l4-6 M6 18h2 M16 18h2",
  plugins: "M9 3v5 M15 3v5 M6 8h12v4a6 6 0 0 1-12 0z M12 18v3",
  skills: "M12 3l2.2 5.6L20 9l-4.5 3.8L17 19l-5-3-5 3 1.5-6.2L4 9l5.8-.4z",
  rules: "M12 3v18 M5 7h14 M5 7l-3 7a3 3 0 0 0 6 0z M19 7l-3 7a3 3 0 0 0 6 0z",
  checker: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M8 12.5l3 3 5-6",
  planning: "M4 4h9v3H4z M8 10.5h11v3H8z M6 17h8v3H6z",
  files: "M3 6h6l2 2h10v11H3z",
  identity: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7",
  layers: "M12 3l9 4.5-9 4.5-9-4.5z M3 12l9 4.5 9-4.5 M3 16.5L12 21l9-4.5",
  solutions: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M12 3v3 M12 18v3 M3 12h3 M18 12h3 M5.6 5.6l2.1 2.1 M16.3 16.3l2.1 2.1 M18.4 5.6l-2.1 2.1 M7.7 16.3l-2.1 2.1",
  sun: "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M12 2v3 M12 19v3 M2 12h3 M19 12h3 M4.9 4.9l2.1 2.1 M17 17l2.1 2.1 M19.1 4.9L17 7 M7 17l-2.1 2.1",
  moon: "M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z",
  account: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7",
  close: "M5 5l14 14 M19 5L5 19",
  app: "M4 4h16v16H4z M4 9h16 M9 9v11",
  select: "M5 3l13 7-6 2-2 6z M12 12l6 6",
  box: "M4 4h16v16H4z M8 4v16 M4 8h16",
  scale: "M3 8h18v8H3z M7 8v4 M11 8v3 M15 8v4 M19 8v3",
  origin: "M12 3v18 M3 12h18 M12 12m-3 0a3 3 0 1 0 6 0 3 3 0 1 0-6 0",
  node: "M5 5h14v14H5z M12 9v6 M9 12h6",
  line: "M4 19l5-9 5 5 6-10 M4 19h0 M20 5h0",
  erase: "M4 16l9-9 7 7-5 5H8z M10 10l7 7 M8 21h12",
  undo: "M9 14L4 9l5-5 M4 9h10a6 6 0 0 1 0 12h-3",
  redo: "M15 14l5-5-5-5 M20 9H10a6 6 0 0 0 0 12h3",
  fit: "M4 9V4h5 M20 9V4h-5 M4 15v5h5 M20 15v5h-5",
  upload: "M12 16V4 M7 9l5-5 5 5 M4 16v4h16v-4",
  help: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.7.4-1.1.9-1.1 1.8 M12 17h0",
  file: "M6 3h9l4 4v14H6z M14 3v5h5",
  trash: "M4 7h16 M9 7V4h6v3 M6 7l1 14h10l1-14",
  pan: "M12 3v18 M3 12h18 M12 3l-3 3 M12 3l3 3 M12 21l-3-3 M12 21l3-3 M3 12l3-3 M3 12l3 3 M21 12l-3-3 M21 12l-3 3",
  split: "M3 12h7 M14 12h7 M12 5v14 M9.5 7.5L12 5l2.5 2.5",
  measure: "M3 17L17 3l4 4L7 21z M7 13l2 2 M10 10l2 2 M13 7l2 2",
  route: "M6 20a2 2 0 1 0 .01 0z M18 4a2 2 0 1 0 .01 0z M8 19h6a4 4 0 0 0 4-4V6",
  pin: "M12 21s6-5.2 6-10a6 6 0 1 0-12 0c0 4.8 6 10 6 10z M12 13a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  lock: "M6 11h12v9H6z M8 11V8a4 4 0 0 1 8 0v3",
  unlock: "M6 11h12v9H6z M8 11V8a4 4 0 0 1 7.5-2",
  copy: "M8 8h11v12H8z M5 16V4h11",
  paste: "M9 4h6v3H9z M6 6h12v14H6z M9 12h6 M9 16h6",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  grid: "M4 4h16v16H4z M4 9.3h16 M4 14.7h16 M9.3 4v16 M14.7 4v16",
  magnet: "M5 4v7a7 7 0 0 0 14 0V4 M5 8h4 M15 8h4",
  image: "M3 7h4l2-3h6l2 3h4v13H3z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  print: "M7 9V3h10v6 M7 17H4v-7h16v7h-3 M7 14h10v7H7z",
  star: "M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.5 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z",
  more: "M5 12h.01 M12 12h.01 M19 12h.01",
  search: "M10 17a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M15 15l6 6",
  alignL: "M4 3v18 M8 7h12v4H8z M8 14h7v4H8z",
  alignR: "M20 3v18 M4 7h12v4H4z M9 14h7v4H9z",
  alignT: "M3 4h18 M7 8v12h4V8z M14 8v7h4V8z",
  alignB: "M3 20h18 M7 4v12h4V4z M14 9v7h4V9z",
  alignH: "M12 3v18 M6 7h12v4H6z M8 14h8v4H8z",
  alignV: "M3 12h18 M7 6v12h4V6z M14 8v8h4V8z",
  distH: "M4 3v18 M20 3v18 M10 8h4v8h-4z",
  distV: "M3 4h18 M3 20h18 M8 10v4h8v-4z",
  rotate: "M20 12a8 8 0 1 1-3-6.2 M20 4v5h-5",
  mirror: "M12 3v18 M8 7L3 12l5 5z M16 7l5 5-5 5z",
  resize: "M4 20V10h10v10z M10 14L20 4 M14 4h6v6",
  crop: "M6 2v16h16 M2 6h16v16",
  check: "M5 12.5l4.5 4.5L19 7",
  warn: "M12 3L2 20h20z M12 10v5 M12 18h.01",
  up: "M12 20V6 M6 12l6-6 6 6",
  down: "M12 4v14 M6 12l6 6 6-6",
  chat: "M4 5h16v11H9l-5 4z",
  people: "M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3 20c0-3.3 2.7-5 6-5s6 1.7 6 5 M17 10a2.5 2.5 0 1 0 0-5 M16 15c3 0 5 1.7 5 5",
  history: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M12 7v5l3 2",
  template: "M4 4h7v7H4z M13 4h7v4h-7z M13 10h7v10h-7z M4 13h7v7H4z",
  save: "M5 3h12l3 3v15H5z M8 3v6h8V3 M8 21v-7h8v7",
  reserve: "M4 4h16v16H4z M4 4l16 16 M20 4L4 20",
  keyboard: "M3 6h18v12H3z M7 10h.01 M11 10h.01 M15 10h.01 M7 14h10",
  clash: "M4 4l8 8 M20 4l-8 8 M4 20l8-8 M20 20l-8-8 M12 12h.01",
};

/** Which icon each section of the navigation uses (by the key of its label), so the two applications share one set. */
export const NAV_ICON: Record<string, string> = {
  "u.nav.projects": "projects", "u.nav.new": "new", "u.nav.data": "data", "nav.norms": "norms", "nav.dashboard": "dashboard", "nav.plugins": "plugins", "nav.skills": "skills",
  "nav.rules": "rules", "nav.checker": "checker", "nav.planning": "planning", "nav.projects": "files", "nav.identity": "identity", "nav.layers": "layers", "nav.solutions": "solutions",
};

export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="square" strokeLinejoin="miter" aria-hidden focusable="false">
      <path d={PATHS[name] ?? PATHS.app} />
    </svg>
  );
}

/** The mark of the platform: a trace over a frame, in the colours of the interface. */
export function Logo() {
  return (
    <svg className="logo" width="28" height="28" viewBox="0 0 28 28" aria-hidden focusable="false">
      <rect x="2" y="2" width="24" height="24" rx="3" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M2 20 L10 12 L15 17 L26 6" fill="none" stroke="var(--marker)" strokeWidth="2.5" strokeLinecap="square" />
      <circle cx="10" cy="12" r="2" fill="var(--marker)" />
    </svg>
  );
}
