import { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { Me } from "./api";
import { Key, useI18n } from "./i18n";
import { useTheme } from "./theme";

export interface NavItem {
  to: string;
  key: Key;
  icon: string;
  end?: boolean;
}

/** Sidebar + main area shared by the web app and the console. */
export function Shell({ nav, me, children }: { nav: NavItem[]; me?: Me | null; children: ReactNode }) {
  const { t, lang, setLang } = useI18n();
  const theme = useTheme();
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <b>{t("app.name")}</b>
          <span>{me?.org || t("app.tagline")}</span>
        </div>
        {nav.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => "nav" + (isActive ? " active" : "")}>
            <span aria-hidden>{n.icon}</span>
            {t(n.key)}
          </NavLink>
        ))}
        <div className="spacer" />
        {me?.name && <div className="who muted">{me.name}</div>}
        <div className="tools">
          <button onClick={() => setLang(lang === "es" ? "en" : "es")} aria-label="Language">{lang === "es" ? "EN" : "ES"}</button>
          <button onClick={theme.toggle} aria-label={t("theme.toggle")} title={t("theme.toggle")}>{theme.isDark ? "☀" : "☾"}</button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
