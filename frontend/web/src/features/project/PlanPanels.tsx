import { addCircuit, Drawing, freeCircuits, Ref, remove, removeCircuit, setAttr, updateCircuit, updateLine, updateNode } from "./planEditing";
import { Derived, Kind, Profile } from "./PlanEditor";

/** The side panels of the plan editor: the properties of what is selected, and the circuits routed over the drawing. Text goes through `t`; changes go out through `onChange`. */
export interface BoardCircuit { tag: string; description: string; board: string }

interface PropsProps {
  drawing: Drawing; selected: Ref | null; derived: Derived | null; profile: Profile | undefined; lang: "es" | "en"; boardCircuits: BoardCircuit[];
  readOnly: boolean; onChange: (d: Drawing) => void; onSelect: (r: Ref | null) => void; t: (key: string) => string;
}

const nameOf = (k: Kind | undefined, lang: "es" | "en") => (k ? `${k.id} · ${k.etiqueta[lang] ?? k.etiqueta.es}` : "");

export function Properties({ drawing, selected, derived, profile, lang, boardCircuits, readOnly, onChange, onSelect, t }: PropsProps) {
  if (!selected) return <div className="card"><b>{t("layout.props")}</b><p className="muted small" style={{ margin: "6px 0 0" }}>{t("layout.props.none")}</p></div>;
  const node = selected.type === "node" ? drawing.nodes.find((n) => n.id === selected.id) : undefined;
  const line = selected.type === "line" ? drawing.lines.find((l) => l.id === selected.id) : undefined;
  const item = node ?? line;
  if (!item) return null;
  const kind = (node ? profile?.nodes : profile?.lines)?.find((k) => k.id === item.kind);
  const attrs = (item.attrs ?? {}) as Record<string, unknown>;
  const derivedTag = node ? derived?.nodes?.find((n) => n.id === node.id)?.tag : derived?.stretches?.find((s) => s.line === line?.id)?.line_tag;
  const carried = line ? (derived?.stretches ?? []).filter((s) => s.line === line.id && s.carries && s.carries.length > 0) : [];
  const patch = (p: object) => onChange(node ? updateNode(drawing, node.id, p) : updateLine(drawing, item.id, p));
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}><b>{t("layout.props")}</b><span className="muted small">{nameOf(kind, lang)}</span></div>
      <div className="fgrid" style={{ marginTop: 6 }}>
        <label className="field"><span>{t("layout.col.tag")}</span>
          <input disabled={readOnly} value={item.tag ?? ""} placeholder={derivedTag} onChange={(e) => patch({ tag: e.target.value })} /></label>
        {(kind?.atributos ?? []).map((a) => a === "circuito" && line ? (
          <label key={a} className="field"><span>{t("layout.col.circuit")}</span>
            <select disabled={readOnly} value={line.circuit ?? ""} onChange={(e) => patch({ circuit: e.target.value })}>
              <option value="">–</option>
              {boardCircuits.map((c) => <option key={c.tag} value={c.tag}>{c.tag}{c.description ? ` · ${c.description}` : ""}</option>)}
            </select></label>
        ) : (
          <label key={a} className="field"><span>{a.replace(/_/g, " ")}</span>
            <input disabled={readOnly} value={String(attrs[a] ?? "")} onChange={(e) => patch({ attrs: setAttr(attrs, a, e.target.value) })} /></label>
        ))}
      </div>
      {kind?.un_solo_circuito && <p className="muted small" style={{ margin: "6px 0 0" }}>{t("layout.props.single")}</p>}
      {node && (
        <label className="row small" style={{ marginTop: 6 }}><input type="checkbox" disabled={readOnly} checked={drawing.outlet === node.id} onChange={(e) => onChange({ ...drawing, outlet: e.target.checked ? node.id : "" })} />{t("layout.props.outlet")}</label>
      )}
      {carried.length > 0 && (
        <div className="small" style={{ marginTop: 6 }}><b>{t("layout.props.carries")}</b>
          <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>{carried.map((s) => <li key={s.tag}><span className="mono">{s.tag}</span>: {(s.carries ?? []).map((c) => `${c.circuit}${c.ternas > 1 ? ` ×${c.ternas}` : ""}`).join(", ")} · {s.cables} {t("layout.props.cables")}</li>)}</ul>
        </div>
      )}
      {!readOnly && <div style={{ marginTop: 8 }}><button onClick={() => { onChange(remove(drawing, selected)); onSelect(null); }}>{t("layout.tool.erase")}</button></div>}
    </div>
  );
}

interface CircuitsProps {
  drawing: Drawing; derived: Derived | null; boardCircuits: BoardCircuit[]; readOnly: boolean; focus: string; onFocus: (tag: string) => void;
  onChange: (d: Drawing) => void; t: (key: string) => string;
}

export function Circuits({ drawing, derived, boardCircuits, readOnly, focus, onFocus, onChange, t }: CircuitsProps) {
  const tagOf = (id: string) => derived?.nodes?.find((n) => n.id === id)?.tag ?? id;
  const free = freeCircuits(drawing, boardCircuits.map((c) => c.tag));
  const nodeOptions = (
    <>{<option value="">–</option>}{drawing.nodes.map((n) => <option key={n.id} value={n.id}>{tagOf(n.id)}</option>)}</>
  );
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <b>{t("layout.circuits")}</b>
        {!readOnly && <button disabled={free.length === 0} onClick={() => onChange(addCircuit(drawing, free[0]))}>+ {t("layout.circuits.add")}</button>}
      </div>
      <p className="muted small" style={{ margin: "4px 0 6px" }}>{boardCircuits.length === 0 ? t("layout.circuits.noBoard") : t("layout.circuits.help")}</p>
      {drawing.circuits.length > 0 && (
        <div style={{ overflowX: "auto" }}><table>
          <thead><tr><th>{t("layout.col.circuit")}</th><th>{t("layout.circuits.from")}</th><th>{t("layout.circuits.to")}</th><th>{t("layout.circuits.ternas")}</th><th>{t("layout.circuits.route")}</th><th /></tr></thead>
          <tbody>
            {drawing.circuits.map((c, i) => {
              const r = derived?.circuits?.[c.tag];
              return (
                <tr key={i} className={focus === c.tag ? "on" : ""}>
                  <td><select disabled={readOnly} value={c.tag} onChange={(e) => onChange(updateCircuit(drawing, i, { tag: e.target.value }))}>
                    {[c.tag, ...free].filter((x, k, a) => a.indexOf(x) === k).map((x) => <option key={x} value={x}>{x}</option>)}</select></td>
                  <td><select disabled={readOnly} value={c.from} onChange={(e) => onChange(updateCircuit(drawing, i, { from: e.target.value }))}>{nodeOptions}</select></td>
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
