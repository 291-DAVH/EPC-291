import { ReactNode, useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Me, api } from "./api";
import { signOut } from "./auth";
import { Key, useI18n } from "./i18n";
import { Icon, Logo, NAV_ICON } from "./icons";
import { useTheme } from "./theme";

export interface NavItem {
  to: string;
  key: Key;
  icon: string;
  end?: boolean;
}

/** The application window shared by the web app and the console: title bar, a rail of sections, the workspace and a status bar (a phone gets a top bar and bottom tabs instead). */
export function Shell({ nav, me, children }: { nav: NavItem[]; me?: Me | null; children: ReactNode }) {
  const { t, lang, setLang } = useI18n();
  const theme = useTheme();
  const where = useLocation().pathname;
  const [menu, setMenu] = useState(false);                                // the account (who, which organization, sign out) opens from the title bar
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setMenu(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const viewAs = async (org: string, role: string) => {                // the engineering team looks at the platform as an organization, a member of it or an independent professional
    await api("/auth/view-as", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ org, role }) });
    window.location.assign("/");
  };
  return (
    <div className="shell">
      <a className="skip" href="#main">{t("app.skip")}</a>
      <header className="titlebar">
        <div className="brand">
          <Logo />
          <div className="brand-text">
            <b>{t("app.name")}</b>
            <span>{me?.org || t("app.tagline")}</span>
          </div>
        </div>
        <div className="tools">
          <button className="lang" onClick={() => setLang(lang === "es" ? "en" : "es")} aria-label="Language">{lang === "es" ? "EN" : "ES"}</button>
          <button onClick={theme.toggle} aria-label={t("theme.toggle")} title={t("theme.toggle")}><Icon name={theme.isDark ? "sun" : "moon"} size={18} /></button>
          <button className="menu-btn" onClick={() => setMenu(!menu)} aria-expanded={menu} aria-controls="account" aria-label={t("app.menu")} title={t("app.menu")}><Icon name={menu ? "close" : "account"} size={18} /></button>
        </div>
      </header>
      <nav className="navmain" aria-label={t("app.navigation")}>
        {nav.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => "nav" + (isActive ? " active" : "")} title={t(n.key)}>
            <Icon name={NAV_ICON[n.key] ?? "app"} size={22} />
            <span className="nav-label">{t(n.key)}</span>
          </NavLink>
        ))}
      </nav>
      <div id="account" className={"account" + (menu ? " open" : "")} onClick={() => setMenu(false)}>
        {me?.role === "admin" && (me.app_url || me.console_url) && (
          <div className="expertlinks">
            {me.app_url && <a className="nav" href={me.app_url}><Icon name="projects" size={18} />{t("acct.goApp")}</a>}
            {me.console_url && <a className="nav" href={me.console_url}><Icon name="dashboard" size={18} />{t("acct.goConsole")}</a>}
          </div>
        )}
        {me?.organizations && (me.organizations.length > 1 || ((me.role === "admin" || me.can_view_as) && me.organizations.length > 0)) && (
          <label className="orgswitch" onClick={(e) => e.stopPropagation()}>
            <span className="muted small">{t("acct.switchOrg")}</span>
            <select value={me.org_slug ?? ""} onChange={async (e) => { await api("/auth/switch-org", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ org: e.target.value }) }); window.location.assign("/"); }}>
              {(me.role === "admin" || me.can_view_as) && <option value="">{t("acct.allOrgs")}</option>}
              {me.organizations.map((o) => <option key={o.slug} value={o.slug}>{o.name}</option>)}
            </select>
          </label>
        )}
        {me?.can_view_as && me.org_slug && (
          <label className="orgswitch" onClick={(e) => e.stopPropagation()}>
            <span className="muted small">{t("acct.viewAs")}</span>
            <select value={me.viewing_as ?? ""} onChange={async (e) => { await viewAs(me.org_slug ?? "", e.target.value); }}>
              <option value="">{t("acct.view.team")}</option>
              {me.organizations?.find((o) => o.slug === me.org_slug)?.kind === "individual"
                ? <option value="owner">{t("acct.view.individual")}</option>
                : <>{(["owner", "admin", "member"] as const).map((r) => <option key={r} value={r}>{t(("acct.view." + r) as Key)}</option>)}</>}
            </select>
          </label>
        )}
        {me?.name && <div className="who muted">{me.name}{me.account_type && <div className="small">{t(("acct.type." + me.account_type) as Key)}</div>}</div>}
        {me?.auth === "required" && me.authenticated && <button onClick={signOut}>{t("auth.logout")}</button>}
        {!me?.name && !(me?.auth === "required" && me.authenticated) && <div className="who muted small">{t("app.tagline")}</div>}
      </div>
      <main className="main" id="main" tabIndex={-1}>
        {me?.org_validation === "pending" && !me.viewing_as && (
          <div className="alert warn small" role="status" style={{ marginBottom: 12 }}>{t("co.pending")}</div>
        )}
        {me?.viewing_as && (
          <div className="alert warn" role="status" style={{ marginBottom: 12 }}>
            {t("acct.viewing")} <b>{t((me.org_kind === "individual" ? "acct.view.individual" : "acct.view." + me.viewing_as) as Key)}</b> · <b>{me.org}</b>
            {" "}<button onClick={() => viewAs(me.org_slug ?? "", "")}>{t("acct.viewBack")}</button>
          </div>
        )}
        {children}
      </main>
      <footer className="statusbar" role="contentinfo">
        <span className="led" aria-hidden /> <span>{t("app.ready")}</span>
        {me?.org && <span>{me.org}</span>}
        <span className="mono path">{where}</span>
        <span className="grow" />
        {me?.name && <span>{me.name}</span>}
        {me?.role === "admin" && <span>{t("app.statusAdmin")}</span>}
      </footer>
    </div>
  );
}
