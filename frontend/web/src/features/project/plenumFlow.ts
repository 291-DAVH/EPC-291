/** The decisions around the board of the building and its plenum (vertical shaft): which levels have to be made for a board to sit on its level, where the plenum is asked for when a level is added, how far a
 *  plenum reaches and where to offer it. The rules are the backend's (`layout/plenums.py`); these are the questions the screens ask before they call it. */
import type { Pt } from "./planEditing";

export const ELECTRICAL = "electrica_BT";

export interface PlenumDef { code: string; discipline: string; kind?: string; level: string; x_m: number; y_m: number; altura_m: number; up: number | null; down: number | null }
export interface BoardPlace { id: string; name: string; level?: string; location?: string }

/** `L-1` is -1, `L2` is 2; NaN when it is not a level. */
export const levelNumber = (key: string): number => {
  const m = /^L(-?\d{1,2})$/.exec(key.split("@")[0]);
  return m ? Number(m[1]) : NaN;
};
export const levelKey = (n: number): string => `L${n}`;

/** Whether a plenum crosses a level: its own, and the ones within its reach up and down (null: all of them). */
export function covers(p: Pick<PlenumDef, "level" | "up" | "down">, base: string): boolean {
  const here = levelNumber(base), start = levelNumber(p.level);
  if (here === start) return true;
  const reach = here > start ? p.up : p.down;
  return reach === null || Math.abs(here - start) <= reach;
}

/** The levels to make so that `target` exists with no gap: the ground level first when there is nothing, then the ones between what exists and the target, in the order they are made. */
export function levelsToMake(existing: string[], target: string): string[] {
  const t = levelNumber(target);
  if (Number.isNaN(t)) return [];
  const have = new Set(existing.map(levelNumber).filter((n) => !Number.isNaN(n)));
  if (have.size === 0) return [...new Set([0, ...(t < 0 ? range(-1, t) : t > 0 ? range(1, t) : [])])].map(levelKey);
  const lo = Math.min(...have), hi = Math.max(...have);
  return (t > hi ? range(hi + 1, t) : t < lo ? range(lo - 1, t) : []).map(levelKey);
}

const range = (from: number, to: number): number[] => (from <= to ? Array.from({ length: to - from + 1 }, (_, i) => from + i) : Array.from({ length: from - to + 1 }, (_, i) => from - i));

/** The levels the board can be put on: the ones that exist and the ones one step beyond; with nothing made yet, from three below the ground level to three above it. */
export function levelChoices(existing: string[]): string[] {
  const have = existing.map(levelNumber).filter((n) => !Number.isNaN(n));
  if (have.length === 0) return range(-3, 3).map(levelKey);
  return range(Math.min(...have) - 1, Math.max(...have) + 1).map(levelKey).sort((a, b) => levelNumber(a) - levelNumber(b));
}

/** The level a plenum is asked for when a level is added: the one of the board when no plenum crosses it (the board is the start of the shaft). Nothing when there is no board with a level or one already does. */
export function plenumNeededAt(boards: BoardPlace[], plenums: PlenumDef[], discipline = ELECTRICAL): string | null {
  const level = boards.find((b) => b.level && !Number.isNaN(levelNumber(b.level)))?.level;
  if (!level) return null;
  return plenums.some((p) => p.discipline === discipline && covers(p, level)) ? null : level;
}

/** Where to propose the plenum: a metre to the right of the board, or the origin when the board is not drawn. Metres from the origin of the plan, y up. */
export const plenumNear = (board: Pt | null): Pt => (board ? [Math.round((board[0] + 1) * 100) / 100, Math.round(board[1] * 100) / 100] : [0, 0]);

/** The reach as the person says it: `all`, or a number of levels up and down. */
export function reachOf(all: boolean, up: string, down: string): { up: number | null; down: number | null } | null {
  if (all) return { up: null, down: null };
  if (up.trim() === "" || down.trim() === "") return null;
  const u = Number(up), d = Number(down);
  return Number.isInteger(u) && Number.isInteger(d) && u >= 0 && d >= 0 && u <= 50 && d <= 50 ? { up: u, down: d } : null;
}

/** The disciplines other than the electrical one that have a kind of vertical shaft and a drawing, and no plenum yet at the level: the ones the program asks about, since a shaft is not always needed. */
export function otherShafts(profiles: { id: string; nodes: { id: string; vertical?: boolean }[] }[], sheetDisciplines: string[], plenums: PlenumDef[], level: string): string[] {
  const drawn = new Set(sheetDisciplines);
  return profiles.filter((p) => p.id !== ELECTRICAL && drawn.has(p.id) && p.nodes.some((n) => n.vertical) && !plenums.some((x) => x.discipline === p.id && covers(x, level))).map((p) => p.id);
}
