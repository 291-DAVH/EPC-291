import { Navigate, Route, Routes } from "react-router-dom";
import { Me, NavItem, Page, Shell, State, useApi, useI18n } from "@epc/ui";
import Overview from "./features/overview/Overview";
import Plugins from "./features/plugins/Plugins";
import Skills from "./features/skills/Skills";
import Rules from "./features/rules/Rules";
import Checker from "./features/checker/Checker";
import ProjectFiles from "./features/project-files/ProjectFiles";
import Planning from "./features/planning/Planning";

const NAV: NavItem[] = [
  { to: "/", key: "nav.dashboard", icon: "◈", end: true },
  { to: "/plugins", key: "nav.plugins", icon: "◫" },
  { to: "/skills", key: "nav.skills", icon: "✦" },
  { to: "/rules", key: "nav.rules", icon: "§" },
  { to: "/checker", key: "nav.checker", icon: "✓" },
  { to: "/planning", key: "nav.planning", icon: "▥" },
  { to: "/files", key: "nav.projects", icon: "▤" },
];

/** Technical console: only the admin role sees it (the API refuses everything else with 403). */
export default function App() {
  const { t } = useI18n();
  const me = useApi<Me>("/me");
  const admin = me.data?.role === "admin";
  return (
    <Shell nav={admin ? NAV : []} me={me.data}>
      {!me.data ? (
        <State loading={me.loading} error={me.error} />
      ) : !admin ? (
        <Page title={t("console.denied.title")} help={t("console.denied.help")}>{null}</Page>
      ) : (
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/plugins" element={<Plugins />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/checker" element={<Checker />} />
          <Route path="/planning" element={<Planning />} />
          <Route path="/files" element={<ProjectFiles />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </Shell>
  );
}
