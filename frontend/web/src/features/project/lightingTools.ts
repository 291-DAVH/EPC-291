import type { Drawing, Pt } from "./planEditing";
import type { LightActivity, LightMap, RoomLighting } from "./lightingApi";

/** What the person set for the lighting panel of a sheet: the limit of power density and the tariff they want checked, the hours of use, whether to choose a luminaire for the rooms that have none, whether to draw
 *  the illuminance map, and the templates of room parameters they saved. Kept with the sheet. */
export interface LightSettings {
  power_limit_w_m2?: number; kwh_price?: number; hours_default?: number; auto_luminaire?: boolean; map?: boolean; templates?: Record<string, RoomLighting>;
}

const NUMBERS = ["power_limit_w_m2", "kwh_price", "hours_default"] as const;

export const settingsOf = (d: Drawing): LightSettings => d.lighting_settings ?? {};

/** The drawing with a setting changed; an empty, false or not-a-number value takes the setting out. */
export function setSetting(d: Drawing, key: keyof LightSettings, value: unknown): Drawing {
  const next: Record<string, unknown> = { ...(d.lighting_settings ?? {}) };
  const empty = value === undefined || value === null || value === "" || value === false || (typeof value === "number" && !Number.isFinite(value));
  if (empty) delete next[key]; else next[key] = value;
  const { lighting_settings: _old, ...rest } = d;
  return Object.keys(next).length ? { ...rest, lighting_settings: next as LightSettings } : rest;
}

/** The settings that go to the calculation as options. */
export function settingsOptions(s: LightSettings | undefined): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const k of NUMBERS) if (typeof s?.[k] === "number") out[k] = s[k];
  if (s?.auto_luminaire) out.auto_luminaire = true;
  return out;
}

const withLighting = (d: Drawing, id: string, lighting: RoomLighting | undefined): Drawing => ({
  ...d,
  rooms: (d.rooms ?? []).map((r) => {
    if (r.id !== id) return r;
    const { lighting: _old, ...rest } = r;
    return lighting && Object.keys(lighting).length ? { ...rest, lighting: { ...lighting } } : rest;
  }),
});

/** What a room says about its lighting, put in other rooms too (replacing what they said). */
export function copyLighting(d: Drawing, from: string, to: string[]): { drawing: Drawing; copied: number } {
  const source = (d.rooms ?? []).find((r) => r.id === from)?.lighting;
  const targets = to.filter((id) => id !== from && (d.rooms ?? []).some((r) => r.id === id));
  if (!source) return { drawing: d, copied: 0 };
  return { drawing: targets.reduce((acc, id) => withLighting(acc, id, source), d), copied: targets.length };
}

/** A room's parameters saved under a name, to use in other rooms of the sheet (the same name replaces the template). */
export function saveTemplate(d: Drawing, name: string, from: string): Drawing {
  const source = (d.rooms ?? []).find((r) => r.id === from)?.lighting;
  const clean = name.trim();
  if (!source || !clean) return d;
  return setSetting(d, "templates", { ...(d.lighting_settings?.templates ?? {}), [clean]: { ...source } });
}

export function applyTemplate(d: Drawing, id: string, name: string): Drawing {
  const template = d.lighting_settings?.templates?.[name];
  return template ? withLighting(d, id, template) : d;
}

export function removeTemplate(d: Drawing, name: string): Drawing {
  const { [name]: _gone, ...rest } = d.lighting_settings?.templates ?? {};
  return setSetting(d, "templates", Object.keys(rest).length ? rest : undefined);
}

const HINTS: [RegExp, string][] = [
  [/noct|evening|adult/i, "education.evening_classroom"],
  [/biblio|lectura|reading|library/i, "education.reading_room"],
  [/aula|clase|classroom|escuela|school/i, "education.classroom"],
  [/pasillo|corredor|circulaci|hall|escalera|corridor|stair|lobby/i, "circulation.indoor"],
  [/dep[oó]sito|almac|bodega|storage|warehouse/i, "room.storage"],
  [/estar|living|sala|comedor|dormitorio|bedroom/i, "room.living"],
  [/dibujo|dise[nñ]o|drawing/i, "task.drawing"],
  [/oficina|office|administr|escritorio/i, "task.reading"],
  [/taller|workshop/i, "task.fine"],
];

/** The activity a room's name points to ("Aula 3" is a classroom), when the engine has it; the first word that matches wins. */
export function suggestActivity(name: string, activities: Pick<LightActivity, "id">[]): string | undefined {
  const hit = HINTS.find(([re]) => re.test(name))?.[1];
  return hit && activities.some((a) => a.id === hit) ? hit : undefined;
}

type Segment = [Pt, Pt];

/** The line where a map crosses a level of lux: marching squares over the lattice of cell centres. A square with a cell outside the outline (no value) gives no line. */
export function contoursOf(m: LightMap, level: number): Segment[] {
  const v = (i: number, j: number) => m.values[j * m.nx + i];
  const cx = (i: number) => m.x0 + (i + 0.5) * m.dx;
  const cy = (j: number) => m.y0 + (j + 0.5) * m.dy;
  const out: Segment[] = [];
  for (let j = 0; j < m.ny - 1; j++) {
    for (let i = 0; i < m.nx - 1; i++) {
      const [a, b, c, d] = [v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)];                // top-left, top-right, bottom-right, bottom-left
      if ([a, b, c, d].some((x) => x === null || x === undefined)) continue;
      const [A, B, C, D] = [a as number, b as number, c as number, d as number];
      const at = (p: number, q: number, p0: number, p1: number): number => (q === p ? p0 : p0 + ((level - p) / (q - p)) * (p1 - p0));
      const edge = {
        top: [at(A, B, cx(i), cx(i + 1)), cy(j)] as Pt, right: [cx(i + 1), at(B, C, cy(j), cy(j + 1))] as Pt,
        bottom: [at(D, C, cx(i), cx(i + 1)), cy(j + 1)] as Pt, left: [cx(i), at(A, D, cy(j), cy(j + 1))] as Pt,
      };
      const idx = (A >= level ? 8 : 0) | (B >= level ? 4 : 0) | (C >= level ? 2 : 0) | (D >= level ? 1 : 0);
      for (const [p, q] of CASES[idx] ?? []) out.push([edge[p], edge[q]]);
    }
  }
  return out;
}

type Edge = "top" | "right" | "bottom" | "left";
const CASES: Record<number, [Edge, Edge][]> = {
  1: [["left", "bottom"]], 2: [["bottom", "right"]], 3: [["left", "right"]], 4: [["top", "right"]], 5: [["left", "bottom"], ["top", "right"]], 6: [["top", "bottom"]], 7: [["left", "top"]],
  8: [["left", "top"]], 9: [["top", "bottom"]], 10: [["left", "top"], ["bottom", "right"]], 11: [["top", "right"]], 12: [["left", "right"]], 13: [["bottom", "right"]], 14: [["left", "bottom"]],
};

/** Round levels of lux between the lowest and the highest of a map, about `count` of them (steps of 1, 2, 2.5 or 5 times a power of ten). */
export function levelsOf(min: number, max: number, count = 5): number[] {
  if (!(max > min)) return [];
  const raw = (max - min) / count;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((k) => k * pow).find((s) => s >= raw) ?? 10 * pow;
  const first = Math.ceil(min / step) * step;
  const levels: number[] = [];
  for (let x = first; x < max; x += step) levels.push(Math.round(x * 1000) / 1000);
  return levels.filter((x) => x > min);
}

const LABEL_GAP_PX = 30;                                 // the least distance on the screen between two numbers of a map: they must not crowd the plan

/** The lux to write over a map, one every few cells so that two numbers are never closer than `LABEL_GAP_PX` on the screen (`u` is how many units of the plan a pixel is). Cells with no value (outside the outline) have none. */
export function valueLabels(m: LightMap, u: number): { x: number; y: number; text: string }[] {
  const stride = Math.max(1, Math.ceil((LABEL_GAP_PX * u) / Math.max(Math.min(m.dx, m.dy), 1e-9)));
  const out: { x: number; y: number; text: string }[] = [];
  const first = (n: number) => Math.min(Math.floor(stride / 2), Math.floor((n - 1) / 2));                  // a map zoomed out far still has one number, in its middle
  for (let j = first(m.ny); j < m.ny; j += stride) {
    for (let i = first(m.nx); i < m.nx; i += stride) {
      const v = m.values[j * m.nx + i];
      if (v !== null && v !== undefined) out.push({ x: m.x0 + (i + 0.5) * m.dx, y: m.y0 + (j + 0.5) * m.dy, text: String(Math.round(v)) });
    }
  }
  return out;
}
