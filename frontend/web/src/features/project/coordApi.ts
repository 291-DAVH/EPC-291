import { useCallback, useEffect, useState } from "react";
import { api } from "@epc/ui";
import type { Pt } from "./planEditing";
import type { Pin, RefItem } from "./planTypes";

/** What the web reads from the coordination API (see backend `coordination`): footprints of other disciplines, clashes, threads and what a discipline should look at. */
export interface ClashRef { sheet: string; discipline: string; level: string; id: string; tag: string; kind: string; shape: string }
export interface Clash { id: string; type: "hard" | "clearance" | "maintenance"; severity: "error" | "warning"; gap_m: number; clearance_m: number; point_m: Pt; level: string; level_number: number; a: ClashRef; b: ClashRef; status: "open" | "accepted"; reason: string; by?: string; at?: string }
export interface ClashResult { clashes: Clash[]; sources: Record<string, "issued" | "working">; counts: { total: number; open: number; accepted: number; hard: number } }
export interface ThreadEvent { at: string; by: string; status: string; comment: string }
export interface Thread { id: string; kind: "comment" | "request" | "opening" | "reservation"; from_discipline: string; to_discipline: string; title: string; text: string; status: string; sheet: string; level: string; point_m: Pt | null; geom: Record<string, unknown> | null; created_at: string; created_by: string; history: ThreadEvent[] }
export interface Exchange { id: string; owner: string; consumers: string[]; tag: string; field: string; value: unknown; unit: string; version: number; states: Record<string, "delivered" | "pending" | "outdated">; updated_at: string; updated_by: string }
export interface MatrixCell { owner: string; consumer: string; delivered: number; pending: number; outdated: number; total: number }
export interface Emission { discipline: string; rev: number; at: string; by: string; note: string; sheets: string[]; elements: number; issues: number }
export interface CoordOverview { disciplines: string[]; drawn: string[]; emissions: Emission[]; members: Record<string, string[]>; counts: { total: number; open: number; accepted: number; hard: number; threads: number }; sources: Record<string, string>; settings: { story_height_m: number }; matrix: MatrixCell[] }
export interface Notifications { discipline: string; open_clashes: number; new_clashes: Clash[]; requests: Thread[]; data: Exchange[]; count: number }
export interface Rule { a?: string; b?: string; kinds_a?: string[]; kinds_b?: string[]; clearance_m?: number; ignore?: boolean; disabled?: boolean; why?: string }
export interface RulesView { default: Rule[]; inherited: Rule[]; own: Rule[]; effective: Rule[] }

export const base = (client: string, code: string) => `/projects/${client}/${code}/coordination`;
export const levelOf = (sheet: string) => sheet.split("@")[0];

/** What the editor needs about the other disciplines on a sheet: their footprints, the clashes and threads of its level, and the number of things for its discipline to look at. */
export function useCoordination(client: string, code: string, sheet: string, discipline: string) {
  const [reference, setReference] = useState<RefItem[]>([]);
  const [clashes, setClashes] = useState<Clash[]>([]);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [count, setCount] = useState(0);
  const [rev, setRev] = useState(0);
  const level = levelOf(sheet);
  const reload = useCallback(() => setRev((n) => n + 1), []);
  useEffect(() => {
    if (!sheet || !discipline) { setReference([]); setClashes([]); setThreads([]); setCount(0); return; }
    let live = true;
    const b = base(client, code);
    api<{ items: RefItem[] }>(`${b}/reference?discipline=${encodeURIComponent(discipline)}&level=${encodeURIComponent(level)}`).then((r) => live && setReference(r.items)).catch(() => live && setReference([]));
    api<ClashResult>(`${b}/clashes`).then((r) => live && setClashes(r.clashes)).catch(() => live && setClashes([]));
    api<Thread[]>(`${b}/threads?level=${encodeURIComponent(level)}`).then((r) => live && setThreads(r)).catch(() => live && setThreads([]));
    api<Notifications>(`${b}/notifications?discipline=${encodeURIComponent(discipline)}`).then((r) => live && setCount(r.count)).catch(() => live && setCount(0));
    return () => { live = false; };
  }, [client, code, sheet, discipline, level, rev]);
  return { reference, clashes, threads, count, reload };
}

/** The marks the plan shows for clashes and threads of the level. A resolved or accepted one stays, quiet. */
export function pinsFor(clashes: Clash[], threads: Thread[], discipline: string, level: string, t: (k: string) => string): Pin[] {
  const out: Pin[] = clashes.filter((c) => c.level === level && (c.a.discipline === discipline || c.b.discipline === discipline))
    .map((c) => ({ id: "clash:" + c.id, kind: "clash" as const, at_m: c.point_m, tone: c.status === "accepted" ? "done" as const : c.type === "hard" ? "bad" as const : "warn" as const, label: `${t("plan.clash." + c.type)} · ${c.a.tag} ↔ ${c.b.tag}` }));
  threads.filter((x) => x.point_m && (x.level === level || !x.level)).forEach((x) => {
    const quiet = x.status === "resolved" || x.status === "released" || x.status === "rejected";
    out.push({ id: "thread:" + x.id, kind: x.kind, at_m: x.point_m!, tone: quiet ? "done" : x.kind === "comment" ? "warn" : "info", label: `${x.id} · ${x.title || x.text.slice(0, 40)}` });
  });
  return out;
}
