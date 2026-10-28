import { useState } from "react";
import { Badge, Icon, Key, useI18n } from "@epc/ui";
import type { Drawing } from "./planEditing";
import type { LightActivity } from "./lightingApi";
import { applyTemplate, copyLighting, LightSettings, removeTemplate, saveTemplate, setSetting, settingsOf, suggestActivity } from "./lightingTools";

/** What the panel offers around the fields of a room and of the sheet: the settings of the sheet, the tools of a room (suggestion, copy, templates) and the table that compares luminaires. */
export interface CompareRow { luminaire: string; name: string; installed: number; power_w: number | null; density_w_m2: number | null; average_lux: number; target_lux: number; complies: boolean; spacing: string; favorite: boolean; illustrative: boolean }

const num = (text: string): number | undefined => {
  const n = parseFloat(text.replace(",", "."));
  return Number.isFinite(n) && n >= 0 ? n : undefined;
};

export function SettingsBox({ drawing, canWrite, onChange }: { drawing: Drawing; canWrite: boolean; onChange: (d: Drawing) => void }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const s: LightSettings = settingsOf(drawing);
  const field = (key: "power_limit_w_m2" | "kwh_price" | "hours_default", label: string, placeholder: string) => (
    <label>{label}
      <input disabled={!canWrite} inputMode="decimal" defaultValue={s[key] ?? ""} placeholder={placeholder} key={key + (s[key] ?? "")} onBlur={(e) => onChange(setSetting(drawing, key, num(e.target.value)))} /></label>
  );
  return (
    <details className="small" style={{ margin: "6px 0 8px" }}>
      <summary>{tl("light.settings")}</summary>
      <div className="light-fields" style={{ marginTop: 6 }}>
        {field("power_limit_w_m2", tl("light.limit"), "W/m²")}
        {field("hours_default", tl("light.hours"), "h/año")}
        {field("kwh_price", tl("light.price"), "$/kWh")}
        <label style={{ alignContent: "end" }}><span><input type="checkbox" disabled={!canWrite} checked={!!s.auto_luminaire} onChange={(e) => onChange(setSetting(drawing, "auto_luminaire", e.target.checked))} /> {tl("light.auto")}</span></label>
      </div>
      <p className="muted small" style={{ margin: "4px 0 0" }}>{tl("light.settingsHelp")}</p>
    </details>
  );
}

export function RoomTools({ drawing, roomId, activities, canWrite, onChange, onCompare, comparable }: {
  drawing: Drawing; roomId: string; activities: Pick<LightActivity, "id" | "label">[]; canWrite: boolean; onChange: (d: Drawing) => void; onCompare: () => void; comparable: boolean;
}) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const room = (drawing.rooms ?? []).find((r) => r.id === roomId);
  const others = (drawing.rooms ?? []).filter((r) => r.id !== roomId);
  const [picked, setPicked] = useState<string[]>([]);
  const [name, setName] = useState("");
  if (!room || !canWrite) return null;
  const suggested = !room.lighting?.activity && !room.lighting?.exterior ? suggestActivity(room.name, activities) : undefined;
  const templates = Object.keys(settingsOf(drawing).templates ?? {});
  const hasParams = !!room.lighting && Object.keys(room.lighting).length > 0;
  return (
    <div className="row small" style={{ gap: 6, flexWrap: "wrap", margin: "4px 0" }}>
      {suggested && <button onClick={() => onChange({ ...drawing, rooms: drawing.rooms!.map((r) => (r.id === roomId ? { ...r, lighting: { ...(r.lighting ?? {}), activity: suggested } } : r)) })}>{tl("light.suggested")}: {activities.find((a) => a.id === suggested)?.label}</button>}
      {comparable && <button onClick={onCompare}>{tl("light.compare")}</button>}
      {hasParams && others.length > 0 && (
        <details>
          <summary>{tl("light.copyTo")}</summary>
          <div style={{ display: "grid", gap: 2, margin: "4px 0" }}>
            {others.map((o) => <label key={o.id}><input type="checkbox" checked={picked.includes(o.id)} onChange={(e) => setPicked(e.target.checked ? [...picked, o.id] : picked.filter((x) => x !== o.id))} /> {o.name || o.id}</label>)}
            <button disabled={!picked.length} onClick={() => { onChange(copyLighting(drawing, roomId, picked).drawing); setPicked([]); }}>{tl("light.copy")}</button>
          </div>
        </details>
      )}
      <details>
        <summary>{tl("light.templates")}</summary>
        <div style={{ display: "grid", gap: 4, margin: "4px 0" }}>
          {templates.map((n) => (
            <span key={n} className="row" style={{ gap: 4 }}>
              <button onClick={() => onChange(applyTemplate(drawing, roomId, n))}>{n}</button>
              <button onClick={() => onChange(removeTemplate(drawing, n))} aria-label={`${tl("solutions.remove")} ${n}`} title={tl("solutions.remove")}><Icon name="close" size={12} /></button>
            </span>
          ))}
          {hasParams && (
            <span className="row" style={{ gap: 4 }}>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder={tl("light.templateName")} style={{ width: 120 }} />
              <button disabled={!name.trim()} onClick={() => { onChange(saveTemplate(drawing, name, roomId)); setName(""); }}>{tl("light.templateSave")}</button>
            </span>
          )}
          {!templates.length && !hasParams && <span className="muted">{tl("light.templatesNone")}</span>}
        </div>
      </details>
    </div>
  );
}

export function CompareTable({ rows, best, onUse, onClose }: { rows: CompareRow[]; best: string | null; onUse: (id: string) => void; onClose: () => void }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  return (
    <div className="coord-item" style={{ margin: "6px 0" }}>
      <div className="row between"><b>{tl("light.compare")}</b><button onClick={onClose} aria-label={tl("common.close")}><Icon name="close" size={12} /></button></div>
      <table className="table small" style={{ width: "100%" }}>
        <thead><tr><th>{tl("light.luminaire")}</th><th>#</th><th>W</th><th>W/m²</th><th /></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.luminaire}>
              <td>{r.name}{r.luminaire === best && <> <Badge tone="ok">{tl("light.best")}</Badge></>}{r.favorite && " ★"}{!r.complies && <> <Badge tone="bad">{tl("light.notMeets")}</Badge></>}</td>
              <td>{r.installed}</td><td>{r.power_w ?? "–"}</td><td>{r.density_w_m2 ?? "–"}</td>
              <td><button onClick={() => onUse(r.luminaire)}>{tl("light.use")}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted small" style={{ margin: "4px 0 0" }}>{tl("light.compareNote")}</p>
    </div>
  );
}
