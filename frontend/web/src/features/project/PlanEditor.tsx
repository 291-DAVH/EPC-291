import { useEffect, useMemo, useRef, useState } from "react";
import { addLine, addNode, commit, DLine, dist, Drawing, History, metresPerUnit, ortho, pick, Pt, redo, Ref, remove, setOrigin, setScale, snap, undo } from "./planEditing";

/** The canvas of the plan-drawing editor: the plan as an underlay, a toolbar, and what the person draws over it. It computes nothing about the engineering
 *  (lengths, tags, the graph): the parent gives it what the engine derived. Text goes through `t`; data comes in props and changes go out through `onChange`. */
export interface Kind { id: string; etiqueta: { es: string; en: string }; prefijo_tag: string; simbolo_2d: string; capa_dxf: string }
export interface Profile { id: string; name: { es: string; en: string }; lines: Kind[]; nodes: Kind[]; shortcuts: Record<string, string> }
export interface DerivedNode { id: string; tag: string; kind: string; placed: boolean; x_m: number; y_m: number }
export interface DerivedStretch { tag: string; line: string; line_tag: string; kind: string; from: string; to: string; length_m: number; circuit: string | null }
export interface Derived {
  ready: boolean; plan?: { metres_per_unit: number; origin: Pt }; nodes?: DerivedNode[]; stretches?: DerivedStretch[]; warnings?: string[];
  schedule?: { lines: Record<string, { lines: number; stretches: number; length_m: number }>; nodes: Record<string, number>; circuit_routes: Record<string, { stretches: string[]; length_m: number }>; length_by_line_m: Record<string, number>; total_length_m: number };
  network?: { invert_m: Record<string, number>; validated: boolean; rule: string } | null;
}
type Tool = "select" | "scale" | "origin" | "node" | "line" | "erase";
interface View { x: number; y: number; w: number; h: number }

const PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"];
const NODE_PX = 9;

export interface Props {
  drawing: Drawing; onChange: (next: Drawing) => void; derived: Derived | null; profile: Profile | undefined; lang: "es" | "en"; underlayUrl: string | null;
  readOnly?: boolean; t: (key: string) => string; onScaleAsk?: () => void;
}

function Sym({ id, x, y, s, color, sel }: { id: string; x: number; y: number; s: number; color: string; sel: boolean }) {
  const common = { fill: "#fff", stroke: sel ? "#d62728" : color, strokeWidth: sel ? 3 : 1.6, vectorEffect: "non-scaling-stroke" as const };
  const r = s / 2;
  if (id === "boca_registro") return <g><circle cx={x} cy={y} r={r} {...common} /><circle cx={x} cy={y} r={r * 0.4} {...common} /></g>;
  if (id === "caja_pase") return <g><rect x={x - r} y={y - r} width={s} height={s} {...common} /><circle cx={x} cy={y} r={r * 0.5} {...common} /></g>;
  if (id === "tablero") return <g><rect x={x - r} y={y - r * 0.6} width={s} height={s * 0.6} {...common} /><line x1={x - r} y1={y} x2={x + r} y2={y} {...common} /></g>;
  return <g><rect x={x - r} y={y - r} width={s} height={s} {...common} /><line x1={x - r} y1={y - r} x2={x + r} y2={y + r} {...common} /><line x1={x - r} y1={y + r} x2={x + r} y2={y - r} {...common} /></g>;
}

export default function PlanEditor({ drawing, onChange, derived, profile, lang, underlayUrl, readOnly, t }: Props) {
  const [tool, setTool] = useState<Tool>("select");
  const [kindId, setKindId] = useState("");
  const [draft, setDraft] = useState<Pt[]>([]);
  const [hover, setHover] = useState<Pt | null>(null);
  const [scalePts, setScalePts] = useState<Pt[]>([]);
  const [scaleText, setScaleText] = useState("");
  const [selected, setSelected] = useState<Ref | null>(null);
  const [hist, setHist] = useState<History>({ past: [], future: [] });
  const [img, setImg] = useState<{ w: number; h: number } | null>(null);
  const scaleInput = useRef<HTMLInputElement>(null);
  const [view, setView] = useState<View>({ x: 0, y: 0, w: 1200, h: 800 });
  const box = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const pan = useRef<{ sx: number; sy: number; v: View } | null>(null);

  const lineKinds = profile?.lines ?? [];
  const nodeKinds = profile?.nodes ?? [];
  const kindName = (k: Kind) => k.etiqueta[lang] ?? k.etiqueta.es;
  const kindOf = (id: string) => [...lineKinds, ...nodeKinds].find((k) => k.id === id);
  const colorOf = (id: string) => PALETTE[Math.max(0, lineKinds.findIndex((k) => k.id === id)) % PALETTE.length];
  const k = metresPerUnit(drawing);

  useEffect(() => {                                    // the plan underlay: its size sets the first view
    if (!underlayUrl) { setImg(null); return; }
    const i = new Image();
    i.onload = () => { setImg({ w: i.naturalWidth || 1200, h: i.naturalHeight || 800 }); setView({ x: 0, y: 0, w: i.naturalWidth || 1200, h: i.naturalHeight || 800 }); };
    i.src = underlayUrl;
  }, [underlayUrl]);
  useEffect(() => {                                    // the kind selected must be one the tool can use
    const list = tool === "node" ? nodeKinds : lineKinds;
    if (!list.some((x) => x.id === kindId)) setKindId(list[0]?.id ?? "");
  }, [profile, tool]);

  useEffect(() => { if (scalePts.length === 2) scaleInput.current?.focus(); }, [scalePts.length]);

  const upp = () => (box.current ? view.w / Math.max(1, box.current.clientWidth) : 1);     // view units per screen pixel
  const toView = (e: { clientX: number; clientY: number }): Pt => {
    const r = svgRef.current!.getBoundingClientRect();
    return [view.x + ((e.clientX - r.left) / r.width) * view.w, view.y + ((e.clientY - r.top) / r.height) * view.h];
  };
  const apply = (next: Drawing) => { setHist(commit(hist, drawing)); onChange(next); };
  const doUndo = () => { const r = undo(hist, drawing); setHist(r.h); if (r.d !== drawing) onChange(r.d); };
  const doRedo = () => { const r = redo(hist, drawing); setHist(r.h); if (r.d !== drawing) onChange(r.d); };
  const finishLine = () => { if (draft.length >= 2 && kindId) apply(addLine(drawing, kindId, draft)); setDraft([]); };
  const cancel = () => { setDraft([]); setScalePts([]); setSelected(null); };

  const choose = (next: Tool) => { cancel(); setTool(next); };
  const confirmScale = () => {
    const meters = parseFloat(scaleText.replace(",", "."));
    if (scalePts.length === 2 && meters > 0) { apply(setScale(drawing, scalePts[0], scalePts[1], meters)); setScalePts([]); setScaleText(""); setTool("select"); }
  };

  const onDown = (e: React.PointerEvent) => {
    if (e.button === 1 || (tool === "select" && e.button === 0 && !pick(drawing, toView(e), 8 * upp()))) {
      pan.current = { sx: e.clientX, sy: e.clientY, v: view };                      // the middle button, or an empty spot with the select tool, drags the view
      (e.target as Element).setPointerCapture?.(e.pointerId);
    }
    if (e.button !== 0 || (readOnly && tool !== "select")) return;
    const raw = toView(e);
    const tol = 8 * upp();
    if (tool === "select") setSelected(pick(drawing, raw, tol));
    else if (tool === "erase") { const hit = pick(drawing, raw, tol); if (hit) { apply(remove(drawing, hit)); setSelected(null); } }
    else if (tool === "origin") { apply(setOrigin(drawing, raw)); setTool("select"); }
    else if (tool === "scale") { if (scalePts.length < 2) setScalePts([...scalePts, snap(drawing, raw, tol)]); }
    else if (tool === "node" && kindId) apply(addNode(drawing, kindId, snap(drawing, raw, tol)));
    else if (tool === "line" && kindId) {
      let p = snap(drawing, raw, tol);
      if (e.shiftKey && draft.length > 0) p = ortho(draft[draft.length - 1], p);
      if (draft.length === 0 || dist(draft[draft.length - 1], p) > 1e-6) setDraft([...draft, p]);
    }
  };
  const onMove = (e: React.PointerEvent) => {
    if (pan.current) {
      const r = svgRef.current!.getBoundingClientRect();
      const p = pan.current;
      setView({ ...p.v, x: p.v.x - ((e.clientX - p.sx) / r.width) * p.v.w, y: p.v.y - ((e.clientY - p.sy) / r.height) * p.v.h });
      return;
    }
    const raw = toView(e);
    let p = snap(drawing, raw, 8 * upp());
    if (tool === "line" && e.shiftKey && draft.length > 0) p = ortho(draft[draft.length - 1], p);
    setHover(p);
  };
  const onUp = () => { pan.current = null; };
  const onWheel = (e: React.WheelEvent) => {
    const factor = e.deltaY > 0 ? 1.15 : 1 / 1.15;
    const at = toView(e);
    setView({ x: at[0] - (at[0] - view.x) * factor, y: at[1] - (at[1] - view.y) * factor, w: view.w * factor, h: view.h * factor });
  };
  const onKey = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); doUndo(); return; }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") { e.preventDefault(); doRedo(); return; }
    if (e.key === "Escape") cancel();
    else if (e.key === "Enter") finishLine();
    else if ((e.key === "Delete" || e.key === "Backspace") && selected && !readOnly) { apply(remove(drawing, selected)); setSelected(null); }
    else if (profile?.shortcuts[e.key.toLowerCase()]) {
      const id = profile.shortcuts[e.key.toLowerCase()];
      if (nodeKinds.some((n) => n.id === id)) { cancel(); setTool("node"); setKindId(id); } else if (lineKinds.some((l) => l.id === id)) { cancel(); setTool("line"); setKindId(id); }
    }
  };

  const nodeTag = useMemo(() => Object.fromEntries((derived?.nodes ?? []).map((n) => [n.id, n.tag])), [derived]);
  const lineTag = useMemo(() => Object.fromEntries((derived?.stretches ?? []).map((s) => [s.line, s.line_tag])), [derived]);
  const auto = (derived?.nodes ?? []).filter((n) => !n.placed);
  const kr = derived?.plan?.metres_per_unit;
  const autoPos = (n: DerivedNode): Pt => (kr ? [drawing.origin[0] + n.x_m / kr, drawing.origin[1] - n.y_m / kr] : [0, 0]);
  const u = upp();
  const polyline = (pts: Pt[]) => pts.map((p) => p.join(",")).join(" ");
  const mid = (l: DLine): Pt => { const a = l.points[0], b = l.points[l.points.length - 1]; return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; };
  const tools: { id: Tool; key: string; write: boolean }[] = [
    { id: "select", key: "layout.tool.select", write: false }, { id: "scale", key: "layout.tool.scale", write: true }, { id: "origin", key: "layout.tool.origin", write: true },
    { id: "node", key: "layout.tool.node", write: true }, { id: "line", key: "layout.tool.line", write: true }, { id: "erase", key: "layout.tool.erase", write: true },
  ];
  const hint = { select: "", scale: "layout.hint.scale", origin: "layout.hint.origin", node: "layout.hint.node", line: "layout.hint.line", erase: "layout.hint.erase" }[tool];

  return (
    <div className="card" tabIndex={0} onKeyDown={onKey} style={{ outline: "none" }}>
      <div className="row" style={{ flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
        {tools.filter((x) => !readOnly || !x.write).map((x) => <button key={x.id} className={tool === x.id ? "primary" : ""} onClick={() => choose(x.id)}>{t(x.key)}</button>)}
        {(tool === "node" ? nodeKinds : tool === "line" ? lineKinds : []).map((kd) => (
          <button key={kd.id} className={kindId === kd.id ? "primary" : ""} onClick={() => setKindId(kd.id)} title={kd.capa_dxf}>{kd.id} · {kindName(kd)}</button>
        ))}
        <span style={{ flex: 1 }} />
        {!readOnly && <><button onClick={doUndo} disabled={hist.past.length === 0}>{t("layout.undo")}</button><button onClick={doRedo} disabled={hist.future.length === 0}>{t("layout.redo")}</button></>}
        <button onClick={() => setView(img ? { x: 0, y: 0, w: img.w, h: img.h } : { x: 0, y: 0, w: 1200, h: 800 })}>{t("layout.fit")}</button>
      </div>
      <div className="muted small" style={{ minHeight: 18 }}>
        {hint && t(hint)} {k === null ? <b style={{ color: "var(--bad)" }}>{t("layout.notCalibrated")}</b> : <span>{t("layout.scaleIs")} 1 u = {k.toFixed(4)} m</span>}
      </div>
      {tool === "scale" && scalePts.length === 2 && (
        <div className="row" style={{ margin: "6px 0" }}>
          <span>{t("layout.scaleDistance")}</span>
          <input ref={scaleInput} value={scaleText} onChange={(e) => setScaleText(e.target.value)} onKeyDown={(e) => { e.stopPropagation(); if (e.key === "Enter") confirmScale(); }} style={{ width: 90 }} />
          <button className="primary" onClick={confirmScale}>{t("layout.apply")}</button><button onClick={cancel}>{t("layout.cancel")}</button>
        </div>
      )}
      <div ref={box} style={{ border: "1px solid var(--line, #ccc)", background: "#fff", height: 560, overflow: "hidden", touchAction: "none" }}>
        <svg ref={svgRef} width="100%" height="100%" viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`} preserveAspectRatio="xMinYMin meet" onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}
          onWheel={onWheel} onDoubleClick={finishLine} onContextMenu={(e) => e.preventDefault()} style={{ cursor: tool === "select" ? "default" : "crosshair", display: "block" }}>
          {underlayUrl && img && <image href={underlayUrl} x={0} y={0} width={img.w} height={img.h} />}
          {drawing.scale && <g stroke="#ff7f0e" strokeWidth={1.5} vectorEffect="non-scaling-stroke"><line x1={drawing.scale.p1[0]} y1={drawing.scale.p1[1]} x2={drawing.scale.p2[0]} y2={drawing.scale.p2[1]} strokeDasharray="6 4" vectorEffect="non-scaling-stroke" />
            <text x={(drawing.scale.p1[0] + drawing.scale.p2[0]) / 2} y={(drawing.scale.p1[1] + drawing.scale.p2[1]) / 2 - 4 * u} fontSize={11 * u} fill="#ff7f0e" stroke="none">{drawing.scale.distance_m} m</text></g>}
          {scalePts.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r={4 * u} fill="#ff7f0e" />)}
          {drawing.lines.map((l) => {
            const sel = selected?.type === "line" && selected.id === l.id;
            return <g key={l.id}><polyline points={polyline(l.points)} fill="none" stroke={sel ? "var(--bad, #d62728)" : colorOf(l.kind)} strokeWidth={sel ? 4 : 2.2} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
              {lineTag[l.id] && <text x={mid(l)[0]} y={mid(l)[1] - 5 * u} fontSize={11 * u} textAnchor="middle" fill={colorOf(l.kind)} stroke="#fff" strokeWidth={3 * u} paintOrder="stroke">{lineTag[l.id]}</text>}</g>;
          })}
          {draft.length > 0 && <polyline points={polyline([...draft, ...(hover ? [hover] : [])])} fill="none" stroke={colorOf(kindId)} strokeWidth={2} strokeDasharray="5 4" vectorEffect="non-scaling-stroke" />}
          {auto.map((n) => { const p = autoPos(n); return <circle key={n.id} cx={p[0]} cy={p[1]} r={(n.kind === "J" ? 3.5 : 4.5) * u} fill={n.kind === "J" ? "#555" : "none"} stroke={n.kind === "J" ? "#555" : "#d62728"} strokeWidth={1.5} vectorEffect="non-scaling-stroke"><title>{n.tag}</title></circle>; })}
          {drawing.nodes.map((n) => {
            const sel = selected?.type === "node" && selected.id === n.id;
            const sym = kindOf(n.kind)?.simbolo_2d ?? "camara";
            return <g key={n.id}><Sym id={sym} x={n.x} y={n.y} s={NODE_PX * 2 * u} color="#222" sel={sel} />
              <text x={n.x + NODE_PX * 1.2 * u} y={n.y - NODE_PX * 1.2 * u} fontSize={11 * u} fill="#222" stroke="#fff" strokeWidth={3 * u} paintOrder="stroke">{nodeTag[n.id] ?? n.id}</text>
              {drawing.outlet === n.id && <circle cx={n.x} cy={n.y} r={NODE_PX * 1.6 * u} fill="none" stroke="#2ca02c" strokeWidth={2} vectorEffect="non-scaling-stroke" />}</g>;
          })}
          <g stroke="#2ca02c" strokeWidth={1.5} vectorEffect="non-scaling-stroke"><line x1={drawing.origin[0] - 10 * u} y1={drawing.origin[1]} x2={drawing.origin[0] + 10 * u} y2={drawing.origin[1]} vectorEffect="non-scaling-stroke" />
            <line x1={drawing.origin[0]} y1={drawing.origin[1] - 10 * u} x2={drawing.origin[0]} y2={drawing.origin[1] + 10 * u} vectorEffect="non-scaling-stroke" />
            <text x={drawing.origin[0] + 12 * u} y={drawing.origin[1] - 4 * u} fontSize={11 * u} fill="#2ca02c" stroke="none">0,0</text></g>
          {hover && (tool === "node" || tool === "line" || tool === "scale") && <circle cx={hover[0]} cy={hover[1]} r={3 * u} fill="none" stroke="#999" vectorEffect="non-scaling-stroke" />}
        </svg>
      </div>
    </div>
  );
}
