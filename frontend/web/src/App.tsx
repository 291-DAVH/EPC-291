import { Navigate, Route, Routes } from "react-router-dom";
import { Me, NavItem, Norms, Shell, useApi } from "@epc/ui";
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
  const me = useApi<Me>("/me");
  if (me.data?.role === "standards") {                    // the norm reviewer works in the console
    return (
      <Shell nav={[{ to: "/norms", key: "nav.norms", icon: "§" }]} me={me.data}>
        <Routes><Route path="/norms" element={<Norms />} /><Route path="*" element={<Navigate to="/norms" replace />} /></Routes>
      </Shell>
    );
  }
  const staff = me.data?.role === "admin";                // the norms and the technical console are the platform team's
  const orgdata = !!me.data?.abilities?.orgdata?.includes("read");     // clients, issuing companies and personnel: each organization's own
  const accounts = me.data?.auth === "required";          // with real accounts everyone gets an account page (password, and the people of the organization for its owner)
  const canWrite = !me.data || !!me.data.abilities?.app?.includes("write");           // inspectors and auditors only read: no "new project"
  const nav = [...NAV.filter((n) => canWrite || n.to !== "/new"), ...(orgdata ? [{ to: "/data", key: "u.nav.data", icon: "▤" } as NavItem] : []), ...(staff ? [{ to: "/norms", key: "nav.norms", icon: "§" } as NavItem] : []), ...(accounts ? [{ to: "/account", key: "u.nav.account", icon: "☺" } as NavItem] : [])];
  return (
    <Shell nav={nav} me={me.data}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewProjectPage />} />
        <Route path="/projects/:client/:code" element={<Project />} />
        {accounts && <Route path="/account" element={<Account />} />}
        {orgdata && <Route path="/data" element={<Data />} />}
        {staff && <Route path="/norms" element={<Norms />} />}
        <Route path="*" element={me.data || me.error ? <Navigate to="/" replace /> : null} />
      </Routes>
    </Shell>
  );
}
