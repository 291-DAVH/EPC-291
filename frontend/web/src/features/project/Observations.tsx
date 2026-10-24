import { FormEvent, useState } from "react";
import { ApiError, Badge, RegisterDef, RegisterRecord, State, api, useApi, useI18n } from "@epc/ui";

const json = { "Content-Type": "application/json" };
const TONE: Record<string, "ok" | "warn" | "bad" | "accent" | undefined> = { critical: "bad", major: "warn", minor: "accent", info: undefined };

/** Observations of inspections and audits on a project: inspectors and auditors write them, the customer's managers answer, the inspector closes. */
export default function Observations({ base, can }: { base: string; can: (subject: string, action: string) => boolean }) {
  const { t, lang } = useI18n();
  const [rev, setRev] = useState(0);
  const def = useApi<RegisterDef>(`${base}/observations/definition?lang=${lang}`);
  const list = useApi<RegisterRecord[]>(`${base}/observations?r=${rev}`);
  const [form, setForm] = useState({ title: "", type: "inspection", severity: "minor", description: "" });
  const [reply, setReply] = useState<Record<string, string>>({});
  const [err, setErr] = useState("");
  const canWrite = can("observation", "write");
  const canRespond = can("observation", "respond");
  if (!def.data || !list.data) return <State loading error={def.error || list.error} />;
  const field = (id: string) => def.data!.fields.find((f) => f.id === id)!;
  const label = (id: string, v: unknown) => field(id).options?.find((o) => o.id === v)?.label ?? String(v ?? "");
  const run = async (fn: () => Promise<unknown>) => {
    try { await fn(); setErr(""); setRev((n) => n + 1); } catch (x) { setErr(x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || String(x.status) : "error"); }
  };
  const create = (e: FormEvent) => {
    e.preventDefault();
    run(async () => { await api(`${base}/observations`, { method: "POST", headers: json, body: JSON.stringify(form) }); setForm({ ...form, title: "", description: "" }); });
  };
  const patch = (id: string, body: object) => run(() => api(`${base}/observations/${id}`, { method: "PATCH", headers: json, body: JSON.stringify(body) }));
  const select = (id: string, value: string, set: (v: string) => void) => (
    <label className="field"><span>{field(id).label}</span>
      <select value={value} onChange={(e) => set(e.target.value)}>{field(id).options!.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}</select>
    </label>
  );
  return (
    <div className="grid" style={{ gap: 14 }}>
      <p className="muted small" style={{ margin: 0 }}>{t("obs.help")}</p>
      {err && <div className="alert bad">{err}</div>}
      {canWrite && (
        <form className="card" onSubmit={create}>
          <h2 style={{ marginTop: 0 }}>{t("obs.new")}</h2>
          <div className="fgrid">
            <label className="field" style={{ gridColumn: "1 / -1" }}><span>{field("title").label} *</span><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></label>
            {select("type", form.type, (v) => setForm({ ...form, type: v }))}
            {select("severity", form.severity, (v) => setForm({ ...form, severity: v }))}
            <label className="field" style={{ gridColumn: "1 / -1" }}><span>{field("description").label}</span><textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
          </div>
          <div className="row" style={{ marginTop: 10 }}><button className="primary" type="submit">{t("obs.record")}</button></div>
        </form>
      )}
      {list.data.length === 0 ? <div className="state">{t("obs.none")}</div> : list.data.map((o) => (
        <div className="card" key={o.id}>
          <div className="row between">
            <div><span className="mono muted">{o.id}</span> · <b>{String(o.title)}</b></div>
            <div className="row"><Badge tone={TONE[String(o.severity)]}>{label("severity", o.severity)}</Badge><Badge tone={o.status === "closed" ? "ok" : o.status === "answered" ? "accent" : "warn"}>{label("status", o.status)}</Badge></div>
          </div>
          <div className="muted small">{label("type", o.type)} · {o.created_by} · {o.opened}</div>
          {o.description ? <p style={{ margin: "8px 0" }}>{String(o.description)}</p> : null}
          {o.response ? <div className="answer"><b>{field("response").label}:</b> {String(o.response)}</div> : null}
          {o.status !== "closed" && canRespond && !canWrite && (
            <div className="row" style={{ marginTop: 8 }}>
              <input style={{ flex: 1, minWidth: 220 }} placeholder={t("obs.replyPlaceholder")} value={reply[o.id] ?? ""} onChange={(e) => setReply({ ...reply, [o.id]: e.target.value })} />
              <button className="primary" disabled={!(reply[o.id] ?? "").trim()} onClick={() => patch(o.id, { response: reply[o.id] })}>{t("obs.reply")}</button>
            </div>
          )}
          {o.status !== "closed" && canWrite && <div className="row" style={{ marginTop: 8 }}><button onClick={() => patch(o.id, { status: "closed" })}>{t("obs.close")}</button></div>}
        </div>
      ))}
    </div>
  );
}
