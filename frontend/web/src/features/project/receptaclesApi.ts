import { addNode, DNode, Drawing, Pt, Room } from "./planEditing";

/** The socket outlets of the rooms of a sheet: what the person says about each room, the request to the calculation, and what comes back reduced to what the panel and the plan show.
 *  The calculation is the backend's (`epc_receptacles`); nothing here decides how many outlets a room needs. */
export interface RoomReceptacles { use?: string; receptacle?: string; count?: number; height_m?: number; norm?: "771" | "770"; wet?: boolean }
export interface RecUse { id: string; label: string; basis: "area" | "perimeter" | "fixed"; per_m2: number | null; per_m: number | null; min: number; family: string; wet: boolean; confidence: number; source: string }
export interface RecOutlet { id: string; name: string; kind: "general" | "special"; poles?: number | null; rated_a?: number | null; power_va: number | null; height_m: number | null; ip: string; illustrative: boolean; level: string }
export interface ReceptaclesOptions { uses: RecUse[]; receptacles: RecOutlet[]; norms: string[] }
export interface RecCheck { id: string; ok: boolean; message: string }
export interface RecRoomResult {
  id: string; name: string; use: string; basis: string; family: "TUG" | "TUE"; receptacle: string; area_m2: number; perimeter_m: number; required: number; installed: number; power_va_each: number; load_va: number; circuits_min: number;
  layout: { mode: "proposed" | "drawn" }; checks: RecCheck[]; estimate: { reason: string; confidence: number; source: string };
}
export interface RecPlacement { tag: string; x: number; y: number; z_m: number | null; wall: string; kind: "TG" | "TE" }
export interface ReceptaclesProposal {
  result: { rooms: RecRoomResult[]; warnings: string[]; counts: { rooms: number; outlets: number; required: number; warnings: number } } | null;
  placements: Record<string, RecPlacement[]>;
  skipped: { id: string; name: string; reason: string }[];
  warnings: string[];
}

const KEYS: (keyof RoomReceptacles)[] = ["use", "receptacle", "count", "height_m", "norm", "wet"];
export const CALC = "calc";                               // `attrs.receptacles.source` of an outlet that the calculation placed: the one the next calculation of its room replaces
const KINDS = ["TG", "TE"];

/** The drawing with a change to what a room says about its outlets; an empty value is taken out, and a room with nothing left has no `receptacles` at all. */
export function setRoomReceptacles(d: Drawing, roomId: string, patch: Partial<Record<keyof RoomReceptacles, unknown>>): Drawing {
  return {
    ...d,
    rooms: (d.rooms ?? []).map((r: Room) => {
      if (r.id !== roomId) return r;
      const next: Record<string, unknown> = { ...(r.receptacles ?? {}) };
      for (const [k, v] of Object.entries(patch)) {
        if (v === undefined || v === null || v === "" || v === false || (typeof v === "number" && !Number.isFinite(v))) delete next[k]; else next[k] = v;
      }
      const { receptacles: _old, ...rest } = r;
      return Object.keys(next).length ? { ...rest, receptacles: next as RoomReceptacles } : rest;
    }),
  };
}

/** A room can be calculated when it says what it is for. */
export const isReady = (r: RoomReceptacles | undefined): boolean => !!r?.use;

/** The request of the calculation for the rooms of a sheet: their outlines and what each says about its outlets (only the rooms that say something). */
export function requestOf(d: Drawing, lang: "es" | "en", options: { use_drawn?: boolean; norm?: "771" | "770" } = {}) {
  const rooms = d.rooms ?? [];
  const nodes = options.use_drawn ? d.nodes.filter((n) => KINDS.includes(n.kind)).map((n) => ({ id: n.id, kind: n.kind, x: n.x, y: n.y, tag: n.tag ?? "", attrs: n.attrs ?? {} })) : undefined;
  return {
    sheet: { scale: d.scale, rooms: rooms.map((r) => ({ id: r.id, name: r.name, points: r.points })), ...(nodes ? { nodes } : {}) },
    rooms: Object.fromEntries(rooms.filter((r) => r.receptacles).map((r) => [r.id, Object.fromEntries(KEYS.filter((k) => r.receptacles![k] !== undefined && r.receptacles![k] !== "").map((k) => [k, r.receptacles![k]]))])),
    options,
    lang,
  };
}

/** A proposal made by checking the plan as it is drawn: there is nothing to apply, the outlets are the ones already there. */
export const isDrawn = (p: ReceptaclesProposal): boolean => (p.result?.rooms ?? []).length > 0 && (p.result?.rooms ?? []).every((r) => r.layout.mode === "drawn");
export const hasPlacements = (p: ReceptaclesProposal): boolean => Object.values(p.placements).some((l) => l.length > 0) && !isDrawn(p);

export interface RecMark { room: string; tag: string; at: Pt }
/** The outlets of every room as marks to draw over the plan until the person decides. */
export function marksOf(p: ReceptaclesProposal | null): RecMark[] {
  return p && !isDrawn(p) ? Object.entries(p.placements).flatMap(([room, list]) => list.map((m) => ({ room, tag: m.tag, at: [m.x, m.y] as Pt }))) : [];
}

const isCalc = (n: DNode, room: string): boolean => {
  const r = (n.attrs?.receptacles ?? {}) as { source?: string; room?: string };
  return KINDS.includes(n.kind) && r.source === CALC && r.room === room;
};

/** The outlet a calculation replaced that was nearest to a new one and had a circuit: the new one takes its place in that circuit, so recalculating does not undo the circuits. */
const nearestWithCircuit = (old: DNode[], at: Pt): DNode | undefined => old.filter((n) => n.circuit).sort((a, b) => Math.hypot(a.x - at[0], a.y - at[1]) - Math.hypot(b.x - at[0], b.y - at[1]))[0];

/** Put the outlets of a proposal in the drawing: in each room that was calculated the ones a previous calculation placed are replaced (the ones the person drew or moved by hand are not touched), and each new one
 *  carries its room, its outlet and its apparent power so that the design of the circuits can use it. Tags go on from the highest of the drawing, by kind (`TG-` general use, `TE-` special use). */
export function applyReceptacles(d: Drawing, p: ReceptaclesProposal): { drawing: Drawing; added: number; removed: number } {
  let work: Drawing = d;
  let added = 0, removed = 0;
  const rooms = Object.keys(p.placements).filter((id) => p.placements[id].length > 0);
  const dropped = work.nodes.filter((n) => rooms.some((r) => isCalc(n, r)));
  work = { ...work, nodes: work.nodes.filter((n) => !dropped.includes(n)) };
  removed = dropped.length;
  const numberOf = (kind: string, tag: string | undefined): number => (tag?.startsWith(`${kind}-`) ? Number(tag.slice(kind.length + 1)) || 0 : 0);
  const last: Record<string, number> = Object.fromEntries(KINDS.map((k) => [k, work.nodes.reduce((m, n) => Math.max(m, numberOf(k, n.tag)), 0)]));
  for (const room of rooms) {
    const result = p.result?.rooms.find((r) => r.id === room);
    const replaced = dropped.filter((n) => isCalc(n, room));
    for (const m of p.placements[room]) {
      work = addNode(work, m.kind, [m.x, m.y]);
      const id = work.nodes[work.nodes.length - 1].id;
      const receptacles = { source: CALC, room, ...(result?.receptacle ? { receptacle: result.receptacle } : {}), ...(result?.power_va_each ? { power_va: result.power_va_each } : {}), ...(m.z_m ? { height_m: m.z_m } : {}) };
      const inherited = nearestWithCircuit(replaced, [m.x, m.y]);
      work = { ...work, nodes: work.nodes.map((n) => (n.id === id ? { ...n, tag: `${m.kind}-${String(++last[m.kind]).padStart(3, "0")}`, attrs: { receptacles }, ...(inherited ? { circuit: inherited.circuit, ...(inherited.board ? { board: inherited.board } : {}) } : {}) } : n)) };
      added++;
    }
  }
  return { drawing: work, added, removed };
}
