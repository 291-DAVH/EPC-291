import { addNode, DNode, Drawing, Pt, Room } from "./planEditing";

/** The lighting of the rooms of a sheet: what the person says about each room, the request to the calculation, and what comes back reduced to what the panel and the plan show.
 *  The calculation is the backend's (`epc_lighting`); nothing here computes light. */
export interface RoomLighting {
  activity?: string; luminaire?: string; method?: "lumen" | "zonal"; height_m?: number; target_lux?: number; coefficient_of_utilisation?: number;
  norm_rule?: string;                                                                     // the id of a rule of a norm, approved in the norms review, that gives the target
  emergency_luminaire?: string; ugr_calculated?: number;                                  // antipanic emergency lighting of the room, and the UGR it was given from outside
  exterior?: boolean; beam_utilisation?: number; enclosure?: "open" | "closed";        // an exterior area: floodlights from its area and its target
}
export interface LightActivity { id: string; label: string; em_lux: number; ugr_l: number | null; ra: number | null; source: string }
export interface LightLuminaire { id: string; name: string; kind: "interior" | "exterior"; lamps: number; lamp_flux_lm: number; power_w: number | null; illustrative: boolean; level: string }
export interface NormRule { id: string; norm: string; clause: string; summary: string; value: number; status: "pending" | "approved" | "rejected" | "stale" }
export interface LightingOptions { norm_rules?: NormRule[]; activities: LightActivity[]; materials: { id: string; label: string; range: [number, number] }[]; systems: { id: string; label: string }[]; methods: string[]; luminaires: LightLuminaire[] }

export interface Estimate { value: number; reason: string; confidence: number }
export interface SpacingAxis { checked: boolean; status?: "ok" | "within_tolerance" | "exceeds"; spacing_m?: number; max_spacing_m?: number }
export interface UgrResult { result: "not_verifiable" | "meets" | "does_not_meet"; limit: number | null; calculated: number | null }
export interface RoomResult {
  id: string; name: string; method: string; ugr?: UgrResult;
  target: Estimate & { activity?: string; norm_rule?: string; norm?: string; clause?: string };
  factors: { cu: Estimate; maintenance: Estimate };
  reflectances: { ceiling: Estimate; walls: Estimate; floor: Estimate };
  layout: { installed: number; required: number; rows_across_width: number; columns_along_length: number; spacing_check: { along_length: SpacingAxis; across_width: SpacingAxis } };
  verification: { average_lux: number; target_lux: number; complies: boolean; margin_pct: number };
  points: { computed: boolean; min_over_avg?: number; avg_lux?: number };
  energy: { installed_power_w: number | null; power_density_w_m2: number | null };
}
/** The study kept with a sheet: what the last calculation applied to the plan gave, and whether the rooms and luminaires are still the ones it was made for. */
export interface LightingStudy {
  exists: boolean; stale?: boolean; report?: boolean; saved_at?: string; saved_by?: string;
  result?: LightingProposal["result"]; skipped?: LightingProposal["skipped"]; warnings?: string[];
}
export interface EmergencyResult {
  id: string; name: string; layout: { installed: number; columns_along_length: number; rows_across_width: number };
  criteria: { min_lux: Estimate; max_over_min: Estimate }; verification: { complies: boolean; min_lux?: number; max_over_min?: number }; routes: { id: string; complies: boolean }[];
  energy: { installed_power_w: number | null };
}
export interface AreaResult {
  id: string; name: string; area_m2: number; target: Estimate; factors: { beam_utilisation: Estimate; maintenance: Estimate }; flux: { luminaires_required: number };
  verification: { average_lux: number; target_lux: number; complies: boolean; margin_pct: number }; energy: { installed_power_w: number | null };
}
/** The illuminance of the cells of a room, row by row from its corner (view units), `null` where a cell is outside the outline. */
export interface LightMap { x0: number; y0: number; dx: number; dy: number; nx: number; ny: number; values: (number | null)[]; min: number; max: number }
export interface Placement { tag: string; x: number; y: number; z_m: number }
export interface LightingProposal {
  emergency_placements?: Record<string, Placement[]>;
  result: { rooms: RoomResult[]; areas?: AreaResult[]; emergency?: EmergencyResult[]; warnings: string[]; counts: { rooms: number; luminaires: number } } | null;
  maps?: Record<string, LightMap>;
  placements: Record<string, Placement[]>;
  rooms: { id: string; name: string; length_m: number; width_m: number; exact: boolean; corner: Pt }[];
  skipped: { id: string; name: string; reason: string }[];
  warnings: string[];
  fingerprint: string;
}

const KEYS: (keyof RoomLighting)[] = ["activity", "luminaire", "method", "height_m", "target_lux", "coefficient_of_utilisation", "exterior", "beam_utilisation", "enclosure", "emergency_luminaire", "ugr_calculated", "norm_rule"];

/** The drawing with a change to what a room says about its lighting; a value that is empty is taken out, and a room with nothing left has no `lighting` at all. */
export function setRoomLighting(d: Drawing, roomId: string, patch: Partial<Record<keyof RoomLighting, unknown>>): Drawing {
  return {
    ...d,
    rooms: (d.rooms ?? []).map((r: Room) => {
      if (r.id !== roomId) return r;
      const next: Record<string, unknown> = { ...(r.lighting ?? {}) };
      for (const [k, v] of Object.entries(patch)) {
        if (v === undefined || v === null || v === "" || v === false || (typeof v === "number" && !Number.isFinite(v))) delete next[k]; else next[k] = v;
      }
      const { lighting: _old, ...rest } = r;
      return Object.keys(next).length ? { ...rest, lighting: next as RoomLighting } : rest;
    }),
  };
}

/** A room can be calculated when it has a luminaire and either an activity or a target; an exterior area needs its target (there is no table of typical ones). */
export const isReady = (l: RoomLighting | undefined): boolean => !!l?.luminaire && (l.exterior ? !!l.target_lux : !!(l.activity || l.target_lux || l.norm_rule));

/** Number typed in a field: a decimal comma is allowed; anything that is not a positive number is nothing. */
export function parsePositive(text: string): number | undefined {
  const n = parseFloat(text.replace(",", "."));
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

/** The request of the calculation for the rooms of a sheet: their outlines and what each says about its lighting (only the rooms that say something). */
export function requestOf(d: Drawing, lang: "es" | "en", options: { compute_points?: boolean; point_step_m?: number; map?: boolean } = {}) {
  const rooms = d.rooms ?? [];
  return {
    sheet: { scale: d.scale, rooms: rooms.map((r) => ({ id: r.id, name: r.name, points: r.points })) },
    rooms: Object.fromEntries(rooms.filter((r) => r.lighting).map((r) => [r.id, pick(r.lighting!)])),
    options,
    lang,
  };
}

const pick = (l: RoomLighting): Record<string, unknown> => Object.fromEntries(KEYS.filter((k) => l[k] !== undefined && l[k] !== "").map((k) => [k, l[k]]));

export type SpacingState = "ok" | "tolerance" | "over" | "na";
export interface Card {
  id: string; name: string; installed: number; required: number; average: number; target: number; complies: boolean; margin: number;
  spacing: SpacingState; uniformity: number | null; power_w: number | null; density: number | null; unsure: string[]; ugr: UgrResult["result"]; ugrLimit: number | null;
}

const SURE = 0.6;                                         // under this confidence an estimate is shown as something to confirm

/** What a card of the panel shows of the result of one room: the verdict against the target, the spacing, the uniformity, the power and what was estimated with little confidence. */
export function cardOf(r: RoomResult): Card {
  const axes = [r.layout.spacing_check.along_length, r.layout.spacing_check.across_width].filter((a) => a.checked);
  const spacing: SpacingState = !axes.length ? "na" : axes.some((a) => a.status === "exceeds") ? "over" : axes.some((a) => a.status === "within_tolerance") ? "tolerance" : "ok";
  const estimates: [string, Estimate][] = [["target", r.target], ["cu", r.factors.cu], ["maintenance", r.factors.maintenance], ["ceiling", r.reflectances.ceiling], ["walls", r.reflectances.walls], ["floor", r.reflectances.floor]];
  return {
    id: r.id, name: r.name, installed: r.layout.installed, required: r.layout.required, average: r.verification.average_lux, target: r.verification.target_lux, complies: r.verification.complies,
    margin: r.verification.margin_pct, spacing, uniformity: r.points.computed ? r.points.min_over_avg ?? null : null, power_w: r.energy.installed_power_w, density: r.energy.power_density_w_m2,
    unsure: estimates.filter(([, e]) => e.confidence < SURE).map(([k]) => k), ugr: r.ugr?.result ?? "not_verifiable", ugrLimit: r.ugr?.limit ?? null,
  };
}

/** The luminaires of every room as marks to draw over the plan. */
export interface LightMark { room: string; tag: string; at: Pt; emergency?: boolean }
export function marksOf(p: LightingProposal | null): LightMark[] {
  return p ? Object.entries(p.placements).flatMap(([room, list]) => list.map((m) => ({ room, tag: m.tag, at: [m.x, m.y] as Pt }))) : [];
}

/** The emergency luminaires of every room as marks to draw over the plan (they are not nodes of the drawing: the profile has no kind for them). */
export function emergencyMarksOf(p: LightingProposal | null): LightMark[] {
  return p ? Object.entries(p.emergency_placements ?? {}).flatMap(([room, list]) => list.map((m) => ({ room, tag: m.tag, at: [m.x, m.y] as Pt, emergency: true }))) : [];
}

/** What a card of the panel shows of the emergency lighting of a room: the luminaires, the verdict, the lowest lux and the routes that comply. */
export function emergencyCardOf(e: EmergencyResult) {
  return { id: e.id, name: e.name, installed: e.layout.installed, complies: e.verification.complies, min: e.verification.min_lux ?? null, ratio: e.verification.max_over_min ?? null,
           routesOk: e.routes.filter((r) => r.complies).length, routes: e.routes.length, unsure: ([["emin", e.criteria.min_lux], ["ratio", e.criteria.max_over_min]] as [string, Estimate][]).filter(([, x]) => x.confidence < SURE).map(([k]) => k) };
}

export const hasPlacements = (p: LightingProposal): boolean => Object.values(p.placements).some((l) => l.length > 0);

export const CALC = "calc";                               // `attrs.lighting.source` of a luminaire that the calculation placed: the one the next calculation of its room replaces

const isCalc = (n: DNode, room: string): boolean => {
  const l = (n.attrs?.lighting ?? {}) as { source?: string; room?: string };
  return n.kind === "LU" && l.source === CALC && l.room === room;
};

/** Put the luminaires of a proposal in the drawing: in each room that was calculated the ones a previous calculation placed are replaced (the ones the person drew or moved by hand are not touched), and each new
 *  one carries its room, its luminaire and its power so that the design of the circuits can use it. Tags go on from the highest `LU-` of the drawing. */
export function applyLighting(d: Drawing, p: LightingProposal): { drawing: Drawing; added: number; removed: number } {
  const rooms = Object.keys(p.placements).filter((id) => p.placements[id].length > 0);
  const results = new Map((p.result?.rooms ?? []).map((r) => [r.id, r]));
  const dropped = d.nodes.filter((n) => rooms.some((r) => isCalc(n, r)));
  let work: Drawing = { ...d, nodes: d.nodes.filter((n) => !dropped.includes(n)) };
  let tag = work.nodes.reduce((m, n) => Math.max(m, Number(/^LU-(\d+)$/.exec(n.tag ?? "")?.[1] ?? 0)), 0);
  let added = 0;
  for (const room of rooms) {
    const r = results.get(room);
    const watts = r && r.layout.installed > 0 && r.energy.installed_power_w ? r.energy.installed_power_w / r.layout.installed : undefined;
    const luminaire = (d.rooms ?? []).find((x) => x.id === room)?.lighting?.luminaire;
    for (const m of p.placements[room]) {
      work = addNode(work, "LU", [m.x, m.y]);
      const id = work.nodes[work.nodes.length - 1].id;
      const lighting = { source: CALC, room, ...(luminaire ? { luminaire } : {}), ...(watts ? { power_w: Math.round(watts * 10) / 10 } : {}), height_m: m.z_m };
      work = { ...work, nodes: work.nodes.map((n) => (n.id === id ? { ...n, tag: `LU-${String(++tag).padStart(3, "0")}`, attrs: { lighting } } : n)) };
      added++;
    }
  }
  return { drawing: work, added, removed: dropped.length };
}

/** The cells of a map to draw: each with its place and size (view units) and where its lux falls between the lowest and the highest of the room (0 to 1). */
export function cellsOf(m: LightMap): { x: number; y: number; w: number; h: number; t: number }[] {
  const span = m.max - m.min || 1;
  return m.values.flatMap((v, n) => (v === null ? [] : [{ x: m.x0 + (n % m.nx) * m.dx, y: m.y0 + Math.floor(n / m.nx) * m.dy, w: m.dx, h: m.dy, t: (v - m.min) / span }]));
}

export const mapsOf = (p: LightingProposal | null): LightMap[] => (p ? Object.values(p.maps ?? {}) : []);

/** What a card of the panel shows of an exterior area: floodlights, the verdict against the target, the power and what was estimated with little confidence. */
export function areaCardOf(a: AreaResult) {
  return { id: a.id, name: a.name, area_m2: a.area_m2, floodlights: a.flux.luminaires_required, average: a.verification.average_lux, target: a.verification.target_lux, complies: a.verification.complies,
           margin: a.verification.margin_pct, power_w: a.energy.installed_power_w, unsure: ([["target", a.target], ["beam", a.factors.beam_utilisation], ["maintenance", a.factors.maintenance]] as [string, Estimate][]).filter(([, e]) => e.confidence < SURE).map(([k]) => k) };
}
