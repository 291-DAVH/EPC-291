import type { Drawing, Pt, Room } from "./planEditing";

/** The lighting of the rooms of a sheet: what the person says about each room, the request to the calculation, and what comes back reduced to what the panel and the plan show.
 *  The calculation is the backend's (`epc_lighting`); nothing here computes light. */
export interface RoomLighting {
  activity?: string; luminaire?: string; method?: "lumen" | "zonal"; height_m?: number; target_lux?: number; coefficient_of_utilisation?: number;
}
export interface LightActivity { id: string; label: string; em_lux: number; ugr_l: number | null; ra: number | null; source: string }
export interface LightLuminaire { id: string; name: string; kind: "interior" | "exterior"; lamps: number; lamp_flux_lm: number; power_w: number | null; illustrative: boolean; level: string }
export interface LightingOptions { activities: LightActivity[]; materials: { id: string; label: string; range: [number, number] }[]; systems: { id: string; label: string }[]; methods: string[]; luminaires: LightLuminaire[] }

export interface Estimate { value: number; reason: string; confidence: number }
export interface SpacingAxis { checked: boolean; status?: "ok" | "within_tolerance" | "exceeds"; spacing_m?: number; max_spacing_m?: number }
export interface RoomResult {
  id: string; name: string; method: string;
  target: Estimate & { activity?: string };
  factors: { cu: Estimate; maintenance: Estimate };
  reflectances: { ceiling: Estimate; walls: Estimate; floor: Estimate };
  layout: { installed: number; required: number; rows_across_width: number; columns_along_length: number; spacing_check: { along_length: SpacingAxis; across_width: SpacingAxis } };
  verification: { average_lux: number; target_lux: number; complies: boolean; margin_pct: number };
  points: { computed: boolean; min_over_avg?: number; avg_lux?: number };
  energy: { installed_power_w: number | null; power_density_w_m2: number | null };
}
export interface Placement { tag: string; x: number; y: number; z_m: number }
export interface LightingProposal {
  result: { rooms: RoomResult[]; warnings: string[]; counts: { rooms: number; luminaires: number } } | null;
  placements: Record<string, Placement[]>;
  rooms: { id: string; name: string; length_m: number; width_m: number; exact: boolean; corner: Pt }[];
  skipped: { id: string; name: string; reason: string }[];
  warnings: string[];
  fingerprint: string;
}

const KEYS: (keyof RoomLighting)[] = ["activity", "luminaire", "method", "height_m", "target_lux", "coefficient_of_utilisation"];

/** The drawing with a change to what a room says about its lighting; a value that is empty is taken out, and a room with nothing left has no `lighting` at all. */
export function setRoomLighting(d: Drawing, roomId: string, patch: Partial<Record<keyof RoomLighting, unknown>>): Drawing {
  return {
    ...d,
    rooms: (d.rooms ?? []).map((r: Room) => {
      if (r.id !== roomId) return r;
      const next: Record<string, unknown> = { ...(r.lighting ?? {}) };
      for (const [k, v] of Object.entries(patch)) {
        if (v === undefined || v === null || v === "" || (typeof v === "number" && !Number.isFinite(v))) delete next[k]; else next[k] = v;
      }
      const { lighting: _old, ...rest } = r;
      return Object.keys(next).length ? { ...rest, lighting: next as RoomLighting } : rest;
    }),
  };
}

/** A room can be calculated when it has a luminaire and either an activity or a target. */
export const isReady = (l: RoomLighting | undefined): boolean => !!l?.luminaire && !!(l.activity || l.target_lux);

/** Number typed in a field: a decimal comma is allowed; anything that is not a positive number is nothing. */
export function parsePositive(text: string): number | undefined {
  const n = parseFloat(text.replace(",", "."));
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

/** The request of the calculation for the rooms of a sheet: their outlines and what each says about its lighting (only the rooms that say something). */
export function requestOf(d: Drawing, lang: "es" | "en", options: { compute_points?: boolean; point_step_m?: number } = {}) {
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
  spacing: SpacingState; uniformity: number | null; power_w: number | null; density: number | null; unsure: string[];
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
    unsure: estimates.filter(([, e]) => e.confidence < SURE).map(([k]) => k),
  };
}

/** The luminaires of every room as marks to draw over the plan. */
export function marksOf(p: LightingProposal | null): { room: string; tag: string; at: Pt }[] {
  return p ? Object.entries(p.placements).flatMap(([room, list]) => list.map((m) => ({ room, tag: m.tag, at: [m.x, m.y] as Pt }))) : [];
}
