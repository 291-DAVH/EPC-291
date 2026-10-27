import { useState } from "react";
import { addCircuit, assignCircuit, Drawing, freeCircuits, loadsOf, ofKind, Ref, removeCircuit, removeMany, setAttr, updateCircuit, updateLine, updateNode } from "./planEditing";
import { isLocked, setLocked, unlocked } from "./planTools";
import { Derived, Kind, Profile } from "./PlanEditor";

/** The side panels of the plan editor: the properties of what is selected (one element, or many to give them a circuit at once), and the circuits routed over the drawing.
 *  Text goes through `t`; changes go out through `onChange`. */
export interface BoardCircuit { tag: string; description: string; board: string }

interface PropsProps {
  drawing: Drawing; selection: Ref[]; derived: Derived | null; profile: Profile | undefined; lang: "es" | "en"; boardCircuits: BoardCircuit[];
  readOnly: boolean; onChange: (d: Drawing) => void; onSelect: (r: Ref[]) => void; t: (key: string) => string;
}

const nameOf = (k: Kind | undefined, lang: "es" | "en") => (k ? `${k.id} · ${k.etiqueta[lang] ?? k.etiqueta.es}` : "");
export const loadKindsOf = (profile: Profile | undefined): Set<string> => new Set((profile?.nodes ?? []).filter((k) => k.carga).map((k) => k.id));

function CircuitSelect({ value, boardCircuits, disabled, onPick, empty }: { value: string; boardCircuits: BoardCircuit[]; disabled?: boolean; onPick: (tag: string) => void; empty: string }) {
  return (
    <select disabled={disabled} value={value} onChange={(e) => onPick(e.target.value)}>
      <option value="">{empty}</option>
      {boardCircuits.map((c) => <option key={c.tag} value={c.tag}>{c.tag}{c.description ? ` · ${c.description}` : ""}</option>)}
    </select>
  );
}

/** Pick everything of one kind (all the luminaires, all the TUG sockets...): the quick way to select what was placed before giving it a circuit. */
function ByKind({ drawing, profile, lang, onSelect, t }: { drawing: Drawing; profile: Profile | undefined; lang: "es" | "en"; onSelect: (r: Ref[]) => void; t: (k: string) => string }) {
  const kinds = (profile?.nodes ?? []).filter((k) => k.carga && drawing.nodes.some((n) => n.kind === k.id));
  if (kinds.length === 0) return null;
  return (
    <div className="row small" style={{ flexWrap: "wrap", gap: 6, marginTop: 8 }}>
      <span className="muted">{t("layout.sel.byKind")}</span>
      {kinds.map((k) => <button key={k.id} onClick={() => onSelect(ofKind(drawing, k.id))}>{k.id} ({drawing.nodes.filter((n) => n.kind === k.id).length})</button>)}
    </div>
  );
}

function Many({ drawing, selection, profile, lang, boardCircuits, readOnly, onChange, onSelect, t }: PropsProps) {
  const [tag, setTag] = useState("");
  const loads = loadKindsOf(profile);
  const nodes = selection.filter((r) => r.type === "node").map((r) => drawing.nodes.find((n) => n.id === r.id)).filter((n) => !!n);
  const mine = nodes.filter((n) => n && loads.has(n.kind));
  const counts = Object.entries(mine.reduce<Record<string, number>>((acc, n) => ({ ...acc, [n!.kind]: (acc[n!.kind] ?? 0) + 1 }), {}));
  const apply = (value: string) => onChange(assignCircuit(drawing, selection, value, loads).drawing);
  return (
    <div className="card">
      <b>{selection.length} {t("layout.sel.selected")}</b>
      <p className="small muted" style={{ margin: "4px 0" }}>{counts.map(([k, n]) => `${k}: ${n}`).join(" · ")}{selection.length > mine.length ? ` · ${t("layout.sel.ignored")} ${selection.length - mine.length}` : ""}</p>
      {!readOnly && mine.length > 0 && (
        <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
          <span>{t("layout.sel.assign")}</span>
          <CircuitSelect value={tag} boardCircuits={boardCircuits} onPick={setTag} empty="–" />
          <button className="primary" disabled={!tag} onClick={() => apply(tag)}>{t("layout.apply")}</button>
          <button onClick={() => apply("")}>{t("layout.sel.clear")}</button>
        </div>
      )}
      <div className="row" style={{ marginTop: 8, gap: 6 }}>
        <button onClick={() => onSelect([])}>{t("layout.sel.none")}</button>
        {!readOnly && <button onClick={() => { onChange(removeMany(drawing, unlocked(drawing, selection))); onSelect([]); }}>{t("layout.tool.erase")}</button>}
        {!readOnly && <button onClick={() => onChange(setLocked(drawing, selection, !selection.every((r) => isLocked(drawing, r))))}>{t("plan.act.lock")}</button>}
      </div>
      <ByKind drawing={drawing} profile={profile} lang={lang} onSelect={onSelect} t={t} />
    </div>
  );
}

export function Properties(props: PropsProps) {
  const { drawing, selection, derived, profile, lang, boardCircuits, readOnly, onChange, onSelect, t } = props;
  if (selection.length > 1) return <Many {...props} />;
  if (selection.length === 0) {
    return <div className="card"><b>{t("layout.props")}</b><p className="muted small" style={{ margin: "6px 0 0" }}>{t("layout.props.none")}</p><ByKind drawing={drawing} profile={profile} lang={lang} onSelect={onSelect} t={t} /></div>;
  }
  const selected = selection[0];
  const node = selected.type === "node" ? drawing.nodes.find((n) => n.id === selected.id) : undefined;
  const line = selected.type === "line" ? drawing.lines.find((l) => l.id === selected.id) : undefined;
  const item = node ?? line;
  if (!item) return null;
  const kind = (node ? profile?.nodes : profile?.lines)?.find((k) => k.id === item.kind);
  const attrs = (item.attrs ?? {}) as Record<string, unknown>;
  const derivedTag = node ? derived?.nodes?.find((n) => n.id === node.id)?.tag : derived?.stretches?.find((s) => s.line === line?.id)?.line_tag;
  const carried = line ? (derived?.stretches ?? []).filter((s) => s.line === line.id && s.carries && s.carries.length > 0) : [];
  const patch = (p: object) => onChange(node ? updateNode(drawing, node.id, p) : updateLine(drawing, item.id, p));
  const circuitField = (value: string) => (
    <label className="field"><span>{t("layout.col.circuit")}</span>
      <CircuitSelect value={value} boardCircuits={boardCircuits} disabled={readOnly} onPick={(c) => patch({ circuit: c })} empty="–" /></label>
  );
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}><b>{t("layout.props")}</b><span className="muted small">{nameOf(kind, lang)}</span></div>
      <div className="fgrid" style={{ marginTop: 6 }}>
        <label className="field"><span>{t("layout.col.tag")}</span>
          <input disabled={readOnly} value={item.tag ?? ""} placeholder={derivedTag} onChange={(e) => patch({ tag: e.target.value })} /></label>
        {node && kind?.carga && circuitField(node.circuit ?? "")}
        {(kind?.atributos ?? []).map((a) => a === "circuito" && line ? <div key={a}>{circuitField(line.circuit ?? "")}</div> : (
          <label key={a} className="field"><span>{a.replace(/_/g, " ")}</span>
            <input disabled={readOnly} value={String(attrs[a] ?? "")} onChange={(e) => patch({ attrs: setAttr(attrs, a, e.target.value) })} /></label>
        ))}
      </div>
      {kind?.un_solo_circuito && <p className="muted small" style={{ margin: "6px 0 0" }}>{t("layout.props.single")}</p>}
      {node && !kind?.carga && (
        <label className="row small" style={{ marginTop: 6 }}><input type="checkbox" disabled={readOnly} checked={drawing.outlet === node.id} onChange={(e) => onChange({ ...drawing, outlet: e.target.checked ? node.id : "" })} />{t("layout.props.outlet")}</label>
      )}
      {carried.length > 0 && (
        <div className="small" style={{ marginTop: 6 }}><b>{t("layout.props.carries")}</b>
          <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>{carried.map((s) => <li key={s.tag}><span className="mono">{s.tag}</span>: {(s.carries ?? []).map((c) => `${c.circuit}${c.ternas > 1 ? ` ×${c.ternas}` : ""}`).join(", ")} · {s.cables} {t("layout.props.cables")}</li>)}</ul>
        </div>
      )}
      <Geometry item={item} kind={kind} node={!!node} readOnly={readOnly} patch={patch} t={t} />
      {!readOnly && <div className="row" style={{ marginTop: 8, gap: 6 }}>
        <button onClick={() => { onChange(removeMany(drawing, unlocked(drawing, selection))); onSelect([]); }} disabled={isLocked(drawing, selected)}>{t("layout.tool.erase")}</button>
        <button aria-pressed={isLocked(drawing, selected)} onClick={() => onChange(setLocked(drawing, selection, !isLocked(drawing, selected)))}>{t(isLocked(drawing, selected) ? "plan.act.unlock" : "plan.act.lock")}</button>
      </div>}
    </div>
  );
}

const GEOM_FIELDS = ["z_m", "ancho_m", "alto_m", "libre_m"];

/** What the element occupies in space: the numbers other disciplines see (never anything else of the drawing), a turn for symbols and the link of a shaft with its twin on another level. */
function Geometry({ item, kind, node, readOnly, patch, t }: { item: { attrs?: Record<string, unknown> }; kind: Kind | undefined; node: boolean; readOnly: boolean; patch: (p: object) => void; t: (k: string) => string }) {
  const attrs = (item.attrs ?? {}) as Record<string, unknown>;
  const fields = [...GEOM_FIELDS, ...(kind?.vertical ? ["altura_m"] : [])];
  return (
    <details className="geom" style={{ marginTop: 8 }}>
      <summary>{t("plan.geom")}</summary>
      <p className="muted small" style={{ margin: "4px 0" }}>{t("plan.geom.help")}</p>
      <div className="fgrid">
        {fields.map((f) => (
          <label key={f} className="field"><span>{t("plan.geom." + f)}</span>
            <input disabled={readOnly} inputMode="decimal" value={String(attrs[f] ?? "")} placeholder={String(kind?.geom?.[f] ?? "")} onChange={(e) => patch({ attrs: setAttr(attrs, f, e.target.value) })} /></label>
        ))}
        {node && <label className="field"><span>{t("plan.geom.rot_deg")}</span><input disabled={readOnly} inputMode="decimal" value={String(attrs.rot_deg ?? "")} placeholder="0" onChange={(e) => patch({ attrs: setAttr(attrs, "rot_deg", e.target.value) })} /></label>}
        {node && kind?.vertical && <label className="field"><span>{t("plan.geom.enlace")}</span><input disabled={readOnly} value={String(attrs.enlace ?? "")} placeholder="L1:n3" onChange={(e) => patch({ attrs: setAttr(attrs, "enlace", e.target.value) })} /></label>}
      </div>
    </details>
  );
}

interface CircuitsProps {
  drawing: Drawing; derived: Derived | null; boardCircuits: BoardCircuit[]; profile: Profile | undefined; readOnly: boolean; focus: string; onFocus: (tag: string) => void;
  onChange: (d: Drawing) => void; onSelect: (r: Ref[]) => void; t: (key: string) => string;
}

export function Circuits({ drawing, derived, boardCircuits, profile, readOnly, focus, onFocus, onChange, onSelect, t }: CircuitsProps) {
  const tagOf = (id: string) => derived?.nodes?.find((n) => n.id === id)?.tag ?? id;
  const free = freeCircuits(drawing, boardCircuits.map((c) => c.tag));
  const loads = loadKindsOf(profile);
  const nodeOptions = <><option value="">–</option>{drawing.nodes.map((n) => <option key={n.id} value={n.id}>{tagOf(n.id)}</option>)}</>;
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <b>{t("layout.circuits")}</b>
        {!readOnly && <button disabled={free.length === 0} onClick={() => onChange(addCircuit(drawing, free[0]))}>+ {t("layout.circuits.add")}</button>}
      </div>
      <p className="muted small" style={{ margin: "4px 0 6px" }}>{boardCircuits.length === 0 ? t("layout.circuits.noBoard") : t("layout.circuits.help")}</p>
      {drawing.circuits.length > 0 && (
        <div style={{ overflowX: "auto" }}><table>
          <thead><tr><th>{t("layout.col.circuit")}</th><th>{t("layout.circuits.from")}</th><th>{t("layout.circuits.loads")}</th><th>{t("layout.circuits.to")}</th><th>{t("layout.circuits.ternas")}</th><th>{t("layout.circuits.route")}</th><th /></tr></thead>
          <tbody>
            {drawing.circuits.map((c, i) => {
              const r = derived?.circuits?.[c.tag];
              const n = loadsOf(drawing, c.tag, loads);
              return (
                <tr key={i} className={focus === c.tag ? "on" : ""}>
                  <td><select disabled={readOnly} value={c.tag} onChange={(e) => onChange(updateCircuit(drawing, i, { tag: e.target.value }))}>
                    {[c.tag, ...free].filter((x, k, a) => a.indexOf(x) === k).map((x) => <option key={x} value={x}>{x}</option>)}</select></td>
                  <td><select disabled={readOnly} value={c.from} onChange={(e) => onChange(updateCircuit(drawing, i, { from: e.target.value }))}>{nodeOptions}</select></td>
                  <td>{n > 0 ? <button className="linkbtn" onClick={() => onSelect(drawing.nodes.filter((x) => x.circuit === c.tag && loads.has(x.kind)).map((x) => ({ type: "node" as const, id: x.id })))}>{n}</button> : "0"}</td>
                  <td><select disabled={readOnly} value={c.to} onChange={(e) => onChange(updateCircuit(drawing, i, { to: e.target.value }))}>{nodeOptions}</select></td>
                  <td><input style={{ width: 52 }} type="number" min={1} max={99} disabled={readOnly} value={c.ternas}
                    onChange={(e) => onChange(updateCircuit(drawing, i, { ternas: Math.max(1, Math.min(99, parseInt(e.target.value, 10) || 1)) }))} /></td>
                  <td className="small">{r ? (r.found ? <button className="linkbtn" onClick={() => onFocus(focus === c.tag ? "" : c.tag)}>{r.length_m} m · {r.cable_length_m} m {t("layout.circuits.cable")}</button> : <span style={{ color: "var(--bad)" }}>{t("layout.circuits.noRoute")}</span>) : "–"}</td>
                  <td>{!readOnly && <button onClick={() => onChange(removeCircuit(drawing, i))}>×</button>}</td>
                </tr>
              );
            })}
          </tbody>
        </table></div>
      )}
    </div>
  );
}
