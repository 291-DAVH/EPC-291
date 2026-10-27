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
