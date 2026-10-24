import { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { Me, api } from "./api";
import { signOut } from "./auth";
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
        {me?.role === "admin" && (me.app_url || me.console_url) && (
          <div className="expertlinks">
            {me.app_url && <a className="nav" href={me.app_url}><span aria-hidden>▦</span>{t("acct.goApp")}</a>}
            {me.console_url && <a className="nav" href={me.console_url}><span aria-hidden>◈</span>{t("acct.goConsole")}</a>}
          </div>
        )}
        <div className="spacer" />
        {me?.organizations && (me.organizations.length > 1 || (me.role === "admin" && me.organizations.length > 0)) && (
          <label className="orgswitch">
            <span className="muted small">{t("acct.switchOrg")}</span>
            <select value={me.org_slug ?? ""} onChange={async (e) => { await api("/auth/switch-org", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ org: e.target.value }) }); window.location.assign("/"); }}>
              {me.role === "admin" && <option value="">{t("acct.allOrgs")}</option>}
              {me.organizations.map((o) => <option key={o.slug} value={o.slug}>{o.name}</option>)}
            </select>
          </label>
        )}
        {me?.name && <div className="who muted">{me.name}{me.account_type && <div className="small">{t(("acct.type." + me.account_type) as Key)}</div>}</div>}
        {me?.auth === "required" && me.authenticated && <button onClick={signOut}>{t("auth.logout")}</button>}
        <div className="tools">
          <button onClick={() => setLang(lang === "es" ? "en" : "es")} aria-label="Language">{lang === "es" ? "EN" : "ES"}</button>
          <button onClick={theme.toggle} aria-label={t("theme.toggle")} title={t("theme.toggle")}>{theme.isDark ? "☀" : "☾"}</button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
