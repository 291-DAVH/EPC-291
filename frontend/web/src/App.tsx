import { Navigate, Route, Routes } from "react-router-dom";
import { Me, NavItem, Page, Shell, useApi, useI18n } from "@epc/ui";
import Dashboard from "./features/portfolio/Dashboard";
import Project from "./features/project/Project";
import NewProjectPage from "./features/new-project/NewProjectPage";
import Data from "./features/data/Data";
import Account from "./features/account/Account";

const NAV: NavItem[] = [
  { to: "/", key: "u.nav.projects", icon: "▦", end: true },
  { to: "/new", key: "u.nav.new", icon: "+" },
];

export default function App() {
  const { t } = useI18n();
  const me = useApi<Me>("/me");
  if (me.data?.role === "standards") {                    // the norm reviewer works in the console
    return <Shell nav={[]} me={me.data}><Page title={t("norms.web.title")} help={t("norms.web.help")}>{null}</Page></Shell>;
  }
  const admin = me.data?.role === "admin";                // master data is configuration of the office: admin/engineer only
  const accounts = me.data?.auth === "required";          // with real accounts everyone gets an account page (password, and the people of the organization for its owner)
  const nav = [...NAV, ...(admin ? [{ to: "/data", key: "u.nav.data", icon: "▤" } as NavItem] : []), ...(accounts ? [{ to: "/account", key: "u.nav.account", icon: "☺" } as NavItem] : [])];
  return (
    <Shell nav={nav} me={me.data}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewProjectPage />} />
        <Route path="/projects/:client/:code" element={<Project />} />
        {accounts && <Route path="/account" element={<Account />} />}
        {admin && <Route path="/data" element={<Data />} />}
        <Route path="*" element={me.data || me.error ? <Navigate to="/" replace /> : null} />
      </Routes>
    </Shell>
  );
}
