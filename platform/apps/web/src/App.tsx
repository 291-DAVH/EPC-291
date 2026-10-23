import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { Me, useApi } from "./api";
import { Key, useI18n } from "./i18n";
import Dashboard from "./pages/Dashboard";
import Project from "./pages/Project";
import NewProjectPage from "./pages/NewProjectPage";
import AdminHome from "./pages/admin/AdminHome";
import Plugins from "./pages/admin/Plugins";
import Skills from "./pages/admin/Skills";
import Rules from "./pages/admin/Rules";
import Checker from "./pages/admin/Checker";
import ProjectFiles from "./pages/admin/ProjectFiles";

const NAV: { to: string; key: Key; icon: string; end?: boolean }[] = [
  { to: "/", key: "u.nav.projects", icon: "▦", end: true },
  { to: "/new", key: "u.nav.new", icon: "+" },
];
const ADMIN_NAV: { to: string; key: Key; icon: string; end?: boolean }[] = [
  { to: "/admin", key: "nav.dashboard", icon: "◈", end: true },
  { to: "/admin/plugins", key: "nav.plugins", icon: "◫" },
  { to: "/admin/skills", key: "nav.skills", icon: "✦" },
  { to: "/admin/rules", key: "nav.rules", icon: "§" },
  { to: "/admin/checker", key: "nav.checker", icon: "✓" },
  { to: "/admin/files", key: "nav.projects", icon: "▤" },
];

function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark" | "">(() => {
    try {
      return (localStorage.getItem("theme") as "light" | "dark") || "";
    } catch {
      return "";
    }
  });
  useEffect(() => {
    const el = document.documentElement;
    if (theme) el.setAttribute("data-theme", theme);
    else el.removeAttribute("data-theme");
    try {
      theme ? localStorage.setItem("theme", theme) : localStorage.removeItem("theme");
    } catch {
      /* storage unavailable */
    }
  }, [theme]);
  const isDark = theme ? theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  return { toggle: () => setTheme(isDark ? "light" : "dark"), isDark };
}

export default function App() {
  const { t, lang, setLang } = useI18n();
  const theme = useTheme();
  const me = useApi<Me>("/me");
  const admin = me.data?.role === "admin";
  const link = (n: (typeof NAV)[number]) => (
    <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => "nav" + (isActive ? " active" : "")}>
      <span aria-hidden>{n.icon}</span>
      {t(n.key)}
    </NavLink>
  );
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <b>{t("app.name")}</b>
          <span>{me.data?.org || t("app.tagline")}</span>
        </div>
        {NAV.map(link)}
        {admin && (
          <>
            <div className="navsep">{t("u.nav.console")}</div>
            {ADMIN_NAV.map(link)}
          </>
        )}
        <div className="spacer" />
        {me.data?.name && <div className="who muted">{me.data.name}</div>}
        <div className="tools">
          <button onClick={() => setLang(lang === "es" ? "en" : "es")} aria-label="Language">{lang === "es" ? "EN" : "ES"}</button>
          <button onClick={theme.toggle} aria-label={t("theme.toggle")} title={t("theme.toggle")}>{theme.isDark ? "☀" : "☾"}</button>
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewProjectPage />} />
          <Route path="/projects/:client/:code" element={<Project />} />
          {admin && (
            <>
              <Route path="/admin" element={<AdminHome />} />
              <Route path="/admin/plugins" element={<Plugins />} />
              <Route path="/admin/skills" element={<Skills />} />
              <Route path="/admin/rules" element={<Rules />} />
              <Route path="/admin/checker" element={<Checker />} />
              <Route path="/admin/files" element={<ProjectFiles />} />
            </>
          )}
          <Route path="*" element={me.data || me.error ? <Navigate to="/" replace /> : null} />
        </Routes>
      </main>
    </div>
  );
}
