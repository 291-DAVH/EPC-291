import type { Pt } from "./planEditing";

/** What the editor shows that does not belong to the drawing being edited. All of it comes from the parent, already in the units it needs. */

/** The footprint another discipline gave to the others (metres, from the origin of the project). Only where it is and how big: never its drawing or its calculations. */
export interface RefItem { sheet: string; discipline: string; level: string; id: string; kind: string; shape: "node" | "line"; tag: string; points: Pt[]; width_m: number; z0: number; z1: number; origin?: string }

/** A mark on the plan about a place: a clash, a note, a request, an opening, a reserved space. `at_m` is in metres from the origin. */
export interface Pin { id: string; kind: "clash" | "comment" | "request" | "opening" | "reservation"; at_m: Pt; label: string; tone: "bad" | "warn" | "info" | "done" }

/** The same discipline on the level above or below, faint behind the drawing, already in the view units of this sheet. */
export interface Ghost { key: string; level: string; nodes: Pt[]; lines: Pt[][] }

export const DISCIPLINE_COLORS = ["#8e44ad", "#16a085", "#c0392b", "#2980b9", "#d35400", "#7f8c8d", "#27ae60", "#b8860b"];
/** A stable colour for each discipline (the same everywhere it appears). */
export const colorOfDiscipline = (id: string): string => {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return DISCIPLINE_COLORS[h % DISCIPLINE_COLORS.length];
};
