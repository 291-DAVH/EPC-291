import { useEffect, useState } from "react";
import { ApiError, JSON_HEADERS, NormPoint, NormPointRow, NormUnit, api, useApi } from "../api";
import { Badge, Page, State } from "../components";
import { useI18n } from "../i18n";

const STATUS_TONE: Record<string, "ok" | "bad" | "warn" | undefined> = { approved: "ok", rejected: "bad", stale: "warn", pending: undefined };

function errorText(x: unknown): string {
  return x instanceof ApiError ? Object.entries(x.fieldErrors).map(([k, v]) => `${k}: ${v}`).join(" · ") || String(x.status) : "error";
}

/** Review of the norm data by the norm reviewer: by norm, every point (rule, calculation table, design criterion) can be corrected and approved. */
export default function Norms() {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const units = useApi<NormUnit[]>(`/norms/units?r=${rev}`);
  const [unitId, setUnitId] = useState("");
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [key, setKey] = useState<string | null>(null);
  const reload = () => setRev((n) => n + 1);
  const unit = units.data?.find((u) => u.id === unitId) ?? units.data?.[0];
  const pts = useApi<{ total: number; items: NormPointRow[] }>(unit ? `/norms/units/${encodeURIComponent(unit.id)}/points?status=${status}&q=${encodeURIComponent(q)}&r=${rev}` : null);
  return (
    <Page title={t("norms.title")} help={t("norms.help")}>
      {!units.data ? <State loading={units.loading} error={units.error} /> : (
        <div className="normgrid">
          <div className="card normunits">
            {units.data.map((u) => {
              const c = u.counts;
              return (
                <button key={u.id} className={"normunit" + (unit?.id === u.id ? " on" : "")} onClick={() => { setUnitId(u.id); setKey(null); }}>
                  <b>{u.name}</b>
                  <span className="muted small">{t(("norms.kind." + u.kind) as never)} · {c.approved}/{c.total} {t("norms.approvedShort")}{c.stale ? ` · ${c.stale} ${t("norms.stale").toLowerCase()}` : ""}{c.rejected ? ` · ${c.rejected} ${t("norms.rejected").toLowerCase()}` : ""}</span>
                  <span className="progress"><span style={{ width: `${c.total ? (100 * c.approved) / c.total : 0}%` }} /></span>
                </button>
              );
            })}
          </div>
          <div className="normmain">
            {unit && (
              <div className="card">
                <div className="row between">
                  <h2 style={{ margin: 0 }}>{unit.name}</h2>
                  <div className="row">
                    <input placeholder={t("common.search")} value={q} onChange={(e) => setQ(e.target.value)} />
                    <select value={status} onChange={(e) => setStatus(e.target.value)}>
                      <option value="">{t("common.all")}</option>
                      {["pending", "approved", "rejected", "stale"].map((s) => <option key={s} value={s}>{t(("norms." + s) as never)}</option>)}
                    </select>
                  </div>
                </div>
                {!pts.data ? <State loading={pts.loading} error={pts.error} /> : pts.data.items.length === 0 ? <div className="state">{t("common.none")}</div> : (
                  <div className="scroll">
                    <table>
                      <thead><tr><th>{t("norms.point")}</th><th>{t("norms.group")}</th><th>{t("norms.ref")}</th><th>{t("norms.status")}</th><th>{t("norms.by")}</th></tr></thead>
                      <tbody>
                        {pts.data.items.map((p) => (
                          <tr key={p.key} className={"clickable" + (key === p.key ? " sel" : "")} onClick={() => setKey(p.key)}>
                            <td><b>{p.title}</b><div className="muted small mono">{p.key}</div></td>
                            <td className="small">{p.group}</td>
                            <td className="small">{p.ref}</td>
                            <td><Badge tone={STATUS_TONE[p.status]}>{t(("norms." + p.status) as never)}</Badge></td>
                            <td className="small">{p.by ? `${p.by} · ${new Date(p.at!).toLocaleDateString()}` : ""}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
            {unit && key && <PointEditor key={unit.id + key} unitId={unit.id} pointKey={key} onChanged={reload} onClose={() => setKey(null)} />}
          </div>
        </div>
      )}
    </Page>
  );
}

type Draft = Record<string, string>;

function toDraft(p: NormPoint): Draft {
  const v = p.value as Record<string, any>;
  if (p.kind === "rule") {
    return { tema: v.tema, regla: v.regla, tipo: v.tipo, aplica_a: (v.aplica_a ?? []).join(", "), parametros: JSON.stringify(v.parametros ?? {}, null, 1),
             norma: v.fuente?.norma ?? "", edicion: v.fuente?.edicion ?? "", clausula: v.fuente?.clausula ?? "", pagina_impresa: String(v.fuente?.pagina_impresa ?? "") };
  }
  if (p.kind === "lighting_rule") {
    return { summary: v.summary ?? "", value: v.value === null || v.value === undefined ? "" : String(v.value), unit: v.unit ?? "lx", plane: v.plane ?? "", clause: v.clause ?? "" };
  }
  if (p.kind === "criterion") {
    return { label_es: v.label.es, label_en: v.label.en, unit: v.unit ?? "", default: String(v.default), options: (v.options ?? []).join(", "), min: String(v.min ?? ""), max: String(v.max ?? "") };
  }
  return { value: JSON.stringify(v, null, 1) };
}

/** The patch with only what the reviewer changed. Throws a text when a field cannot be read. */
function toPatch(p: NormPoint, d: Draft, o: Draft): Record<string, unknown> {
  const v = p.value as Record<string, any>;
  const patch: Record<string, unknown> = {};
  const changed = (k: string) => d[k] !== o[k];
  if (p.kind === "rule") {
    for (const k of ["tema", "regla", "tipo"]) if (changed(k)) patch[k] = d[k];
    if (changed("aplica_a")) patch.aplica_a = d.aplica_a.split(",").map((x) => x.trim()).filter(Boolean);
    if (changed("parametros")) { try { patch.parametros = JSON.parse(d.parametros); } catch { throw new Error("parametros: JSON"); } }
    const f: Record<string, unknown> = {};
    for (const k of ["norma", "edicion", "clausula"]) if (changed(k)) f[k] = d[k];
    if (changed("pagina_impresa")) f.pagina_impresa = Number(d.pagina_impresa);
    if (Object.keys(f).length) patch.fuente = f;
  } else if (p.kind === "lighting_rule") {
    for (const k of ["summary", "unit", "plane", "clause"]) if (changed(k)) patch[k] = d[k];
    if (changed("value")) patch.value = Number(d.value);
  } else if (p.kind === "criterion") {
    if (changed("label_es") || changed("label_en")) patch.label = { es: d.label_es, en: d.label_en };
    if (changed("unit")) patch.unit = d.unit;
    const numeric = v.type === "number" || (v.options ?? []).every((x: unknown) => typeof x === "number");
    const val = (s: string) => (numeric ? Number(s) : s);
    if (changed("default")) patch.default = val(d.default);
    if (changed("options")) patch.options = d.options.split(",").map((x) => x.trim()).filter(Boolean).map(val);
    if (changed("min")) patch.min = Number(d.min);
    if (changed("max")) patch.max = Number(d.max);
  } else if (changed("value")) {
    try { patch.value = JSON.parse(d.value); } catch { throw new Error("value: JSON"); }
  }
  return patch;
}

function PointEditor({ unitId, pointKey, onChanged, onClose }: { unitId: string; pointKey: string; onChanged: () => void; onClose: () => void }) {
  const { t } = useI18n();
  const path = `/norms/units/${encodeURIComponent(unitId)}/points/${encodeURIComponent(pointKey)}`;
  const [rev, setRev] = useState(0);
  const pt = useApi<NormPoint>(`${path}?r=${rev}`);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [orig, setOrig] = useState<Draft | null>(null);
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  useEffect(() => { if (pt.data) { const d = toDraft(pt.data); setDraft(d); setOrig(d); } }, [pt.data]);
  if (!pt.data || !draft || !orig) return <State loading={pt.loading} error={pt.error} />;
  const p = pt.data;
  const set = (k: string, v: string) => setDraft({ ...draft, [k]: v });
  const done = (text: string) => { setMsg({ ok: true, text }); setNote(""); setRev((n) => n + 1); onChanged(); };
  const run = async (fn: () => Promise<unknown>, ok: string) => { try { await fn(); done(ok); } catch (x) { setMsg({ ok: false, text: x instanceof Error && !(x instanceof ApiError) ? x.message : errorText(x) }); } };
  const dirty = JSON.stringify(draft) !== JSON.stringify(orig);
  const save = (approve: boolean) => run(() => api(path, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ patch: toPatch(p, draft, orig), note, approve }) }), approve ? t("norms.savedApproved") : t("norms.saved"));
  const field = (k: string, label: string, wide = false, area = false, mono = false) => (
    <label className="field" style={wide ? { gridColumn: "1 / -1" } : undefined}>
      <span>{label}</span>
      {area ? <textarea rows={mono ? 8 : 3} className={mono ? "mono" : ""} value={draft[k]} onChange={(e) => set(k, e.target.value)} /> : <input value={draft[k]} onChange={(e) => set(k, e.target.value)} />}
    </label>
  );
  return (
    <div className="card" style={{ marginTop: 14 }}>
      <div className="row between">
        <div><h3 style={{ margin: 0 }}>{p.title}</h3><div className="muted small mono">{p.key} · {p.ref}</div></div>
        <div className="row"><Badge tone={STATUS_TONE[p.status]}>{t(("norms." + p.status) as never)}</Badge><button onClick={onClose}>{t("common.close")}</button></div>
      </div>
      {p.status === "stale" && <div className="alert" style={{ marginTop: 8 }}>{t("norms.staleHelp")}</div>}
      {p.review?.note && <div className="muted small" style={{ marginTop: 6 }}>{p.review.by} · {new Date(p.review.at).toLocaleString()}: {p.review.note}</div>}

      <div className="fgrid" style={{ marginTop: 10 }}>
        {p.kind === "rule" && (<>
          {field("tema", t("norms.f.topic"), true)}
          {field("regla", t("norms.f.rule"), true, true)}
          <label className="field"><span>{t("norms.f.type")}</span><select value={draft.tipo} onChange={(e) => set("tipo", e.target.value)}>{["obligatorio", "recomendado", "prohibido"].map((x) => <option key={x}>{x}</option>)}</select></label>
          {field("aplica_a", t("norms.f.appliesTo"))}
          {field("norma", t("norms.f.standard"))}{field("edicion", t("norms.f.edition"))}{field("clausula", t("norms.f.clause"))}{field("pagina_impresa", t("norms.f.page"))}
          {field("parametros", t("norms.f.params"), true, true, true)}
        </>)}
        {p.kind === "lighting_rule" && (<>
          {field("summary", t("norms.f.summary"), true, true)}
          {field("value", t("norms.f.level"))}
          <label className="field"><span>{t("norms.f.unit")}</span><select value={draft.unit} onChange={(e) => set("unit", e.target.value)}>{["lx", "ratio"].map((x) => <option key={x}>{x}</option>)}</select></label>
          {field("plane", t("norms.f.plane"))}{field("clause", t("norms.f.clause"))}
        </>)}
        {p.kind === "criterion" && (<>
          {field("label_es", t("norms.f.labelEs"), true)}{field("label_en", t("norms.f.labelEn"), true)}
          {field("default", t("norms.f.default"))}{field("unit", t("norms.f.unit"))}
          {(p.value as any).type === "choice" ? field("options", t("norms.f.options")) : (<>{field("min", "min")}{field("max", "max")}</>)}
        </>)}
        {p.kind === "table" && (<>
          <div className="muted small" style={{ gridColumn: "1 / -1" }}>{t("norms.f.tableHelp")}</div>
          {field("value", t("norms.f.value"), true, true, true)}
        </>)}
        <label className="field" style={{ gridColumn: "1 / -1" }}><span>{t("norms.note")}</span><input value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("norms.notePlaceholder")} /></label>
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        {dirty && <button onClick={() => save(false)}>{t("norms.save")}</button>}
        {dirty ? <button className="primary" onClick={() => save(true)}>{t("norms.saveApprove")}</button>
               : <button className="primary" onClick={() => run(() => api(`${path}/approve`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ note }) }), t("norms.approvedOk"))}>{t("norms.approve")}</button>}
        <button onClick={() => note.trim() ? run(() => api(`${path}/reject`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ note }) }), t("norms.rejectedOk")) : setMsg({ ok: false, text: t("norms.needNote") })}>{t("norms.reject")}</button>
      </div>
      {msg && <div className={"alert " + (msg.ok ? "ok" : "bad")} style={{ marginTop: 10 }}>{msg.text}</div>}

      <h4>{t("norms.history")}</h4>
      {p.history.length === 0 ? <div className="muted small">{t("norms.noHistory")}</div> : (
        <ul className="qlist">
          {p.history.map((h, i) => (
            <li key={i} className="small">
              <b>{new Date(h.at).toLocaleString()}</b> · {h.by} · {t(("norms.act." + h.action) as never)}{h.note ? ` — ${h.note}` : ""}
              {h.changes && h.changes.length > 0 && <div className="muted mono">{h.changes.slice(0, 6).map((c) => `${c[0]}: ${JSON.stringify(c[1])} → ${JSON.stringify(c[2])}`).join(" · ")}{h.changes.length > 6 ? ` … (+${h.changes.length - 6})` : ""}</div>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
