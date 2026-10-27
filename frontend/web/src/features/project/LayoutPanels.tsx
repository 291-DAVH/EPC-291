import { Badge, Icon, State, useApi } from "@epc/ui";
import type { Ref } from "./planEditing";
import type { Problem } from "./planTools";

/** The contents of the tabs of the layout side panel that only show things: the schedule the engine derived, its warnings, the kept states of the drawing and the checks before making files. */
type T = (key: string) => string;

export function WarningsPanel({ warnings, onJump, tl }: { warnings: string[]; onJump: (w: string) => void; tl: T }) {
  if (!warnings.length) return <div className="state">–</div>;
  return <ul className="small warn-list">{warnings.map((w, i) => <li key={i}><button className="linkbtn" onClick={() => onJump(w)} title={tl("plan.warning.go")}>{w}</button></li>)}</ul>;
}

interface Snap { id: string; at: string; nodes: number; lines: number }

/** The earlier states the server kept of this sheet: look at one over the drawing, or go back to it (what is there now is kept too). */
export function HistoryPanel({ root, level, rev, canWrite, comparing, onCompare, onRestore, tl }: {
  root: string; level: string; rev: number; canWrite: boolean; comparing: string; onCompare: (id: string) => void; onRestore: (id: string) => void; tl: T;
}) {
  const list = useApi<Snap[]>(`${root}/${level}/history?r=${rev}`);
  if (!list.data) return <State loading={list.loading} />;
  if (!list.data.length) return <div className="state">{tl("plan.history.none")}</div>;
  return (
    <div>
      <p className="muted small" style={{ margin: "0 0 6px" }}>{tl("plan.history.help")}</p>
      <ul className="coord-list">
        {list.data.map((s) => (
          <li key={s.id} className={"coord-item" + (comparing === s.id ? " on" : "")}>
            <div className="row" style={{ justifyContent: "space-between" }}><span className="mono small">{s.at.replace("T", " ")}</span><span className="small muted">{s.nodes} {tl("plan.stat.nodes")} · {s.lines} {tl("plan.stat.lines")}</span></div>
            <div className="row" style={{ gap: 6, marginTop: 4 }}>
              <button aria-pressed={comparing === s.id} onClick={() => onCompare(comparing === s.id ? "" : s.id)}><Icon name="eye" size={14} /> {tl(comparing === s.id ? "plan.history.hide" : "plan.history.compare")}</button>
              {canWrite && <button onClick={() => { if (window.confirm(tl("plan.history.confirm"))) onRestore(s.id); }}><Icon name="history" size={14} /> {tl("plan.history.restore")}</button>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** What to look at before making the files: the errors stop it, the warnings can be accepted. */
export function ChecksPanel({ problems, describe, onGo, onForce, onClose, tl }: {
  problems: Problem[]; describe: (p: Problem) => string; onGo: (p: Problem) => void; onForce: () => void; onClose: () => void; tl: T;
}) {
  const errors = problems.filter((p) => p.severity === "error");
  return (
    <div className="wb-float wb-checks" role="dialog" aria-label={tl("plan.checks")}>
      <div className="row" style={{ justifyContent: "space-between", width: "100%" }}><b>{tl("plan.checks")}</b><button className="strip-btn" onClick={onClose} aria-label={tl("layout.cancel")}><Icon name="close" size={14} /></button></div>
      {problems.length === 0 && <p className="small" style={{ margin: 0 }}><Icon name="check" size={14} /> {tl("plan.checks.ok")}</p>}
      <ul className="small warn-list" style={{ width: "100%" }}>
        {problems.map((p, i) => <li key={i}><Badge tone={p.severity === "error" ? "bad" : "warn"}>{tl(p.severity === "error" ? "plan.checks.error" : "plan.checks.warn")}</Badge> <button className="linkbtn" onClick={() => onGo(p)}>{describe(p)}</button></li>)}
      </ul>
      <div className="row" style={{ gap: 6 }}>
        {problems.length > 0 && <button className="primary" disabled={errors.length > 0} onClick={onForce}>{tl("plan.checks.go")}</button>}<button onClick={onClose}>{tl(problems.length > 0 ? "layout.cancel" : "plan.checks.close")}</button>
      </div>
    </div>
  );
}

export interface Changes {
  has_snapshot: boolean; count?: number; scale_changed?: boolean; origin_changed?: boolean; circuits_changed?: boolean; discipline_changed?: boolean;
  nodes?: Record<"added" | "removed" | "changed", { id: string; kind: string; tag: string }[]>; lines?: Record<"added" | "removed" | "changed", { id: string; kind: string; tag: string }[]>;
}

/** What differs from the drawing the DXF and PDF were made from, before making them again. */
export function ChangesPanel({ data, onGo, onClose, tl }: { data: Changes; onGo: (r: Ref) => void; onClose: () => void; tl: T }) {
  const groups = (["nodes", "lines"] as const).flatMap((part) => (["added", "changed", "removed"] as const).map((what) => ({ part, what })));
  const flags = [data.scale_changed && "scale", data.origin_changed && "origin", data.circuits_changed && "circuits", data.discipline_changed && "discipline"].filter(Boolean) as string[];
  return (
    <div className="wb-float wb-checks" role="dialog" aria-label={tl("plan.changes")}>
      <div className="row" style={{ justifyContent: "space-between", width: "100%" }}><b>{tl("plan.changes")}</b><button className="strip-btn" onClick={onClose} aria-label={tl("layout.cancel")}><Icon name="close" size={14} /></button></div>
      {!data.has_snapshot && <p className="small muted" style={{ margin: 0 }}>{tl("plan.changes.none")}</p>}
      {data.has_snapshot && !data.count && !flags.length && <p className="small" style={{ margin: 0 }}><Icon name="check" size={14} /> {tl("plan.changes.same")}</p>}
      {flags.length > 0 && <p className="small" style={{ margin: 0 }}>{flags.map((f) => tl("plan.changes." + f)).join(" · ")}</p>}
      {data.has_snapshot && groups.map(({ part, what }) => {
        const list = data[part]?.[what] ?? [];
        return list.length ? <div key={part + what} className="small" style={{ width: "100%" }}><b>{tl("plan.changes." + what)} · {tl("plan.stat." + (part === "nodes" ? "nodes" : "lines"))} ({list.length})</b>
          <div className="row" style={{ flexWrap: "wrap", gap: 4, marginTop: 2 }}>{list.map((x) => <button key={x.id} className="linkbtn" disabled={what === "removed"} onClick={() => onGo({ type: part === "nodes" ? "node" : "line", id: x.id })}>{x.tag || `${x.kind}:${x.id}`}</button>)}</div></div> : null;
      })}
    </div>
  );
}
