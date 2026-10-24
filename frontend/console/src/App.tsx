import { Navigate, Route, Routes } from "react-router-dom";
import { Me, NavItem, Page, Shell, State, useApi, useI18n } from "@epc/ui";
import Overview from "./features/overview/Overview";
import Plugins from "./features/plugins/Plugins";
import Skills from "./features/skills/Skills";
import Rules from "./features/rules/Rules";
import Checker from "./features/checker/Checker";
import ProjectFiles from "./features/project-files/ProjectFiles";
import Planning from "./features/planning/Planning";
import Identity from "./features/identity/Identity";
import Norms from "./features/norms/Norms";

const NAV: NavItem[] = [
  { to: "/", key: "nav.dashboard", icon: "◈", end: true },
  { to: "/plugins", key: "nav.plugins", icon: "◫" },
  { to: "/skills", key: "nav.skills", icon: "✦" },
  { to: "/rules", key: "nav.rules", icon: "§" },
  { to: "/checker", key: "nav.checker", icon: "✓" },
  { to: "/planning", key: "nav.planning", icon: "▥" },
  { to: "/files", key: "nav.projects", icon: "▤" },
  { to: "/identity", key: "nav.identity", icon: "☺" },
  { to: "/norms", key: "nav.norms", icon: "§" },
];
const REVIEWER_NAV: NavItem[] = [{ to: "/norms", key: "nav.norms", icon: "§" }];

/** Technical console: only the admin role sees it (the API refuses everything else with 403). */
export default function App() {
  const { t } = useI18n();
  const me = useApi<Me>("/me");
  const admin = me.data?.role === "admin";
  const reviewer = me.data?.role === "standards";          // the norm reviewer sees only the norms review
  return (
    <Shell nav={admin ? NAV : reviewer ? REVIEWER_NAV : []} me={me.data}>
      {!me.data ? (
        <State loading={me.loading} error={me.error} />
      ) : reviewer ? (
        <Routes>
          <Route path="/norms" element={<Norms />} />
          <Route path="*" element={<Navigate to="/norms" replace />} />
        </Routes>
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
          <Route path="/identity" element={<Identity />} />
          <Route path="/norms" element={<Norms />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </Shell>
  );
}
