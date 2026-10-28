import { Badge, Icon, Key, useI18n } from "@epc/ui";
import type { Drawing } from "./planEditing";
import { CompareRow, CompareTable, RoomTools, SettingsBox } from "./LightingExtras";
import { exportMapPng } from "./lightMapExport";
import { settingsOf } from "./lightingTools";
import { AreaResult, areaCardOf, Card, cardOf, EmergencyResult, emergencyCardOf, EnergyCheck, hasPlacements, isDrawn, LightingStudy, isReady, LightingOptions, LightingProposal, parsePositive, RoomLighting, setRoomLighting } from "./lightingApi";

/** Lighting: for each room marked on the plan, what it is for and which luminaire; the program calculates how many go in and where, and shows it over the plan and as a card per room until the
 *  person decides. The numbers are the backend's (`epc_lighting`); this panel only asks and shows. */
interface Props {
  drawing: Drawing; options: LightingOptions | undefined; proposal: LightingProposal | null; busy: boolean; canWrite: boolean;
  onChange: (d: Drawing) => void; onCalc: () => void; onApply: () => void; showMap: boolean; onMap: (on: boolean) => void; onVerify: () => void; compare: { room: string; options: CompareRow[]; best: string | null } | null; onCompare: (room: string) => void; onUse: (room: string, luminaire: string) => void; onCloseCompare: () => void; studyError: string; applied: string; study: LightingStudy | undefined; onReport: () => void; reported: string; onDiscard: () => void; onNewRoom: () => void; onLook: (at: [number, number]) => void;
}

const ESTIMATES = ["target", "cu", "maintenance", "ceiling", "walls", "floor"];

export default function LightingPanel({ drawing, options, proposal, busy, canWrite, onChange, onCalc, onApply, showMap, onMap, onVerify, compare, onCompare, onUse, onCloseCompare, studyError, applied, study, onReport, reported, onDiscard, onNewRoom, onLook }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const rooms = drawing.rooms ?? [];
  const interior = (options?.luminaires ?? []).filter((l) => l.kind === "interior");
  const exterior = (options?.luminaires ?? []).filter((l) => l.kind === "exterior");
  const set = (id: string, patch: Partial<Record<keyof RoomLighting, unknown>>) => onChange(setRoomLighting(drawing, id, patch));
  const auto = !!settingsOf(drawing).auto_luminaire;
  const ready = rooms.some((r) => isReady(r.lighting, auto));
  const hasDrawn = drawing.nodes.some((n) => n.kind === "LU");
  return (
    <div className="lighting">
      <p className="muted small" style={{ margin: "0 0 8px" }}>{tl("light.help")}</p>
      {studyError && <div className="alert bad small" style={{ marginBottom: 8 }}>{studyError}</div>}
      <SettingsBox drawing={drawing} canWrite={canWrite} onChange={onChange} />
      {!drawing.scale && <div className="alert warn small">{tl("light.needScale")}</div>}
      {rooms.length === 0 && <p className="muted small">{tl("design.noRooms")}</p>}
      <ul className="coord-list">
        {rooms.map((r) => {
          const l = r.lighting ?? {};
          const activity = options?.activities.find((a) => a.id === l.activity);
          const ext = !!l.exterior;
          const lum = (ext ? exterior : interior).find((x) => x.id === l.luminaire);
          return (
            <li key={r.id} className="coord-item">
              <div className="row" style={{ gap: 6 }}>
                <b style={{ flex: 1 }}>{r.name || r.id}</b>
                <button onClick={() => onLook([r.points.reduce((s, p) => s + p[0], 0) / r.points.length, r.points.reduce((s, p) => s + p[1], 0) / r.points.length])} title={tl("coord.go")} aria-label={tl("coord.go")}><Icon name="fit" size={14} /></button>
              </div>
              <label className="small" style={{ display: "block", margin: "4px 0" }}>
                <input type="checkbox" disabled={!canWrite} checked={ext} onChange={(e) => set(r.id, { exterior: e.target.checked, luminaire: "", activity: "" })} /> {tl("light.exterior")}
              </label>
              <div className="light-fields">
                {!ext && (options?.norm_rules?.length ?? 0) > 0 && <label>{tl("light.normRule")}
                  <select disabled={!canWrite} value={l.norm_rule ?? ""} onChange={(e) => set(r.id, { norm_rule: e.target.value })}>
                    <option value="">–</option>{options!.norm_rules!.map((n) => <option key={n.id} value={n.id} disabled={n.status !== "approved"}>{n.norm} · {n.summary} ({n.value} lx){n.status !== "approved" ? ` — ${tl("light.normRule.pending")}` : ""}</option>)}
                  </select></label>}
                {!ext && <label>{tl("light.activity")}
                  <select disabled={!canWrite} value={l.activity ?? ""} onChange={(e) => set(r.id, { activity: e.target.value })}>
                    <option value="">–</option>{options?.activities.map((a) => <option key={a.id} value={a.id}>{a.label} ({a.em_lux} lx)</option>)}
                  </select></label>}
                <label>{tl("light.luminaire")}
                  <select disabled={!canWrite} value={l.luminaire ?? ""} onChange={(e) => set(r.id, { luminaire: e.target.value })}>
                    <option value="">–</option>{(ext ? exterior : interior).map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                  </select></label>
                {!ext && <><label>{tl("light.method")}
                  <select disabled={!canWrite} value={l.method ?? "lumen"} onChange={(e) => set(r.id, { method: e.target.value === "zonal" ? "zonal" : "" })}>
                    <option value="lumen">{tl("light.method.lumen")}</option><option value="zonal">{tl("light.method.zonal")}</option>
                  </select></label>
                <label>{tl("light.height")}
                  <input disabled={!canWrite} inputMode="decimal" defaultValue={l.height_m ?? ""} placeholder="2,6" key={"h" + r.id + (l.height_m ?? "")} onBlur={(e) => set(r.id, { height_m: parsePositive(e.target.value) })} /></label></>}
                <label>{tl("light.target")}
                  <input disabled={!canWrite} inputMode="numeric" defaultValue={l.target_lux ?? ""} placeholder={activity ? String(activity.em_lux) : "lx"} key={"t" + r.id + (l.target_lux ?? "")} onBlur={(e) => set(r.id, { target_lux: parsePositive(e.target.value) })} /></label>
                {!ext && <label>{tl("light.emergency")}
                  <select disabled={!canWrite} value={l.emergency_luminaire ?? ""} onChange={(e) => set(r.id, { emergency_luminaire: e.target.value })}>
                    <option value="">–</option>{interior.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                  </select></label>}
                {!ext && <label>{tl("light.ugr")}
                  <input disabled={!canWrite} inputMode="decimal" defaultValue={l.ugr_calculated ?? ""} placeholder="–" key={"u" + r.id + (l.ugr_calculated ?? "")} onBlur={(e) => set(r.id, { ugr_calculated: parsePositive(e.target.value) })} /></label>}
                {!ext && <label>{tl("light.cu")}
                  <input disabled={!canWrite} inputMode="decimal" defaultValue={l.coefficient_of_utilisation ?? ""} placeholder="–" key={"c" + r.id + (l.coefficient_of_utilisation ?? "")} onBlur={(e) => set(r.id, { coefficient_of_utilisation: parsePositive(e.target.value) })} /></label>}
                {ext && <><label>{tl("light.beam")}
                  <input disabled={!canWrite} inputMode="decimal" defaultValue={l.beam_utilisation ?? ""} placeholder="0,75" key={"b" + r.id + (l.beam_utilisation ?? "")} onBlur={(e) => set(r.id, { beam_utilisation: parsePositive(e.target.value) })} /></label>
                  <label>{tl("light.enclosure")}
                    <select disabled={!canWrite} value={l.enclosure ?? "open"} onChange={(e) => set(r.id, { enclosure: e.target.value === "closed" ? "closed" : "" })}>
                      <option value="open">{tl("light.enclosure.open")}</option><option value="closed">{tl("light.enclosure.closed")}</option>
                    </select></label></>}
              </div>
              {ext && !l.target_lux && <div className="small" style={{ color: "var(--warn)" }}>{tl("light.exteriorTarget")}</div>}
              {activity && !l.norm_rule && <div className="small muted" title={activity.source}>{tl("light.targetFrom")}: {activity.source}</div>}
              {l.norm_rule && !l.target_lux && <div className="small muted">{tl("light.targetFrom")}: {options?.norm_rules?.find((n) => n.id === l.norm_rule)?.norm ?? ""} · {options?.norm_rules?.find((n) => n.id === l.norm_rule)?.clause ?? l.norm_rule}</div>}
              {lum?.illustrative && <div className="small muted">{tl("light.illustrative")}</div>}
              <RoomTools drawing={drawing} roomId={r.id} activities={options?.activities ?? []} canWrite={canWrite} onChange={onChange} onCompare={() => onCompare(r.id)} comparable={isReady({ ...l, luminaire: l.luminaire || "-" })} />
              {compare?.room === r.id && <CompareTable rows={compare.options} best={compare.best} onUse={(id) => onUse(r.id, id)} onClose={onCloseCompare} />}
            </li>
          );
        })}
      </ul>
      {canWrite && <button onClick={onNewRoom}><Icon name="room" size={14} /> {tl("design.newRoom")}</button>}
      {canWrite && <div className="row" style={{ gap: 6, marginTop: 8 }}>
        <button className="primary" disabled={busy || !drawing.scale || !ready} onClick={onCalc}>{busy ? tl("design.working") : tl("light.calc")}</button>
        {hasDrawn && <button disabled={busy || !drawing.scale || !ready} onClick={onVerify} title={tl("light.verifyHelp")}>{tl("light.verify")}</button>}
        {proposal && hasPlacements(proposal) && <button className="primary" onClick={onApply}>{tl("light.apply")}</button>}
        <label className="small"><input type="checkbox" checked={showMap} onChange={(e) => onMap(e.target.checked)} /> {tl("light.map")}</label>
        {proposal && <button onClick={onDiscard}>{tl("design.discard")}</button>}
      </div>}
      {!ready && rooms.length > 0 && <p className="muted small">{tl("light.needFields")}</p>}
      {study?.exists && <Study study={study} canWrite={canWrite} reported={reported} onReport={onReport} />}
      {applied && <div className="alert ok small" style={{ marginTop: 8 }}>{applied}</div>}
      {proposal && <Result proposal={proposal} />}
    </div>
  );
}

function Result({ proposal }: { proposal: LightingProposal }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const cards = (proposal.result?.rooms ?? []).map(cardOf);
  const energy = proposal.energy_checks ?? {};
  return (
    <div style={{ marginTop: 10 }}>
      {proposal.skipped.map((s) => <div key={s.id} className="alert small" style={{ margin: "4px 0" }}><b>{s.name || s.id}</b>: {s.reason}</div>)}
      {isDrawn(proposal) && <div className="alert small" style={{ margin: "4px 0" }}>{tl("light.drawnNote")}</div>}
      {cards.map((c) => <RoomCard key={c.id} c={c} energy={energy[c.id]} />)}
      {(proposal.result?.areas ?? []).map((a) => <AreaCard key={a.id} a={a} energy={energy[a.id]} />)}
      {(proposal.result?.emergency ?? []).map((e) => <EmergencyCard key={e.id} e={e} />)}
      {Object.keys(proposal.maps ?? {}).length > 0 && <MapLegend proposal={proposal} />}
      {proposal.warnings.length > 0 && (
        <details className="small" style={{ marginTop: 6 }}><summary>{tl("light.warnings")} ({proposal.warnings.length})</summary>
          <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>{proposal.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></details>
      )}
      <p className="muted small" style={{ margin: "8px 0 0" }}>{tl("light.preview")}</p>
    </div>
  );
}

function RoomCard({ c, energy }: { c: Card; energy?: EnergyCheck }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  return (
    <div className="coord-item" style={{ margin: "6px 0" }}>
      <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
        <b>{c.name || c.id}</b>
        <Badge tone={c.complies ? "ok" : "bad"}>{c.complies ? tl("light.meets") : tl("light.notMeets")}</Badge>
      </div>
      <div className="small">{c.average.toFixed(0)} lx {c.complies ? "≥" : "<"} {c.target.toFixed(0)} lx ({c.margin > 0 ? "+" : ""}{c.margin.toFixed(1)} %)</div>
      <div className="small">{c.installed} {c.drawn ? tl("light.drawn") : tl("light.luminaires")} ({tl("light.needed")}: {c.required})</div>
      {c.source && <div className="small muted" title={c.source}>{tl("light.targetFrom")}: {c.source.length > 70 ? c.source.slice(0, 70) + "…" : c.source}</div>}
      <EnergyLine energy={energy} />
      <div className="small muted">
        {c.spacing !== "na" && <>{tl("light.spacing")}: {tl(`light.spacing.${c.spacing}`)} · </>}
        {c.uniformity !== null && <>{tl("light.uniformity")}: {c.uniformity.toFixed(2)} · </>}
        {c.power_w !== null && <>{c.power_w.toFixed(0)} W{c.density !== null && <> ({c.density.toFixed(1)} W/m²)</>}</>}
      </div>
      {c.unsure.length > 0 && <div className="small" style={{ color: "var(--warn)" }}>{tl("light.confirm")}: {c.unsure.filter((k) => ESTIMATES.includes(k)).map((k) => tl(`light.est.${k}`)).join(", ")}</div>}
      <div className="small muted">UGR: {tl(`light.ugr.${c.ugr}`)}{c.ugrLimit !== null && <> (≤ {c.ugrLimit})</>}</div>
    </div>
  );
}

/** The study kept with the sheet: when it was made, whether it is still good for the rooms as they are drawn now, and its report. */
function Study({ study, canWrite, reported, onReport }: { study: LightingStudy; canWrite: boolean; reported: string; onReport: () => void }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const rooms = study.result?.rooms ?? [];
  const meets = rooms.filter((r) => r.verification.complies).length;
  return (
    <div className="coord-item" style={{ marginTop: 10 }}>
      <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
        <b>{tl("light.study")}</b>
        <Badge tone={study.stale ? "warn" : "ok"}>{study.stale ? tl("light.study.stale") : tl("light.study.fresh")}</Badge>
      </div>
      <div className="small muted">{study.saved_at}{study.saved_by ? ` · ${study.saved_by}` : ""}</div>
      <div className="small">{rooms.length} {tl("light.rooms")} · {meets} {tl("light.meets")}</div>
      {study.stale && <div className="small" style={{ color: "var(--warn)" }}>{tl("light.study.staleHelp")}</div>}
      {study.report && <div className="small" style={{ marginTop: 4 }}>{tl("light.reportIn")}</div>}
      {canWrite && <button style={{ marginTop: 6 }} disabled={study.stale} onClick={onReport}>{tl(study.report ? "light.reportAgain" : "light.report")}</button>}
      {reported && !study.stale && <div className="small" style={{ marginTop: 4 }}>{reported}</div>}
    </div>
  );
}

function AreaCard({ a, energy }: { a: AreaResult; energy?: EnergyCheck }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const c = areaCardOf(a);
  return (
    <div className="coord-item" style={{ margin: "6px 0" }}>
      <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
        <b>{c.name || c.id}</b>
        <Badge tone={c.complies ? "ok" : "bad"}>{c.complies ? tl("light.meets") : tl("light.notMeets")}</Badge>
        <Badge>{tl("light.exterior")}</Badge>
      </div>
      <div className="small">{c.average.toFixed(0)} lx {c.complies ? "≥" : "<"} {c.target.toFixed(0)} lx ({c.margin > 0 ? "+" : ""}{c.margin.toFixed(1)} %)</div>
      <div className="small">{tl("light.floodlights")}: {c.floodlights} · {c.area_m2.toFixed(0)} m²{c.power_w !== null && <> · {c.power_w.toFixed(0)} W</>}</div>
      <EnergyLine energy={energy} />
      <div className="small muted">{tl("light.floodlightsNote")}</div>
      {c.unsure.length > 0 && <div className="small" style={{ color: "var(--warn)" }}>{tl("light.confirm")}: {c.unsure.map((k) => tl(`light.est.${k}`)).join(", ")}</div>}
    </div>
  );
}

/** The scale of the colours of the illuminance map: from the darkest cell of the rooms to the brightest. */
function MapLegend({ proposal }: { proposal: LightingProposal }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const maps = Object.values(proposal.maps ?? {});
  const low = Math.min(...maps.map((m) => m.min)), high = Math.max(...maps.map((m) => m.max));
  return (
    <div className="small" style={{ margin: "6px 0" }}>
      <div style={{ height: 8, borderRadius: 4, background: "linear-gradient(to right, hsl(240 80% 50%), hsl(120 80% 50%), hsl(0 80% 50%))" }} />
      <div className="row" style={{ justifyContent: "space-between" }}><span>{low.toFixed(0)} lx</span><span>{t("light.map" as Key)}</span><span>{high.toFixed(0)} lx</span></div>
      <div className="row" style={{ gap: 4, flexWrap: "wrap", marginTop: 4 }}>
        {Object.entries(proposal.maps ?? {}).map(([id, m]) => <button key={id} onClick={() => exportMapPng(m, `${tl("light.map")}_${proposal.result?.rooms.find((r) => r.id === id)?.name ?? id}`)}>{tl("light.exportMap")}: {proposal.result?.rooms.find((r) => r.id === id)?.name ?? id}</button>)}
      </div>
    </div>
  );
}

function EmergencyCard({ e }: { e: EmergencyResult }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const c = emergencyCardOf(e);
  return (
    <div className="coord-item" style={{ margin: "6px 0" }}>
      <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
        <b>{c.name || c.id}</b>
        <Badge tone={c.complies ? "ok" : "bad"}>{c.complies ? tl("light.meets") : tl("light.notMeets")}</Badge>
        <Badge>{tl("light.emergencyTitle")}</Badge>
      </div>
      <div className="small">{c.installed} {tl("light.luminaires")}{c.min !== null && <> · {c.min.toFixed(2)} lx min{c.ratio !== null && <> · max/min {c.ratio.toFixed(1)}</>}</>}{c.routes > 0 && <> · {tl("light.routes")}: {c.routesOk}/{c.routes}</>}</div>
      <div className="small muted">{tl("light.emergencyNote")}</div>
      {c.unsure.length > 0 && <div className="small" style={{ color: "var(--warn)" }}>{tl("light.confirm")}: {c.unsure.map((k) => tl(`light.est.${k}`)).join(", ")}</div>}
    </div>
  );
}

/** What the installed power means: against the limit the person set, and the energy and cost of a year when the hours and the tariff are known. */
function EnergyLine({ energy }: { energy?: EnergyCheck }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  if (!energy || (energy.limit_w_m2 === null && energy.annual_kwh === null)) return null;
  return (
    <div className="small muted">
      {energy.limit_w_m2 !== null && <>{energy.density_w_m2?.toFixed(1)} W/m² {energy.complies ? "≤" : ">"} {energy.limit_w_m2} <Badge tone={energy.complies ? "ok" : "bad"}>{energy.complies ? tl("light.underLimit") : tl("light.overLimit")}</Badge> </>}
      {energy.annual_kwh !== null && <>{energy.annual_kwh.toFixed(0)} kWh/{tl("light.year")}</>}{energy.annual_cost !== null && <> · {energy.annual_cost.toFixed(2)}</>}
    </div>
  );
}
