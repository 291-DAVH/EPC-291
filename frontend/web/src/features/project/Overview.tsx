import { DeliverableItem, Key, PortfolioProject, ReportItem, RequirementItem, useApi, useFmt, useI18n } from "@epc/ui";
import type { Tab } from "./tabs";

export default function Overview({ d, base, rev, go }: { d: PortfolioProject; base: string; rev: number; go: (t: Tab) => void }) {
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
