import { useState } from "react";
import { Badge, FeederRow, Key, SldFeeder, WiringDefaults, useI18n } from "@epc/ui";

interface Props {
  feeders: SldFeeder[];
  rows: FeederRow[];                                           // what the last calculation gave, by position
  phases: string[]; methods: string[]; insulations: string[]; materials: string[];
  defaults?: WiringDefaults;
  blocked: string;                                             // why nothing can be added now ("" when it can)
  busy: boolean;
  onChange: (next: SldFeeder[]) => void;                       // the board saves and calculates with them
}

interface Editing { index: number | null; draft: SldFeeder }
const blank = (): SldFeeder => ({ name: "", source: "", phase: "3F", length_m: 0, load_a: null, method: "", insulation: "", material: "" });
const num = (v: string): number | null => (v.trim() === "" ? null : Number(v.replace(",", ".")));

/** The acometidas of a board: the cables that feed it (the utility, a generator...), each with its own phase, length, current and wiring, sized like any circuit. */
export default function FeedersCard({ feeders, rows, phases, methods, insulations, materials, defaults, blocked, busy, onChange }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const [editing, setEditing] = useState<Editing | null>(null);
  const [err, setErr] = useState("");
  const close = () => { setEditing(null); setErr(""); };
  const set = (patch: Partial<SldFeeder>) => setEditing((e) => (e ? { ...e, draft: { ...e.draft, ...patch } } : e));
  const accept = () => {
    if (!editing) return;
    const name = editing.draft.name.trim();
    if (name && feeders.some((f, i) => i !== editing.index && f.name.trim() === name)) { setErr(tl("feeder.nameTaken")); return; }
    const next = { ...editing.draft, name, source: editing.draft.source.trim() };
    onChange(editing.index === null ? [...feeders, next] : feeders.map((f, i) => (i === editing.index ? next : f)));
    close();
  };
  const pick = (value: string, items: string[], on: (v: string) => void, label: (v: string) => string, byDefault?: string) => (
    <select value={value} onChange={(e) => on(e.target.value)}>
      <option value="">{tl("sld.byCriteria")}{byDefault ? ` (${label(byDefault)})` : ""}</option>
      {items.map((x) => <option key={x} value={x}>{label(x)}</option>)}
    </select>
  );
  const method = (m: string) => `${m} · ${tl("sld.method." + m)}`;
  const wiring = (f: SldFeeder, r?: FeederRow) => `${r?.metodo || f.method || "–"} · ${(r?.material || f.material || defaults?.material || "").replace(/^./, (x) => x.toUpperCase())} ${(r?.aislacion || f.insulation || defaults?.insulation || "").toUpperCase()}`;
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
        <h2 style={{ margin: 0 }}>{tl("feeder.title")} <span className="muted small">({feeders.length})</span></h2>
        <button className={editing ? "" : "primary"} disabled={!!blocked || busy} title={blocked} onClick={() => (editing?.index === null ? close() : (setEditing({ index: null, draft: blank() }), setErr("")))}>
          {editing?.index === null ? tl("projects.cancel") : `+ ${tl("feeder.add")}`}
        </button>
      </div>
      <p className="muted small" style={{ margin: "6px 0 8px" }}>{tl("feeder.help")}</p>
      {blocked && <p className="small" role="alert" style={{ margin: "0 0 8px", color: "var(--bad, #b3261e)" }}>{blocked}</p>}
      {feeders.length === 0 && !editing && <div className="state">{tl("feeder.none")}</div>}
      {feeders.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table className="sldtable">
            <thead><tr>{(["feeder.name", "feeder.source", "sld.phase", "sld.length", "feeder.load", "sld.install", "sld.col.ib", "sld.col.in", "sld.col.s", "sld.col.du", "sld.col.device", "sld.col.ok"] as Key[]).map((h) => <th key={h}>{tl(h)}</th>)}<th /></tr></thead>
            <tbody>
              {feeders.map((f, i) => {
                const r = rows[i];
                return (
                  <tr key={i} className={editing?.index === i ? "draft" : undefined}>
                    <td className="mono">{r?.name || f.name || `ACOMETIDA-${i + 1}`}</td><td>{f.source}</td><td>{f.phase}</td><td className="mono">{f.length_m}</td>
                    <td className="mono">{f.load_a ?? tl("feeder.head")}</td><td style={{ whiteSpace: "nowrap" }}>{wiring(f, r)}</td>
                    <td className="mono">{r?.Ib}</td><td className="mono">{r?.In}</td><td className="mono">{r?.S_mm2}</td><td className="mono">{r?.du_pct}</td><td>{r?.disp}</td>
                    <td>{r?.cumple == null ? "" : r.cumple ? <Badge tone="ok">✓</Badge> : <Badge tone="bad">✗</Badge>}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button onClick={() => { setEditing({ index: i, draft: { ...f } }); setErr(""); }} title={tl("sld.editRow")} aria-label={tl("sld.editRow")} disabled={busy}>✎</button>{" "}
                      <button onClick={() => { onChange(feeders.filter((_, j) => j !== i)); close(); }} title={tl("sld.removeRow")} aria-label={tl("sld.removeRow")} disabled={busy}>✕</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {editing && (
        <div role="group" aria-label={tl("feeder.title")} style={{ marginTop: 12 }} onKeyDown={(e) => { if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT") { e.preventDefault(); accept(); } else if (e.key === "Escape") close(); }}>
          <p className="small" style={{ margin: "0 0 6px" }}><b>{editing.index === null ? tl("feeder.new") : `${tl("sld.editing")} ${feeders[editing.index]?.name || `ACOMETIDA-${editing.index + 1}`}`}</b></p>
          <div className="fgrid">
            <label className="field"><span>{tl("feeder.name")}</span><input autoFocus maxLength={30} value={editing.draft.name} onChange={(e) => set({ name: e.target.value })} placeholder={tl("feeder.nameHint")} /></label>
            <label className="field"><span>{tl("feeder.source")}</span><input maxLength={80} value={editing.draft.source} onChange={(e) => set({ source: e.target.value })} placeholder={tl("feeder.sourceHint")} /></label>
            <label className="field"><span>{tl("sld.phase")}</span><select value={editing.draft.phase} onChange={(e) => set({ phase: e.target.value })}>{phases.map((p) => <option key={p}>{p}</option>)}</select></label>
            <label className="field"><span>{tl("sld.length")}</span><input type="number" step="any" min={0} value={editing.draft.length_m} onChange={(e) => set({ length_m: Number(e.target.value) })} /></label>
            <label className="field"><span>{tl("feeder.load")}</span><input type="number" step="any" min={0} value={editing.draft.load_a ?? ""} onChange={(e) => set({ load_a: num(e.target.value) })} placeholder={tl("feeder.loadHint")} /></label>
            <label className="field"><span>{tl("sld.install")}</span>{pick(editing.draft.method ?? "", methods, (v) => set({ method: v }), method, defaults?.method)}</label>
            <label className="field"><span>{tl("sld.insulation")}</span>{pick(editing.draft.insulation ?? "", insulations, (v) => set({ insulation: v }), (m) => m.toUpperCase(), defaults?.insulation)}</label>
            <label className="field"><span>{tl("sld.conductor")}</span>{pick(editing.draft.material ?? "", materials, (v) => set({ material: v }), (m) => tl("sld.material." + m), defaults?.material)}</label>
          </div>
          {err && <p className="small" role="alert" style={{ margin: "6px 0 0", color: "var(--bad, #b3261e)" }}>{err}</p>}
          <div className="row" style={{ gap: 8, marginTop: 8 }}>
            <button className="primary" onClick={accept} disabled={busy}>{tl("sld.accept")}</button>
            <button onClick={close}>{tl("projects.cancel")}</button>
          </div>
        </div>
      )}
      {rows.some((r) => r.avisos && r.avisos.length > 0) && <ul className="muted small" style={{ margin: "8px 0 0" }}>{rows.flatMap((r) => (r.avisos ?? []).map((a) => <li key={r.name + a}>{r.name}: {a}</li>))}</ul>}
    </div>
  );
}
