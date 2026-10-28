import type { Drawing } from "./planEditing";

/** What the plan editor needs of the sizing of the automatic design: the cable of each circuit and the conduit or tray that carries the cables of each stretch (see `layout/service.design_sizing`). */
export interface SizedBox { line: string; tag: string; kind: string; circuits: string[]; cables: number; size: Record<string, number>; used_pct: number; limit_pct: number; cable_mm: number[]; fits: boolean }
export interface SizedCircuit { tag: string; section_mm2?: number | null; in_a?: number | null; ib_a?: number | null; du_pct?: number | null; complies?: boolean | null; length_m?: number | null; plenums: string[]; rise_m: number; found: boolean }
export interface Sizing { containers: SizedBox[]; circuits: SizedCircuit[]; warnings: string[] }

/** `Ø32` for a conduit, `200×50` for a tray (mm). */
export const sizeLabel = (size: Record<string, number>): string => (size.diametro_mm ? `Ø${size.diametro_mm}` : `${size.ancho_mm}×${size.alto_mm}`);

const mean = (xs: number[]): number => xs.reduce((s, x) => s + x, 0) / xs.length;

/** The drawing with the sizes approved: each conduit its internal diameter, each tray its width and height, and the cable diameter the fill was computed with (so the plan shows the same fill). */
export function applySizing(d: Drawing, s: Sizing): Drawing {
  const by = new Map(s.containers.filter((c) => c.line).map((c) => [c.line, c]));
  return { ...d, lines: d.lines.map((ln) => { const c = by.get(ln.id); return c ? { ...ln, attrs: { ...(ln.attrs ?? {}), ...c.size, diametro_cable_mm: Math.round(mean(c.cable_mm) * 10) / 10 } } : ln; }) };
}

/** The circuits whose cable did not comply or whose route the engine did not find, and the stretches nothing holds: what the person has to look at before approving. */
export const attention = (s: Sizing): { circuits: string[]; containers: string[] } => ({
  circuits: s.circuits.filter((c) => !c.found || c.complies === false || !c.section_mm2).map((c) => c.tag),
  containers: s.containers.filter((c) => !c.fits).map((c) => c.tag),
});
