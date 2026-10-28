import { useRef, useState } from "react";
import { api, errorText, JSON_HEADERS } from "@epc/ui";
import type { Drawing } from "./planEditing";
import { applyProposal, applyRuns, Proposal, RunsProposal } from "./planTools";
import type { Sizing } from "./autoDesign";

/** Where the automatic design is: asking the server, showing a proposal to accept, the detail of the sizing to approve, or stopped (with the reason) / finished. */
export type AutoStage = null | { step: "busy"; what: "runs" | "wiring" | "sizing" } | { step: "runs"; proposal: RunsProposal } | { step: "wiring"; proposal: Proposal } | { step: "sizing"; sizing: Sizing }
  | { step: "stop"; why: string } | { step: "done" };

interface Ctx {
  root: string; level: string;
  families: () => Record<string, Record<string, number>>;
  board: () => { node: string; id: string };             // the board symbol on the plan the runs start from, and the board of the project it stands for (read when needed: the hook is called before the plan is known)
  commit: (d: Drawing) => Promise<void>;                 // save the drawing now
  preview: (r: RunsProposal | null) => void;             // show (or hide) the proposed runs on the plan
}

const warningsOf = (w: string[]): string => w.join(" ") || "-";

/** Once the luminaires are accepted: the route of the conduits and trays is proposed; accepted, the circuits are proposed over it; accepted, the circuits are created in the board, the cables are sized with
 *  the length the plan measured (plenums included) and the conduits and trays with the cables; the detail is shown and, approved, the sizes are written on the plan. */
export function useAutoDesign(ctx: Ctx) {
  const [stage, setStage] = useState<AutoStage>(null);
  const work = useRef<Drawing | null>(null);
  const post = <T,>(path: string, body: unknown) => api<T>(`${ctx.root}/${ctx.level}/design/${path}`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(body) });
  const asking = (d: Drawing) => ({ drawing: d, families: ctx.families(), board: ctx.board().node });
  const stop = (x: unknown) => { ctx.preview(null); setStage({ step: "stop", why: typeof x === "string" ? x : errorText(x) }); };

  const wiring = async (d: Drawing) => {
    setStage({ step: "busy", what: "wiring" });
    try {
      const p = await post<Proposal>("wiring", asking(d));
      if (p.circuits.length) setStage({ step: "wiring", proposal: p }); else stop(warningsOf(p.warnings));
    } catch (x) { stop(x); }
  };
  const start = async (d: Drawing) => {
    work.current = d;
    if (!ctx.board().node) { stop("noBoard"); return; }
    if (d.lines.length) { await wiring(d); return; }                              // the runs are already drawn: the wiring goes over them
    setStage({ step: "busy", what: "runs" });
    try {
      const r = await post<RunsProposal>("runs", asking(d));
      if (!r.lines.length) { stop(warningsOf(r.warnings)); return; }
      ctx.preview(r); setStage({ step: "runs", proposal: r });
    } catch (x) { stop(x); }
  };
  const acceptRuns = async () => {
    if (stage?.step !== "runs" || !work.current) return;
    const next = applyRuns(work.current, stage.proposal);
    work.current = next; ctx.preview(null);
    try { await ctx.commit(next); await wiring(next); } catch (x) { stop(x); }
  };
  const acceptWiring = async () => {
    if (stage?.step !== "wiring" || !work.current) return;
    const p = stage.proposal;
    setStage({ step: "busy", what: "sizing" });
    try {
      await post("circuits", { board: ctx.board().id, circuits: p.circuits.map((c) => ({ tag: c.tag, description: c.description, load: c.va, unit: "VA" })) });
      const next = applyProposal(work.current, p);
      work.current = next;
      await ctx.commit(next);                                                    // the board measures the lengths on the saved plan
      setStage({ step: "sizing", sizing: await post<Sizing>("sizing", { board: ctx.board().id }) });
    } catch (x) { stop(x); }
  };
  const approve = async (apply: (d: Drawing, s: Sizing) => Drawing) => {
    if (stage?.step !== "sizing" || !work.current) return;
    try { const next = apply(work.current, stage.sizing); work.current = next; await ctx.commit(next); setStage({ step: "done" }); } catch (x) { stop(x); }
  };
  const close = () => { ctx.preview(null); setStage(null); };
  return { stage, start, acceptRuns, acceptWiring, approve, close };
}
