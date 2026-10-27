import { useState } from "react";
import { Badge, Icon, Key, useI18n } from "@epc/ui";
import type { Derived, Profile } from "./PlanEditor";
import type { Drawing } from "./planEditing";
import { centroidOf, loadsByRoom, Limits, Proposal, RunsProposal, removeRoom, renameRoom } from "./planTools";

/** Automatic design: the rooms marked on the plan, the limits per circuit, the circuits, trunk and branches the program proposes for the loads placed in them, and the button that accepts it. */
interface Props {
  drawing: Drawing; profile: Profile | undefined; proposal: Proposal | null; runs: RunsProposal | null; busy: boolean; canWrite: boolean; limitsOverride: Record<string, Partial<Limits>>;
  onLimits: (v: Record<string, Partial<Limits>>) => void; onProposeRuns: () => void; onApplyRuns: () => void; onDiscardRuns: () => void; onPropose: () => void; onApply: (createInBoard: boolean) => void; onDiscard: () => void;
  onChange: (d: Drawing) => void; onNewRoom: () => void; onLook: (at: [number, number]) => void; derived: Derived | null;
}

export default function DesignPanel({ drawing, profile, proposal, runs, busy, canWrite, limitsOverride, onLimits, onProposeRuns, onApplyRuns, onDiscardRuns, onPropose, onApply, onDiscard, onChange, onNewRoom, onLook }: Props) {
  const { t, lang } = useI18n();
  const tl = (k: string) => t(k as Key);
  const [inBoard, setInBoard] = useState(true);
  const loadKinds = new Set((profile?.nodes ?? []).filter((n) => n.carga).map((n) => n.id));
  const counts = loadsByRoom(drawing, loadKinds);
  const rooms = drawing.rooms ?? [];
  const families = proposal?.limits ?? {};
  const setLimit = (f: string, key: "max_outlets" | "va_per_outlet", v: string) => { const n = parseFloat(v.replace(",", ".")); onLimits({ ...limitsOverride, [f]: { ...(limitsOverride[f] ?? {}), [key]: Number.isFinite(n) && n > 0 ? n : undefined } }); };
  return (
    <div className="design">
      <p className="muted small" style={{ margin: "0 0 8px" }}>{tl("design.help")}</p>
      <h4 className="coord-h">{tl("design.step1")}</h4>
      <p className="muted small" style={{ margin: "0 0 6px" }}>{tl("design.runsHelp")}</p>
      {canWrite && <button className="primary" disabled={busy} onClick={onProposeRuns}>{busy ? tl("design.working") : tl("design.proposeRuns")}</button>}
      {runs && (
        <div style={{ marginTop: 8 }}>
          {runs.warnings.map((w, i) => <div key={i} className="alert warn small" style={{ margin: "4px 0" }}>{w}</div>)}
          {runs.lines.length > 0 && <>
            <p className="small" style={{ margin: "6px 0" }}>{runs.lines.filter((l) => l.role === "trunk").length} {tl("design.trunks")} · {runs.lines.filter((l) => l.role === "stub").length} {tl("design.branches")} · {tl("design.noBends")}
              {" "}({tl(`design.${runs.orientation}` as Key)}; {(runs.stats as { trunk_length?: number }).trunk_length} + {(runs.stats as { stub_length?: number }).stub_length} {(runs.stats as { in_metres?: boolean }).in_metres ? "m" : "u"}). {tl("design.cables")}</p>
            {canWrite && <div className="row" style={{ gap: 6 }}><button className="primary" disabled={busy} onClick={onApplyRuns}><Icon name="check" size={14} /> {tl("design.applyRuns")}</button><button onClick={onDiscardRuns}>{tl("design.discard")}</button></div>}
          </>}
        </div>
      )}

      <h4 className="coord-h">{tl("design.step2")}</h4>
      <p className="muted small" style={{ margin: "0 0 6px" }}>{tl("design.wiringHelp")}</p>
      <h4 className="coord-h">{tl("design.rooms")}</h4>
      {rooms.length === 0 && <p className="muted small">{tl("design.noRooms")}</p>}
      <ul className="coord-list">
        {rooms.map((r) => {
          const c = counts.rooms[r.id] ?? {};
          return (
            <li key={r.id} className="coord-item">
              <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                <input disabled={!canWrite} value={r.name} onChange={(e) => onChange(renameRoom(drawing, r.id, e.target.value))} aria-label={tl("plan.room.name")} style={{ flex: 1, minWidth: 100 }} />
                <button onClick={() => onLook(centroidOf(r.points))} title={tl("coord.go")} aria-label={tl("coord.go")}><Icon name="fit" size={14} /></button>
                {canWrite && <button onClick={() => onChange(removeRoom(drawing, r.id))} title={tl("coord.delete")} aria-label={tl("coord.delete")}><Icon name="trash" size={14} /></button>}
              </div>
              <div className="small muted">{Object.entries(c).map(([k, n]) => `${k}: ${n}`).join(" · ") || tl("design.noLoads")}</div>
            </li>
          );
        })}
      </ul>
      {canWrite && <button onClick={onNewRoom}><Icon name="room" size={14} /> {tl("design.newRoom")}</button>}
      {counts.outside > 0 && rooms.length > 0 && <p className="small" style={{ color: "var(--warn)" }}>{counts.outside} {tl("design.outside")}</p>}

      <h4 className="coord-h">{tl("design.circuits")}</h4>
      {Object.keys(families).length > 0 && (
        <table className="coord-rules"><thead><tr><th>{tl("design.family")}</th><th>{tl("design.max")}</th><th>{tl("design.va")}</th></tr></thead>
          <tbody>{Object.entries(families).map(([f, l]) => (
            <tr key={f}><td><b>{f}</b> <span className="muted small">{l.label[lang] ?? l.label.es}</span></td>
              <td><input disabled={!canWrite} inputMode="numeric" defaultValue={l.max_outlets} onBlur={(e) => setLimit(f, "max_outlets", e.target.value)} style={{ width: 54 }} /></td>
              <td><input disabled={!canWrite} inputMode="decimal" defaultValue={l.va_per_outlet} onBlur={(e) => setLimit(f, "va_per_outlet", e.target.value)} style={{ width: 66 }} /></td></tr>
          ))}</tbody></table>
      )}
      {canWrite && <button className="primary" disabled={busy || rooms.length === 0} onClick={onPropose}>{busy ? tl("design.working") : tl("design.propose")}</button>}
      {rooms.length === 0 && <span className="muted small"> {tl("design.needRooms")}</span>}
      <p className="muted small">{tl("design.typical")}</p>

      {proposal && (
        <div style={{ marginTop: 10 }}>
          {proposal.warnings.map((w, i) => <div key={i} className="alert warn small" style={{ margin: "4px 0" }}>{w}</div>)}
          {proposal.circuits.length === 0 ? <div className="state">{tl("design.none")}</div> : <>
            <table className="coord-rules"><thead><tr><th>{tl("layout.col.circuit")}</th><th>{tl("design.room")}</th><th>{tl("design.outlets")}</th><th>VA</th></tr></thead>
              <tbody>{proposal.circuits.map((c) => <tr key={c.tag}><td className="mono"><b>{c.tag}</b></td><td>{c.room_name}</td><td className="mono">{c.outlets}</td><td className="mono">{c.va}</td></tr>)}</tbody></table>
            <p className="small muted" style={{ margin: "6px 0" }}>{tl("design.cableFollows")}</p>
            {canWrite && <>
              <label className="vp-row"><input type="checkbox" checked={inBoard} onChange={(e) => setInBoard(e.target.checked)} /> {tl("design.inBoard")}</label>
              <div className="row" style={{ gap: 6, marginTop: 6 }}><button className="primary" disabled={busy} onClick={() => onApply(inBoard)}><Icon name="check" size={14} /> {tl("design.apply")}</button><button onClick={onDiscard}>{tl("design.discard")}</button></div>
            </>}
          </>}
        </div>
      )}
      {!proposal && drawing.circuits.length > 0 && <p className="small" style={{ marginTop: 8 }}><Badge tone="ok">{drawing.circuits.length}</Badge> {tl("design.already")}</p>}
    </div>
  );
}
