/** More pure rules of the plan-drawing editor: snapping, splitting, copying, aligning, transforming, measuring, checking and routing. No React here, so they are tested alone.
 *  Coordinates are the units of the view (the pixels of the plan, y down); metres appear only where a scale `k` (metres per unit) is passed. */
import { DLine, DNode, Drawing, dist, drawnJunctions, mapElements, moveElements, nextId, Pt, Ref, sameRef, segmentDistance, UnderlayOpts } from "./planEditing";
export type { UnderlayOpts };

const EPS = 1e-6;
const same = (a: Pt, b: Pt) => Math.abs(a[0] - b[0]) < EPS && Math.abs(a[1] - b[1]) < EPS;
const ref = (type: Ref["type"], id: string): Ref => ({ type, id });

// ---------------------------------------------------------------- snapping
export interface SnapOpts { grid?: number; mid?: boolean; ref?: Pt[]; walls?: ArchWall[] }
export type SnapKind = "node" | "end" | "ref" | "wall" | "mid" | "grid" | "none";
export interface Snapped { p: Pt; kind: SnapKind }
const RANK: Record<SnapKind, number> = { node: 0, end: 1, ref: 2, wall: 3, mid: 4, grid: 5, none: 6 };

/** The point to use for a click: the nearest node, line end, vertex of a reference drawing or segment midpoint within `tol` (nodes first), else the grid point, else the point itself. */
export function snapEx(d: Drawing, at: Pt, tol: number, o: SnapOpts = {}): Snapped {
  const found: { p: Pt; kind: SnapKind; gap: number }[] = [];
  const consider = (p: Pt, kind: SnapKind) => { const gap = dist(p, at); if (gap <= tol) found.push({ p, kind, gap }); };
  d.nodes.forEach((n) => consider([n.x, n.y], "node"));
  d.lines.forEach((l) => {
    consider(l.points[0], "end"); consider(l.points[l.points.length - 1], "end");
    if (o.mid) l.points.slice(0, -1).forEach((a, i) => consider([(a[0] + l.points[i + 1][0]) / 2, (a[1] + l.points[i + 1][1]) / 2], "mid"));
  });
  (o.ref ?? []).forEach((p) => consider(p, "ref"));
  const w = o.walls ? wallSnap(o.walls, at, tol) : null;
  if (w) consider(w, "wall");
  found.sort((a, b) => RANK[a.kind] - RANK[b.kind] || a.gap - b.gap);
  if (found.length) return { p: found[0].p, kind: found[0].kind };
  if (o.grid && o.grid > 0) return { p: [d.origin[0] + Math.round((at[0] - d.origin[0]) / o.grid) * o.grid, d.origin[1] + Math.round((at[1] - d.origin[1]) / o.grid) * o.grid], kind: "grid" };
  return { p: at, kind: "none" };
}

// ---------------------------------------------------------------- locks
export const isLocked = (d: Drawing, r: Ref): boolean => (r.type === "node" ? d.nodes.find((n) => n.id === r.id)?.attrs?.locked : d.lines.find((l) => l.id === r.id)?.attrs?.locked) === true;
/** The part of a selection that may be changed. */
export const unlocked = (d: Drawing, refs: Ref[]): Ref[] => refs.filter((r) => !isLocked(d, r));

function withAttr(attrs: Record<string, unknown> | undefined, key: string, on: boolean): Record<string, unknown> {
  const next = { ...(attrs ?? {}) };
  if (on) next[key] = true; else delete next[key];
  return next;
}

export function setLocked(d: Drawing, refs: Ref[], on: boolean): Drawing {
  const has = (type: Ref["type"], id: string) => refs.some((r) => r.type === type && r.id === id);
  return { ...d, nodes: d.nodes.map((n) => (has("node", n.id) ? { ...n, attrs: withAttr(n.attrs, "locked", on) } : n)), lines: d.lines.map((l) => (has("line", l.id) ? { ...l, attrs: withAttr(l.attrs, "locked", on) } : l)) };
}

// ---------------------------------------------------------------- splitting a line
function closestOnLine(points: Pt[], at: Pt): { seg: number; p: Pt; gap: number } {
  let best = { seg: 0, p: points[0], gap: Infinity };
  for (let i = 0; i + 1 < points.length; i++) {
    const a = points[i], b = points[i + 1];
    const dx = b[0] - a[0], dy = b[1] - a[1], n = dx * dx + dy * dy;
    const t = n === 0 ? 0 : Math.max(0, Math.min(1, ((at[0] - a[0]) * dx + (at[1] - a[1]) * dy) / n));
    const p: Pt = [a[0] + t * dx, a[1] + t * dy], gap = dist(p, at);
    if (gap < best.gap) best = { seg: i, p, gap };
  }
  return best;
}

const dedupe = (pts: Pt[]): Pt[] => pts.filter((p, i) => i === 0 || !same(p, pts[i - 1]));

/** Cut a line in two at the point of it closest to `at`, optionally putting a node there. Both halves keep the kind, the circuit and the attributes of the original; the second gets a new id. */
export function splitLineAt(d: Drawing, lineId: string, at: Pt, nodeKind?: string): { drawing: Drawing; nodeId?: string; lineId?: string } {
  const l = d.lines.find((x) => x.id === lineId);
  if (!l || l.points.length < 2) return { drawing: d };
  const { seg, p } = closestOnLine(l.points, at);
  const left = dedupe([...l.points.slice(0, seg + 1), p]), right = dedupe([p, ...l.points.slice(seg + 1)]);
  if (left.length < 2 || right.length < 2) return { drawing: d };                     // the cut falls on an end: nothing to split
  const second = nextId(d, "l");
  let next: Drawing = { ...d, lines: d.lines.flatMap((x) => (x.id === lineId ? [{ ...x, points: left }, { ...x, id: second, points: right, tag: "" }] : [x])) };
  let nodeId: string | undefined;
  if (nodeKind) { nodeId = nextId(next, "n"); next = { ...next, nodes: [...next.nodes, { id: nodeId, kind: nodeKind, x: p[0], y: p[1] }] }; }
  return { drawing: next, nodeId, lineId: second };
}

// ---------------------------------------------------------------- copy, paste, array
export interface Clip { nodes: DNode[]; lines: DLine[] }

export function copyElements(d: Drawing, refs: Ref[]): Clip {
  const nodes = d.nodes.filter((n) => refs.some((r) => r.type === "node" && r.id === n.id));
  const lines = d.lines.filter((l) => refs.some((r) => r.type === "line" && r.id === l.id));
  return JSON.parse(JSON.stringify({ nodes, lines }));
}

/** Put a copy of a clip in the drawing moved by `offset`. The copies get new ids and no tags (the engine tags them); they keep kind, circuit and attributes. Returns what was added, selected. */
export function pasteClip(d: Drawing, clip: Clip, offset: Pt): { drawing: Drawing; refs: Ref[] } {
  let cur = d;
  const refs: Ref[] = [];
  for (const n of clip.nodes) {
    const id = nextId(cur, "n");
    cur = { ...cur, nodes: [...cur.nodes, { ...n, id, tag: "", x: n.x + offset[0], y: n.y + offset[1], attrs: withAttr(n.attrs, "locked", false) }] };
    refs.push(ref("node", id));
  }
  for (const l of clip.lines) {
    const id = nextId(cur, "l");
    cur = { ...cur, lines: [...cur.lines, { ...l, id, tag: "", points: l.points.map((p): Pt => [p[0] + offset[0], p[1] + offset[1]]), attrs: withAttr(l.attrs, "locked", false) }] };
    refs.push(ref("line", id));
  }
  return { drawing: cur, refs };
}

/** `count` further copies of a clip, each `step` after the last (the matrix of luminaires every 3 m). */
export function arrayClip(d: Drawing, clip: Clip, count: number, step: Pt): { drawing: Drawing; refs: Ref[] } {
  let cur = d;
  const refs: Ref[] = [];
  for (let i = 1; i <= Math.min(count, 500); i++) {
    const r = pasteClip(cur, clip, [step[0] * i, step[1] * i]);
    cur = r.drawing;
    refs.push(...r.refs);
  }
  return { drawing: cur, refs };
}

/** Copy a clip to every level of a list: the same arrangement on each repeated floor. Returns one drawing per target. */
export function stampClip(target: Drawing, clip: Clip): Drawing {
  return pasteClip(target, clip, [0, 0]).drawing;
}

/** A clip as the template stores it: positions relative to its own top-left corner, so it can be put anywhere. */
export function normalizeClip(clip: Clip): Clip {
  const pts: Pt[] = [...clip.nodes.map((n): Pt => [n.x, n.y]), ...clip.lines.flatMap((l) => l.points)];
  if (!pts.length) return clip;
  const x0 = Math.min(...pts.map((p) => p[0])), y0 = Math.min(...pts.map((p) => p[1]));
  return { nodes: clip.nodes.map((n) => ({ ...n, x: n.x - x0, y: n.y - y0, circuit: undefined, tag: "" })), lines: clip.lines.map((l) => ({ ...l, tag: "", circuit: undefined, points: l.points.map((p): Pt => [p[0] - x0, p[1] - y0]) })) };
}

// ---------------------------------------------------------------- what is selected
export const polylineLength = (pts: Pt[]): number => pts.slice(1).reduce((s, p, i) => s + dist(pts[i], p), 0);

export interface SelectionStats { nodes: number; lines: number; byKind: Record<string, number>; length_m: number | null; circuits: string[] }
export function selectionStats(d: Drawing, refs: Ref[], k: number | null): SelectionStats {
  const nodes = d.nodes.filter((n) => refs.some((r) => r.type === "node" && r.id === n.id));
  const lines = d.lines.filter((l) => refs.some((r) => r.type === "line" && r.id === l.id));
  const byKind: Record<string, number> = {};
  [...nodes, ...lines].forEach((e) => { byKind[e.kind] = (byKind[e.kind] ?? 0) + 1; });
  const circuits = [...new Set([...nodes, ...lines].map((e) => e.circuit).filter((c): c is string => !!c))].sort();
  return { nodes: nodes.length, lines: lines.length, byKind, length_m: k === null ? null : Math.round(lines.reduce((s, l) => s + polylineLength(l.points), 0) * k * 100) / 100, circuits };
}

/** The box around some elements (all of them without `refs`) with a margin, or null for an empty drawing. */
export function boundsOf(d: Drawing, refs?: Ref[], margin = 0.1, minSize = 20): { x: number; y: number; w: number; h: number } | null {
  const take = (r: Ref) => !refs || refs.some((q) => sameRef(q, r));
  const pts: Pt[] = [...d.nodes.filter((n) => take(ref("node", n.id))).map((n): Pt => [n.x, n.y]), ...d.lines.filter((l) => take(ref("line", l.id))).flatMap((l) => l.points)];
  if (!pts.length) return null;
  const x0 = Math.min(...pts.map((p) => p[0])), x1 = Math.max(...pts.map((p) => p[0])), y0 = Math.min(...pts.map((p) => p[1])), y1 = Math.max(...pts.map((p) => p[1]));
  const w = Math.max(x1 - x0, minSize), h = Math.max(y1 - y0, minSize);
  return { x: x0 - w * margin, y: y0 - h * margin, w: w * (1 + 2 * margin), h: h * (1 + 2 * margin) };
}

// ---------------------------------------------------------------- align and transform
export type AlignMode = "left" | "right" | "top" | "bottom" | "hcenter" | "vcenter";

/** Line the selected nodes up on one side or on their middle; the cables that end on them follow. */
export function alignNodes(d: Drawing, refs: Ref[], mode: AlignMode): Drawing {
  const ids = new Set(refs.filter((r) => r.type === "node").map((r) => r.id));
  const sel = d.nodes.filter((n) => ids.has(n.id));
  if (sel.length < 2) return d;
  const xs = sel.map((n) => n.x), ys = sel.map((n) => n.y);
  const target = { left: Math.min(...xs), right: Math.max(...xs), hcenter: (Math.min(...xs) + Math.max(...xs)) / 2, top: Math.min(...ys), bottom: Math.max(...ys), vcenter: (Math.min(...ys) + Math.max(...ys)) / 2 }[mode];
  const horizontal = mode === "left" || mode === "right" || mode === "hcenter";
  return sel.reduce((cur, n) => moveElements(cur, [ref("node", n.id)], horizontal ? target - n.x : 0, horizontal ? 0 : target - n.y), d);
}

/** Space the selected nodes evenly between the first and the last along an axis. */
export function distributeNodes(d: Drawing, refs: Ref[], axis: "x" | "y"): Drawing {
  const ids = new Set(refs.filter((r) => r.type === "node").map((r) => r.id));
  const sel = d.nodes.filter((n) => ids.has(n.id)).sort((a, b) => a[axis] - b[axis]);
  if (sel.length < 3) return d;
  const first = sel[0][axis], step = (sel[sel.length - 1][axis] - first) / (sel.length - 1);
  return sel.reduce((cur, n, i) => moveElements(cur, [ref("node", n.id)], axis === "x" ? first + step * i - n.x : 0, axis === "y" ? first + step * i - n.y : 0), d);
}

export type Transform = { type: "rotate"; deg: number } | { type: "mirror"; axis: "x" | "y" } | { type: "scale"; factor: number };

/** Turn, flip or resize the selection around the middle of its box. */
export function transformGroup(d: Drawing, refs: Ref[], op: Transform): Drawing {
  const box = boundsOf(d, refs, 0, 0);
  if (!box || refs.length === 0) return d;
  const c: Pt = [box.x + box.w / 2, box.y + box.h / 2];
  const rad = op.type === "rotate" ? (op.deg * Math.PI) / 180 : 0;
  const fn = (p: Pt): Pt => {
    const x = p[0] - c[0], y = p[1] - c[1];
    if (op.type === "rotate") return [c[0] + x * Math.cos(rad) - y * Math.sin(rad), c[1] + x * Math.sin(rad) + y * Math.cos(rad)];
    if (op.type === "mirror") return op.axis === "x" ? [c[0] - x, p[1]] : [p[0], c[1] - y];
    return op.factor > 0 ? [c[0] + x * op.factor, c[1] + y * op.factor] : p;
  };
  return mapElements(d, refs, fn);
}

// ---------------------------------------------------------------- measuring
/** Angle at `v` between the directions to `a` and to `b`, in degrees (0 to 180). */
export function measureAngle(a: Pt, v: Pt, b: Pt): number {
  const u: Pt = [a[0] - v[0], a[1] - v[1]], w: Pt = [b[0] - v[0], b[1] - v[1]];
  const n = Math.hypot(u[0], u[1]) * Math.hypot(w[0], w[1]);
  return n === 0 ? 0 : (Math.acos(Math.max(-1, Math.min(1, (u[0] * w[0] + u[1] * w[1]) / n))) * 180) / Math.PI;
}

export function polygonArea(pts: Pt[]): number {
  let s = 0;
  pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; s += p[0] * q[1] - q[0] * p[1]; });
  return Math.abs(s) / 2;
}

export const toMetres = (p: Pt, origin: Pt, k: number): Pt => [(p[0] - origin[0]) * k, -(p[1] - origin[1]) * k];
export const fromMetres = (m: Pt, origin: Pt, k: number): Pt => [origin[0] + m[0] / k, origin[1] - m[1] / k];

// ---------------------------------------------------------------- the plan underlay
/** How much to turn the underlay (degrees, added to its current turn) so that the line between two points taken on the screen becomes horizontal (vertical with `vertical`). */
export function alignDelta(p1: Pt, p2: Pt, vertical = false): number {
  const angle = (Math.atan2(p2[1] - p1[1], p2[0] - p1[0]) * 180) / Math.PI;
  const target = vertical ? 90 : 0;
  let delta = target - angle;
  while (delta > 90) delta -= 180;                                                  // never more than a quarter turn: the same line, the nearest way
  while (delta < -90) delta += 180;
  return Math.round(delta * 1000) / 1000;
}

// ---------------------------------------------------------------- checks
export interface Problem { code: "dup_node" | "orphan_node" | "isolated_line" | "no_scale" | "empty" | "circuit_unrouted" | "circuit_open" | "link_missing" | "link_far" | "link_oneway"; severity: "error" | "warn"; ref?: Ref; at?: Pt; tag?: string }

function touches(l: DLine, p: Pt, tol: number): boolean {
  return l.points.some((q, i) => (i + 1 < l.points.length ? segmentDistance(p, q, l.points[i + 1]) : dist(p, q)) <= tol);
}

const turn = (o: Pt, a: Pt, b: Pt) => Math.sign((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]));

function crosses(a: DLine, b: DLine): boolean {
  if (a.points.some((p) => touches(b, p, 1e-3)) || b.points.some((p) => touches(a, p, 1e-3))) return true;
  return a.points.slice(0, -1).some((p, i) => b.points.slice(0, -1).some((q, j) => {
    const p2 = a.points[i + 1], q2 = b.points[j + 1];
    return turn(p, p2, q) !== turn(p, p2, q2) && turn(q, q2, p) !== turn(q, q2, p2);
  }));
}

/** Parts of the drawing that are probably a slip: two nodes on top of each other, a node no cable reaches, and a group of cables with no node at all. */
export function findProblems(d: Drawing, tol: number): Problem[] {
  const out: Problem[] = [];
  d.nodes.forEach((n, i) => d.nodes.slice(i + 1).filter((m) => dist([n.x, n.y], [m.x, m.y]) <= tol).forEach((m) => out.push({ code: "dup_node", severity: "warn", ref: ref("node", m.id), at: [m.x, m.y], tag: n.id })));
  d.nodes.filter((n) => d.lines.length > 0 && !d.lines.some((l) => touches(l, [n.x, n.y], tol))).forEach((n) => out.push({ code: "orphan_node", severity: "warn", ref: ref("node", n.id), at: [n.x, n.y] }));
  const group = d.lines.map((_, i) => i);
  const root = (i: number): number => (group[i] === i ? i : (group[i] = root(group[i])));
  d.lines.forEach((a, i) => d.lines.forEach((b, j) => { if (j > i && root(i) !== root(j) && crosses(a, b)) group[root(j)] = root(i); }));
  const withNode = new Set(d.lines.map((l, i) => (d.nodes.some((n) => touches(l, [n.x, n.y], tol)) ? root(i) : -1)));
  d.lines.forEach((l, i) => { if (!withNode.has(root(i)) && root(i) === i) out.push({ code: "isolated_line", severity: "warn", ref: ref("line", l.id), at: l.points[0] }); });
  return out;
}

export interface RouteInfo { found?: boolean; unreached?: string[] }
/** What to look at before making the files: the scale, an empty drawing, circuits that are not routed or leave loads out, plus the slips of `findProblems`. */
export function generationChecks(d: Drawing, circuits: Record<string, RouteInfo> | undefined, tol: number): Problem[] {
  const out: Problem[] = [];
  if (!d.scale) out.push({ code: "no_scale", severity: "error" });
  if (!d.nodes.length && !d.lines.length) out.push({ code: "empty", severity: "error" });
  d.circuits.forEach((c) => {
    const r = circuits?.[c.tag];
    if (!r || r.found === false) out.push({ code: "circuit_unrouted", severity: "error", tag: c.tag });
    else if (r.unreached && r.unreached.length) out.push({ code: "circuit_open", severity: "warn", tag: c.tag });
  });
  return [...out, ...findProblems(d, tol)];
}

// ---------------------------------------------------------------- routes through the drawn network
export interface RoutePath { lines: string[]; points: Pt[]; length: number }

/** The shortest way along the lines between two nodes of the drawing (the length is in view units), or null when they are not joined. */
export function shortestRoute(d: Drawing, fromId: string, toId: string, tol: number): RoutePath | null {
  const a = d.nodes.find((n) => n.id === fromId), b = d.nodes.find((n) => n.id === toId);
  if (!a || !b) return null;
  const verts: Pt[] = [];
  const vid = (p: Pt): number => { const i = verts.findIndex((q) => dist(p, q) <= tol); if (i >= 0) return i; verts.push(p); return verts.length - 1; };
  d.lines.forEach((l) => l.points.forEach(vid));
  drawnJunctions(d).forEach(vid);
  const s = vid([a.x, a.y]), e = vid([b.x, b.y]);
  const adj: { to: number; w: number; line: string }[][] = verts.map(() => []);
  d.lines.forEach((l) => l.points.slice(0, -1).forEach((p, i) => {
    const q = l.points[i + 1], len2 = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2;
    const on = verts.map((v, k) => ({ k, t: len2 ? ((v[0] - p[0]) * (q[0] - p[0]) + (v[1] - p[1]) * (q[1] - p[1])) / len2 : 0, v })).filter((c) => c.t > -1e-9 && c.t < 1 + 1e-9 && segmentDistance(c.v, p, q) <= tol).sort((x, y) => x.t - y.t);
    on.slice(0, -1).forEach((c, j) => { const n = on[j + 1]; if (n.k !== c.k) { const w = dist(c.v, n.v); adj[c.k].push({ to: n.k, w, line: l.id }); adj[n.k].push({ to: c.k, w, line: l.id }); } });
  }));
  const best = verts.map(() => Infinity), from: { v: number; line: string }[] = verts.map(() => ({ v: -1, line: "" })), done = verts.map(() => false);
  best[s] = 0;
  for (;;) {
    let u = -1;
    best.forEach((g, i) => { if (!done[i] && g < Infinity && (u < 0 || g < best[u])) u = i; });
    if (u < 0 || u === e) break;
    done[u] = true;
    adj[u].forEach((x) => { if (best[u] + x.w < best[x.to]) { best[x.to] = best[u] + x.w; from[x.to] = { v: u, line: x.line }; } });
  }
  if (best[e] === Infinity) return null;
  const points: Pt[] = [], lines: string[] = [];
  for (let v = e; v >= 0; v = from[v].v) { points.unshift(verts[v]); if (from[v].line && !lines.includes(from[v].line)) lines.unshift(from[v].line); if (v === s) break; }
  return { lines, points, length: best[e] };
}

// ---------------------------------------------------------------- labels
export interface LabelBox { id: string; x: number; y: number; w: number; h: number }

/** Offsets that keep text labels from lying on top of each other: each label stays where it is if free, else takes the nearest free spot around it. */
export function spreadLabels(labels: LabelBox[]): Record<string, Pt> {
  const placed: { x: number; y: number; w: number; h: number }[] = [];
  const out: Record<string, Pt> = {};
  const hit = (a: { x: number; y: number; w: number; h: number }) => placed.some((b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h);
  [...labels].sort((p, q) => p.y - q.y || p.x - q.x).forEach((l) => {
    const tries: Pt[] = [[0, 0], [0, -l.h], [0, l.h], [l.w * 0.6, 0], [-l.w * 0.6, 0], [l.w * 0.6, -l.h], [l.w * 0.6, l.h], [-l.w * 0.6, -l.h], [-l.w * 0.6, l.h], [0, -2 * l.h], [0, 2 * l.h]];
    const pick = tries.find((o) => !hit({ x: l.x + o[0], y: l.y + o[1], w: l.w, h: l.h })) ?? [0, 0];
    placed.push({ x: l.x + pick[0], y: l.y + pick[1], w: l.w, h: l.h });
    out[l.id] = pick;
  });
  return out;
}

/** The elements a warning of the engine talks about: its text names them by tag (TB-001, CA-003/2...). */
export function warningTargets(text: string, nodes: { id: string; tag: string }[], stretches: { line: string; tag: string; line_tag: string }[]): Ref[] {
  const found: Ref[] = [];
  nodes.filter((n) => n.tag && text.includes(n.tag)).forEach((n) => found.push(ref("node", n.id)));
  stretches.filter((s) => (s.tag && text.includes(s.tag)) || (s.line_tag && text.includes(s.line_tag))).forEach((s) => { if (!found.some((r) => r.type === "line" && r.id === s.line)) found.push(ref("line", s.line)); });
  return found;
}

// ---------------------------------------------------------------- selecting by crossing
/** Select by a box dragged right to left (as CAD does): what is inside the box and what it touches. */
export function inBoxCross(d: Drawing, a: Pt, b: Pt): Ref[] {
  const [x0, x1] = [Math.min(a[0], b[0]), Math.max(a[0], b[0])], [y0, y1] = [Math.min(a[1], b[1]), Math.max(a[1], b[1])];
  const inside = (p: Pt) => p[0] >= x0 && p[0] <= x1 && p[1] >= y0 && p[1] <= y1;
  const edges: [Pt, Pt][] = [[[x0, y0], [x1, y0]], [[x1, y0], [x1, y1]], [[x1, y1], [x0, y1]], [[x0, y1], [x0, y0]]];
  const hits = (p: Pt, q: Pt) => inside(p) || inside(q) || edges.some(([e, f]) => turn(p, q, e) !== turn(p, q, f) && turn(e, f, p) !== turn(e, f, q));
  return [
    ...d.nodes.filter((n) => inside([n.x, n.y])).map((n) => ref("node", n.id)),
    ...d.lines.filter((l) => l.points.slice(0, -1).some((p, i) => hits(p, l.points[i + 1]))).map((l) => ref("line", l.id)),
  ];
}

// ---------------------------------------------------------------- the vertices of a drawn underlay
/** The points of a vector underlay (a DXF shown as an SVG) in the units of the view, to snap to. Reads lines, polylines, polygons and the straight parts of paths. */
export function svgVertices(text: string, width: number, height: number, limit = 40000): Pt[] {
  let doc: Document;
  try { doc = new DOMParser().parseFromString(text, "image/svg+xml"); } catch { return []; }
  const root = doc.documentElement;
  if (!root || root.nodeName !== "svg") return [];
  const vb = (root.getAttribute("viewBox") ?? "").split(/[\s,]+/).map(Number);
  const [vx, vy, vw, vh] = vb.length === 4 && vb.every((n) => Number.isFinite(n)) && vb[2] > 0 && vb[3] > 0 ? vb : [0, 0, parseFloat(root.getAttribute("width") ?? "") || width, parseFloat(root.getAttribute("height") ?? "") || height];
  const sx = width / vw, sy = height / vh, s = Math.min(sx, sy);              // preserveAspectRatio meet, centred
  const ox = (width - vw * s) / 2, oy = (height - vh * s) / 2;
  const out: Pt[] = [];
  const add = (x: number, y: number) => { if (Number.isFinite(x) && Number.isFinite(y) && out.length < limit) out.push([ox + (x - vx) * s, oy + (y - vy) * s]); };
  const nums = (t: string) => (t.match(/-?\d*\.?\d+(?:e[-+]?\d+)?/gi) ?? []).map(Number);
  doc.querySelectorAll("line").forEach((l) => { add(+(l.getAttribute("x1") ?? NaN), +(l.getAttribute("y1") ?? NaN)); add(+(l.getAttribute("x2") ?? NaN), +(l.getAttribute("y2") ?? NaN)); });
  doc.querySelectorAll("polyline,polygon").forEach((p) => { const n = nums(p.getAttribute("points") ?? ""); for (let i = 0; i + 1 < n.length; i += 2) add(n[i], n[i + 1]); });
  doc.querySelectorAll("path").forEach((p) => {
    const d = p.getAttribute("d") ?? "";
    if (/[AaCcSsQqTt]/.test(d)) return;                                          // curves have no vertices to snap to (their ends are in the next commands)
    const n = nums(d);
    for (let i = 0; i + 1 < n.length; i += 2) add(n[i], n[i + 1]);
  });
  return out;
}

/** Nearest-point lookup over many points (the vertices of a plan) without comparing against all of them: points are bucketed in square cells of `cell` units. */
export function pointIndex(points: Pt[], cell: number): (at: Pt, tol: number) => Pt | null {
  const grid = new Map<string, Pt[]>();
  const key = (cx: number, cy: number) => `${cx},${cy}`;
  points.forEach((p) => { const k = key(Math.floor(p[0] / cell), Math.floor(p[1] / cell)); (grid.get(k) ?? grid.set(k, []).get(k)!).push(p); });
  return (at, tol) => {
    const r = Math.ceil(tol / cell);
    const cx = Math.floor(at[0] / cell), cy = Math.floor(at[1] / cell);
    let best: Pt | null = null, gap = tol;
    for (let i = -r; i <= r; i++) for (let j = -r; j <= r; j++) for (const p of grid.get(key(cx + i, cy + j)) ?? []) { const g = dist(p, at); if (g <= gap) { best = p; gap = g; } }
    return best;
  };
}

// ---------------------------------------------------------------- the same group on another level
export interface Frame { origin: Pt; k: number }

/** A clip drawn on one sheet, as it must be put on another that has its own origin and scale: positions go through metres. */
export function convertClip(clip: Clip, from: Frame, to: Frame): Clip {
  const conv = (p: Pt): Pt => fromMetres(toMetres(p, from.origin, from.k), to.origin, to.k);
  return { nodes: clip.nodes.map((n) => { const q = conv([n.x, n.y]); return { ...n, x: q[0], y: q[1] }; }), lines: clip.lines.map((l) => ({ ...l, points: l.points.map(conv) })) };
}

export interface LinkTarget { drawing: Drawing; k: number | null }

/** Shafts (and any node) that say they continue on another level with `enlace` = `L1:n3`: the twin must exist, sit at the same place (within `tolM`) and point back. */
export function linkProblems(d: Drawing, base: string, k: number | null, resolve: (level: string) => LinkTarget | undefined, tolM = 0.3): Problem[] {
  const out: Problem[] = [];
  d.nodes.forEach((n) => {
    const m = typeof n.attrs?.enlace === "string" ? /^(L-?\d+):(.+)$/.exec(n.attrs.enlace.trim()) : null;
    if (!m) return;
    const target = resolve(m[1]), twin = target?.drawing.nodes.find((x) => x.id === m[2]);
    const at: Pt = [n.x, n.y], here = ref("node", n.id);
    if (!target || !twin) { out.push({ code: "link_missing", severity: "warn", ref: here, at, tag: n.attrs!.enlace as string }); return; }
    if (k && target.k && dist(toMetres(at, d.origin, k), toMetres([twin.x, twin.y], target.drawing.origin, target.k)) > tolM) out.push({ code: "link_far", severity: "warn", ref: here, at, tag: n.attrs!.enlace as string });
    if ((typeof twin.attrs?.enlace === "string" ? twin.attrs.enlace.trim() : "") !== `${base}:${n.id}`) out.push({ code: "link_oneway", severity: "warn", ref: here, at, tag: n.attrs!.enlace as string });
  });
  return out;
}

// ---------------------------------------------------------------- walls recognized in the plan
export interface ArchWall { id: string; a: Pt; b: Pt; thickness: number; confidence: number }
export interface ArchOpening { id: string; kind: "door" | "window" | "opening"; at: Pt; width: number; angle: number; wall: string; confidence: number; reason: string; hinge?: Pt; swing?: Pt }
export interface Architecture {
  source: string; size: [number, number]; units_per_metre: number | null; wall_thickness: number | null; walls: ArchWall[]; openings: ArchOpening[]; warnings: string[];
  scale_hint: { units_per_metre: number; basis: string; confidence: number } | null; counts: { walls: number; doors: number; windows: number; openings: number };
}

/** The faces of a wall as two segments, at half its thickness either side of its centre line. */
export function wallFaces(w: ArchWall): [Pt, Pt][] {
  const dx = w.b[0] - w.a[0], dy = w.b[1] - w.a[1], n = Math.hypot(dx, dy) || 1;
  const ox = (-dy / n) * (w.thickness / 2), oy = (dx / n) * (w.thickness / 2);
  return [[[w.a[0] + ox, w.a[1] + oy], [w.b[0] + ox, w.b[1] + oy]], [[w.a[0] - ox, w.a[1] - oy], [w.b[0] - ox, w.b[1] - oy]]];
}

/** The point of a face of a wall (or its corner) nearest to `at` within `tol`, so that a cable can run along the wall. Corners win over the middle of a face. */
export function wallSnap(walls: ArchWall[], at: Pt, tol: number): Pt | null {
  let best: { p: Pt; gap: number } | null = null;
  const consider = (p: Pt, gap: number) => { if (gap <= tol && (!best || gap < best.gap)) best = { p, gap }; };
  for (const w of walls) {
    for (const [a, b] of wallFaces(w)) {
      const dx = b[0] - a[0], dy = b[1] - a[1], n = dx * dx + dy * dy;
      const t = n === 0 ? 0 : Math.max(0, Math.min(1, ((at[0] - a[0]) * dx + (at[1] - a[1]) * dy) / n));
      const p: Pt = [a[0] + t * dx, a[1] + t * dy];
      consider(a, dist(a, at));                                                   // the corners of the face are preferred a little to its middle
      consider(b, dist(b, at));
      consider(p, dist(p, at) + tol * 0.25);
    }
  }
  return best ? (best as { p: Pt }).p : null;
}

/** While drawing a line: the next point is moved so that the segment runs parallel to a wall near it, when it was nearly so (within `maxDeg`). */
export function parallelToWall(prev: Pt, p: Pt, walls: ArchWall[], reach: number, maxDeg = 8): Pt {
  const dx = p[0] - prev[0], dy = p[1] - prev[1], len = Math.hypot(dx, dy);
  if (len < 1e-9) return p;
  const here = (Math.atan2(dy, dx) * 180) / Math.PI;
  for (const w of walls) {
    if (segmentDistance(p, w.a, w.b) > reach) continue;
    const wa = (Math.atan2(w.b[1] - w.a[1], w.b[0] - w.a[0]) * 180) / Math.PI;
    const d = Math.abs(here - wa) % 180, diff = Math.min(d, 180 - d);
    if (diff > maxDeg) continue;
    const ux = Math.cos((wa * Math.PI) / 180), uy = Math.sin((wa * Math.PI) / 180), s = dx * ux + dy * uy;
    return [prev[0] + ux * s, prev[1] + uy * s];
  }
  return p;
}

// ---------------------------------------------------------------- rooms and the automatic design
export interface ProposalCircuit { tag: string; family: string; room: string; room_name: string; loads: string[]; outlets: number; from: string; to: string; via: string[]; ternas: number; va: number; va_per_outlet: number; description: string }
export interface RunLine { kind: string; points: Pt[]; role: "trunk" | "stub" }
export interface RunStats { orientation: string; trunks: number; stubs: number; bends: number; trunk_length: number; stub_length: number; in_metres: boolean }
/** Step 1 of the design: the straight trays and conduits proposed for the loads (shown on the plan until accepted). */
export interface RunsProposal { orientation: string; lines: RunLine[]; stats: RunStats | Record<string, never>; warnings: string[] }
export interface Limits { prefix: string; max_outlets: number; va_per_outlet: number; label: { es: string; en: string } }
/** Step 2: the circuits by room over the runs already drawn, and whether the engine reaches every load of each one. */
export interface Proposal { board: string; circuits: ProposalCircuit[]; assignments: Record<string, string>; unassigned: string[]; warnings: string[]; limits: Record<string, Limits>; routes: Record<string, { found: boolean; unreached?: string[] }> }

export const insidePolygon = (p: Pt, poly: Pt[]): boolean => {
  let hit = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (yi > p[1] !== yj > p[1] && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};

export const centroidOf = (pts: Pt[]): Pt => [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length];

/** The four corners of the box with opposite corners a and b (null when it has no width or no height). */
export function rectCorners(a: Pt, b: Pt): Pt[] | null {
  if (Math.abs(a[0] - b[0]) < 1e-6 || Math.abs(a[1] - b[1]) < 1e-6) return null;
  return [a, [b[0], a[1]], b, [a[0], b[1]]];
}
/** The closed outline of that box as a path that ends on b (so the preview adds no stray line to the pointer). */
export function rectOutline(a: Pt, b: Pt): Pt[] {
  const c = rectCorners(a, b);
  return c ? [b, c[3], a, c[1], b] : [a, b];
}

export function addRoom(d: Drawing, name: string, points: Pt[]): Drawing {
  if (points.length < 3) return d;
  const rooms = d.rooms ?? [];
  let n = rooms.length + 1;
  while (rooms.some((r) => r.id === `r${n}`)) n++;
  return { ...d, rooms: [...rooms, { id: `r${n}`, name, points }] };
}
export const removeRoom = (d: Drawing, id: string): Drawing => ({ ...d, rooms: (d.rooms ?? []).filter((r) => r.id !== id) });
export const renameRoom = (d: Drawing, id: string, name: string): Drawing => ({ ...d, rooms: (d.rooms ?? []).map((r) => (r.id === id ? { ...r, name } : r)) });

/** How many loads of each kind lie in each room (the smallest room that holds them), and those in none. */
export function loadsByRoom(d: Drawing, loadKinds: Set<string>): { rooms: Record<string, Record<string, number>>; outside: number } {
  const rooms: Record<string, Record<string, number>> = {};
  let outside = 0;
  const area = (poly: Pt[]) => Math.abs(poly.reduce((s, p, i) => s + p[0] * poly[(i + 1) % poly.length][1] - poly[(i + 1) % poly.length][0] * p[1], 0)) / 2;
  const sorted = [...(d.rooms ?? [])].sort((a, b) => area(a.points) - area(b.points));
  d.nodes.filter((n) => loadKinds.has(n.kind)).forEach((n) => {
    const r = sorted.find((x) => x.points.length >= 3 && insidePolygon([n.x, n.y], x.points));
    if (!r) { outside++; return; }
    (rooms[r.id] ??= {})[n.kind] = (rooms[r.id][n.kind] ?? 0) + 1;
  });
  return { rooms, outside };
}

/** The drawing with the accepted runs: a tray (BN) per trunk and a conduit (CN) per stub. */
export function applyRuns(d: Drawing, p: RunsProposal): Drawing {
  let cur = d;
  for (const ln of p.lines) cur = { ...cur, lines: [...cur.lines, { id: nextId(cur, "l"), kind: ln.kind, points: ln.points }] };
  return cur;
}

/** The drawing with the accepted wiring: the circuits (origin, destination) and the circuit of every load. A circuit the drawing already routes is left as it is; the cable follows the runs. */
export function applyProposal(d: Drawing, p: Proposal): Drawing {
  const cur = d;
  const nodes = cur.nodes.map((n) => (p.assignments[n.id] ? { ...n, circuit: p.assignments[n.id] } : n));
  const have = new Set(cur.circuits.map((c) => c.tag));
  const circuits = [...cur.circuits, ...p.circuits.filter((c) => !have.has(c.tag)).map((c) => ({ tag: c.tag, from: c.from, to: c.to, via: c.via, ternas: c.ternas }))];
  return { ...cur, nodes, circuits };
}

// ---------------------------------------------------------------- boards: the board symbol and the loads belong to a board made in Engineering
export interface BoardRef { id: string; name: string; level?: string; location?: string }          // a board of the project and, when it was said, the level and the place it is in
/** What to do when something is placed: nothing; there is no board to stand for (make it in Engineering first); take this one; or ask which of these. */
export type BoardPlan = { action: "none" } | { action: "missing" } | { action: "set"; board: BoardRef } | { action: "ask"; options: BoardRef[] };

const boardsOn = (d: Drawing, boards: BoardRef[], isBoard: (kind: string) => boolean): BoardRef[] => {
  const ids = new Set(d.nodes.filter((n) => isBoard(n.kind) && n.board).map((n) => n.board));
  return boards.filter((b) => ids.has(b.id));
};

const choose = (options: BoardRef[]): BoardPlan => (options.length === 1 ? { action: "set", board: options[0] } : { action: "ask", options });

/** A board symbol stands for a board of the project that is not on the plan yet; a load is fed from the board on the plan (asking when there are two or more). */
export function boardPlan(d: Drawing, boards: BoardRef[], kind: string, isBoard: (kind: string) => boolean, isLoad: (kind: string) => boolean): BoardPlan {
  if (isBoard(kind)) {
    const placed = new Set(boardsOn(d, boards, isBoard).map((b) => b.id));
    const free = boards.filter((b) => !placed.has(b.id));
    return free.length ? { action: "ask", options: free } : { action: "missing" };               // a board symbol always asks which board it is: the list says where each one is
  }
  if (!isLoad(kind)) return { action: "none" };
  const on = boardsOn(d, boards, isBoard);
  return on.length ? choose(on) : { action: "none" };
}

/** The node tied to a board; a board symbol also takes the name of its board as its tag. */
export const withBoard = (d: Drawing, nodeId: string, board: BoardRef, asSymbol: boolean): Drawing => ({
  ...d, nodes: d.nodes.map((n) => (n.id === nodeId ? { ...n, board: board.id, ...(asSymbol ? { tag: board.name } : {}) } : n)),
});

// ---------------------------------------------------------------- plans: a discipline can have several on a level (lighting and sockets of the electrical one)
/** What a sheet is called in the tabs: its discipline and, when it has one, the name of its plan. */
export const planLabel = (discipline: string, planName?: string): string => (planName ? `${discipline} · ${planName}` : discipline);

/** The part of a sheet's key that names its plan: lowercase letters, digits and hyphens, as the backend asks. */
export function planSlug(name: string): string {
  const s = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 24).replace(/-+$/, "");
  return s || "plano";
}

/** The key of a new sheet of a discipline on a level: the plain one (`L0@hvac`) while it has no sheet there, then one per plan (`L0@hvac.tomas`), made unique. */
export function newSheetKey(base: string, discipline: string, keys: string[], planName: string, hasSheet: boolean): string {
  const plain = `${base}@${discipline}`;
  if (!hasSheet && !keys.includes(plain)) return plain;
  const slug = planSlug(planName);
  let key = `${plain}.${slug}`, n = 2;
  while (keys.includes(key)) key = `${plain}.${slug.slice(0, 21)}-${n++}`;               // up to 24 characters, as the backend asks
  return key;
}

/** The kinds a plan offers: those of its subdiscipline, or every kind of the discipline when it has none (or an old plan names one the profile no longer has). */
export function allowedKinds(subs: { id: string; kinds: string[] }[] | undefined, chosen: string | undefined): string[] | undefined {
  return (subs ?? []).find((x) => x.id === chosen)?.kinds;
}
