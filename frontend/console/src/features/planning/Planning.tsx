import { FormEvent, useState } from "react";
import { ApiError, BacklogItem, BacklogView, Badge, Gantt, Key, Page, Project, ScheduleView, State, WbsTree, WbsView, api, useApi, useI18n } from "@epc/ui";

const STATUSES = ["backlog", "todo", "doing", "done"] as const;
const TYPES = ["task", "change", "risk", "question", "defect"] as const;
const PRIORITIES = ["P1", "P2", "P3"] as const;
const prioTone = (p: string) => (p === "P1" ? "bad" : p === "P2" ? "warn" : undefined);

/** Internal planning of one project: backlog (editable), WBS and schedule (read-only here; written by the engineer or by Claude). */
export default function Planning() {
  const { t } = useI18n();
  const projects = useApi<Project[]>("/projects");
  const [pid, setPid] = useState("");
  const list = projects.data?.filter((p) => !p.is_template) ?? [];
  const id = pid || list[0]?.id || "";
  return (
    <Page title={t("nav.planning")} help={t("bl.help")}>
      <label className="field" style={{ maxWidth: 420, marginBottom: 14 }}>
        <span>{t("bl.project")}</span>
        <select value={id} onChange={(e) => setPid(e.target.value)}>
          {list.map((p) => <option key={p.id} value={p.id}>{p.id} · {p.name}</option>)}
        </select>
      </label>
      {projects.loading || projects.error ? <State loading={projects.loading} error={projects.error} /> : id && <Board key={id} id={id} />}
    </Page>
  );
}

function Board({ id }: { id: string }) {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const backlog = useApi<BacklogView>(`/projects/${id}/backlog?r=${rev}`);
  const wbs = useApi<WbsView>(`/app/projects/${id}/wbs`);
  const sch = useApi<ScheduleView>(`/app/projects/${id}/schedule`);
  const [err, setErr] = useState<Record<string, string>>({});
  const [form, setForm] = useState({ title: "", type: "task", priority: "P2", estimate_h: 0 });

  const add = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api(`/projects/${id}/backlog`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
      setForm({ ...form, title: "" });
      setErr({});
      setRev((n) => n + 1);
    } catch (x) {
      if (x instanceof ApiError) setErr(x.fieldErrors);
    }
  };
  const move = async (it: BacklogItem, status: string) => {
    await api(`/projects/${id}/backlog/${it.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) });
    setRev((n) => n + 1);
  };

  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{t("bl.title")}</h2>
          {backlog.data && (
            <span className="muted small">
              {STATUSES.map((s) => `${t(("bl.s." + s) as Key)} ${backlog.data!.counts[s]}`).join(" · ")} · {backlog.data.estimate_open_h} {t("bl.openHours")}
            </span>
          )}
        </div>
        <form className="row" style={{ margin: "12px 0", alignItems: "flex-end", flexWrap: "wrap" }} onSubmit={add}>
          <label className="field" style={{ flex: "1 1 260px" }}>
            <span>{t("bl.newTitle")}</span>
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} aria-invalid={!!err.title} />
          </label>
          <label className="field">
            <span>{t("bl.type")}</span>
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {TYPES.map((x) => <option key={x} value={x}>{t(("bl.t." + x) as Key)}</option>)}
            </select>
          </label>
          <label className="field">
            <span>{t("bl.priority")}</span>
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              {PRIORITIES.map((x) => <option key={x}>{x}</option>)}
            </select>
          </label>
          <label className="field" style={{ width: 120 }}>
            <span>{t("bl.estimate")}</span>
            <input type="number" min={0} value={form.estimate_h} onChange={(e) => setForm({ ...form, estimate_h: Number(e.target.value) })} />
          </label>
          <button className="primary" type="submit">{t("bl.add")}</button>
        </form>
        {backlog.data && backlog.data.items.length === 0 && <div className="state">{t("bl.empty")}</div>}
        {backlog.data && backlog.data.items.length > 0 && (
          <table>
            <tbody>
              {backlog.data.items.map((it) => (
                <tr key={it.id}>
                  <td className="mono">{it.id}</td>
                  <td>{it.title}</td>
                  <td><Badge>{t(("bl.t." + it.type) as Key)}</Badge></td>
                  <td><Badge tone={prioTone(it.priority)}>{it.priority}</Badge></td>
                  <td className="mono">{it.estimate_h} h</td>
                  <td>
                    <select value={it.status} aria-label={t("bl.status")} onChange={(e) => move(it, e.target.value)}>
                      {STATUSES.map((s) => <option key={s} value={s}>{t(("bl.s." + s) as Key)}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {sch.data && sch.data.activities.length > 0 && <Gantt schedule={sch.data} today={new Date().toISOString().slice(0, 10)} />}
      {wbs.data && wbs.data.nodes.length > 0 && <WbsTree wbs={wbs.data} />}
    </div>
  );
}
