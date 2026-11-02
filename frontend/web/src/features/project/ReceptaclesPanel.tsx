import { Badge, Key, useI18n } from "@epc/ui";
import type { Drawing } from "./planEditing";
import { hasPlacements, isDrawn, isReady, ReceptaclesOptions, ReceptaclesProposal, RecRoomResult, RoomReceptacles, setRoomReceptacles } from "./receptaclesApi";

interface Props {
  drawing: Drawing; options: ReceptaclesOptions | undefined; proposal: ReceptaclesProposal | null; busy: boolean; canWrite: boolean; error: string; applied: { added: number; removed: number } | null;
  onChange: (d: Drawing) => void; onCalc: () => void; onVerify: () => void; onApply: () => void; onLook: (at: [number, number]) => void;
}

const SURE = 0.6;                                         // under this confidence an estimate is shown as something to confirm

/** Socket outlets: for each room marked on the plan, what it is for; the program calculates how many outlets it needs and where they go along the walls, and shows them over the plan until the person
 *  decides. The numbers are the backend's (`epc_receptacles`); this panel only asks and shows. */
export default function ReceptaclesPanel({ drawing, options, proposal, busy, canWrite, error, applied, onChange, onCalc, onVerify, onApply, onLook }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const rooms = drawing.rooms ?? [];
  const set = (id: string, patch: Partial<Record<keyof RoomReceptacles, unknown>>) => onChange(setRoomReceptacles(drawing, id, patch));
  const ready = rooms.some((r) => isReady(r.receptacles));
  const hasDrawn = drawing.nodes.some((n) => n.kind === "TG" || n.kind === "TE");
  const result = (id: string): RecRoomResult | undefined => proposal?.result?.rooms.find((r) => r.id === id);
  return (
    <div className="lighting">
      <p className="muted small" style={{ margin: "0 0 8px" }}>{tl("rec.help")}</p>
      {error && <div className="alert bad small" style={{ marginBottom: 8 }}>{error}</div>}
      {!drawing.scale && <div className="alert warn small">{tl("light.needScale")}</div>}
      {rooms.length === 0 && <p className="muted small">{tl("design.noRooms")}</p>}
      <ul className="coord-list">
        {rooms.map((r) => {
          const l = r.receptacles ?? {};
          const use = options?.uses.find((u) => u.id === l.use);
          const res = result(r.id);
          return (
            <li key={r.id} className="coord-item">
              <div className="row" style={{ gap: 6 }}>
                <b style={{ flex: 1 }}>{r.name || r.id}</b>
                <button onClick={() => onLook([r.points.reduce((s, p) => s + p[0], 0) / r.points.length, r.points.reduce((s, p) => s + p[1], 0) / r.points.length])} title={tl("coord.go")} aria-label={`${tl("coord.go")} ${r.name || r.id}`}>⌖</button>
              </div>
              <div className="light-fields">
                <label>{tl("rec.use")}
                  <select disabled={!canWrite} value={l.use ?? ""} onChange={(e) => set(r.id, { use: e.target.value })}>
                    <option value="">–</option>{options?.uses.map((u) => <option key={u.id} value={u.id}>{u.label}</option>)}
                  </select></label>
                <label>{tl("rec.outlet")}
                  <select disabled={!canWrite} value={l.receptacle ?? ""} onChange={(e) => set(r.id, { receptacle: e.target.value })}>
                    <option value="">{tl("rec.byUse")}</option>{options?.receptacles.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                  </select></label>
                <label>{tl("rec.count")}
                  <input disabled={!canWrite} inputMode="numeric" defaultValue={l.count ?? ""} placeholder={tl("rec.auto")} key={"c" + r.id + (l.count ?? "")} onBlur={(e) => { const n = parseInt(e.target.value, 10); set(r.id, { count: Number.isFinite(n) && n >= 0 ? n : undefined }); }} /></label>
                <label>{tl("rec.height")}
                  <input disabled={!canWrite} inputMode="decimal" defaultValue={l.height_m ?? ""} placeholder="0,3" key={"h" + r.id + (l.height_m ?? "")} onBlur={(e) => { const n = parseFloat(e.target.value.replace(",", ".")); set(r.id, { height_m: Number.isFinite(n) && n >= 0 ? n : undefined }); }} /></label>
                <label>{tl("rec.norm")}
                  <select disabled={!canWrite} value={l.norm ?? ""} onChange={(e) => set(r.id, { norm: e.target.value })}>
                    <option value="">–</option>{options?.norms.map((n) => <option key={n} value={n}>AEA 90364-7-{n}</option>)}
                  </select></label>
              </div>
              {use && <p className="muted small" style={{ margin: "4px 0 0" }}>{use.basis === "area" ? tl("rec.perArea").replace("{n}", String(use.per_m2)) : use.basis === "perimeter" ? tl("rec.perPerimeter").replace("{n}", String(use.per_m)) : tl("rec.fixed")} · {tl("rec.min")} {use.min}{use.confidence < SURE ? ` · ${tl("rec.toVerify")}` : ""}</p>}
              {res && (
                <div className="small" style={{ marginTop: 4 }}>
                  <Badge tone={res.checks.every((c) => c.ok) ? "ok" : "bad"}>{res.installed}/{res.required} · {res.family}</Badge>{" "}
                  <span className="muted">{res.load_va} VA · {res.circuits_min} {tl("rec.circuits")} · {res.layout.mode === "drawn" ? tl("rec.drawn") : res.estimate.reason}</span>
                  {res.checks.filter((c) => !c.ok).map((c) => <div key={c.id} className="alert warn small" style={{ marginTop: 4 }}>{c.message}</div>)}
                </div>
              )}
            </li>
          );
        })}
      </ul>
      <div className="row" style={{ gap: 6, flexWrap: "wrap", margin: "8px 0" }}>
        <button className="primary" disabled={!canWrite || busy || !ready || !drawing.scale} onClick={onCalc}>{tl("rec.calc")}</button>
        <button disabled={busy || !ready || !hasDrawn || !drawing.scale} onClick={onVerify} title={tl("rec.verifyHelp")}>{tl("rec.verify")}</button>
        {proposal && hasPlacements(proposal) && <button className="primary" disabled={!canWrite} onClick={onApply}>{tl("rec.apply")}</button>}
      </div>
      {applied && <div className="alert ok small">{tl("rec.applied").replace("{n}", String(applied.added)).replace("{r}", String(applied.removed))}</div>}
      {proposal && isDrawn(proposal) && <p className="muted small">{tl("rec.nothingToApply")}</p>}
      {proposal?.skipped.map((s) => <div key={s.id} className="alert warn small" style={{ marginBottom: 4 }}>{s.name || s.id}: {s.reason}</div>)}
      {proposal?.warnings.map((w, i) => <div key={i} className="muted small">{w}</div>)}
    </div>
  );
}
