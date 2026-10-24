import { FormEvent, useState } from "react";
import { ApiError, Badge, RegisterDef, RegisterField, RegisterRecord, RegistersView, State, api, useApi, useI18n } from "@epc/ui";

const json = { "Content-Type": "application/json" };

function optionLabel(f: RegisterField, v: unknown): string {
  return f.options?.find((o) => o.id === v)?.label ?? (v == null ? "" : String(v));
}

/** Project registers of the methodology (risks, changes, issues, decisions, assumptions, stakeholders). Records are never deleted: they change status and keep their history. */
export default function Registers({ client, code }: { client: string; code: string }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/registers`;
  const [rev, setRev] = useState(0);
  const view = useApi<RegistersView>(`${base}?r=${rev}`);
  const [kind, setKind] = useState("");
  if (!view.data) return <State loading={view.loading} error={view.error} />;
  if (view.data.available === false) return <div className="state">{t("reg.unavailable")} ({view.data.methodology.toUpperCase()})</div>;
  const def = view.data.registers.find((r) => r.id === kind) ?? view.data.registers[0];
  return (
    <div className="grid" style={{ gap: 14 }}>
      <p className="muted small" style={{ margin: 0 }}>{t("reg.help")}</p>
      <div className="subtabs" role="tablist">
        {view.data.registers.map((r) => (
          <button key={r.id} role="tab" aria-selected={def.id === r.id} className={def.id === r.id ? "on" : ""} onClick={() => setKind(r.id)}>
            {r.name} <span className="muted small">{r.counts.active}</span>
          </button>
        ))}
      </div>
      <Register key={def.id} base={base} def={def} onChanged={() => setRev((n) => n + 1)} rev={rev} />
    </div>
  );
}

function Register({ base, def, onChanged, rev }: { base: string; def: RegisterDef; onChanged: () => void; rev: number }) {
  const { t } = useI18n();
  const list = useApi<RegisterRecord[]>(`${base}/${def.id}?r=${rev}`);
  const [showClosed, setShowClosed] = useState(false);
  const [form, setForm] = useState<{ id: string | null; values: Record<string, unknown> } | null>(null);
  const [err, setErr] = useState<Record<string, string>>({});
  const fields = new Map(def.fields.map((f) => [f.id, f]));
  const blank = () => Object.fromEntries(def.fields.map((f) => [f.id, f.default ?? ""]));

  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    const body: Record<string, unknown> = {};
    for (const f of def.fields) {
      const v = form.values[f.id];
      if (form.id === null || v !== (list.data?.find((r) => r.id === form.id)?.[f.id] ?? "")) body[f.id] = v === "" ? null : v;
    }
    try {
      await api(form.id ? `${base}/${def.id}/${form.id}` : `${base}/${def.id}`, { method: form.id ? "PATCH" : "POST", headers: json, body: JSON.stringify(body) });
      setForm(null); setErr({}); onChanged();
    } catch (x) { setErr(x instanceof ApiError ? x.fieldErrors : { error: String(x) }); }
  };
  const set = (id: string, v: unknown) => form && setForm({ ...form, values: { ...form.values, [id]: v } });
  const cell = (r: RegisterRecord, id: string) => {
    if (id === "level") return r.level == null ? "" : <Badge tone={r.level_name === "high" ? "bad" : r.level_name === "medium" ? "warn" : "ok"}>{String(r.level)}</Badge>;
    const f = fields.get(id);
    if (!f) return String(r[id] ?? "");
    if (f.type === "enum") return id === "status" ? <Badge tone={def.closed_states.includes(String(r[id])) ? undefined : "accent"}>{optionLabel(f, r[id])}</Badge> : optionLabel(f, r[id]);
    return String(r[id] ?? "");
  };
  const label = (id: string) => (id === "level" ? t("reg.level") : fields.get(id)?.label ?? id);
  const rows = (list.data ?? []).filter((r) => showClosed || !def.closed_states.includes(String(r.status)));
  const editing = form?.id ? list.data?.find((r) => r.id === form.id) : null;

  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="card">
        <div className="row between">
          <h2 style={{ margin: 0 }}>{def.name}</h2>
          <div className="row">
            {def.closed_states.length > 0 && <label className="small"><input type="checkbox" checked={showClosed} onChange={(e) => setShowClosed(e.target.checked)} /> {t("reg.showClosed")}</label>}
            {!form && <button className="primary" onClick={() => { setForm({ id: null, values: blank() }); setErr({}); }}>+ {t("reg.new")}</button>}
          </div>
        </div>
        {!list.data ? <State loading={list.loading} error={list.error} /> : rows.length === 0 ? <div className="state">{t("reg.none")}</div> : (
          <table>
            <thead><tr><th>{t("reg.id")}</th>{def.columns.map((c) => <th key={c}>{label(c)}</th>)}<th /></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono"><b>{r.id}</b></td>
                  {def.columns.map((c) => <td key={c}>{cell(r, c)}</td>)}
                  <td><button onClick={() => { setForm({ id: r.id, values: Object.fromEntries(def.fields.map((f) => [f.id, r[f.id] ?? ""])) }); setErr({}); }}>{t("reg.edit")}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {form && (
        <form className="card" onSubmit={save}>
          <h3 style={{ marginTop: 0 }}>{form.id ? `${t("reg.edit")} ${form.id}` : `${t("reg.new")} · ${def.name}`}</h3>
          <div className="fgrid">
            {def.fields.map((f) => (
              <label key={f.id} className="field" style={f.type === "longtext" ? { gridColumn: "1 / -1" } : undefined}>
                <span>{f.label}{f.required ? " *" : ""}</span>
                {f.type === "enum" ? (
                  <select value={String(form.values[f.id] ?? "")} onChange={(e) => set(f.id, e.target.value)}>
                    {!f.required && <option value="" />}
                    {f.options!.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
                  </select>
                ) : f.type === "longtext" ? (
                  <textarea rows={3} value={String(form.values[f.id] ?? "")} onChange={(e) => set(f.id, e.target.value)} />
                ) : (
                  <input type={f.type === "number" ? "number" : f.type === "date" ? "date" : "text"} min={f.min} max={f.max} value={String(form.values[f.id] ?? "")} onChange={(e) => set(f.id, e.target.value)} />
                )}
                {err[f.id] && <span className="small" style={{ color: "var(--bad)" }}>{err[f.id]}</span>}
              </label>
            ))}
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="primary" type="submit">{t("reg.save")}</button>
            <button type="button" onClick={() => { setForm(null); setErr({}); }}>{t("common.close")}</button>
          </div>
          {err.error && <div className="alert bad" style={{ marginTop: 8 }}>{err.error}</div>}
          {editing && (
            <>
              <h4>{t("reg.history")}</h4>
              <ul className="qlist">
                {[...editing.history].reverse().map((h, i) => (
                  <li key={i} className="small">
                    <b>{new Date(h.at).toLocaleString()}</b> · {h.by} · {h.action === "created" ? t("reg.created") : Object.entries(h.changes ?? {}).map(([k, v]) => `${label(k)}: ${String(v[0] ?? "") || "—"} → ${String(v[1] ?? "") || "—"}`).join("; ")}
                  </li>
                ))}
              </ul>
            </>
          )}
        </form>
      )}
    </div>
  );
}
