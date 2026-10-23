import { FormEvent, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ApiError, DeliverableItem, Gantt, InputItem, PortfolioProject, ReportItem, RequirementItem, ScheduleView, WbsTree, WbsView, useApi } from "@epc/ui";
import { Badge, HealthBadge, Progress, State, phaseKey, useFmt } from "@epc/ui";
import { Key, useI18n } from "@epc/ui";

const TABS = ["overview", "plan", "deliverables", "inputs", "requirements", "reports"] as const;
type Tab = (typeof TABS)[number];

export default function Project() {
  const { client = "", code = "" } = useParams();
  const { t } = useI18n();
  const fmt = useFmt();
  const [sp, setSp] = useSearchParams();
  const tab = (TABS.includes(sp.get("tab") as Tab) ? sp.get("tab") : "overview") as Tab;
  const base = `/app/projects/${client}/${code}`;
  const p = useApi<PortfolioProject>(base);
  const [rev, setRev] = useState(0);                       // bump to reload lists after sending information
  const go = (x: Tab, extra: Record<string, string> = {}) => setSp({ tab: x, ...extra });

  if (p.error) return <div className="state err">{t("u.p.notFound")} <Link to="/">{t("u.p.back")}</Link></div>;
  if (!p.data) return <State loading />;
  const d = p.data;
  const closed = d.state !== "active";

  return (
    <>
      <Link to="/" className="muted">← {t("u.p.back")}</Link>
      <div className="phead">
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
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((x) => (
          <button key={x} role="tab" aria-selected={tab === x} className={tab === x ? "on" : ""} onClick={() => go(x)}>
            {t(("u.tab." + x) as Key)}
            {x === "inputs" && d.inputs.open > 0 && <span className="dot">{d.inputs.open}</span>}
          </button>
        ))}
      </div>

      {tab === "overview" && <Overview d={d} base={base} rev={rev} go={go} />}
      {tab === "plan" && <Plan base={base} />}
      {tab === "deliverables" && <Deliverables base={base} />}
      {tab === "inputs" && <Inputs base={base} rev={rev} onSent={() => setRev((n) => n + 1)} initialKind={sp.get("kind") || "voice_of_customer"} />}
      {tab === "requirements" && <Requirements base={base} rev={rev} />}
      {tab === "reports" && <Reports base={base} go={go} />}
    </>
  );
}

/* ---------------- overview ---------------- */
function Overview({ d, base, rev, go }: { d: PortfolioProject; base: string; rev: number; go: (t: Tab) => void }) {
  const { t } = useI18n();
  const fmt = useFmt();
  const dels = useApi<DeliverableItem[]>(base + "/deliverables?r=" + rev);
  const reqs = useApi<RequirementItem[]>(base + "/requirements?r=" + rev);
  const reps = useApi<ReportItem[]>(base + "/reports");
  const counts = (s: string) => dels.data?.filter((x) => x.status === s).length ?? 0;
  const openQ = reqs.data?.filter((r) => r.open_questions.length > 0).length ?? 0;
  const attention: [string, string, Tab][] = [];
  if (d.deliverables.overdue > 0) attention.push([`${t("u.p.overdueDeliverables")}: ${d.deliverables.overdue}`, "bad", "deliverables"]);
  if (d.inputs.open > 0) attention.push([`${t("u.p.openInputs")}: ${d.inputs.open}`, "accent", "inputs"]);
  if (openQ > 0) attention.push([`${t("u.p.openQuestions")}: ${openQ}`, "warn", "requirements"]);
  return (
    <div className="cols2">
      <div className="card">
        <h2>{t("u.p.milestones")}</h2>
        <ol className="miles">
          {(d.milestones ?? []).map((m) => (
            <li key={m.name} className={m.done ? "done" : ""}>
              <span className="mdot" />
              <div><b>{m.name}</b><div className="muted small">{fmt.date(m.date)}</div></div>
            </li>
          ))}
        </ol>
      </div>
      <div className="grid" style={{ gap: 14 }}>
        <div className="card">
          <h2>{t("u.p.attention")}</h2>
          {attention.length === 0 ? <div className="alert ok">{t("u.p.noAttention")}</div> : attention.map(([txt, tone, tb]) => (
            <button key={txt} className={"alert " + (tone === "bad" ? "bad" : "")} style={{ width: "100%", textAlign: "left" }} onClick={() => go(tb)}>{txt}</button>
          ))}
        </div>
        <div className="card">
          <h2>{t("u.tab.deliverables")}</h2>
          <div className="row">
            {(["delivered", "in_review", "in_progress", "planned"] as const).map((s) => (
              <div key={s} className="mini"><b>{counts(s)}</b><span>{t(("u.ds." + s) as Key)}</span></div>
            ))}
          </div>
        </div>
        <div className="card">
          <h2>{t("u.p.latestReports")}</h2>
          {reps.data?.slice(0, 3).map((r) => (
            <div key={r.id} className="item"><b>{r.title}</b> <span className="muted">· {fmt.date(r.date)}</span><div className="muted small">{r.summary}</div></div>
          ))}
          {reps.data?.length === 0 && <p className="muted">{t("u.rp.none")}</p>}
        </div>
      </div>
    </div>
  );
}

/* ---------------- deliverables ---------------- */
function Deliverables({ base }: { base: string }) {
  const { t } = useI18n();
  const fmt = useFmt();
  const { data, loading, error } = useApi<DeliverableItem[]>(base + "/deliverables");
  const [status, setStatus] = useState("");
  const order: Record<string, number> = { in_review: 0, in_progress: 1, planned: 2, delivered: 3 };
  const rows = (data ?? []).filter((x) => !status || x.status === status).sort((a, b) => order[a.status] - order[b.status] || (a.due ?? "").localeCompare(b.due ?? ""));
  const tone = (s: string) => (s === "delivered" ? "ok" : s === "in_review" ? "accent" : s === "in_progress" ? "warn" : undefined);
  return (
    <>
      <State loading={loading} error={error} empty={!!data && data.length === 0} />
      {data && data.length > 0 && (
        <>
          <div className="filters">
            {["", "delivered", "in_review", "in_progress", "planned"].map((s) => (
              <button key={s} className={"chipbtn" + (status === s ? " on" : "")} onClick={() => setStatus(s)}>
                {s ? t(("u.ds." + s) as Key) : t("u.f.all")} <span className="muted">{s ? data.filter((x) => x.status === s).length : data.length}</span>
              </button>
            ))}
          </div>
          <div className="card scroll">
            <table>
              <thead><tr><th>{t("u.d.name")}</th><th>{t("u.d.discipline")}</th><th>{t("u.d.format")}</th><th>{t("u.d.rev")}</th><th>{t("u.d.status")}</th><th>{t("u.d.due")}</th><th /></tr></thead>
              <tbody>
                {rows.map((x) => (
                  <tr key={x.id}>
                    <td><b>{x.name}</b><div className="muted mono small">{x.code}</div></td>
                    <td>{t(("projects.disc." + x.discipline) as Key)}</td>
                    <td><Badge>.{x.format}</Badge></td>
                    <td>{x.revision}</td>
                    <td><Badge tone={tone(x.status)}>{t(("u.ds." + x.status) as Key)}</Badge></td>
                    <td className={x.overdue ? "err" : ""}>{x.status === "delivered" ? `${t("u.d.deliveredOn")} ${fmt.date(x.delivered_on)}` : `${t("u.d.dueOn")} ${fmt.date(x.due)}`}</td>
                    <td>{x.downloadable ? <a className="btn" href={`/api${base}/deliverables/${x.id}/download`}>{t("u.d.download")}</a> : <span className="muted">{x.status === "delivered" ? t("u.d.na") : ""}</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {data && data.length === 0 && <div className="state">{t("u.d.none")}</div>}
    </>
  );
}

/* ---------------- inputs ---------------- */
function Inputs({ base, rev, onSent, initialKind }: { base: string; rev: number; onSent: () => void; initialKind: string }) {
  const { t } = useI18n();
  const fmt = useFmt();
  const [r, setR] = useState(0);
  const list = useApi<InputItem[]>(base + `/inputs?r=${rev}-${r}`);
  const [kind, setKind] = useState(initialKind);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setOk(false);
    setBusy(true);
    const fd = new FormData();
    fd.append("kind", kind);
    fd.append("title", title);
    fd.append("text", text);
    Array.from(files ?? []).forEach((f) => fd.append("files", f));
    try {
      const res = await fetch("/api" + base + "/inputs", { method: "POST", body: fd });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setErrs(new ApiError(res.status, body).fieldErrors);
        if (!Object.keys(new ApiError(res.status, body).fieldErrors).length) setErrs({ text: t("u.i.error") });
      } else {
        setErrs({}); setTitle(""); setText(""); setFiles(null); setOk(true); setR((n) => n + 1); onSent();
        (document.getElementById("input-files") as HTMLInputElement | null)?.setAttribute("value", "");
      }
    } finally {
      setBusy(false);
    }
  };
  const tone = (s: string) => (s === "structured" ? "ok" : s === "analyzing" ? "warn" : "accent");
  return (
    <div className="cols2">
      <form className="card form" onSubmit={submit} noValidate>
        <h2>{t("u.i.title")}</h2>
        <p className="muted">{t("u.i.help")}</p>
        <label className="field"><span>{t("u.i.kind")}</span>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            {["voice_of_customer", "user_story", "meeting_note", "document", "report"].map((k) => <option key={k} value={k}>{t(("u.k." + k) as Key)}</option>)}
          </select>
        </label>
        <label className="field"><span>{t("u.i.subject")}</span>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
          {errs.title && <small className="err">{errs.title}</small>}
        </label>
        <label className="field"><span>{t("u.i.text")}</span>
          <textarea rows={6} value={text} onChange={(e) => setText(e.target.value)} />
          {errs.text && <small className="err">{errs.text}</small>}
        </label>
        <label className="field"><span>{t("u.i.files")}</span>
          <input id="input-files" type="file" multiple onChange={(e) => setFiles(e.target.files)} />
          {errs.files && <small className="err">{errs.files}</small>}
        </label>
        {ok && <div className="alert ok" role="status">{t("u.i.sent")}</div>}
        <div className="row"><button className="primary" type="submit" disabled={busy}>{t("u.i.send")}</button></div>
      </form>
      <div className="card">
        <h2>{t("u.i.list")}</h2>
        <State loading={list.loading && !list.data} error={list.error} />
        {list.data?.length === 0 && <p className="muted">{t("u.i.none")}</p>}
        <div className="scroll">
          {list.data?.map((x) => (
            <div key={x.id} className="item">
              <div className="row between">
                <b>{x.title}</b>
                <Badge tone={tone(x.status)}>{t(("u.is." + x.status) as Key)}</Badge>
              </div>
              <div className="muted small">{t(("u.k." + x.kind) as Key)} · {fmt.date(x.created)} · {x.source}</div>
              {x.text && <p style={{ margin: "6px 0" }}>{x.text}</p>}
              {x.attachments.length > 0 && <div className="muted small">{t("u.i.attachments")}: {x.attachments.map((a) => a.name).join(", ")}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------------- requirements ---------------- */
function Requirements({ base, rev }: { base: string; rev: number }) {
  const { t } = useI18n();
  const { data, loading, error } = useApi<RequirementItem[]>(base + "/requirements?r=" + rev);
  return (
    <>
      <p className="help">{t("u.r.help")}</p>
      <State loading={loading} error={error} />
      {data?.length === 0 && <div className="state">{t("u.r.none")}</div>}
      <div className="grid reqs">
        {data?.map((r) => (
          <div key={r.id} className="card">
            <div className="row between">
              <span className="mono muted">{r.id}</span>
              <div className="row">
                <Badge tone={r.priority === "alta" ? "bad" : r.priority === "media" ? "warn" : undefined}>{t(("u.r.prio." + r.priority) as Key)}</Badge>
                <Badge tone={r.status === "abierto" ? "warn" : "ok"}>{t(("u.r.status." + r.status) as Key)}</Badge>
              </div>
            </div>
            <p style={{ margin: "8px 0", fontWeight: 600 }}>{r.statement}</p>
            <div className="row small"><Badge>{r.type}</Badge>{r.discipline !== "general" && <Badge>{t(("projects.disc." + r.discipline) as Key)}</Badge>}</div>
            {r.acceptance.length > 0 && (<><h4>{t("u.r.acceptance")}</h4><ul>{r.acceptance.map((a) => <li key={a}>{a}</li>)}</ul></>)}
            {r.open_questions.length > 0 && (<><h4 className="warnh">{t("u.r.questions")}</h4><ul>{r.open_questions.map((a) => <li key={a}>{a}</li>)}</ul></>)}
            <div className="muted small">{t("u.r.origin")}: {r.source_titles.join(", ")}</div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ---------------- reports ---------------- */
function Reports({ base, go }: { base: string; go: (t: Tab, x?: Record<string, string>) => void }) {
  const { t } = useI18n();
  const fmt = useFmt();
  const { data, loading, error } = useApi<ReportItem[]>(base + "/reports");
  return (
    <div className="cols2">
      <div className="card">
        <h2>{t("u.rp.title")}</h2>
        <State loading={loading} error={error} />
        {data?.length === 0 && <p className="muted">{t("u.rp.none")}</p>}
        {data?.map((r) => (
          <div key={r.id} className="item">
            <div className="row between">
              <b>{r.title}</b>
              {r.downloadable && <a className="btn" href={`/api${base}/reports/${r.id}/download`}>{t("u.d.download")}</a>}
            </div>
            <div className="muted small">{fmt.date(r.date)} · {r.type}</div>
            <p style={{ margin: "6px 0" }}>{r.summary}</p>
          </div>
        ))}
      </div>
      <div className="card">
        <h2>{t("u.rp.report")}</h2>
        <p className="muted">{t("u.rp.reportHelp")}</p>
        <button className="primary" onClick={() => go("inputs", { kind: "report" })}>{t("u.rp.report")}</button>
      </div>
    </div>
  );
}

/* ---------------- plan (read-only view of the WBS and the schedule) ---------------- */
function Plan({ base }: { base: string }) {
  const { t } = useI18n();
  const wbs = useApi<WbsView>(base + "/wbs");
  const sch = useApi<ScheduleView>(base + "/schedule");
  if (!wbs.data || !sch.data) return <State loading={wbs.loading || sch.loading} error={wbs.error || sch.error} />;
  if (wbs.data.nodes.length === 0 && sch.data.activities.length === 0) return <div className="state">{t("plan.empty")}</div>;
  return (
    <div className="grid" style={{ gap: 14 }}>
      <Gantt schedule={sch.data} today={new Date().toISOString().slice(0, 10)} />
      <WbsTree wbs={wbs.data} />
    </div>
  );
}
