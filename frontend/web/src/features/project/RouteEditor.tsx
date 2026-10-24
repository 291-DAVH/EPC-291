import { useEffect, useRef } from "react";
import { Key, SldSegment, useI18n } from "@epc/ui";

const BURIED = ["buried_direct", "buried_duct", "road_crossing"];
const blank = (kind: string, length: number): SldSegment => ({ kind, length_m: length, label: "", ambient_c: null, soil_c: null, rho_kmw: null, circuits: 1, depth_m: BURIED.includes(kind) ? (kind === "road_crossing" ? 1 : 0.7) : null });
const num = (v: string): number | null => (v.trim() === "" ? null : Number(v.replace(",", ".")));

/** The real route of a cable, stretch by stretch: how it is installed in each one (tray, pass chamber, buried, duct, road crossing...) decides its capacity. */
export default function RouteEditor({ tag, route, kinds, fallbackLength, onChange, onClose }:
  { tag: string; route: SldSegment[]; kinds: string[]; fallbackLength: number; onChange: (r: SldSegment[]) => void; onClose: () => void }) {
  const { t } = useI18n();
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => { box.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [tag]);          // the editor opens below a long table: bring it into view
  const set = (i: number, patch: Partial<SldSegment>) => onChange(route.map((s, j) => (j === i ? { ...s, ...patch } : s)));
  const move = (i: number, d: number) => { const r = [...route]; const k = i + d; if (k < 0 || k >= r.length) return; [r[i], r[k]] = [r[k], r[i]]; onChange(r); };
  const total = route.reduce((a, s) => a + (Number(s.length_m) || 0), 0);
  const kindSel = (v: string, on: (k: string) => void) => <select value={v} onChange={(e) => on(e.target.value)}>{kinds.map((k) => <option key={k} value={k}>{t(("route.k." + k) as Key)}</option>)}</select>;
  return (
    <div className="card" ref={box} style={{ borderColor: "var(--accent)" }}>
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>{t("route.title")} · <span className="mono">{tag || "—"}</span></h3>
        <button onClick={onClose}>{t("route.close")}</button>
      </div>
      <p className="muted small" style={{ margin: "4px 0 8px" }}>{t("route.help")}</p>
      {route.length === 0 && (
        <div className="row" style={{ marginBottom: 8 }}>
          <span className="small muted">{t("route.start")}</span>
          {["tray_perforated", "buried_direct", "buried_duct"].filter((k) => kinds.includes(k)).map((k) => <button key={k} onClick={() => onChange([blank(k, fallbackLength || 10)])}>{t(("route.k." + k) as Key)}</button>)}
        </div>
      )}
      {route.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table className="sldtable">
            <thead><tr><th>#</th><th>{t("route.kind")}</th><th>{t("route.label")}</th><th>{t("route.length")}</th><th>{t("route.circuits")}</th><th>{t("route.temp")}</th><th>{t("route.rho")}</th><th>{t("route.depth")}</th><th /></tr></thead>
            <tbody>
              {route.map((s, i) => {
                const buried = BURIED.includes(s.kind);
                return (
                  <tr key={i}>
                    <td className="mono">{i + 1}</td>
                    <td>{kindSel(s.kind, (k) => set(i, { kind: k, depth_m: BURIED.includes(k) ? (s.depth_m ?? (k === "road_crossing" ? 1 : 0.7)) : null }))}</td>
                    <td><input className="w-desc" value={s.label} onChange={(e) => set(i, { label: e.target.value })} placeholder={t("route.labelHint")} /></td>
                    <td><input className="w-num" type="number" step="any" min="0" value={s.length_m} onChange={(e) => set(i, { length_m: Number(e.target.value) })} /></td>
                    <td><input className="w-num" type="number" step="1" min="1" value={s.circuits} onChange={(e) => set(i, { circuits: Math.max(1, Math.round(Number(e.target.value) || 1)) })} /></td>
                    <td>{buried
                      ? <input className="w-num" type="number" step="any" value={s.soil_c ?? ""} placeholder={t("route.project")} onChange={(e) => set(i, { soil_c: num(e.target.value) })} />
                      : <input className="w-num" type="number" step="any" value={s.ambient_c ?? ""} placeholder={t("route.project")} onChange={(e) => set(i, { ambient_c: num(e.target.value) })} />}</td>
                    <td>{buried ? <input className="w-num" type="number" step="any" value={s.rho_kmw ?? ""} placeholder={t("route.project")} onChange={(e) => set(i, { rho_kmw: num(e.target.value) })} /> : ""}</td>
                    <td>{buried ? <input className="w-num" type="number" step="any" value={s.depth_m ?? ""} onChange={(e) => set(i, { depth_m: num(e.target.value) })} /> : ""}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button onClick={() => move(i, -1)} disabled={i === 0} aria-label={t("route.up")} title={t("route.up")}>↑</button>
                      <button onClick={() => move(i, 1)} disabled={i === route.length - 1} aria-label={t("route.down")} title={t("route.down")}>↓</button>
                      <button onClick={() => onChange(route.filter((_, j) => j !== i))} aria-label={t("sld.removeRow")} title={t("sld.removeRow")}>✕</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <div className="row" style={{ marginTop: 8, flexWrap: "wrap" }}>
        <button onClick={() => onChange([...route, blank(route[route.length - 1]?.kind ?? "tray_perforated", 10)])}>+ {t("route.add")}</button>
        {route.length > 0 && <button onClick={() => onChange([])}>{t("route.clear")}</button>}
        {route.length > 0 && <b className="small">{t("route.total")}: {Math.round(total * 100) / 100} m</b>}
      </div>
      <p className="muted small" style={{ margin: "6px 0 0" }}>{t("route.note")}</p>
    </div>
  );
}
