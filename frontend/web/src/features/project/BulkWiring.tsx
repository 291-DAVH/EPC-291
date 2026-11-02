import { useState } from "react";
import { Key, WiringDefaults, useI18n } from "@epc/ui";

export interface WiringPatch { method?: string; insulation?: string; material?: string }
export const KEEP = "__keep";

/** What to write on the selected circuits: only the fields the person changed (an empty value is "the project criteria"). */
export const patchOf = (method: string, insulation: string, material: string): WiringPatch => ({
  ...(method === KEEP ? {} : { method }), ...(insulation === KEEP ? {} : { insulation }), ...(material === KEEP ? {} : { material }),
});

interface Props { count: number; methods: string[]; insulations: string[]; materials: string[]; defaults?: WiringDefaults; busy: boolean; onApply: (patch: WiringPatch) => void; onClear: () => void }

/** The way several circuits are installed and wired, changed at once (for example every luminaire of a level): the conduit or tray, the insulation and the conductor. */
export default function BulkWiring({ count, methods, insulations, materials, defaults, busy, onApply, onClear }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const [method, setMethod] = useState(KEEP);
  const [insulation, setInsulation] = useState(KEEP);
  const [material, setMaterial] = useState(KEEP);
  const field = (label: string, value: string, set: (v: string) => void, items: string[], show: (v: string) => string, byDefault?: string) => (
    <label className="field"><span>{label}</span>
      <select value={value} onChange={(e) => set(e.target.value)}>
        <option value={KEEP}>{tl("bulk.keep")}</option>
        <option value="">{tl("sld.byCriteria")}{byDefault ? ` (${show(byDefault)})` : ""}</option>
        {items.map((x) => <option key={x} value={x}>{show(x)}</option>)}
      </select>
    </label>
  );
  const patch = patchOf(method, insulation, material);
  return (
    <div className="card" role="group" aria-label={tl("bulk.title")} style={{ margin: "8px 0", background: "var(--bg-soft, transparent)" }}>
      <p className="small" style={{ margin: "0 0 6px" }}><b>{tl("bulk.title").replace("{n}", String(count))}</b></p>
      <div className="fgrid">
        {field(tl("sld.install"), method, setMethod, methods, (m) => `${m} · ${tl("sld.method." + m)}`, defaults?.method)}
        {field(tl("sld.insulation"), insulation, setInsulation, insulations, (m) => m.toUpperCase(), defaults?.insulation)}
        {field(tl("sld.conductor"), material, setMaterial, materials, (m) => tl("sld.material." + m), defaults?.material)}
      </div>
      <div className="row" style={{ gap: 8, marginTop: 8 }}>
        <button className="primary" disabled={busy || Object.keys(patch).length === 0} onClick={() => onApply(patch)}>{tl("bulk.apply")}</button>
        <button onClick={onClear}>{tl("bulk.clear")}</button>
      </div>
    </div>
  );
}
