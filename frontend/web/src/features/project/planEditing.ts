/** Pure editing rules of the plan-drawing editor: what clicking does to the drawing. No React here, so they are tested alone.
 *  Coordinates are the units of the view (the pixels of the plan, y down); the engine turns them into metres. */
export type Pt = [number, number];
export interface Scale { p1: Pt; p2: Pt; distance_m: number }
export interface DNode { id: string; kind: string; x: number; y: number; tag?: string; circuit?: string; attrs?: Record<string, unknown> }
export interface DLine { id: string; kind: string; points: Pt[]; tag?: string; circuit?: string; attrs?: Record<string, unknown> }
export interface DCircuit { tag: string; from: string; to: string; via?: string[]; ternas: number }
export interface Drawing {
  discipline: string; scale: Scale | null; origin: Pt; nodes: DNode[]; lines: DLine[]; circuits: DCircuit[]; outlet: string; outlet_invert_m: number | null; dxf_version: string;
}
export type Ref = { type: "node" | "line"; id: string };

export const blank = (discipline = "electrica_BT"): Drawing => ({ discipline, scale: null, origin: [0, 0], nodes: [], lines: [], circuits: [], outlet: "", outlet_invert_m: null, dxf_version: "" });

export const dist = (a: Pt, b: Pt) => Math.hypot(a[0] - b[0], a[1] - b[1]);

/** Next free id of the form `<prefix><n>` among the nodes and lines (ids are unique across both). */
export function nextId(d: Drawing, prefix: string): string {
  const used = new Set([...d.nodes.map((n) => n.id), ...d.lines.map((l) => l.id)]);
  let n = 1;
  while (used.has(`${prefix}${n}`)) n++;
  return `${prefix}${n}`;
}

export const addNode = (d: Drawing, kind: string, at: Pt): Drawing => ({ ...d, nodes: [...d.nodes, { id: nextId(d, "n"), kind, x: at[0], y: at[1] }] });

/** A line needs two points at least; fewer than that adds nothing. */
export function addLine(d: Drawing, kind: string, points: Pt[]): Drawing {
  if (points.length < 2) return d;
  return { ...d, lines: [...d.lines, { id: nextId(d, "l"), kind, points }] };
}

export function remove(d: Drawing, ref: Ref): Drawing {
  if (ref.type === "node") return { ...d, nodes: d.nodes.filter((n) => n.id !== ref.id), outlet: d.outlet === ref.id ? "" : d.outlet };
  return { ...d, lines: d.lines.filter((l) => l.id !== ref.id) };
}

export const setOrigin = (d: Drawing, at: Pt): Drawing => ({ ...d, origin: at });

/** The scale from two marked points and the real distance; refused when the points coincide or the distance is not positive. */
export function setScale(d: Drawing, p1: Pt, p2: Pt, distanceM: number): Drawing {
  if (dist(p1, p2) < 1e-6 || !(distanceM > 0)) return d;
  return { ...d, scale: { p1, p2, distance_m: distanceM } };
}

/** Real metres of one unit of the view; null while there is no scale. */
export function metresPerUnit(d: Drawing): number | null {
  return d.scale ? d.scale.distance_m / dist(d.scale.p1, d.scale.p2) : null;
}

/** The point to use for a click: the nearest node or line end within `tol` view units, else the point itself. */
export function snap(d: Drawing, at: Pt, tol: number): Pt {
  let best: { p: Pt; d: number } | null = null;
  const consider = (p: Pt) => { const k = dist(p, at); if (k <= tol && (!best || k < best.d)) best = { p, d: k }; };
  d.nodes.forEach((n) => consider([n.x, n.y]));
  d.lines.forEach((l) => { consider(l.points[0]); consider(l.points[l.points.length - 1]); });
  return best ? (best as { p: Pt }).p : at;
}

/** Keep the new segment horizontal or vertical (Shift held): whichever direction is closer. */
export function ortho(prev: Pt, at: Pt): Pt {
  return Math.abs(at[0] - prev[0]) >= Math.abs(at[1] - prev[1]) ? [at[0], prev[1]] : [prev[0], at[1]];
}

/** What is at this point: a node within `tol`, else a line passing within `tol`, else nothing. Nodes win because they sit on top of lines. */
export function pick(d: Drawing, at: Pt, tol: number): Ref | null {
  for (let i = d.nodes.length - 1; i >= 0; i--) if (dist([d.nodes[i].x, d.nodes[i].y], at) <= tol) return { type: "node", id: d.nodes[i].id };
  for (let i = d.lines.length - 1; i >= 0; i--) {
    const pts = d.lines[i].points;
    for (let k = 0; k < pts.length - 1; k++) if (segmentDistance(at, pts[k], pts[k + 1]) <= tol) return { type: "line", id: d.lines[i].id };
  }
  return null;
}

export function segmentDistance(p: Pt, a: Pt, b: Pt): number {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const n = dx * dx + dy * dy;
  const t = n === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n));
  return dist(p, [a[0] + t * dx, a[1] + t * dy]);
}

/** Level names: L0 is the ground level, L1.. go up, L-1.. go down. */
export const levelNumber = (level: string): number => parseInt(level.slice(1), 10);
export const levelName = (n: number): string => `L${n}`;
export function nextLevel(levels: string[], direction: "up" | "down"): string {
  if (levels.length === 0) return "L0";
  const nums = levels.map(levelNumber);
  return levelName(direction === "up" ? Math.max(...nums) + 1 : Math.min(...nums) - 1);
}

/** Undo and redo over whole drawings. */
export interface History { past: Drawing[]; future: Drawing[] }
export const commit = (h: History, current: Drawing): History => ({ past: [...h.past, current].slice(-100), future: [] });
export function undo(h: History, current: Drawing): { h: History; d: Drawing } {
  if (h.past.length === 0) return { h, d: current };
  return { h: { past: h.past.slice(0, -1), future: [current, ...h.future] }, d: h.past[h.past.length - 1] };
}
export function redo(h: History, current: Drawing): { h: History; d: Drawing } {
  if (h.future.length === 0) return { h, d: current };
  return { h: { past: [...h.past, current], future: h.future.slice(1) }, d: h.future[0] };
}

/** A value typed in a properties field: a number when it looks like one, else the text; empty removes the attribute. */
export function parseAttr(text: string): string | number | undefined {
  const t = text.trim();
  if (t === "") return undefined;
  return /^-?\d+([.,]\d+)?$/.test(t) ? parseFloat(t.replace(",", ".")) : t;
}

export function setAttr(attrs: Record<string, unknown> | undefined, key: string, text: string): Record<string, unknown> {
  const next = { ...(attrs ?? {}) };
  const v = parseAttr(text);
  if (v === undefined) delete next[key]; else next[key] = v;
  return next;
}

export const updateLine = (d: Drawing, id: string, patch: Partial<DLine>): Drawing => ({ ...d, lines: d.lines.map((l) => (l.id === id ? { ...l, ...patch } : l)) });
export const updateNode = (d: Drawing, id: string, patch: Partial<DNode>): Drawing => ({ ...d, nodes: d.nodes.map((n) => (n.id === id ? { ...n, ...patch } : n)) });

/** Circuits routed over the drawing: the tag comes from the board (a reference, never typed); the origin and the destination are nodes. */
export const addCircuit = (d: Drawing, tag = ""): Drawing => ({ ...d, circuits: [...d.circuits, { tag, from: "", to: "", ternas: 1 }] });
export const updateCircuit = (d: Drawing, index: number, patch: Partial<DCircuit>): Drawing => ({ ...d, circuits: d.circuits.map((c, i) => (i === index ? { ...c, ...patch } : c)) });
export const removeCircuit = (d: Drawing, index: number): Drawing => ({ ...d, circuits: d.circuits.filter((_, i) => i !== index) });
/** The board circuits not yet routed on this drawing (a circuit is routed once; its parallel cables are its ternas). */
export const freeCircuits = (d: Drawing, all: string[]): string[] => all.filter((t) => !d.circuits.some((c) => c.tag === t));

/** Selection of several elements at once: a box, a kind, or Shift-click. Only nodes and whole lines inside a box are taken. */
export const sameRef = (a: Ref, b: Ref) => a.type === b.type && a.id === b.id;
export const toggle = (sel: Ref[], ref: Ref): Ref[] => (sel.some((r) => sameRef(r, ref)) ? sel.filter((r) => !sameRef(r, ref)) : [...sel, ref]);
export const merge = (sel: Ref[], more: Ref[]): Ref[] => [...sel, ...more.filter((m) => !sel.some((r) => sameRef(r, m)))];

export function inBox(d: Drawing, a: Pt, b: Pt): Ref[] {
  const [x0, x1] = [Math.min(a[0], b[0]), Math.max(a[0], b[0])];
  const [y0, y1] = [Math.min(a[1], b[1]), Math.max(a[1], b[1])];
  const inside = (p: Pt) => p[0] >= x0 && p[0] <= x1 && p[1] >= y0 && p[1] <= y1;
  return [
    ...d.nodes.filter((n) => inside([n.x, n.y])).map((n): Ref => ({ type: "node", id: n.id })),
    ...d.lines.filter((l) => l.points.every(inside)).map((l): Ref => ({ type: "line", id: l.id })),
  ];
}

export const ofKind = (d: Drawing, kind: string): Ref[] => d.nodes.filter((n) => n.kind === kind).map((n): Ref => ({ type: "node", id: n.id }));

export function removeMany(d: Drawing, refs: Ref[]): Drawing {
  return refs.reduce((acc, r) => remove(acc, r), d);
}

/** Give the loads in the selection (luminaires, sockets, HVAC...: the kinds in `loadKinds`) a circuit of the board, or none with an empty tag. Returns the drawing and how many were changed. */
export function assignCircuit(d: Drawing, refs: Ref[], tag: string, loadKinds: Set<string>): { drawing: Drawing; changed: number } {
  const ids = new Set(refs.filter((r) => r.type === "node").map((r) => r.id));
  let changed = 0;
  const nodes = d.nodes.map((n) => {
    if (!ids.has(n.id) || !loadKinds.has(n.kind)) return n;
    changed++;
    const { circuit: _old, ...rest } = n;
    return tag ? { ...rest, circuit: tag } : rest;
  });
  return { drawing: { ...d, nodes }, changed };
}

/** How many loads each circuit has in this drawing. */
export function loadsOf(d: Drawing, tag: string, loadKinds: Set<string>): number {
  return d.nodes.filter((n) => n.circuit === tag && loadKinds.has(n.kind)).length;
}

/** Move the selected elements by a delta. Nodes move; a selected line moves with all its points; the points of other lines that sit on a moved node follow it, so the network stays joined. */
export function moveElements(d: Drawing, refs: Ref[], dx: number, dy: number): Drawing {
  if (!dx && !dy) return d;
  const nodeIds = new Set(refs.filter((r) => r.type === "node").map((r) => r.id));
  const lineIds = new Set(refs.filter((r) => r.type === "line").map((r) => r.id));
  const moved = d.nodes.filter((n) => nodeIds.has(n.id));
  const shift = (p: Pt): Pt => [p[0] + dx, p[1] + dy];
  const follows = (p: Pt) => moved.some((n) => Math.abs(n.x - p[0]) < 1e-6 && Math.abs(n.y - p[1]) < 1e-6);
  return {
    ...d,
    nodes: d.nodes.map((n) => (nodeIds.has(n.id) ? { ...n, x: n.x + dx, y: n.y + dy } : n)),
    lines: d.lines.map((l) => (lineIds.has(l.id) ? { ...l, points: l.points.map(shift) } : { ...l, points: l.points.map((p) => (follows(p) ? shift(p) : p)) })),
  };
}

/** Move some points of one line by their own deltas; the nodes and the points of other lines sitting on a moved point follow it, so the network stays joined. */
function movePoints(d: Drawing, lineId: string, moves: { i: number; to: Pt }[]): Drawing {
  const line = d.lines.find((l) => l.id === lineId);
  if (!line) return d;
  const at = (a: Pt, b: Pt) => Math.abs(a[0] - b[0]) < 1e-6 && Math.abs(a[1] - b[1]) < 1e-6;
  const jumps = moves.map((m) => ({ from: line.points[m.i], to: m.to }));
  const dest = (p: Pt): Pt => jumps.find((j) => at(j.from, p))?.to ?? p;
  return {
    ...d,
    nodes: d.nodes.map((n) => { const q = dest([n.x, n.y]); return q[0] === n.x && q[1] === n.y ? n : { ...n, x: q[0], y: q[1] }; }),
    lines: d.lines.map((l) => (l.id === lineId ? { ...l, points: l.points.map((p, i) => moves.find((m) => m.i === i)?.to ?? p) } : { ...l, points: l.points.map(dest) })),
  };
}

/** Stretch the end of a line along its own direction: the end goes to the closest point of the axis of its last segment, so the line stays straight (orthogonal when it was). */
export function stretchEnd(d: Drawing, lineId: string, end: 0 | 1, target: Pt): Drawing {
  const l = d.lines.find((x) => x.id === lineId);
  if (!l || l.points.length < 2) return d;
  const i = end === 0 ? 0 : l.points.length - 1;
  const anchor = l.points[end === 0 ? 1 : i - 1];
  const ux = l.points[i][0] - anchor[0], uy = l.points[i][1] - anchor[1];
  const len = Math.hypot(ux, uy);
  if (len < 1e-9) return d;
  const t = ((target[0] - anchor[0]) * ux + (target[1] - anchor[1]) * uy) / len;
  if (t < 1e-6) return d;                                                              // never folds back over the line
  return movePoints(d, lineId, [{ i, to: [anchor[0] + (ux / len) * t, anchor[1] + (uy / len) * t] }]);
}

/** Move one segment of a line sideways (perpendicular to itself) by the part of `offset` across it; its neighbours stretch to follow. */
export function moveSegment(d: Drawing, lineId: string, seg: number, offset: Pt): Drawing {
  const l = d.lines.find((x) => x.id === lineId);
  if (!l || seg < 0 || seg + 1 >= l.points.length) return d;
  const a = l.points[seg], b = l.points[seg + 1];
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
  if (len < 1e-9) return d;
  const n: Pt = [-(b[1] - a[1]) / len, (b[0] - a[0]) / len];
  const k = offset[0] * n[0] + offset[1] * n[1];
  return movePoints(d, lineId, [{ i: seg, to: [a[0] + n[0] * k, a[1] + n[1] * k] }, { i: seg + 1, to: [b[0] + n[0] * k, b[1] + n[1] * k] }]);
}
