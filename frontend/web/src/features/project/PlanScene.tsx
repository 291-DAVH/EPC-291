import { useMemo } from "react";
import { DLine, Drawing, Pt, Ref, sameRef } from "./planEditing";
import type { Derived, Kind, Prim, Profile } from "./PlanEditor";
import type { PlanPrefs } from "./planPrefs";
import { colorOfDiscipline, Ghost, Pin, RefItem } from "./planTypes";
import { Architecture, centroidOf, fromMetres, isLocked, Problem, RoutePath, SnapKind, spreadLabels, UnderlayOpts, wallFaces } from "./planTools";

/** The drawing as the canvas shows it: the underlay, what is drawn, what other disciplines occupy, marks and aids. It only draws what the editor gives it; it holds no state. */
export const NODE_PX = 9;
const PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"];
const CIRCUIT_PALETTE = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#008080", "#9a6324", "#800000", "#808000", "#000075"];
const DRAWN_HERE = ["luminaria", "tomacorriente", "tomacorriente_especial", "hvac", "boca_registro", "caja_pase", "tablero"];
const TONE: Record<Pin["tone"], string> = { bad: "#d62728", warn: "#e08a00", info: "#2f6fdd", done: "#7a8190" };
const FILL_TONE: Record<string, string> = { ok: "#2e9e57", near: "#e08a00", over: "#d62728" };

export function Sym({ id, x, y, s, color, sel, prims, ghost = false }: { id: string; x: number; y: number; s: number; color: string; sel: boolean; prims?: Prim[]; ghost?: boolean }) {
  const common = { fill: ghost ? "none" : "#fff", stroke: sel ? "#d62728" : color, strokeWidth: sel ? 3 : 1.6, vectorEffect: "non-scaling-stroke" as const, strokeDasharray: ghost ? "3 2" : undefined };
  const r = s / 2;
  if (prims && !DRAWN_HERE.includes(id)) {
    return <g>{prims.map((p, i) => p.t === "rect" ? <rect key={i} x={x - p.w * s / 2} y={y - p.h * s / 2} width={p.w * s} height={p.h * s} {...common} /> : p.t === "circle" ? <circle key={i} cx={x} cy={y} r={p.r * s} {...common} /> : <line key={i} x1={x + p.a[0] * s} y1={y + p.a[1] * s} x2={x + p.b[0] * s} y2={y + p.b[1] * s} {...common} />)}</g>;
  }
  if (id === "luminaria") return <g><circle cx={x} cy={y} r={r} {...common} /><line x1={x - r * 0.7} y1={y - r * 0.7} x2={x + r * 0.7} y2={y + r * 0.7} {...common} /><line x1={x - r * 0.7} y1={y + r * 0.7} x2={x + r * 0.7} y2={y - r * 0.7} {...common} /></g>;
  if (id === "tomacorriente" || id === "tomacorriente_especial") {
    return <g><circle cx={x} cy={y} r={r} {...common} /><line x1={x - r} y1={y} x2={x + r} y2={y} {...common} /><line x1={x} y1={y} x2={x} y2={y - r} {...common} />{id === "tomacorriente_especial" && <circle cx={x} cy={y + r * 0.45} r={r * 0.25} {...common} />}</g>;
  }
  if (id === "hvac") return <g><rect x={x - r} y={y - r} width={s} height={s} {...common} /><circle cx={x} cy={y} r={r * 0.55} {...common} /><line x1={x - r * 0.4} y1={y - r * 0.4} x2={x + r * 0.4} y2={y + r * 0.4} {...common} /></g>;
  if (id === "boca_registro") return <g><circle cx={x} cy={y} r={r} {...common} /><circle cx={x} cy={y} r={r * 0.4} {...common} /></g>;
  if (id === "caja_pase") return <g><rect x={x - r} y={y - r} width={s} height={s} {...common} /><circle cx={x} cy={y} r={r * 0.5} {...common} /></g>;
  if (id === "tablero") return <g><rect x={x - r} y={y - r * 0.6} width={s} height={s * 0.6} {...common} /><line x1={x - r} y1={y} x2={x + r} y2={y} {...common} /></g>;
  return <g><rect x={x - r} y={y - r} width={s} height={s} {...common} /><line x1={x - r} y1={y - r} x2={x + r} y2={y + r} {...common} /><line x1={x - r} y1={y + r} x2={x + r} y2={y - r} {...common} /></g>;
}

export interface SceneProps {
  drawing: Drawing; profile?: Profile; derived: Derived | null; lang: "es" | "en"; u: number; k: number | null; prefs: PlanPrefs; tool: string; readOnly?: boolean;
  selection: Ref[]; highlight: string[]; focusCircuit: string; hoverRef: Ref | null;
  underlayUrl: string | null; img: { w: number; h: number } | null; underlayOpts: UnderlayOpts;
  draft: Pt[]; hover: Pt | null; kindId: string; snapMark: { p: Pt; kind: SnapKind } | null; scalePts: Pt[]; marquee: { a: Pt; b: Pt } | null;
  measure: Pt[]; route: RoutePath | null; routeFrom: string; guides: { x?: number; y?: number } | null; architecture: Architecture | null; roomDraft: Pt[]; proposal: import("./planTools").RunsProposal | null;
  reference: RefItem[]; ghosts: Ghost[]; pins: Pin[]; problems: Problem[]; onPin: (id: string) => void; grabLine: (e: React.PointerEvent, g: { line: string; end?: 0 | 1; seg?: number }) => void;
  t: (key: string) => string;
}

const polyline = (pts: Pt[]) => pts.map((p) => p.join(",")).join(" ");
const mid = (l: DLine): Pt => { const a = l.points[0], b = l.points[l.points.length - 1]; return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; };

export default function PlanScene(p: SceneProps) {
  const { drawing, profile, derived, u, k, prefs, selection, highlight, focusCircuit } = p;
  const kinds = [...(profile?.lines ?? []), ...(profile?.nodes ?? [])];
  const kindOf = (id: string): Kind | undefined => kinds.find((x) => x.id === id);
  const colorOf = (id: string) => PALETTE[Math.max(0, (profile?.lines ?? []).findIndex((x) => x.id === id)) % PALETTE.length];
  const circuitColor = (tag: string) => { const i = drawing.circuits.findIndex((c) => c.tag === tag); return i < 0 ? "#999" : CIRCUIT_PALETTE[i % CIRCUIT_PALETTE.length]; };
  const isSel = (r: Ref) => selection.some((q) => sameRef(q, r));
  const nodeTag = useMemo(() => Object.fromEntries((derived?.nodes ?? []).map((n) => [n.id, n.tag])), [derived]);
  const lineTag = useMemo(() => Object.fromEntries((derived?.stretches ?? []).map((s) => [s.line, s.line_tag])), [derived]);
  const lengthOf = useMemo(() => { const m: Record<string, number> = {}; (derived?.stretches ?? []).forEach((s) => { m[s.line] = (m[s.line] ?? 0) + s.length_m; }); return m; }, [derived]);
  const fillOf = useMemo(() => {
    const byTag = Object.fromEntries((derived?.schedule?.containers ?? []).filter((c) => c.fill).map((c) => [c.tag, c.fill!]));
    const m: Record<string, NonNullable<(typeof byTag)[string]>> = {};
    (derived?.stretches ?? []).forEach((s) => { const f = byTag[s.tag]; if (f && (!m[s.line] || f.used_pct > m[s.line].used_pct)) m[s.line] = f; });
    return m;
  }, [derived]);
  const circuitOfLine = useMemo(() => { const m: Record<string, string> = {}; (derived?.stretches ?? []).forEach((s) => { if (!m[s.line] && s.carries?.length) m[s.line] = s.carries[0].circuit; }); return m; }, [derived]);
  const kr = derived?.plan?.metres_per_unit;
  const auto = (derived?.nodes ?? []).filter((n) => !n.placed);
  const autoPos = (n: { x_m: number; y_m: number }): Pt => (kr ? [drawing.origin[0] + n.x_m / kr, drawing.origin[1] - n.y_m / kr] : [0, 0]);
  const dim = (circuit: string | undefined, lineId?: string) => prefs.isolate && !!focusCircuit && circuit !== focusCircuit && !(lineId && highlight.includes(lineId));
  const lineColor = (l: DLine) => (prefs.color === "circuit" ? circuitColor(l.circuit || circuitOfLine[l.id] || "") : colorOf(l.kind));
  const layerOf = (kind: string) => kindOf(kind)?.capa_dxf ?? "";
  const shownLines = drawing.lines.filter((l) => !prefs.hidden.includes(l.kind) && !prefs.hiddenLayers.includes(layerOf(l.kind)));
  const shownNodes = drawing.nodes.filter((n) => !prefs.hiddenLayers.includes(layerOf(n.kind)));
  const archOn = (layer: string) => !prefs.hiddenLayers.includes(layer);

  // text labels, kept off each other
  const labels = useMemo(() => {
    if (!prefs.labels) return [];
    const out: { id: string; x: number; y: number; w: number; h: number; text: string; color: string; anchor: "start" | "middle" }[] = [];
    const size = 11 * u;
    shownLines.forEach((l) => {
      const base = lineTag[l.id]; if (!base) return;
      const text = prefs.lengths && lengthOf[l.id] ? `${base} · ${lengthOf[l.id].toFixed(1)} m` : base;
      const f = fillOf[l.id];
      const m = mid(l);
      out.push({ id: "l:" + l.id, x: m[0] - text.length * 3 * u, y: m[1] - 5 * u - size, w: text.length * 6 * u, h: size * 1.2, text: f ? `${text} · ${f.used_pct}%` : text, color: f ? FILL_TONE[f.status] : colorOf(l.kind), anchor: "middle" });
    });
    shownNodes.forEach((n) => {
      const inv = derived?.network?.invert_m?.[n.id];
      const text = `${nodeTag[n.id] ?? n.id}${n.circuit ? ` · ${n.circuit}` : ""}${inv !== undefined ? ` ▼${inv}` : ""}`;
      out.push({ id: "n:" + n.id, x: n.x + NODE_PX * 1.2 * u, y: n.y - NODE_PX * 1.2 * u - size, w: text.length * 6 * u, h: size * 1.2, text, color: "#222", anchor: "start" });
    });
    return out;
  }, [drawing, derived, prefs.labels, prefs.lengths, prefs.hiddenLayers, prefs.hidden, u, nodeTag, lineTag, lengthOf, fillOf]);
  const offsets = useMemo(() => (labels.length > 400 ? {} : spreadLabels(labels)), [labels]);                  // a very large drawing keeps its labels where they are: moving them would cost more than it helps

  const op = p.underlayOpts;
  const crop = op.crop;
  const iw = p.img?.w ?? 0, ih = p.img?.h ?? 0;
  const showUnder = p.underlayUrl && p.img && !op.hidden && archOn("ARQ-FONDO");
  const coarse = u > 0 && typeof window !== "undefined" && window.matchMedia?.("(pointer: coarse)").matches;
  const hs = (coarse ? 9 : 5) * u;
  const selLine = !p.readOnly && p.tool === "select" && selection.length === 1 && selection[0].type === "line" ? drawing.lines.find((x) => x.id === selection[0].id) : undefined;
  const refPx = (it: RefItem): Pt[] => it.points.map((m) => (k ? fromMetres(m, drawing.origin, k) : [0, 0]));

  return (
    <>
      {showUnder && (
        <g transform={op.rotation ? `rotate(${op.rotation} ${iw / 2} ${ih / 2})` : undefined} clipPath={crop ? "url(#under-crop)" : undefined}>
          {crop && <defs><clipPath id="under-crop"><rect x={crop.x} y={crop.y} width={crop.w} height={crop.h} /></clipPath></defs>}
          <image href={p.underlayUrl!} x={0} y={0} width={iw} height={ih} opacity={op.opacity ?? 1} />
        </g>
      )}
      {prefs.rooms && (drawing.rooms ?? []).map((r, i) => {
        const c = centroidOf(r.points), hue = (i * 67) % 360;
        return <g key={r.id} data-ui pointerEvents="none"><polygon points={r.points.map((q) => q.join(",")).join(" ")} fill={`hsl(${hue} 70% 55%)`} fillOpacity={0.12} stroke={`hsl(${hue} 60% 40%)`} strokeWidth={1.2} strokeDasharray="8 4" vectorEffect="non-scaling-stroke" />
          <text x={c[0]} y={c[1]} fontSize={13 * u} textAnchor="middle" fill={`hsl(${hue} 60% 30%)`} stroke="#fff" strokeWidth={3 * u} paintOrder="stroke">{r.name}</text></g>;
      })}
      {p.roomDraft.length > 0 && <polyline data-ui points={polyline([...p.roomDraft, ...(p.hover ? [p.hover] : [])])} fill="none" stroke="#7c3aed" strokeWidth={2} strokeDasharray="6 4" vectorEffect="non-scaling-stroke" />}
      {p.proposal && <g data-ui pointerEvents="none">
        {p.proposal.lines.map((ln, i) => <polyline key={i} points={polyline(ln.points)} fill="none" stroke={ln.role === "trunk" ? "#7c3aed" : "#db2777"} strokeWidth={ln.role === "trunk" ? 5 : 3} strokeOpacity={0.55} strokeDasharray="10 5" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />)}
      </g>}
      {p.architecture && prefs.arch && (
        <g data-ui pointerEvents="none">
          {archOn("ARQ-MUROS") && p.architecture.walls.map((w) => <polygon key={w.id} points={[...wallFaces(w)[0], ...wallFaces(w)[1].slice().reverse()].map((q) => q.join(",")).join(" ")} fill="#6b7280" fillOpacity={0.4} stroke="#374151" strokeWidth={1} vectorEffect="non-scaling-stroke"><title>{`${w.id} · ${Math.round(w.confidence * 100)}%`}</title></polygon>)}
          {p.architecture.openings.filter((o) => archOn(o.kind === "door" ? "ARQ-PUERTAS" : o.kind === "window" ? "ARQ-VENTANAS" : "ARQ-HUECOS")).map((o) => {
            const a = o.angle * Math.PI / 180, ux = Math.cos(a) * o.width / 2, uy = Math.sin(a) * o.width / 2;
            const color = o.kind === "door" ? "#b45309" : o.kind === "window" ? "#2563eb" : "#9ca3af";
            return <g key={o.id}><line x1={o.at[0] - ux} y1={o.at[1] - uy} x2={o.at[0] + ux} y2={o.at[1] + uy} stroke={color} strokeWidth={3} vectorEffect="non-scaling-stroke"><title>{`${o.id} · ${o.kind} · ${Math.round(o.confidence * 100)}%`}</title></line>
              {o.hinge && o.swing && <line x1={o.hinge[0]} y1={o.hinge[1]} x2={o.swing[0]} y2={o.swing[1]} stroke={color} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />}</g>;
          })}
        </g>
      )}
      {p.ghosts.filter(() => prefs.ghosts).map((g) => (
        <g key={g.key} opacity={0.35} stroke="#7a8190" fill="none" data-ui>
          {g.lines.map((pts, i) => <polyline key={i} points={polyline(pts)} strokeDasharray="6 4" strokeWidth={1.4} vectorEffect="non-scaling-stroke" />)}
          {g.nodes.map((q, i) => <circle key={i} cx={q[0]} cy={q[1]} r={4 * u} strokeWidth={1.4} vectorEffect="non-scaling-stroke" />)}
          <text x={(g.lines[0]?.[0] ?? g.nodes[0] ?? [0, 0])[0]} y={(g.lines[0]?.[0] ?? g.nodes[0] ?? [0, 0])[1] - 6 * u} fontSize={10 * u} fill="#7a8190" stroke="none">{g.level}</text>
        </g>
      ))}
      {prefs.refs && k !== null && p.reference.filter((it) => !prefs.hiddenDisc.includes(it.discipline)).map((it) => {
        const c = colorOfDiscipline(it.discipline), pts = refPx(it), w = Math.max(it.width_m / k, 2 * u);
        const tip = <title>{`${it.discipline} · ${it.kind} ${it.tag}`}</title>;
        return it.shape === "line"
          ? <polyline key={it.sheet + it.id} points={polyline(pts)} fill="none" stroke={c} strokeOpacity={it.origin === "reservation" ? 0.25 : 0.35} strokeWidth={w} strokeLinecap="butt" strokeLinejoin="round" strokeDasharray={it.origin === "reservation" ? "8 5" : undefined}>{tip}</polyline>
          : <rect key={it.sheet + it.id} x={pts[0][0] - w / 2} y={pts[0][1] - w / 2} width={w} height={w} fill={c} fillOpacity={0.3} stroke={c} strokeOpacity={0.6} strokeWidth={1} vectorEffect="non-scaling-stroke">{tip}</rect>;
      })}
      {drawing.scale && <g stroke="#ff7f0e" strokeWidth={1.5} vectorEffect="non-scaling-stroke"><line x1={drawing.scale.p1[0]} y1={drawing.scale.p1[1]} x2={drawing.scale.p2[0]} y2={drawing.scale.p2[1]} strokeDasharray="6 4" vectorEffect="non-scaling-stroke" />
        <text x={(drawing.scale.p1[0] + drawing.scale.p2[0]) / 2} y={(drawing.scale.p1[1] + drawing.scale.p2[1]) / 2 - 4 * u} fontSize={11 * u} fill="#ff7f0e" stroke="none">{drawing.scale.distance_m} m</text></g>}
      {p.scalePts.map((q, i) => <circle key={i} cx={q[0]} cy={q[1]} r={4 * u} fill="#ff7f0e" data-ui />)}
      {shownLines.map((l) => {
        const sel = isSel({ type: "line", id: l.id }), lit = highlight.includes(l.id), hov = p.hoverRef?.type === "line" && p.hoverRef.id === l.id;
        const f = fillOf[l.id];
        return <g key={l.id} opacity={dim(l.circuit || circuitOfLine[l.id], l.id) ? 0.18 : 1}>
          {lit && <polyline points={polyline(l.points)} fill="none" stroke="#ff2bd6" strokeOpacity={0.45} strokeWidth={9} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />}
          {f && f.status !== "ok" && <polyline points={polyline(l.points)} fill="none" stroke={FILL_TONE[f.status]} strokeOpacity={0.35} strokeWidth={8} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />}
          <polyline points={polyline(l.points)} fill="none" stroke={sel ? "var(--bad, #d62728)" : lineColor(l)} strokeWidth={sel ? 4 : hov ? 3.4 : 2.2} strokeDasharray={isLocked(drawing, { type: "line", id: l.id }) ? "9 3" : undefined} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
        </g>;
      })}
      {p.draft.length > 0 && <polyline points={polyline([...p.draft, ...(p.hover ? [p.hover] : [])])} fill="none" stroke={colorOf(p.kindId)} strokeWidth={2} strokeDasharray="5 4" vectorEffect="non-scaling-stroke" data-ui />}
      {p.guides && <g data-ui pointerEvents="none" stroke="#c0392b" strokeWidth={1} strokeDasharray="6 4" vectorEffect="non-scaling-stroke">
        {p.guides.x !== undefined && <line x1={p.guides.x} x2={p.guides.x} y1={-1e5} y2={1e5} vectorEffect="non-scaling-stroke" />}
        {p.guides.y !== undefined && <line y1={p.guides.y} y2={p.guides.y} x1={-1e5} x2={1e5} vectorEffect="non-scaling-stroke" />}
      </g>}
      {p.tool === "node" && p.hover && p.kindId && !p.readOnly && <g data-ui pointerEvents="none" opacity={0.5}><Sym id={kindOf(p.kindId)?.simbolo_2d ?? "camara"} x={p.hover[0]} y={p.hover[1]} s={NODE_PX * 2 * u} color="#2f6fdd" sel={false} prims={profile?.symbols?.[kindOf(p.kindId)?.simbolo_2d ?? ""]} ghost /></g>}
      {p.tool === "line" && p.draft.length === 0 && p.hover && !p.readOnly && <circle data-ui pointerEvents="none" cx={p.hover[0]} cy={p.hover[1]} r={4 * u} fill="none" stroke={colorOf(p.kindId)} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />}
      {p.route && <polyline points={polyline(p.route.points)} fill="none" stroke="#ff2bd6" strokeWidth={5} strokeOpacity={0.6} vectorEffect="non-scaling-stroke" strokeLinejoin="round" data-ui />}
      {auto.map((n) => { const q = autoPos(n); return <circle key={n.id} cx={q[0]} cy={q[1]} r={(n.kind === "J" ? 3.5 : 4.5) * u} fill={n.kind === "J" ? "#555" : "none"} stroke={n.kind === "J" ? "#555" : "#d62728"} strokeWidth={1.5} vectorEffect="non-scaling-stroke"><title>{n.tag}</title></circle>; })}
      {shownNodes.map((n) => {
        const sel = isSel({ type: "node", id: n.id }), sym = kindOf(n.kind)?.simbolo_2d ?? "camara";
        const rot = typeof n.attrs?.rot_deg === "number" ? (n.attrs.rot_deg as number) : 0;
        return <g key={n.id} opacity={dim(n.circuit) ? 0.18 : 1}>
          <g transform={rot ? `rotate(${rot} ${n.x} ${n.y})` : undefined}><Sym id={sym} x={n.x} y={n.y} s={NODE_PX * 2 * u} color="#222" sel={sel} prims={profile?.symbols?.[sym]} /></g>
          {n.circuit && <circle cx={n.x} cy={n.y} r={NODE_PX * 1.5 * u} fill="none" stroke={circuitColor(n.circuit)} strokeWidth={3} vectorEffect="non-scaling-stroke" />}
          {isLocked(drawing, { type: "node", id: n.id }) && <rect x={n.x + NODE_PX * 0.5 * u} y={n.y + NODE_PX * 0.5 * u} width={5 * u} height={5 * u} fill="#222" data-ui />}
          {drawing.outlet === n.id && <circle cx={n.x} cy={n.y} r={NODE_PX * 1.6 * u} fill="none" stroke="#2ca02c" strokeWidth={2} vectorEffect="non-scaling-stroke" />}
        </g>;
      })}
      {labels.map((lb) => { const o = offsets[lb.id] ?? [0, 0]; return <text key={lb.id} x={lb.x + o[0] + (lb.anchor === "middle" ? lb.w / 2 : 0)} y={lb.y + o[1] + lb.h * 0.85} fontSize={11 * u} textAnchor={lb.anchor} fill={lb.color} stroke="#fff" strokeWidth={3 * u} paintOrder="stroke" pointerEvents="none">{lb.text}</text>; })}
      {p.problems.map((pr, i) => pr.at && <g key={i} data-ui><circle cx={pr.at[0]} cy={pr.at[1]} r={12 * u} fill="none" stroke={pr.severity === "error" ? "#d62728" : "#e08a00"} strokeWidth={2} strokeDasharray="3 2" vectorEffect="non-scaling-stroke"><title>{p.t("layout.problem." + pr.code)}</title></circle></g>)}
      {p.pins.filter(() => prefs.pins).map((pin) => { const q = k ? fromMetres(pin.at_m, drawing.origin, k) : [0, 0]; const c = TONE[pin.tone]; return (
        <g key={pin.id} data-ui style={{ cursor: "pointer" }} onPointerDown={(e) => { e.stopPropagation(); p.onPin(pin.id); }}>
          {pin.kind === "clash"
            ? <path d={`M${q[0]} ${q[1] - 12 * u} l${9 * u} ${12 * u} l${-9 * u} ${12 * u} l${-9 * u} ${-12 * u}z`} fill={c} fillOpacity={0.85} stroke="#fff" strokeWidth={1.2} vectorEffect="non-scaling-stroke" />
            : <path d={`M${q[0]} ${q[1]} l${-6 * u} ${-10 * u} a${7 * u} ${7 * u} 0 1 1 ${12 * u} 0z`} fill={c} stroke="#fff" strokeWidth={1.2} vectorEffect="non-scaling-stroke" />}
          <title>{pin.label}</title>
        </g>); })}
      {p.measure.length > 0 && <g data-ui stroke="#0a7" strokeWidth={1.6} fill="none" vectorEffect="non-scaling-stroke"><polyline points={polyline([...p.measure, ...(p.hover && p.measure.length < 3 ? [p.hover] : [])])} strokeDasharray="4 3" vectorEffect="non-scaling-stroke" />{p.measure.map((q, i) => <circle key={i} cx={q[0]} cy={q[1]} r={3 * u} fill="#0a7" />)}</g>}
      {selLine && (
        <g data-ui>
          {selLine.points.slice(0, -1).map((a, i) => { const b = selLine.points[i + 1], m: Pt = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
            return <rect key={`s${i}`} x={m[0] - hs} y={m[1] - hs} width={2 * hs} height={2 * hs} transform={`rotate(45 ${m[0]} ${m[1]})`} fill="#fff" stroke="#4363d8" strokeWidth={1.5} vectorEffect="non-scaling-stroke" style={{ cursor: "move" }} onPointerDown={(e) => p.grabLine(e, { line: selLine.id, seg: i })}><title>{p.t("layout.grip.segment")}</title></rect>; })}
          {([0, 1] as const).map((end) => { const q = selLine.points[end === 0 ? 0 : selLine.points.length - 1];
            return <rect key={`e${end}`} x={q[0] - hs} y={q[1] - hs} width={2 * hs} height={2 * hs} fill="#4363d8" stroke="#fff" strokeWidth={1} vectorEffect="non-scaling-stroke" style={{ cursor: "crosshair" }} onPointerDown={(e) => p.grabLine(e, { line: selLine.id, end })}><title>{p.t("layout.grip.end")}</title></rect>; })}
        </g>
      )}
      {p.marquee && <rect data-ui x={Math.min(p.marquee.a[0], p.marquee.b[0])} y={Math.min(p.marquee.a[1], p.marquee.b[1])} width={Math.abs(p.marquee.a[0] - p.marquee.b[0])} height={Math.abs(p.marquee.a[1] - p.marquee.b[1])} fill="#4363d8" fillOpacity={0.12} stroke="#4363d8" strokeDasharray={p.marquee.b[0] < p.marquee.a[0] ? "2 3" : "4 3"} vectorEffect="non-scaling-stroke" />}
      {p.snapMark && p.snapMark.kind !== "none" && <g data-ui pointerEvents="none" stroke="#0a7" strokeWidth={1.6} fill="none" vectorEffect="non-scaling-stroke">
        {p.snapMark.kind === "mid" ? <path d={`M${p.snapMark.p[0]} ${p.snapMark.p[1] - 6 * u} l${6 * u} ${12 * u} h${-12 * u}z`} vectorEffect="non-scaling-stroke" /> : p.snapMark.kind === "grid" ? <path d={`M${p.snapMark.p[0] - 5 * u} ${p.snapMark.p[1]} h${10 * u} M${p.snapMark.p[0]} ${p.snapMark.p[1] - 5 * u} v${10 * u}`} vectorEffect="non-scaling-stroke" /> : <rect x={p.snapMark.p[0] - 6 * u} y={p.snapMark.p[1] - 6 * u} width={12 * u} height={12 * u} vectorEffect="non-scaling-stroke" />}
      </g>}
      <g stroke="#2ca02c" strokeWidth={1.5} vectorEffect="non-scaling-stroke" data-ui><line x1={drawing.origin[0] - 10 * u} y1={drawing.origin[1]} x2={drawing.origin[0] + 10 * u} y2={drawing.origin[1]} vectorEffect="non-scaling-stroke" />
        <line x1={drawing.origin[0]} y1={drawing.origin[1] - 10 * u} x2={drawing.origin[0]} y2={drawing.origin[1] + 10 * u} vectorEffect="non-scaling-stroke" />
        <text x={drawing.origin[0] + 12 * u} y={drawing.origin[1] - 4 * u} fontSize={11 * u} fill="#2ca02c" stroke="none">0,0</text></g>
    </>
  );
}
