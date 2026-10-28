import { Badge, Icon, Key, useI18n } from "@epc/ui";
import type { Drawing } from "./planEditing";
import { Card, cardOf, hasPlacements, isReady, LightingOptions, LightingProposal, parsePositive, RoomLighting, setRoomLighting } from "./lightingApi";

/** Lighting: for each room marked on the plan, what it is for and which luminaire; the program calculates how many go in and where, and shows it over the plan and as a card per room until the
 *  person decides. The numbers are the backend's (`epc_lighting`); this panel only asks and shows. */
interface Props {
  drawing: Drawing; options: LightingOptions | undefined; proposal: LightingProposal | null; busy: boolean; canWrite: boolean;
  onChange: (d: Drawing) => void; onCalc: () => void; onApply: () => void; applied: string; onDiscard: () => void; onNewRoom: () => void; onLook: (at: [number, number]) => void;
}

const ESTIMATES = ["target", "cu", "maintenance", "ceiling", "walls", "floor"];

export default function LightingPanel({ drawing, options, proposal, busy, canWrite, onChange, onCalc, onApply, applied, onDiscard, onNewRoom, onLook }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const rooms = drawing.rooms ?? [];
  const interior = (options?.luminaires ?? []).filter((l) => l.kind === "interior");
  const set = (id: string, patch: Partial<Record<keyof RoomLighting, unknown>>) => onChange(setRoomLighting(drawing, id, patch));
  const ready = rooms.some((r) => isReady(r.lighting));
  return (
    <div className="lighting">
      <p className="muted small" style={{ margin: "0 0 8px" }}>{tl("light.help")}</p>
      {!drawing.scale && <div className="alert warn small">{tl("light.needScale")}</div>}
      {rooms.length === 0 && <p className="muted small">{tl("design.noRooms")}</p>}
      <ul className="coord-list">
        {rooms.map((r) => {
          const l = r.lighting ?? {};
          const activity = options?.activities.find((a) => a.id === l.activity);
          const lum = interior.find((x) => x.id === l.luminaire);
          return (
            <li key={r.id} className="coord-item">
              <div className="row" style={{ gap: 6 }}>
                <b style={{ flex: 1 }}>{r.name || r.id}</b>
                <button onClick={() => onLook([r.points.reduce((s, p) => s + p[0], 0) / r.points.length, r.points.reduce((s, p) => s + p[1], 0) / r.points.length])} title={tl("coord.go")} aria-label={tl("coord.go")}><Icon name="fit" size={14} /></button>
              </div>
              <div className="light-fields">
                <label>{tl("light.activity")}
                  <select disabled={!canWrite} value={l.activity ?? ""} onChange={(e) => set(r.id, { activity: e.target.value })}>
                    <option value="">–</option>{options?.activities.map((a) => <option key={a.id} value={a.id}>{a.label} ({a.em_lux} lx)</option>)}
                  </select></label>
                <label>{tl("light.luminaire")}
                  <select disabled={!canWrite} value={l.luminaire ?? ""} onChange={(e) => set(r.id, { luminaire: e.target.value })}>
                    <option value="">–</option>{interior.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                  </select></label>
                <label>{tl("light.method")}
                  <select disabled={!canWrite} value={l.method ?? "lumen"} onChange={(e) => set(r.id, { method: e.target.value === "zonal" ? "zonal" : "" })}>
                    <option value="lumen">{tl("light.method.lumen")}</option><option value="zonal">{tl("light.method.zonal")}</option>
                  </select></label>
                <label>{tl("light.height")}
                  <input disabled={!canWrite} inputMode="decimal" defaultValue={l.height_m ?? ""} placeholder="2,6" key={"h" + r.id + (l.height_m ?? "")} onBlur={(e) => set(r.id, { height_m: parsePositive(e.target.value) })} /></label>
                <label>{tl("light.target")}
                  <input disabled={!canWrite} inputMode="numeric" defaultValue={l.target_lux ?? ""} placeholder={activity ? String(activity.em_lux) : "lx"} key={"t" + r.id + (l.target_lux ?? "")} onBlur={(e) => set(r.id, { target_lux: parsePositive(e.target.value) })} /></label>
                <label>{tl("light.cu")}
                  <input disabled={!canWrite} inputMode="decimal" defaultValue={l.coefficient_of_utilisation ?? ""} placeholder="–" key={"c" + r.id + (l.coefficient_of_utilisation ?? "")} onBlur={(e) => set(r.id, { coefficient_of_utilisation: parsePositive(e.target.value) })} /></label>
              </div>
              {activity && <div className="small muted" title={activity.source}>{tl("light.targetFrom")}: {activity.source}</div>}
              {lum?.illustrative && <div className="small muted">{tl("light.illustrative")}</div>}
            </li>
          );
        })}
      </ul>
      {canWrite && <button onClick={onNewRoom}><Icon name="room" size={14} /> {tl("design.newRoom")}</button>}
      {canWrite && <div className="row" style={{ gap: 6, marginTop: 8 }}>
        <button className="primary" disabled={busy || !drawing.scale || !ready} onClick={onCalc}>{busy ? tl("design.working") : tl("light.calc")}</button>
        {proposal && hasPlacements(proposal) && <button className="primary" onClick={onApply}>{tl("light.apply")}</button>}
        {proposal && <button onClick={onDiscard}>{tl("design.discard")}</button>}
      </div>}
      {!ready && rooms.length > 0 && <p className="muted small">{tl("light.needFields")}</p>}
      {applied && <div className="alert ok small" style={{ marginTop: 8 }}>{applied}</div>}
      {proposal && <Result proposal={proposal} />}
    </div>
  );
}

function Result({ proposal }: { proposal: LightingProposal }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const cards = (proposal.result?.rooms ?? []).map(cardOf);
  return (
    <div style={{ marginTop: 10 }}>
      {proposal.skipped.map((s) => <div key={s.id} className="alert small" style={{ margin: "4px 0" }}><b>{s.name || s.id}</b>: {s.reason}</div>)}
      {cards.map((c) => <RoomCard key={c.id} c={c} />)}
      {proposal.warnings.length > 0 && (
        <details className="small" style={{ marginTop: 6 }}><summary>{tl("light.warnings")} ({proposal.warnings.length})</summary>
          <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>{proposal.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></details>
      )}
      <p className="muted small" style={{ margin: "8px 0 0" }}>{tl("light.preview")}</p>
    </div>
  );
}

function RoomCard({ c }: { c: Card }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  return (
    <div className="coord-item" style={{ margin: "6px 0" }}>
      <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
        <b>{c.name || c.id}</b>
        <Badge tone={c.complies ? "ok" : "bad"}>{c.complies ? tl("light.meets") : tl("light.notMeets")}</Badge>
      </div>
      <div className="small">{c.average.toFixed(0)} lx {c.complies ? "≥" : "<"} {c.target.toFixed(0)} lx ({c.margin > 0 ? "+" : ""}{c.margin.toFixed(1)} %)</div>
      <div className="small">{c.installed} {tl("light.luminaires")} ({tl("light.needed")}: {c.required})</div>
      <div className="small muted">
        {c.spacing !== "na" && <>{tl("light.spacing")}: {tl(`light.spacing.${c.spacing}`)} · </>}
        {c.uniformity !== null && <>{tl("light.uniformity")}: {c.uniformity.toFixed(2)} · </>}
        {c.power_w !== null && <>{c.power_w.toFixed(0)} W{c.density !== null && <> ({c.density.toFixed(1)} W/m²)</>}</>}
      </div>
      {c.unsure.length > 0 && <div className="small" style={{ color: "var(--warn)" }}>{tl("light.confirm")}: {c.unsure.filter((k) => ESTIMATES.includes(k)).map((k) => tl(`light.est.${k}`)).join(", ")}</div>}
    </div>
  );
}
