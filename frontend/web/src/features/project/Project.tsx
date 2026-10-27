import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { Badge, HealthBadge, Key, Me, PortfolioProject, Progress, State, phaseKey, useApi, useFmt, useI18n } from "@epc/ui";
import AnalysisPanel from "./AnalysisPanel";
import Deliverables from "./Deliverables";
import Engineering from "./Engineering";
import Inputs from "./Inputs";
import Layout from "./Layout";
import Observations from "./Observations";
import Overview from "./Overview";
import Plan from "./Plan";
import Registers from "./Registers";
import Reporting from "./Reporting";
import Reports from "./Reports";
import Requirements from "./Requirements";
import Catalogs from "./Catalogs";
import Coordination from "./Coordination";
import { ENGINEER_TABS, Tab, TABS } from "./tabs";

export default function Project() {
  const { client = "", code = "" } = useParams();
  const { t } = useI18n();
  const fmt = useFmt();
  const [sp, setSp] = useSearchParams();
  const me = useApi<Me>("/me");
  const can = (subject: string, action: string) => !!me.data?.abilities?.[subject]?.includes(action);
  const engineer = can("workspace", "read");           // the engineering workspace: the engineering team and the people of the organization that owns the project
  const canWrite = can("app", "write");                // inspectors and auditors read only: the screens hide what the server would refuse
  const wanted = sp.get("tab") as Tab;
  const tab = (TABS.includes(wanted) && (!ENGINEER_TABS.includes(wanted) || engineer) ? wanted : "overview") as Tab;
  const base = `/app/projects/${client}/${code}`;
  const p = useApi<PortfolioProject>(base);
  const [rev, setRev] = useState(0);                       // bump to reload lists after sending information
  const go = (x: Tab, extra: Record<string, string> = {}) => setSp({ tab: x, ...extra });

  if (p.error) return <div className="state err">{t("u.p.notFound")} <Link to="/">{t("u.p.back")}</Link></div>;
  if (!p.data) return <State loading />;
  const d = p.data;
  const closed = d.state !== "active";

  const bench = tab === "layout";                      // the layout is a single-page editor: a slim header and the editor takes the rest of the window
  const tabs = (                                       // in the editor the tabs share the header line with the name of the project
    <div className="tabs" role="tablist">
      {TABS.filter((x) => !ENGINEER_TABS.includes(x) || engineer).map((x) => (
        <button key={x} role="tab" aria-selected={tab === x} className={tab === x ? "on" : ""} onClick={() => go(x)}>
          {t(("u.tab." + x) as Key)}
          {x === "inputs" && d.inputs.open > 0 && <span className="dot">{d.inputs.open}</span>}
        </button>
      ))}
    </div>
  );
  return (
    <div className={bench ? "project bench" : "project"}>
      {bench ? (
        <div className="benchbar">
          <Link to="/" className="muted" aria-label={t("u.p.back")}>←</Link>
          <span className="muted">{d.client}</span><span className="mono muted">{d.code}</span><b>{d.name}</b>
          <HealthBadge health={d.health} closed={closed} />
          {tabs}
        </div>
      ) : <Link to="/" className="muted">← {t("u.p.back")}</Link>}
      {!bench && <div className="phead">
        <div>
          <div className="muted">{d.client} · <span className="mono">{d.code}</span></div>
          <h1 style={{ margin: "2px 0 6px" }}>{d.name}</h1>
          <div className="row">
            <HealthBadge health={d.health} closed={closed} />
            <Badge>{t(phaseKey(d.phase))}</Badge>
            {d.disciplines.map((x) => <Badge key={x}>{t(("projects.disc." + x) as Key)}</Badge>)}
          </div>
        </div>
        <div className="pmeta">
          <div className="row"><Progress pct={d.progress} health={d.health} closed={closed} /><b className="mono">{d.progress}%</b></div>
          <div className="muted small">{t("u.card.due")}: {fmt.date(d.due)}</div>
          {d.manager && <div className="muted small">{t("u.card.manager")}: {d.manager}</div>}
          {d.location && <div className="muted small">{t("u.p.location")}: {d.location}</div>}
        </div>
      </div>}

      {!bench && tabs}

      {tab === "overview" && <Overview d={d} base={base} rev={rev} go={go} />}
      {tab === "plan" && <Plan base={base} />}
      {tab === "registers" && <Registers client={client} code={code} />}
      {tab === "engineering" && <Engineering client={client} code={code} onOpenDeliverables={() => go("deliverables")} />}
      {tab === "layout" && <Layout client={client} code={code} canWrite={can("workspace", "write")} />}
      {tab === "coordination" && <Coordination client={client} code={code} discipline="" canWrite={can("workspace", "write")} standalone />}
      {tab === "catalogs" && <Catalogs client={client} code={code} />}
      {tab === "deliverables" && <Deliverables base={base} />}
      {tab === "observations" && <Observations base={base} can={can} />}
      {tab === "inputs" && <Inputs canWrite={canWrite} base={base} rev={rev} onSent={() => setRev((n) => n + 1)} initialKind={sp.get("kind") || "voice_of_customer"} engineer={engineer} client={client} code={code} />}
      {tab === "requirements" && <Requirements canWrite={canWrite} base={base} rev={rev} onChange={() => setRev((n) => n + 1)} />}
      {tab === "reports" && <Reports base={base} go={go} engineer={engineer} client={client} code={code} />}
    </div>
  );
}

/* ---------------- overview ---------------- */
