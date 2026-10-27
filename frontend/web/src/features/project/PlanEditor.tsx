import { useEffect, useMemo, useRef, useState } from "react";
import {
  addCircuit, addLine, addNode, assignCircuit, circuitFor, commit, connectEnds, DLine, dist, Drawing, History, inBox, joinCircuit, merge, metresPerUnit, moveElements, moveSegment, ortho, pick, Pt, redo, Ref,
  removeMany, sameRef, setOrigin, setScale, stretchEnd, toggle, undo, updateCircuit,
} from "./planEditing";
import {
  addRoom, alignDelta, alignNodes, Architecture, RunsProposal, arrayClip, boundsOf, Clip, copyElements, distributeNodes, fromMetres, inBoxCross, isLocked, measureAngle, normalizeClip, pasteClip, pointIndex, parallelToWall, polygonArea, Problem,
  RoutePath, selectionStats, setLocked, shortestRoute, SnapKind, snapEx, splitLineAt, svgVertices, toMetres, transformGroup, unlocked, UnderlayOpts,
} from "./planTools";
import { CommandPalette, Command, ContextMenu, CoordBar, Legend, MenuItem, MiniMap, NumberForm, SelectionStrip, SelectionTable, ShortcutsPanel, TextForm, ToolDef, Toolbox, ViewPanel } from "./PlanChrome";
import PlanScene from "./PlanScene";
import { exportPng, printSheet } from "./planExport";
import { DEFAULT_KEYS, keyOf, PlanPrefs, usePlanPrefs } from "./planPrefs";
import type { Ghost, Pin, RefItem } from "./planTypes";
import { Icon } from "@epc/ui";

/** The canvas of the plan-drawing editor: the plan as an underlay, a toolbox, and what the person draws over it. It computes nothing about the engineering
 *  (lengths, tags, the graph): the parent gives it what the engine derived. Text goes through `t`; data comes in props and changes go out through `onChange`. */
export interface Kind { id: string; etiqueta: { es: string; en: string }; prefijo_tag: string; simbolo_2d: string; capa_dxf: string; atributos?: string[]; un_solo_circuito?: boolean; carga?: boolean; vertical?: boolean; geom?: Record<string, number> }
export type Prim = { t: "rect"; w: number; h: number } | { t: "circle"; r: number } | { t: "line"; a: [number, number]; b: [number, number] };
export interface Profile { id: string; name: { es: string; en: string }; lines: Kind[]; nodes: Kind[]; shortcuts: Record<string, string>; symbols?: Record<string, Prim[]> }
export interface DerivedNode { id: string; tag: string; kind: string; placed: boolean; x_m: number; y_m: number }
export interface DerivedStretch { tag: string; line: string; line_tag: string; kind: string; from: string; to: string; length_m: number; circuit: string | null; carries?: { circuit: string; ternas: number }[]; cables?: number }
export interface DerivedRoute { found: boolean; from: string; to: string; ternas: number; stretches: string[]; lines: string[]; length_m: number; cable_length_m: number; unreached?: string[] }
export interface Fill { used_pct: number; limit_pct: number; cable_mm: number; status: "ok" | "near" | "over" }
export interface Derived {
  ready: boolean; circuits?: Record<string, DerivedRoute>; plan?: { metres_per_unit: number; origin: Pt }; nodes?: DerivedNode[]; stretches?: DerivedStretch[]; warnings?: string[];
  schedule?: { lines: Record<string, { lines: number; stretches: number; length_m: number }>; nodes: Record<string, number>; circuit_routes: Record<string, { stretches: string[]; length_m: number }>; containers: { tag: string; kind: string; circuits: string[]; cables: number; fill?: Fill }[]; length_by_line_m: Record<string, number>; total_length_m: number };
  network?: { invert_m: Record<string, number>; validated: boolean; rule: string } | null;
}
type Tool = "select" | "box" | "pan" | "scale" | "origin" | "node" | "line" | "erase" | "split" | "measure" | "route" | "pin" | "room" | "alignUnderlay" | "cropUnderlay";
interface View { x: number; y: number; w: number; h: number }
type Measure = "dist" | "angle" | "area";

export interface Props {
  prefs?: [PlanPrefs, (p: Partial<PlanPrefs>) => void]; drawing: Drawing; onChange: (next: Drawing) => void; derived: Derived | null; profile: Profile | undefined; lang: "es" | "en"; underlayUrl: string | null; underlayKind?: string;
  readOnly?: boolean; t: (key: string) => string; selection: Ref[]; onSelect: (r: Ref[]) => void; highlight?: string[]; focusCircuit?: string;
  sheetKey?: string; sheetTitle?: string; reference?: RefItem[]; ghosts?: Ghost[]; pins?: Pin[]; onPin?: (id: string) => void; problems?: Problem[];
  freeCircuits?: string[]; circuitTags?: string[]; focusRequest?: { n: number; refs?: Ref[]; at_m?: Pt; at?: Pt }; architecture?: Architecture | null; proposal?: RunsProposal | null; onTool?: (tool: string) => void; roomRequest?: number;
  onNewPin?: (at_m: Pt) => void; onCopyLevels?: (clip: Clip) => void; onReserve?: (lineId: string) => void; onTemplateSave?: (name: string, clip: Clip) => void; pendingClip?: Clip | null; onClipUsed?: () => void;
}

const FIXED_KEYS = [
  { keys: "Ctrl+Z / Ctrl+Y", action: "Deshacer / Rehacer" }, { keys: "Ctrl+C / X / V", action: "Copiar / Cortar / Pegar" }, { keys: "Ctrl+D", action: "Duplicar" }, { keys: "Ctrl+A", action: "Seleccionar todo" },
  { keys: "Ctrl+L", action: "Bloquear" }, { keys: "Ctrl+K", action: "Paleta de comandos" }, { keys: "F / Z", action: "Ajustar vista / a la selección" }, { keys: "Espacio", action: "Mover la vista" },
  { keys: "Flechas", action: "Mover la selección" }, { keys: "Enter / Esc", action: "Terminar / cancelar" }, { keys: "?", action: "Esta ayuda" },
];
const SELECT_TOOLS: ToolDef[] = [
  { id: "select", icon: "select", write: false }, { id: "box", icon: "box", write: false }, { id: "pan", icon: "pan", write: false }, { id: "measure", icon: "measure", write: false }, { id: "pin", icon: "pin", write: false },
  { id: "scale", icon: "scale", write: true }, { id: "origin", icon: "origin", write: true }, { id: "node", icon: "node", write: true }, { id: "line", icon: "line", write: true }, { id: "split", icon: "split", write: true }, { id: "room", icon: "room", write: true },
  { id: "route", icon: "route", write: true }, { id: "erase", icon: "erase", write: true },
];

export default function PlanEditor(props: Props) {
  const { drawing, onChange, derived, profile, lang, underlayUrl, readOnly, t, selection, onSelect, highlight = [] } = props;
  const own = usePlanPrefs();
  const [prefs, setPrefs] = props.prefs ?? own;
  const [tool, setTool] = useState<Tool>("select");
  const [kindId, setKindId] = useState("");
  const [draft, setDraft] = useState<Pt[]>([]);
  const [hover, setHover] = useState<Pt | null>(null);
  const [snapMark, setSnapMark] = useState<{ p: Pt; kind: SnapKind } | null>(null);
  const [cursorM, setCursorM] = useState<Pt | null>(null);
  const [scalePts, setScalePts] = useState<Pt[]>([]);
  const [scaleText, setScaleText] = useState("");
  const [marquee, setMarquee] = useState<{ a: Pt; b: Pt } | null>(null);
  const [hist, setHist] = useState<History>({ past: [], future: [] });
  const [img, setImg] = useState<{ w: number; h: number } | null>(null);
  const [view, setView] = useState<View>({ x: 0, y: 0, w: 1200, h: 800 });
  const [menu, setMenu] = useState<{ at: [number, number]; items: MenuItem[] } | null>(null);
  const [palette, setPalette] = useState(false);
  const [panel, setPanel] = useState<"" | "view" | "keys" | "table">("");
  const [form, setForm] = useState<"" | "array" | "transform" | "template" | "length" | "room">("");
  const [roomDraft, setRoomDraft] = useState<Pt[]>([]);
  const [measureMode, setMeasureMode] = useState<Measure>("dist");
  const [measure, setMeasure] = useState<Pt[]>([]);
  const [routeFrom, setRouteFrom] = useState("");
  const [route, setRoute] = useState<RoutePath | null>(null);
  const [lenText, setLenText] = useState("");
  const [hoverRef, setHoverRef] = useState<Ref | null>(null);
  const [tip, setTip] = useState<{ x: number; y: number; text: string[] } | null>(null);
  const [spaceDown, setSpaceDown] = useState(false);
  const [vertices, setVertices] = useState<((at: Pt, tol: number) => Pt | null) | null>(null);
  const [note, setNote] = useState("");
  const [guides, setGuides] = useState<{ x?: number; y?: number } | null>(null);
  const scaleInput = useRef<HTMLInputElement>(null);
  const box = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const pan = useRef<{ sx: number; sy: number; v: View; u: number } | null>(null);
  const clipboard = useRef<Clip | null>(null);
  const last = useRef<{ type: "node"; kind: string } | { type: "paste" } | { type: "line"; kind: string } | null>(null);
  const pointers = useRef(new Map<number, Pt>());
  const pinch = useRef<{ d: number; v: View } | null>(null);
  const drag = useRef<{ start: Pt; base: Drawing; refs: Ref[]; moved: boolean; alone: boolean } | null>(null);
  const grip = useRef<{ line: string; end?: 0 | 1; seg?: number; start: Pt; base: Drawing; moved: boolean } | null>(null);

  const lineKinds = profile?.lines ?? [];
  const nodeKinds = profile?.nodes ?? [];
  const loadKinds = useMemo(() => new Set(nodeKinds.filter((n) => n.carga).map((n) => n.id)), [profile]);
  const kindName = (kd: Kind) => kd.etiqueta[lang] ?? kd.etiqueta.es;
  const k = metresPerUnit(drawing);
  const under: UnderlayOpts = (drawing as Drawing & { underlay_opts?: UnderlayOpts }).underlay_opts ?? {};
  const baseW = img?.w ?? 1200;
  const fav = (id: string) => prefs.favorites.includes(`${drawing.discipline}:${id}`);
  const write = !readOnly;
  const isSel = (r: Ref) => selection.some((q) => sameRef(q, r));

  useEffect(() => {                                    // the plan underlay: its size sets the first view
    if (!underlayUrl) { setImg(null); return; }
    const i = new Image();
    i.onload = () => { setImg({ w: i.naturalWidth || 1200, h: i.naturalHeight || 800 }); setView({ x: 0, y: 0, w: i.naturalWidth || 1200, h: i.naturalHeight || 800 }); };
    i.src = underlayUrl;
  }, [underlayUrl]);
  useEffect(() => {                                    // the vertices of a vector underlay, to snap to
    setVertices(null);
    if (!underlayUrl || props.underlayKind !== "svg" || !img) return;
    let live = true;
    fetch(underlayUrl).then((r) => r.text()).then((text) => { if (live) { const pts = svgVertices(text, img.w, img.h); if (pts.length) setVertices(() => pointIndex(pts, Math.max(img.w, img.h) / 80)); } }).catch(() => undefined);
    return () => { live = false; };
  }, [underlayUrl, props.underlayKind, img]);
  useEffect(() => {                                    // the kind selected must be one the tool can use
    const list = tool === "node" || tool === "split" ? nodeKinds : lineKinds;
    if (!list.some((x) => x.id === kindId)) setKindId(list[0]?.id ?? "");
  }, [profile, tool]);
  useEffect(() => { if (scalePts.length === 2) scaleInput.current?.focus(); }, [scalePts.length]);
  useEffect(() => { if (note) { const id = window.setTimeout(() => setNote(""), 4000); return () => window.clearTimeout(id); } return undefined; }, [note]);
  useEffect(() => {                                    // a template chosen elsewhere lands in the middle of what is shown
    if (!props.pendingClip || !write) return;
    const c = props.pendingClip;
    const b = boundsOf({ ...drawing, nodes: c.nodes, lines: c.lines }, undefined, 0, 0);
    const at: Pt = [view.x + view.w / 2, view.y + view.h / 2];
    const r = pasteClip(drawing, c, b ? [at[0] - b.x - b.w / 2, at[1] - b.y - b.h / 2] : [0, 0]);
    apply(r.drawing); onSelect(r.refs); props.onClipUsed?.();
  }, [props.pendingClip]);
  useEffect(() => {                                    // the parent asks to look at something (a warning, a clash, a note)
    const r = props.focusRequest;
    if (!r) return;
    if (r.at) setView((v) => ({ ...v, x: r.at![0] - v.w / 2, y: r.at![1] - v.h / 2 }));
    else if (r.at_m && k) { const p = fromMetres(r.at_m, drawing.origin, k); setView((v) => ({ ...v, x: p[0] - v.w / 2, y: p[1] - v.h / 2 })); }
    else if (r.refs?.length) zoomTo(r.refs);
  }, [props.focusRequest?.n]);

  // The drawing is scaled to fit the box keeping its proportions, so the screen-to-view mapping comes from the browser's own matrix of the SVG (never from the box size).
  const upp = () => { const m = svgRef.current?.getScreenCTM(); return m && m.a ? 1 / m.a : 1; };     // view units per screen pixel
  const toView = (e: { clientX: number; clientY: number }): Pt => {
    const svg = svgRef.current!;
    const m = svg.getScreenCTM();
    if (!m) return [view.x, view.y];
    const pt = svg.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const p = pt.matrixTransform(m.inverse());
    return [p.x, p.y];
  };
  const u = upp();
  const apply = (next: Drawing) => { setHist(commit(hist, drawing)); onChange(next); };
  const doUndo = () => { const r = undo(hist, drawing); setHist(r.h); if (r.d !== drawing) onChange(r.d); };
  const doRedo = () => { const r = redo(hist, drawing); setHist(r.h); if (r.d !== drawing) onChange(r.d); };
  const setUnder = (o: UnderlayOpts, history = false) => { const next = { ...drawing, underlay_opts: o } as Drawing; history ? apply(next) : onChange(next); };
  const gridUnits = prefs.grid > 0 && k ? prefs.grid / k : undefined;
  const snapAt = (raw: Pt, tol: number): { p: Pt; kind: SnapKind } => {
    if (!prefs.snap) return { p: raw, kind: "none" };
    const s = snapEx(drawing, raw, tol, { grid: gridUnits, mid: prefs.mid, walls: prefs.walls ? props.architecture?.walls : undefined });
    if (s.kind !== "none" && s.kind !== "grid") return s;
    const v = vertices?.(raw, tol);
    return v ? { p: v, kind: "ref" } : s;
  };
  const straight = (prev: Pt, p: Pt, shift: boolean) => (prefs.ortho !== shift ? ortho(prev, p) : prefs.walls && props.architecture ? parallelToWall(prev, p, props.architecture.walls, 6 * u * 4) : p);      // a line near a wall runs along it
  const selectionOf = (refs: Ref[]) => unlocked(drawing, refs);
  const zoomTo = (refs?: Ref[]) => {
    const b = boundsOf(drawing, refs, 0.2);
    if (!b) return;
    const ratio = view.w / view.h;
    const w = Math.max(b.w, b.h * ratio), h = w / ratio;
    setView({ x: b.x + b.w / 2 - w / 2, y: b.y + b.h / 2 - h / 2, w, h });
  };
  const fit = () => setView(img ? { x: 0, y: 0, w: img.w, h: img.h } : boundsOf(drawing, undefined, 0.15) ? (() => { const b = boundsOf(drawing, undefined, 0.15)!; const ratio = view.w / view.h; const w = Math.max(b.w, b.h * ratio); return { x: b.x + b.w / 2 - w / 2, y: b.y + b.h / 2 - w / ratio / 2, w, h: w / ratio }; })() : { x: 0, y: 0, w: 1200, h: 800 });
  const zoomBy = (f: number, at: Pt) => setView((v) => ({ x: at[0] - (at[0] - v.x) * f, y: at[1] - (at[1] - v.y) * f, w: v.w * f, h: v.h * f }));

  // ---------------------------------------------------------------- doing things to the drawing
  const finishLine = (stop = true) => {
    if (draft.length >= 2 && kindId) {
      let next = addLine(drawing, kindId, draft);
      next = connectEnds(next, next.lines[next.lines.length - 1].id, 25 * u);      // a sketch: the ends are completed or trimmed to touch what is near
      const lastLine = next.lines[next.lines.length - 1];
      const tag = circuitFor(next, selection, lastLine.points[0]);               // from a load or cable of a circuit: the new cable extends that circuit
      if (tag) { next = joinCircuit(next, tag, loadKinds); onSelect([{ type: "line", id: lastLine.id }]); }
      apply(next);
      last.current = { type: "line", kind: kindId };
      setDraft(prefs.chain && !stop ? [lastLine.points[lastLine.points.length - 1]] : []);
      return;
    }
    setDraft([]);
  };
  const cancel = (keepSelection = false) => { setRoomDraft([]); setDraft([]); setScalePts([]); setMarquee(null); setMeasure([]); setRoute(null); setRouteFrom(""); setLenText(""); setForm(""); setMenu(null); if (!keepSelection) onSelect([]); };
  const choose = (next: Tool | string) => { cancel(next === "line"); setPanel(""); setTool(next as Tool); };
  const confirmScale = () => {
    const meters = parseFloat(scaleText.replace(",", "."));
    if (scalePts.length === 2 && meters > 0) { apply(setScale(drawing, scalePts[0], scalePts[1], meters)); setScalePts([]); setScaleText(""); setTool("select"); }
  };
  const copy = (refs = selection) => { if (!refs.length) return false; clipboard.current = copyElements(drawing, refs); setNote(`${refs.length} ${t("plan.copied")}`); return true; };
  const pasteAt = (at: Pt | null) => {
    const c = clipboard.current;
    if (!c || !write) return;
    const b = boundsOf({ ...drawing, nodes: c.nodes, lines: c.lines }, undefined, 0, 0);
    const off: Pt = at && b ? [at[0] - b.x, at[1] - b.y] : [20 * u, 20 * u];
    const r = pasteClip(drawing, c, off);
    apply(r.drawing); onSelect(r.refs); last.current = { type: "paste" };
  };
  const remove = (refs = selection) => {
    const ok = selectionOf(refs);
    if (!ok.length || !write) { if (refs.length && !ok.length) setNote(t("plan.locked")); return; }
    if (ok.length >= 10 && !window.confirm(`${t("plan.confirmBulk")} (${ok.length})`)) return;
    apply(removeMany(drawing, ok)); onSelect([]);
  };
  const lockSelection = () => { if (!selection.length || !write) return; const lockedAll = selection.every((r) => isLocked(drawing, r)); apply(setLocked(drawing, selection, !lockedAll)); };
  const nudge = (dx: number, dy: number) => { const ok = selectionOf(selection); if (ok.length && write) onChange(moveElements(drawing, ok, dx, dy)); };
  const addMeasurePoint = (p: Pt) => setMeasure((m) => (measureMode === "dist" && m.length >= 2) || (measureMode === "angle" && m.length >= 3) ? [p] : [...m, p]);
  const measureText = (): string => {
    if (!k) return t("layout.notCalibrated");
    if (measureMode === "dist" && measure.length >= 2) return `${(dist(measure[0], measure[1]) * k).toFixed(3)} m · Δx ${(Math.abs(measure[1][0] - measure[0][0]) * k).toFixed(2)} · Δy ${(Math.abs(measure[1][1] - measure[0][1]) * k).toFixed(2)}`;
    if (measureMode === "angle" && measure.length >= 3) return `${measureAngle(measure[0], measure[1], measure[2]).toFixed(1)}°`;
    if (measureMode === "area" && measure.length >= 3) return `${(polygonArea(measure) * k * k).toFixed(2)} m² · ${t("plan.perimeter")} ${([...measure, measure[0]].slice(1).reduce((s, q, i) => s + dist(measure[i], q), 0) * k).toFixed(2)} m`;
    return t("plan.measure.hint." + measureMode);
  };
  const acceptRoute = () => {
    const tag = props.freeCircuits?.[0];
    if (!route || !tag) { setNote(t("plan.route.noFree")); return; }
    let next = addCircuit(drawing, tag);
    next = updateCircuit(next, next.circuits.length - 1, { from: routeFrom, to: route.points.length ? (drawing.nodes.find((n) => dist([n.x, n.y], route.points[route.points.length - 1]) < 1e-6)?.id ?? "") : "" });
    apply(next); setRoute(null); setRouteFrom(""); setTool("select"); setNote(`${tag} ${t("plan.route.added")}`);
  };
  const pickFor = (raw: Pt) => pick(drawing, raw, 8 * u);

  // ---------------------------------------------------------------- pointer
  const onDown = (e: React.PointerEvent) => {
    setMenu(null);
    pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pointers.current.size === 2) {                                               // two fingers: zoom and move the view; anything in progress is dropped
      const [a, b] = [...pointers.current.values()];
      pinch.current = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), v: view };
      drag.current = null; grip.current = null; setMarquee(null); pan.current = null;
      return;
    }
    const touch = e.pointerType === "touch";
    const raw = toView(e), tol = (touch ? 14 : 8) * u;
    const wantsPan = e.button === 1 || spaceDown || tool === "pan" || (touch && tool === "select" && !pickFor(raw));
    if (wantsPan) { pan.current = { sx: e.clientX, sy: e.clientY, v: view, u }; (e.target as Element).setPointerCapture?.(e.pointerId); return; }
    if (e.button !== 0 || (readOnly && !["select", "box", "measure", "pin"].includes(tool))) return;
    if (tool === "select") {
      const hit = pick(drawing, raw, tol);
      onSelect(hit ? (e.shiftKey ? toggle(selection, hit) : isSel(hit) ? selection : [hit]) : e.shiftKey ? selection : []);
      if (hit && !e.shiftKey && !readOnly) {                                         // dragging a placed element moves it (the whole selection if it is part of it); a locked one stays
        const refs = unlocked(drawing, isSel(hit) ? selection : [hit]);
        if (refs.length) { drag.current = { start: raw, base: drawing, refs, moved: false, alone: e.altKey }; (e.target as Element).setPointerCapture?.(e.pointerId); }
        else setNote(t("plan.locked"));
      } else if (!hit) { setMarquee({ a: raw, b: raw }); (e.target as Element).setPointerCapture?.(e.pointerId); }
    }
    else if (tool === "box" || tool === "cropUnderlay") { setMarquee({ a: raw, b: raw }); (e.target as Element).setPointerCapture?.(e.pointerId); }
    else if (tool === "erase") { const hit = pick(drawing, raw, tol); if (hit) remove([hit]); }
    else if (tool === "origin") { apply(setOrigin(drawing, snapAt(raw, tol).p)); setTool("select"); }
    else if (tool === "scale") { if (scalePts.length < 2) setScalePts([...scalePts, snapAt(raw, tol).p]); }
    else if (tool === "node" && kindId) { const p = snapAt(raw, tol).p; apply(addNode(drawing, kindId, p)); last.current = { type: "node", kind: kindId }; }
    else if (tool === "line" && kindId) {
      let p = snapAt(raw, tol).p;
      if (draft.length > 0) p = straight(draft[draft.length - 1], p, e.shiftKey);
      if (draft.length === 0 || dist(draft[draft.length - 1], p) > 1e-6) setDraft([...draft, p]);
    }
    else if (tool === "split") {
      const hit = pick({ ...drawing, nodes: [] }, raw, tol);
      if (hit?.type === "line") { const r = splitLineAt(drawing, hit.id, snapAt(raw, tol).p, kindId || undefined); if (r.drawing !== drawing) { apply(r.drawing); if (r.nodeId) onSelect([{ type: "node", id: r.nodeId }]); } }
    }
    else if (tool === "measure") addMeasurePoint(snapAt(raw, tol).p);
    else if (tool === "room") { let p = snapAt(raw, tol).p; if (roomDraft.length > 0) p = straight(roomDraft[roomDraft.length - 1], p, e.shiftKey); if (!roomDraft.length || dist(roomDraft[roomDraft.length - 1], p) > 1e-6) setRoomDraft([...roomDraft, p]); }
    else if (tool === "pin") { if (k && props.onNewPin) props.onNewPin(toMetres(snapAt(raw, tol).p, drawing.origin, k)); setTool("select"); }
    else if (tool === "route") {
      const hit = pick({ ...drawing, lines: [] }, raw, tol);
      if (!hit) return;
      if (!routeFrom) { setRouteFrom(hit.id); setRoute(null); }
      else { const r = shortestRoute(drawing, routeFrom, hit.id, 3 * u); if (r) setRoute(r); else { setNote(t("plan.route.none")); setRouteFrom(""); } }
    }
    else if (tool === "alignUnderlay") {
      const p = toView(e);
      if (measure.length === 0) setMeasure([p]);
      else { setUnder({ ...under, rotation: (under.rotation ?? 0) + alignDelta(measure[0], p, e.shiftKey) }, true); setMeasure([]); setTool("select"); }
    }
  };
  const onMove = (e: React.PointerEvent) => {
    if (pointers.current.has(e.pointerId)) pointers.current.set(e.pointerId, [e.clientX, e.clientY]);
    if (pinch.current && pointers.current.size >= 2) {
      const [a, b] = [...pointers.current.values()];
      const f = pinch.current.d / Math.max(1, Math.hypot(a[0] - b[0], a[1] - b[1]));
      const v0 = pinch.current.v;
      const mid = toView({ clientX: (a[0] + b[0]) / 2, clientY: (a[1] + b[1]) / 2 });
      setView({ x: mid[0] - (mid[0] - v0.x) * f, y: mid[1] - (mid[1] - v0.y) * f, w: v0.w * f, h: v0.h * f });
      return;
    }
    if (pan.current) {
      const p = pan.current;
      setView({ ...p.v, x: p.v.x - (e.clientX - p.sx) * p.u, y: p.v.y - (e.clientY - p.sy) * p.u });
      return;
    }
    const raw = toView(e);
    if (k) setCursorM(toMetres(raw, drawing.origin, k));
    if (grip.current) {
      const g = grip.current;
      g.moved = true;
      onChange(g.end !== undefined ? stretchEnd(g.base, g.line, g.end, snapAt(raw, 8 * u).p) : moveSegment(g.base, g.line, g.seg!, [raw[0] - g.start[0], raw[1] - g.start[1]]));
      return;
    }
    if (drag.current) {
      const g = drag.current;
      let d: Pt = [raw[0] - g.start[0], raw[1] - g.start[1]];
      const only = g.refs.length === 1 && g.refs[0].type === "node" ? g.base.nodes.find((n) => n.id === g.refs[0].id) : undefined;
      if (only) {                                                                                  // a single node snaps onto nodes and line ends, and lines up with the others (guides)
        const sn = snapAt(raw, 8 * u);
        let p = sn.p, found: { x?: number; y?: number } | null = null;
        if (prefs.snap && sn.kind !== "node" && sn.kind !== "end") {
          const others = g.base.nodes.filter((n) => n.id !== only.id), tol = 6 * u;
          const gx = others.find((n) => Math.abs(n.x - p[0]) < tol), gy = others.find((n) => Math.abs(n.y - p[1]) < tol);
          if (gx || gy) { p = [gx ? gx.x : p[0], gy ? gy.y : p[1]]; found = { x: gx?.x, y: gy?.y }; }
        }
        setGuides(found);
        d = [p[0] - only.x, p[1] - only.y];
      }
      if (g.moved || Math.hypot(d[0], d[1]) > 3 * u) {
        g.moved = true;
        onChange(g.alone && only ? { ...g.base, nodes: g.base.nodes.map((n) => (n.id === only.id ? { ...n, x: n.x + d[0], y: n.y + d[1] } : n)) } : moveElements(g.base, g.refs, d[0], d[1]));      // Alt: the node alone, the cables stay where they are
      }
      return;
    }
    if (marquee) setMarquee({ a: marquee.a, b: raw });
    const placing = ["node", "line", "scale", "origin", "split", "measure", "pin", "room"].includes(tool);
    const s = placing ? snapAt(raw, 8 * u) : { p: raw, kind: "none" as SnapKind };
    let p = s.p;
    if (tool === "line" && draft.length > 0) p = straight(draft[draft.length - 1], p, e.shiftKey);
    if (tool === "room" && roomDraft.length > 0) p = straight(roomDraft[roomDraft.length - 1], p, e.shiftKey);
    setHover(p);
    setSnapMark(placing && s.kind !== "none" ? { p: s.p, kind: s.kind } : null);
    if (tool === "select" && !marquee) {
      const h = pick(drawing, raw, 8 * u);
      setHoverRef(h);
      if (h) {
        const r = editorRef.current!.getBoundingClientRect();
        setTip({ x: e.clientX - r.left + 14, y: e.clientY - r.top + 14, text: describe(h) });
      } else setTip(null);
    } else if (tip) { setTip(null); setHoverRef(null); }
  };
  const onUp = (e: React.PointerEvent) => {
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) pinch.current = null;
    pan.current = null;
    setGuides(null);
    if (grip.current) { if (grip.current.moved) setHist(commit(hist, grip.current.base)); grip.current = null; return; }
    if (drag.current) { if (drag.current.moved) setHist(commit(hist, drag.current.base)); drag.current = null; return; }
    if (marquee) {
      const tiny = dist(marquee.a, marquee.b) < 3 * u;
      if (tool === "cropUnderlay" && !tiny) cropUnderlay(marquee.a, marquee.b);
      else if (!tiny) { const found = marquee.b[0] < marquee.a[0] ? inBoxCross(drawing, marquee.a, marquee.b) : inBox(drawing, marquee.a, marquee.b); onSelect(e.shiftKey ? merge(selection, found) : found); }
      setMarquee(null);
      if (tool === "cropUnderlay") setTool("select");
    }
  };
  const cropUnderlay = (a: Pt, b: Pt) => {
    if (!img) return;
    const rad = (-(under.rotation ?? 0) * Math.PI) / 180, c: Pt = [img.w / 2, img.h / 2];
    const back = (p: Pt): Pt => [c[0] + (p[0] - c[0]) * Math.cos(rad) - (p[1] - c[1]) * Math.sin(rad), c[1] + (p[0] - c[0]) * Math.sin(rad) + (p[1] - c[1]) * Math.cos(rad)];
    const [p, q] = [back(a), back(b)];
    setUnder({ ...under, crop: { x: Math.min(p[0], q[0]), y: Math.min(p[1], q[1]), w: Math.abs(p[0] - q[0]), h: Math.abs(p[1] - q[1]) } }, true);
  };
  const describe = (h: Ref): string[] => {
    const out: string[] = [];
    if (h.type === "node") {
      const n = drawing.nodes.find((x) => x.id === h.id); const dn = derived?.nodes?.find((x) => x.id === h.id);
      if (n) out.push(`${dn?.tag ?? n.id} · ${kindName(nodeKinds.find((kd) => kd.id === n.kind) ?? { etiqueta: { es: n.kind, en: n.kind } } as Kind)}`, ...(n.circuit ? [`${t("layout.circuit")}: ${n.circuit}`] : []));
    } else {
      const l = drawing.lines.find((x) => x.id === h.id); const st = derived?.stretches?.filter((x) => x.line === h.id) ?? [];
      if (l) {
        const len = st.reduce((s, x) => s + x.length_m, 0), cables = Math.max(0, ...st.map((x) => x.cables ?? 0));
        const fill = (derived?.schedule?.containers ?? []).find((c) => st.some((x) => x.tag === c.tag && c.fill))?.fill;
        out.push(`${st[0]?.line_tag ?? l.id} · ${kindName(lineKinds.find((kd) => kd.id === l.kind) ?? { etiqueta: { es: l.kind, en: l.kind } } as Kind)}`, ...(len ? [`${len.toFixed(2)} m`] : []), ...(l.circuit ? [`${t("layout.circuit")}: ${l.circuit}`] : []), ...(cables ? [`${cables} ${t("layout.props.cables")}`] : []), ...(fill ? [`${t("plan.fill")} ${fill.used_pct}% / ${fill.limit_pct}%`] : []));
      }
    }
    if (isLocked(drawing, h)) out.push(t("plan.locked"));
    return out;
  };
  const grab = (e: React.PointerEvent, g: { line: string; end?: 0 | 1; seg?: number }) => {      // a handle of the selected line: stretch its end or push a segment sideways
    if (e.button !== 0 || readOnly) return;
    if (isLocked(drawing, { type: "line", id: g.line })) { setNote(t("plan.locked")); return; }
    e.stopPropagation();
    (e.target as Element).setPointerCapture?.(e.pointerId);
    grip.current = { ...g, start: toView(e), base: drawing, moved: false };
  };
  const onWheel = (e: WheelEvent) => {
    e.preventDefault();                                // zooming the canvas must not scroll the page
    zoomBy(e.deltaY > 0 ? 1.15 : 1 / 1.15, toView(e));
  };
  const wheel = useRef(onWheel);
  wheel.current = onWheel;
  useEffect(() => {                                    // React's own wheel handler is passive and cannot stop the page scroll: this one is native
    const el = svgRef.current;
    if (!el) return;
    const h = (e: WheelEvent) => wheel.current(e);
    el.addEventListener("wheel", h, { passive: false });
    return () => el.removeEventListener("wheel", h);
  }, []);

  // ---------------------------------------------------------------- menu and commands
  const insertNodeAt = (lineId: string, at: Pt) => { const r = splitLineAt(drawing, lineId, at, nodeKinds[0]?.id); if (r.drawing !== drawing) { apply(r.drawing); if (r.nodeId) onSelect([{ type: "node", id: r.nodeId }]); } };
  const onContext = (e: React.MouseEvent) => {
    e.preventDefault();
    if (tool !== "select" && tool !== "box") { if (draft.length) finishLine(true); else cancel(true); return; }
    const raw = toView(e), hit = pickFor(raw);
    let sel = selection;
    if (hit && !isSel(hit)) { sel = [hit]; onSelect(sel); }
    const r = editorRef.current!.getBoundingClientRect();
    const has = sel.length > 0, line = hit?.type === "line" ? hit : undefined;
    const anyLoad = write && sel.some((q) => q.type === "node" && drawing.nodes.find((n) => n.id === q.id && loadKinds.has(n.kind)));
    const items: MenuItem[] = [
      { label: t("plan.act.copy"), icon: "copy", run: () => copy(sel), disabled: !has },
      { label: t("plan.act.paste"), icon: "paste", run: () => pasteAt(raw), disabled: !clipboard.current || !write },
      { label: t("plan.act.duplicate"), run: () => { copy(sel); pasteAt(null); }, disabled: !has || !write },
      { sep: true, label: "" },
      { label: t(sel.length && sel.every((q) => isLocked(drawing, q)) ? "plan.act.unlock" : "plan.act.lock"), icon: "lock", run: lockSelection, disabled: !has || !write },
      { label: t("plan.act.insertNode"), icon: "split", run: () => line && insertNodeAt(line.id, raw), disabled: !line || !write },
      ...(anyLoad && props.circuitTags?.length ? [{ label: t("plan.act.assignCircuit"), icon: "route", sub: [{ label: t("plan.act.noCircuit"), run: () => apply(assignCircuit(drawing, sel, "", loadKinds).drawing) }, ...props.circuitTags.map((tag) => ({ label: tag, run: () => apply(assignCircuit(drawing, sel, tag, loadKinds).drawing) }))] } as MenuItem] : []),
      ...(line && props.onReserve && write ? [{ label: t("plan.act.reserve"), icon: "reserve", run: () => props.onReserve!(line.id) } as MenuItem] : []),
      ...(props.onNewPin && k ? [{ label: t("plan.act.pin"), icon: "pin", run: () => props.onNewPin!(toMetres(raw, drawing.origin, k)) } as MenuItem] : []),
      { sep: true, label: "" },
      { label: t("plan.zoomSelection"), icon: "fit", run: () => zoomTo(sel.length ? sel : undefined) },
      { label: t("plan.act.repeat"), run: () => repeat(raw), disabled: !last.current || !write },
      { sep: true, label: "" },
      { label: t("plan.act.delete"), icon: "trash", danger: true, run: () => remove(sel), disabled: !has || !write },
    ];
    setMenu({ at: [e.clientX - r.left, e.clientY - r.top], items });
  };
  const repeat = (at: Pt | null) => {
    const l = last.current;
    if (!l || !write) return;
    if (l.type === "paste") pasteAt(at);
    else if (l.type === "node" && at) apply(addNode(drawing, l.kind, at));
    else if (l.type === "line") { setKindId(l.kind); setTool("line"); }
  };
  const act = (id: string) => {
    const ok = selectionOf(selection);
    if (id === "copy") copy();
    else if (id === "duplicate") { if (copy()) pasteAt(null); }
    else if (id === "delete") remove();
    else if (id === "mirrorH") ok.length && apply(transformGroup(drawing, ok, { type: "mirror", axis: "x" }));
    else if (id === "mirrorV") ok.length && apply(transformGroup(drawing, ok, { type: "mirror", axis: "y" }));
    else if (id.startsWith("align")) { const m = { alignL: "left", alignR: "right", alignT: "top", alignB: "bottom", alignH: "hcenter", alignV: "vcenter" }[id] as Parameters<typeof alignNodes>[2]; apply(alignNodes(drawing, ok, m)); }
    else if (id === "distH") apply(distributeNodes(drawing, ok, "x"));
    else if (id === "distV") apply(distributeNodes(drawing, ok, "y"));
  };
  const commands: Command[] = [
    ...SELECT_TOOLS.filter((x) => write || !x.write).map((x): Command => ({ id: "t." + x.id, group: t("plan.cmd.tools"), label: t("plan.tool." + x.id), hint: keyOf(prefs, x.id).replace("+", ""), run: () => choose(x.id) })),
    { id: "undo", group: t("plan.cmd.edit"), label: t("layout.undo"), hint: "Ctrl+Z", run: doUndo, disabled: !write }, { id: "redo", group: t("plan.cmd.edit"), label: t("layout.redo"), hint: "Ctrl+Y", run: doRedo, disabled: !write },
    { id: "copy", group: t("plan.cmd.edit"), label: t("plan.act.copy"), hint: "Ctrl+C", run: () => copy(), disabled: !selection.length }, { id: "paste", group: t("plan.cmd.edit"), label: t("plan.act.paste"), hint: "Ctrl+V", run: () => pasteAt(hover), disabled: !write }, { id: "dup", group: t("plan.cmd.edit"), label: t("plan.act.duplicate"), hint: "Ctrl+D", run: () => act("duplicate"), disabled: !selection.length || !write },
    { id: "all", group: t("plan.cmd.edit"), label: t("plan.act.selectAll"), hint: "Ctrl+A", run: () => onSelect([...drawing.nodes.map((n): Ref => ({ type: "node", id: n.id })), ...drawing.lines.map((l): Ref => ({ type: "line", id: l.id }))]) },
    { id: "lock", group: t("plan.cmd.edit"), label: t("plan.act.lock"), hint: "Ctrl+L", run: lockSelection, disabled: !selection.length || !write }, { id: "array", group: t("plan.cmd.edit"), label: t("plan.act.array"), run: () => setForm("array"), disabled: !selection.length || !write },
    { id: "transform", group: t("plan.cmd.edit"), label: t("plan.act.transform"), run: () => setForm("transform"), disabled: !selection.length || !write }, { id: "mirrorV", group: t("plan.cmd.edit"), label: t("plan.act.mirrorV"), run: () => act("mirrorV"), disabled: !selection.length || !write },
    { id: "repeat", group: t("plan.cmd.edit"), label: t("plan.act.repeat"), run: () => repeat(hover), disabled: !last.current || !write },
    { id: "fit", group: t("plan.cmd.view"), label: t("layout.fit"), hint: "F", run: fit }, { id: "zsel", group: t("plan.cmd.view"), label: t("plan.zoomSelection"), hint: "Z", run: () => zoomTo(selection.length ? selection : undefined) },
    { id: "view", group: t("plan.cmd.view"), label: t("plan.view"), run: () => setPanel("view") }, { id: "keys", group: t("plan.cmd.view"), label: t("plan.keys"), hint: "?", run: () => setPanel("keys") },
    { id: "snap", group: t("plan.cmd.view"), label: t("plan.snap.on"), run: () => setPrefs({ snap: !prefs.snap }) }, { id: "ortho", group: t("plan.cmd.view"), label: t("plan.snap.ortho"), run: () => setPrefs({ ortho: !prefs.ortho }) },
    { id: "grid", group: t("plan.cmd.view"), label: t("plan.grid"), run: () => setPrefs({ grid: prefs.grid ? 0 : 0.5 }) }, { id: "color", group: t("plan.cmd.view"), label: t("plan.colorBy"), run: () => setPrefs({ color: prefs.color === "kind" ? "circuit" : "kind" }) },
    { id: "lengths", group: t("plan.cmd.view"), label: t("plan.show.lengths"), run: () => setPrefs({ lengths: !prefs.lengths }) }, { id: "labels", group: t("plan.cmd.view"), label: t("plan.show.labels"), run: () => setPrefs({ labels: !prefs.labels }) },
    { id: "isolate", group: t("plan.cmd.view"), label: t("plan.show.isolate"), run: () => setPrefs({ isolate: !prefs.isolate }) },
    { id: "png", group: t("plan.cmd.output"), label: t("plan.export.png"), run: () => doExport("png") }, { id: "print", group: t("plan.cmd.output"), label: t("plan.export.print"), run: () => doExport("print") },
  ];
  const doExport = async (what: "png" | "print") => {
    if (!svgRef.current) return;
    try {
      if (what === "png") await exportPng(svgRef.current, underlayUrl && !under.hidden ? underlayUrl : null, props.sheetTitle || "plan");
      else await printSheet(svgRef.current, underlayUrl && !under.hidden ? underlayUrl : null, { title: props.sheetTitle || "plan", lines: [k ? `1 u = ${k.toFixed(4)} m` : t("layout.notCalibrated"), new Date().toLocaleDateString()] });
    } catch { setNote(t("plan.export.fail")); }
  };

  // ---------------------------------------------------------------- keyboard
  const onKey = (e: React.KeyboardEvent) => {
    const mod = e.ctrlKey || e.metaKey, key = e.key.toLowerCase();
    const on = e.target as HTMLElement;
    if (on.closest?.("input, select, textarea") && !(mod && key === "k")) return;                  // typing in a field of a panel is not a shortcut
    if (mod) {
      const handled = { z: doUndo, y: doRedo, c: () => copy(), x: () => { if (copy()) remove(); }, v: () => pasteAt(hover), d: () => act("duplicate"), l: lockSelection, k: () => setPalette(true),
        a: () => onSelect([...drawing.nodes.map((n): Ref => ({ type: "node", id: n.id })), ...drawing.lines.map((l): Ref => ({ type: "line", id: l.id }))]) }[key];
      if (handled) { e.preventDefault(); handled(); }
      return;
    }
    if (e.key === " ") { if (on.closest?.("button, a, summary")) return; e.preventDefault(); setSpaceDown(true); return; }       // Space on a button presses it; elsewhere it moves the view
    if (tool === "line" && draft.length > 0 && /^[0-9.,]$/.test(e.key) && k) { setLenText((s) => s + e.key); setForm("length"); return; }
    if (form === "length") {
      if (e.key === "Enter") { applyLength(); return; }
      if (e.key === "Backspace") { setLenText((s) => s.slice(0, -1)); return; }
    }
    if (e.key === "Escape") { if (tool === "line" && draft.length > 0) { setDraft([]); setLenText(""); setForm(""); } else { cancel(); if (tool !== "select") setTool("select"); } return; }
    if (e.key === "Enter") { if (tool === "room") { if (roomDraft.length >= 3) setForm("room"); return; } if (tool === "route" && route) acceptRoute(); else if (tool === "line") finishLine(false); else if (tool === "measure" && measureMode === "area") setMeasure((m) => m); else if (tool === "select" && !selection.length) repeat(hover); return; }
    if ((e.key === "Delete" || e.key === "Backspace") && selection.length > 0) { remove(); return; }
    if (e.key.startsWith("Arrow") && selection.length) { e.preventDefault(); const s = (e.shiftKey ? 10 : 1) * u; nudge(e.key === "ArrowLeft" ? -s : e.key === "ArrowRight" ? s : 0, e.key === "ArrowUp" ? -s : e.key === "ArrowDown" ? s : 0); return; }
    if (e.key === "?") { setPanel(panel === "keys" ? "" : "keys"); return; }
    if (key === "f") { fit(); return; }
    if (key === "z") { zoomTo(selection.length ? selection : undefined); return; }
    const named = Object.keys(DEFAULT_KEYS).find((a) => keyOf(prefs, a).replace("+", "") === key && keyOf(prefs, a) !== "");
    if (named && (!readOnly || !SELECT_TOOLS.find((x) => x.id === named)?.write)) { choose(named); return; }
    if (profile?.shortcuts[key] && write) {
      const id = profile.shortcuts[key];
      if (nodeKinds.some((n) => n.id === id)) { cancel(); setTool("node"); setKindId(id); } else if (lineKinds.some((l) => l.id === id)) { cancel(true); setTool("line"); setKindId(id); }
    }
  };
  const applyLength = () => {
    const m = parseFloat(lenText.replace(",", "."));
    const from = draft[draft.length - 1];
    if (!(m > 0) || !k || !from || !hover) { setLenText(""); setForm(""); return; }
    const dx = hover[0] - from[0], dy = hover[1] - from[1], n = Math.hypot(dx, dy) || 1;
    const dir: Pt = prefs.ortho || Math.abs(dx) < 1e-9 || Math.abs(dy) < 1e-9 ? (Math.abs(dx) >= Math.abs(dy) ? [Math.sign(dx) || 1, 0] : [0, Math.sign(dy) || 1]) : [dx / n, dy / n];
    setDraft([...draft, [from[0] + (dir[0] * m) / k, from[1] + (dir[1] * m) / k]]);
    setLenText(""); setForm("");
  };

  // ---------------------------------------------------------------- what the screen shows
  const tools = SELECT_TOOLS.filter((x) => (x.id !== "route" || drawing.discipline === "electrica_BT") && (x.id !== "pin" || !!props.onNewPin));
  const palette2 = tool === "node" || tool === "split" ? nodeKinds : tool === "line" ? lineKinds : [];
  const ordered = [...palette2].sort((a, b) => Number(fav(b.id)) - Number(fav(a.id)));
  const stats = useMemo(() => selectionStats(drawing, selection, k), [drawing, selection, k]);
  const legend = useMemo(() => {
    const PAL = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"], CIR = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#008080", "#9a6324", "#800000", "#808000", "#000075"];
    if (prefs.color === "circuit") return drawing.circuits.map((c, i) => ({ color: CIR[i % CIR.length], label: c.tag || "?" }));
    const used = new Set(drawing.lines.map((l) => l.kind));
    return lineKinds.filter((kd) => used.has(kd.id)).map((kd) => ({ color: PAL[lineKinds.indexOf(kd) % PAL.length], label: `${kd.id} · ${kindName(kd)}` }));
  }, [drawing.lines, drawing.circuits, prefs.color, profile, lang]);
  const lockedAll = selection.length > 0 && selection.every((r) => isLocked(drawing, r));
  const world = useMemo(() => { const b = boundsOf(drawing, undefined, 0.1); return img ? { x: 0, y: 0, w: img.w, h: img.h } : b ?? { x: 0, y: 0, w: 1200, h: 800 }; }, [drawing, img]);
  useEffect(() => { if (props.roomRequest) choose("room"); }, [props.roomRequest]);
  const hint = tool === "measure" ? measureText() : { select: "", box: "layout.hint.box", pan: "plan.hint.pan", scale: "layout.hint.scale", origin: "layout.hint.origin", node: "layout.hint.node", line: "layout.hint.line", erase: "layout.hint.erase", split: "plan.hint.split",
    route: routeFrom ? "plan.hint.route2" : "plan.hint.route1", room: "plan.hint.room", pin: "plan.hint.pin", alignUnderlay: "plan.hint.align", cropUnderlay: "plan.hint.crop" }[tool];
  const hintText = tool === "measure" ? hint : hint ? t(hint) : "";
  const snapName = snapMark && snapMark.kind !== "none" ? t("plan.snapkind." + snapMark.kind) : "";
  const cursor = spaceDown || tool === "pan" ? "grab" : tool === "select" ? "default" : "crosshair";
  const grid = gridUnits && gridUnits / u >= 7 ? gridUnits : 0;

  return (
    <div className="wb-editor" tabIndex={0} ref={editorRef} onKeyDown={onKey} onKeyUp={(e) => { if (e.key === " ") setSpaceDown(false); }}>
      <Toolbox tools={tools} tool={tool} readOnly={readOnly} keys={Object.fromEntries(Object.keys(DEFAULT_KEYS).map((a) => [a, keyOf(prefs, a)]))} t={t} onChoose={choose} canUndo={hist.past.length > 0} canRedo={hist.future.length > 0}
        onUndo={doUndo} onRedo={doRedo} onFit={fit} onSelection={() => zoomTo(selection.length ? selection : undefined)} onPalette={() => setPalette(true)}
        onExport={() => setMenu({ at: [64, 220], items: [{ label: t("plan.export.png"), icon: "image", run: () => doExport("png") }, { label: t("plan.export.print"), icon: "print", run: () => doExport("print") }] })} />
      <div className="wb-canvas" ref={box}>
        {palette2.length > 0 && (
          <div className="wb-kinds" role="group" aria-label={t("layout.kinds")}>
            {ordered.map((kd) => (
              <span key={kd.id} className="kind-row">
                <button className={kindId === kd.id ? "on" : ""} onClick={() => setKindId(kd.id)} title={kd.capa_dxf}><b>{kd.id}</b> {kindName(kd)}</button>
                <button className={"star" + (fav(kd.id) ? " on" : "")} aria-pressed={fav(kd.id)} aria-label={t("plan.favorite")} title={t("plan.favorite")}
                  onClick={() => { const id = `${drawing.discipline}:${kd.id}`; setPrefs({ favorites: fav(kd.id) ? prefs.favorites.filter((x) => x !== id) : [...prefs.favorites, id] }); }}><Icon name="star" size={12} /></button>
              </span>
            ))}
          </div>
        )}
        <div className="wb-corner">
          {!readOnly && selection.length > 0 && <SelectionStrip stats={stats} write={write} t={t} run={act} onCopyLevels={props.onCopyLevels ? () => props.onCopyLevels!(copyElements(drawing, selection)) : undefined} onArray={() => setForm("array")} onTransform={() => setForm("transform")} onTemplate={() => setForm("template")} onLock={lockSelection} locked={lockedAll} />}
          <button className="strip-btn corner-btn" onClick={() => setPanel(panel === "view" ? "" : "view")} aria-pressed={panel === "view"} title={t("plan.view")} aria-label={t("plan.view")}><Icon name="layers" size={16} /></button>
          <button className="strip-btn corner-btn" onClick={() => setPanel(panel === "keys" ? "" : "keys")} aria-pressed={panel === "keys"} title={t("plan.keys")} aria-label={t("plan.keys")}><Icon name="keyboard" size={16} /></button>
        </div>
        {panel === "view" && <ViewPanel prefs={prefs} set={setPrefs} kinds={lineKinds.map((kd) => ({ id: kd.id, name: kindName(kd) }))} underlay={under} onUnderlay={(o) => setUnder(o)} hasUnderlay={!!underlayUrl} onTool={choose} onClose={() => setPanel("")} t={t} />}
        {panel === "keys" && <ShortcutsPanel keys={prefs.keys} set={(keys) => setPrefs({ keys })} fixed={FIXED_KEYS} reserved={Object.keys(profile?.shortcuts ?? {})} t={t} onClose={() => setPanel("")} />}
        {panel === "table" && <SelectionTable stats={stats} t={t} onClose={() => setPanel("")} />}
        {tool === "scale" && scalePts.length === 2 && (
          <div className="wb-float">
            <span>{t("layout.scaleDistance")}</span>
            <input ref={scaleInput} value={scaleText} onChange={(e) => setScaleText(e.target.value)} onKeyDown={(e) => { e.stopPropagation(); if (e.key === "Enter") confirmScale(); }} style={{ width: 90 }} />
            <button className="primary" onClick={confirmScale}>{t("layout.apply")}</button><button onClick={() => cancel()}>{t("layout.cancel")}</button>
          </div>
        )}
        {tool === "measure" && (
          <div className="wb-float" role="group" aria-label={t("plan.tool.measure")}>
            {(["dist", "angle", "area"] as Measure[]).map((m) => <button key={m} className={measureMode === m ? "on" : ""} aria-pressed={measureMode === m} onClick={() => { setMeasureMode(m); setMeasure([]); }}>{t("plan.measure." + m)}</button>)}
            <b className="mono">{measureText()}</b>
          </div>
        )}
        {tool === "route" && route && (
          <div className="wb-float">
            <span>{t("plan.route.found")}: <b className="mono">{k ? `${(route.length * k).toFixed(2)} m` : "–"}</b> · {route.lines.length} {t("plan.stat.lines")}</span>
            <button className="primary" onClick={acceptRoute} disabled={!props.freeCircuits?.length}>{props.freeCircuits?.length ? `${t("plan.route.accept")} ${props.freeCircuits[0]}` : t("plan.route.noFree")}</button><button onClick={() => { setRoute(null); setRouteFrom(""); }}>{t("layout.cancel")}</button>
          </div>
        )}
        {form === "array" && <NumberForm title={t("plan.act.array")} t={t} fields={[{ key: "n", label: t("plan.array.count"), value: 3 }, { key: "dx", label: t("plan.array.dx"), value: 3 }, { key: "dy", label: t("plan.array.dy"), value: 0 }]} onCancel={() => setForm("")}
          onApply={(v) => { if (k) { const r = arrayClip(drawing, copyElements(drawing, selection), Math.max(1, Math.round(v.n)), [v.dx / k, -v.dy / k]); apply(r.drawing); onSelect(r.refs); } setForm(""); }} />}
        {form === "transform" && <NumberForm title={t("plan.act.transform")} t={t} fields={[{ key: "deg", label: t("plan.transform.angle"), value: 90 }, { key: "factor", label: t("plan.transform.scale"), value: 1 }]} onCancel={() => setForm("")}
          onApply={(v) => { let d = drawing; const ok = selectionOf(selection); if (v.deg) d = transformGroup(d, ok, { type: "rotate", deg: v.deg }); if (v.factor > 0 && v.factor !== 1) d = transformGroup(d, ok, { type: "scale", factor: v.factor }); if (d !== drawing) apply(d); setForm(""); }} />}
        {form === "template" && <TextForm title={t("plan.act.template")} label={t("plan.template.name")} t={t} onCancel={() => setForm("")} onApply={(name) => { props.onTemplateSave?.(name, normalizeClip(copyElements(drawing, selection))); setForm(""); }} />}
        {form === "room" && <TextForm title={t("plan.room.new")} label={t("plan.room.name")} t={t} onCancel={() => { setForm(""); setRoomDraft([]); }} onApply={(name) => { apply(addRoom(drawing, name, roomDraft)); setRoomDraft([]); setForm(""); setTool("select"); }} />}
        {form === "length" && <div className="wb-float"><span>{t("plan.length.type")}</span><b className="mono">{lenText || "…"} m</b><small className="muted">{t("plan.length.enter")}</small></div>}
        {note && <div className="wb-note-toast" role="status">{note}</div>}
        {tip && tip.text.length > 0 && <div className="wb-tip" style={{ left: tip.x, top: tip.y }} role="tooltip">{tip.text.map((l, i) => <div key={i}>{i === 0 ? <b>{l}</b> : l}</div>)}</div>}
        <svg ref={svgRef} width="100%" height="100%" viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`} preserveAspectRatio="xMinYMin meet" onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={onUp}
          onDoubleClick={() => { if (tool === "line") finishLine(true); else if (tool === "room" && roomDraft.length >= 3) setForm("room"); }} onContextMenu={onContext} style={{ cursor, display: "block", width: "100%", height: "100%", background: "#fff" }}>
          {grid > 0 && <><defs><pattern id="plan-grid" x={drawing.origin[0]} y={drawing.origin[1]} width={grid} height={grid} patternUnits="userSpaceOnUse"><circle cx={0} cy={0} r={0.9 * u} fill="#9aa3b5" /></pattern></defs><rect data-ui x={view.x} y={view.y} width={view.w} height={view.h} fill="url(#plan-grid)" pointerEvents="none" /></>}
          <PlanScene drawing={drawing} profile={profile} derived={derived} lang={lang} u={u} k={k} prefs={prefs} tool={tool} readOnly={readOnly} selection={selection} highlight={highlight} focusCircuit={props.focusCircuit ?? ""} hoverRef={hoverRef}
            underlayUrl={underlayUrl} img={img} underlayOpts={under} draft={draft} hover={hover} kindId={kindId} snapMark={snapMark} scalePts={scalePts} marquee={marquee} measure={measureMode === "area" || tool === "measure" || tool === "alignUnderlay" ? measure : []}
            route={route} routeFrom={routeFrom} guides={guides} roomDraft={roomDraft} proposal={props.proposal ?? null} architecture={props.underlayKind === "svg" ? null : props.architecture ?? null} reference={props.reference ?? []} ghosts={props.ghosts ?? []} pins={props.pins ?? []} problems={props.problems ?? []} onPin={(id) => props.onPin?.(id)} grabLine={grab} t={t} />
        </svg>
        <Legend title={t(prefs.color === "circuit" ? "plan.colorBy.circuit" : "plan.colorBy.kind")} entries={legend} />
        {prefs.minimap && <MiniMap drawing={drawing} world={world} view={view} t={t} onCenter={(p) => setView((v) => ({ ...v, x: p[0] - v.w / 2, y: p[1] - v.h / 2 }))} />}
        <CoordBar hint={hintText} cursor={prefs.coords ? cursorM : null} zoom={baseW / view.w} snap={snapName} stats={selection.length ? stats : null} scale={k} t={t} onTable={() => setPanel(panel === "table" ? "" : "table")} />
      </div>
      {menu && <ContextMenu at={menu.at} items={menu.items} onClose={() => setMenu(null)} />}
      {palette && <CommandPalette commands={commands} t={t} onClose={() => { setPalette(false); editorRef.current?.focus(); }} />}
    </div>
  );
}
