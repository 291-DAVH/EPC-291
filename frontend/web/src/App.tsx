import { Navigate, Route, Routes } from "react-router-dom";
import { Me, NavItem, Shell, useApi } from "@epc/ui";
import Dashboard from "./features/portfolio/Dashboard";
import Project from "./features/project/Project";
import NewProjectPage from "./features/new-project/NewProjectPage";
import Data from "./features/data/Data";

const NAV: NavItem[] = [
  { to: "/", key: "u.nav.projects", icon: "▦", end: true },
  { to: "/new", key: "u.nav.new", icon: "+" },
];

export default function App() {
  const me = useApi<Me>("/me");
  const admin = me.data?.role === "admin";                // master data is configuration of the office: admin/engineer only
  return (
    <Shell nav={admin ? [...NAV, { to: "/data", key: "u.nav.data", icon: "▤" }] : NAV} me={me.data}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewProjectPage />} />
        <Route path="/projects/:client/:code" element={<Project />} />
        {admin && <Route path="/data" element={<Data />} />}
        <Route path="*" element={me.data || me.error ? <Navigate to="/" replace /> : null} />
      </Routes>
    </Shell>
  );
}
