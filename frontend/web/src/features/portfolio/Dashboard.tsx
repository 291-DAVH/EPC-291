import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Portfolio, PortfolioProject, useApi } from "@epc/ui";
import { Badge, HealthBadge, Page, Progress, State, phaseKey, useFmt } from "@epc/ui";
import { Key, useI18n } from "@epc/ui";

type Sort = "priority" | "due" | "progress" | "name";
const HEALTH_ORDER: Record<string, number> = { delayed: 0, at_risk: 1, on_track: 2 };
const DISCIPLINES = ["electrical", "civil", "hvac", "fire", "mechanical", "instrumentation", "telecom"];

export default function Dashboard() {
  const { t } = useI18n();
  const fmt = useFmt();
  const { data, loading, error } = useApi<Portfolio>("/app/portfolio");
  const [q, setQ] = useState("");
  const [health, setHealth] = useState("");
  const [phase, setPhase] = useState("");
  const [disc, setDisc] = useState("");
  const [clientF, setClientF] = useState("");
  const [state, setState] = useState<"" | "active" | "closed">("");
  const [sort, setSort] = useState<Sort>("priority");
  const [view, setView] = useState<"cards" | "table">(() => (localStorage.getItem("view") as "cards" | "table") || "cards");

  const list = useMemo(() => {
    if (!data) return [];
    const ql = q.trim().toLowerCase();
    return data.projects
      .filter((p) => (!ql || (p.name + " " + p.client + " " + p.code).toLowerCase().includes(ql)) && (!phase || p.phase === phase) && (!disc || p.disciplines.includes(disc)) && (!clientF || p.client === clientF))
      .filter((p) => (!state || p.state === state) && (!health || (p.state === "active" && p.health === health)))
      .sort((a, b) => {
        if (sort === "name") return a.name.localeCompare(b.name);
        if (sort === "progress") return b.progress - a.progress;
        if (sort === "due") return (a.due ?? "9999").localeCompare(b.due ?? "9999");
        return Number(a.state !== "active") - Number(b.state !== "active") || HEALTH_ORDER[a.health] - HEALTH_ORDER[b.health] || (a.due ?? "9999").localeCompare(b.due ?? "9999");
      });
  }, [data, q, health, phase, disc, clientF, state, sort]);
  const clients = useMemo(() => Array.from(new Set((data?.projects ?? []).map((p) => p.client))).sort((a, b) => a.localeCompare(b)), [data]);

  const filtered = !!(q || health || phase || disc || state || clientF);
  const reset = () => { setQ(""); setHealth(""); setPhase(""); setDisc(""); setState(""); setClientF(""); };
  const k = data?.kpis;
  const setV = (v: "cards" | "table") => { setView(v); try { localStorage.setItem("view", v); } catch { /* storage unavailable */ } };

  return (
    <Page title={t("u.dash.title")}>
      <State loading={loading} error={error} />
      {k && (
        <div className="grid kpis">
          <Kpi n={k.active} label={t("u.kpi.active")} onClick={() => { reset(); setState("active"); }} />
          <Kpi n={k.on_track} label={t("u.kpi.onTrack")} tone="ok" active={health === "on_track"} onClick={() => setHealth(health === "on_track" ? "" : "on_track")} />
          <Kpi n={k.at_risk} label={t("u.kpi.atRisk")} tone="warn" active={health === "at_risk"} onClick={() => setHealth(health === "at_risk" ? "" : "at_risk")} />
          <Kpi n={k.delayed} label={t("u.kpi.delayed")} tone="bad" active={health === "delayed"} onClick={() => setHealth(health === "delayed" ? "" : "delayed")} />
          <Kpi n={k.deliverables_delivered} sub={`${t("u.kpi.of")} ${k.deliverables_total}`} label={t("u.kpi.delivered")} />
          <Kpi n={k.deliverables_due_soon} label={t("u.kpi.dueSoon")} />
          <Kpi n={k.inputs_open} label={t("u.kpi.inputs")} />
        </div>
      )}

      <div className="filters">
        <input type="search" placeholder={t("u.f.search")} value={q} onChange={(e) => setQ(e.target.value)} aria-label={t("u.f.search")} />
        <Sel label={t("u.f.client")} value={clientF} onChange={setClientF} all={t("u.f.all")} options={clients.map((c) => [c, c])} />
        <Sel label={t("u.f.health")} value={health} onChange={setHealth} all={t("u.f.all")}
          options={["on_track", "at_risk", "delayed"].map((h) => [h, t(("u.health." + h) as Key)])} />
        <Sel label={t("u.f.phase")} value={phase} onChange={setPhase} all={t("u.f.all")}
          options={["IC", "IB", "ID", "IE", "ASB"].map((p) => [p, t(phaseKey(p))])} />
        <Sel label={t("u.f.discipline")} value={disc} onChange={setDisc} all={t("u.f.all")}
          options={DISCIPLINES.map((d) => [d, t(("projects.disc." + d) as Key)])} />
        <Sel label={t("u.f.state")} value={state} onChange={(v) => setState(v as "" | "active" | "closed")} all={t("u.f.all")}
          options={[["active", t("u.f.active")], ["closed", t("u.f.closed")]]} />
        <label className="row muted">
          {t("u.f.sort")}
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} aria-label={t("u.f.sort")}>
            {(["priority", "due", "progress", "name"] as Sort[]).map((s) => <option key={s} value={s}>{t(("u.sort." + s) as Key)}</option>)}
          </select>
        </label>
        <div className="seg" role="group">
          <button className={view === "cards" ? "on" : ""} onClick={() => setV("cards")}>{t("u.view.cards")}</button>
          <button className={view === "table" ? "on" : ""} onClick={() => setV("table")}>{t("u.view.table")}</button>
        </div>
        {filtered && <button onClick={reset}>{t("u.f.reset")}</button>}
        {data && <span className="muted">{list.length} {t("u.dash.count")}</span>}
      </div>

      {data && list.length === 0 && <div className="state">{t("u.empty")}</div>}

      {view === "cards" ? (
        <div className="grid pcards">
          {list.map((p) => <ProjectCard key={p.id} p={p} today={data!.today} />)}
        </div>
      ) : (
        list.length > 0 && (
          <div className="card scroll">
            <table>
              <thead>
                <tr>
                  <th>{t("u.col.project")}</th><th>{t("u.col.phase")}</th><th>{t("u.col.progress")}</th><th>{t("u.col.status")}</th>
                  <th>{t("u.col.due")}</th><th>{t("u.col.deliverables")}</th><th>{t("u.col.inputs")}</th>
                </tr>
              </thead>
              <tbody>
                {list.map((p) => (
                  <tr key={p.id}>
                    <td><Link to={`/projects/${p.id}`}><b>{p.name}</b></Link><div className="muted">{p.client} · {p.code}</div></td>
                    <td>{t(phaseKey(p.phase))}</td>
                    <td style={{ minWidth: 130 }}><div className="row"><Progress pct={p.progress} health={p.health} closed={p.state !== "active"} /><span className="mono">{p.progress}%</span></div></td>
                    <td><HealthBadge health={p.health} closed={p.state !== "active"} /></td>
                    <td>{fmt.date(p.due)}</td>
                    <td>{p.deliverables.delivered}/{p.deliverables.total}{p.deliverables.overdue > 0 && <> <Badge tone="bad">{p.deliverables.overdue} {t("u.card.overdue")}</Badge></>}</td>
                    <td>{p.inputs.open > 0 ? <Badge tone="accent">{p.inputs.open}</Badge> : <span className="muted">0</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </Page>
  );
}

function Kpi({ n, label, sub, tone, onClick, active }: { n: number; label: string; sub?: string; tone?: "ok" | "warn" | "bad"; onClick?: () => void; active?: boolean }) {
  const inner = (
    <>
      <b className={tone}>{n}{sub && <small> {sub}</small>}</b>
      <span>{label}</span>
    </>
  );
  return onClick ? (
    <button className={"card stat" + (active ? " on" : "")} onClick={onClick} aria-pressed={active}>{inner}</button>
  ) : (
    <div className="card stat">{inner}</div>
  );
}

function Sel({ label, value, onChange, options, all }: { label: string; value: string; onChange: (v: string) => void; options: string[][]; all: string }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} aria-label={label}>
      <option value="">{label}: {all}</option>
      {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  );
}

function ProjectCard({ p, today }: { p: PortfolioProject; today: string }) {
  const { t } = useI18n();
  const fmt = useFmt();
  const closed = p.state !== "active";
  const late = !closed && !!p.due && p.due < today;
  return (
    <Link to={`/projects/${p.id}`} className={"card pcard " + (closed ? "closed" : p.health)}>
      <div className="row between">
        <span className="muted">{p.client}</span>
        <HealthBadge health={p.health} closed={closed} />
      </div>
      <h3>{p.name}</h3>
      <div className="muted mono">{p.code}</div>
      <div className="row" style={{ margin: "10px 0 4px" }}>
        <Progress pct={p.progress} health={p.health} closed={closed} />
        <b className="mono">{p.progress}%</b>
      </div>
      <div className="row between small">
        <Badge>{t(phaseKey(p.phase))}</Badge>
        <span className={late ? "err" : "muted"}>{t("u.card.due")} {fmt.date(p.due)}</span>
      </div>
      {p.next_milestone && !closed && <div className="muted small" style={{ marginTop: 6 }}>{t("u.card.next")}: {p.next_milestone.name} · {fmt.short(p.next_milestone.date)}</div>}
      <div className="row small" style={{ marginTop: 10 }}>
        <Badge tone={p.deliverables.delivered === p.deliverables.total && p.deliverables.total > 0 ? "ok" : undefined}>{p.deliverables.delivered}/{p.deliverables.total} {t("u.card.deliverables")}</Badge>
        {p.deliverables.overdue > 0 && <Badge tone="bad">{p.deliverables.overdue} {t("u.card.overdue")}</Badge>}
        {p.inputs.open > 0 && <Badge tone="accent">{p.inputs.open} {t("u.card.inputs")}</Badge>}
      </div>
    </Link>
  );
}
