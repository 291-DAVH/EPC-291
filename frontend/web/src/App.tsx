import { Navigate, Route, Routes } from "react-router-dom";
import { Me, NavItem, Shell, useApi } from "@epc/ui";
import Dashboard from "./features/portfolio/Dashboard";
import Project from "./features/project/Project";
import NewProjectPage from "./features/new-project/NewProjectPage";

const NAV: NavItem[] = [
  { to: "/", key: "u.nav.projects", icon: "▦", end: true },
  { to: "/new", key: "u.nav.new", icon: "+" },
];

export default function App() {
  const me = useApi<Me>("/me");
  return (
    <Shell nav={NAV} me={me.data}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewProjectPage />} />
        <Route path="/projects/:client/:code" element={<Project />} />
        <Route path="*" element={me.data || me.error ? <Navigate to="/" replace /> : null} />
      </Routes>
    </Shell>
  );
}
