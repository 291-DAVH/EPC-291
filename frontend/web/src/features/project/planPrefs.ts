import { useCallback, useState } from "react";

/** What each person sets for the editor and keeps between sessions: snapping, grid, what is shown, favourite kinds and their own keys. It is a per-viewer convenience (it never reaches the project),
 *  so every read and write is guarded: a browser that blocks storage simply starts from the defaults. */
export interface PlanPrefs {
  snap: boolean; mid: boolean; ortho: boolean; grid: number;           // grid in metres, 0 = off
  chain: boolean;                                                      // after Enter the next line starts where the last one ended
  color: "kind" | "circuit"; lengths: boolean; labels: boolean; coords: boolean;
  refs: boolean; ghosts: boolean; pins: boolean; minimap: boolean;
  hidden: string[];                                                    // kinds of line not shown
  isolate: boolean;                                                    // only the circuit in focus is shown at full strength
  favorites: string[];                                                 // kind ids kept at the top of the palette, as `<discipline>:<kind>`
  keys: Record<string, string>;                                        // the person's own keys for actions
}

export const DEFAULT_PREFS: PlanPrefs = {
  snap: true, mid: true, ortho: false, grid: 0, chain: true, color: "kind", lengths: false, labels: true, coords: true,
  refs: true, ghosts: true, pins: true, minimap: true, hidden: [], isolate: false, favorites: [], keys: {},
};

/** Keys of the tools; the person can change any of them. The kinds of the discipline keep their own letters (see the profile). */
export const DEFAULT_KEYS: Record<string, string> = { select: "1", box: "2", scale: "3", origin: "4", node: "5", line: "6", erase: "7", split: "8", measure: "9", route: "0", pin: "p+", pan: "h+" };

const KEY = "epc.plan.prefs.v1";

function read(): PlanPrefs {
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? { ...DEFAULT_PREFS, ...JSON.parse(raw) } : DEFAULT_PREFS;
  } catch { return DEFAULT_PREFS; }
}

export function usePlanPrefs(): [PlanPrefs, (patch: Partial<PlanPrefs>) => void] {
  const [prefs, setPrefs] = useState<PlanPrefs>(read);
  const update = useCallback((patch: Partial<PlanPrefs>) => {
    setPrefs((cur) => {
      const next = { ...cur, ...patch };
      try { window.localStorage.setItem(KEY, JSON.stringify(next)); } catch { /* storage blocked: the choice lasts until the page closes */ }
      return next;
    });
  }, []);
  return [prefs, update];
}

/** The key of an action: the person's own or the default. */
export const keyOf = (prefs: PlanPrefs, action: string): string => prefs.keys[action] ?? DEFAULT_KEYS[action] ?? "";

// ---------------------------------------------------------------- unsent drafts
const draftKey = (project: string, sheet: string) => `epc.plan.draft.${project}.${sheet}`;

export function saveDraft(project: string, sheet: string, value: unknown): void {
  try { window.localStorage.setItem(draftKey(project, sheet), JSON.stringify({ at: new Date().toISOString(), value })); } catch { /* not kept */ }
}

export function loadDraft<T>(project: string, sheet: string): { at: string; value: T } | null {
  try {
    const raw = window.localStorage.getItem(draftKey(project, sheet));
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

export function clearDraft(project: string, sheet: string): void {
  try { window.localStorage.removeItem(draftKey(project, sheet)); } catch { /* nothing to clear */ }
}
