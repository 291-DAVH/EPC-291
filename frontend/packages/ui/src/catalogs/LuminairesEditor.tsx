import { useEffect, useState } from "react";
import { api, ApiError, JSON_HEADERS, useApi } from "../api";
import { Badge, Page, State } from "../components";
import { Key, useI18n } from "../i18n";

export interface Luminaire { name: { es?: string; en?: string }; kind: "interior" | "exterior"; lamps: number; lamp_flux_lm: number; power_w?: number | null; illustrative?: boolean }
interface LuminairesView { luminaires: Record<string, Luminaire>; own: Record<string, unknown>; default: Record<string, Luminaire>; inherits: string }

const NEW: Luminaire = { name: { es: "", en: "" }, kind: "interior", lamps: 1, lamp_flux_lm: 3000, power_w: null, illustrative: false };
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

/** What a level changes: the entries that differ from what it has now, and `{"disabled": true}` for the ones it took out. The server keeps only what differs from the level below. */
export function changesOf(current: Record<string, Luminaire>, draft: Record<string, Luminaire>): Record<string, unknown> {
  const changes: Record<string, unknown> = {};
  for (const [id, entry] of Object.entries(draft)) if (!same(entry, current[id])) changes[id] = entry;
  for (const id of Object.keys(current)) if (!(id in draft)) changes[id] = { disabled: true };
  return changes;
}

/** The catalogue of luminaires at the level `path` serves (the company's or a project's): the ones the lighting panel offers. Only what differs from the level above is stored; a luminaire of the factory list
 *  can be changed or taken out here without touching the list itself. */
export function LuminairesEditor({ path, bare = false }: { path: string; bare?: boolean }) {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const view = useApi<LuminairesView>(`${path}?rev=${rev}`);
  const [draft, setDraft] = useState<Record<string, Luminaire>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  useEffect(() => { if (view.data) { setDraft(view.data.luminaires); setErrors([]); } }, [view.data]);
  const Wrap = ({ children }: { children: React.ReactNode }) => (bare ? <>{children}</> : <Page title={t("lum.title")} help={t("lum.help")}>{children}</Page>);
  if (!view.data) return <Wrap><State loading={view.loading} error={view.error} /></Wrap>;

  const data = view.data;
  const dirty = !same(draft, data.luminaires);
  const set = (id: string, patch: Partial<Luminaire>) => { setDraft({ ...draft, [id]: { ...draft[id], ...patch } }); setState("idle"); };
  const num = (v: string): number | null => (v.trim() === "" || Number.isNaN(Number(v.replace(",", "."))) ? null : Number(v.replace(",", ".")));
  const send = async (reset: boolean) => {
    setState("saving"); setErrors([]);
    try {
      const v = await api<LuminairesView>(path, reset ? { method: "DELETE" } : { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ luminaires: changesOf(data.luminaires, draft) }) });
      setDraft(v.luminaires); setRev(rev + 1); setState("saved");
    } catch (e) {
      const text = e instanceof ApiError ? Object.values(e.fieldErrors).flatMap((x) => (Array.isArray(x) ? x : [x])).map(String) : [String(e)];
      setErrors(text.length ? text : [String(e)]); setState("idle");
    }
  };
  const add = () => {
    const id = window.prompt(t("lum.newId"))?.trim().toLowerCase().replace(/[^a-z0-9_.-]+/g, "_");
    if (!id || draft[id]) return;
    setDraft({ ...draft, [id]: { ...NEW, name: { es: id, en: id } } }); setState("idle");
  };
  const remove = (id: string) => { if (!window.confirm(t("lum.removeConfirm"))) return; const { [id]: _gone, ...rest } = draft; setDraft(rest); setState("idle"); };
  const own = (id: string) => id in data.own;

  return (
    <Wrap>
      {data.inherits && <p className="muted small">{t(`catalogs.inherits.${data.inherits}` as Key)}</p>}
      <div className="row" style={{ marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
        <button className="primary" disabled={!dirty || state === "saving"} onClick={() => send(false)}>{t("layers.save")}</button>
        <button disabled={!dirty} onClick={() => { setDraft(data.luminaires); setErrors([]); }}>{t("layers.discard")}</button>
        <button onClick={add}>{t("lum.add")}</button>
        <button disabled={Object.keys(data.own).length === 0} onClick={() => { if (window.confirm(t("lum.resetConfirm"))) send(true); }}>{t("layers.reset")}</button>
        {state === "saved" && <Badge tone="ok">{t("layers.saved")}</Badge>}
      </div>
      {errors.length > 0 && <ul className="alert" style={{ margin: "0 0 10px", paddingLeft: 24 }}>{errors.map((e, i) => <li key={i}>{e}</li>)}</ul>}
      <table className="table">
        <thead><tr><th>ID</th><th>ES</th><th>EN</th><th>{t("lum.kind")}</th><th>{t("lum.lamps")}</th><th>{t("lum.flux")}</th><th>{t("lum.power")}</th><th>{t("lum.typical")}</th><th /></tr></thead>
        <tbody>
          {Object.entries(draft).map(([id, e]) => (
            <tr key={id}>
              <td><b>{id}</b>{own(id) && <> <Badge tone="warn">{t("lum.changed")}</Badge></>}</td>
              <td><input value={e.name?.es ?? ""} onChange={(ev) => set(id, { name: { ...e.name, es: ev.target.value } })} aria-label={`${id} ES`} /></td>
              <td><input value={e.name?.en ?? ""} onChange={(ev) => set(id, { name: { ...e.name, en: ev.target.value } })} aria-label={`${id} EN`} /></td>
              <td><select value={e.kind} onChange={(ev) => set(id, { kind: ev.target.value === "exterior" ? "exterior" : "interior" })} aria-label={`${id} ${t("lum.kind")}`}>
                <option value="interior">{t("lum.interior")}</option><option value="exterior">{t("lum.exterior")}</option></select></td>
              <td><input style={{ width: 56 }} inputMode="numeric" defaultValue={e.lamps} key={`l${id}${e.lamps}`} onBlur={(ev) => { const n = num(ev.target.value); if (n !== null) set(id, { lamps: n }); }} aria-label={`${id} ${t("lum.lamps")}`} /></td>
              <td><input style={{ width: 80 }} inputMode="decimal" defaultValue={e.lamp_flux_lm} key={`f${id}${e.lamp_flux_lm}`} onBlur={(ev) => { const n = num(ev.target.value); if (n !== null) set(id, { lamp_flux_lm: n }); }} aria-label={`${id} ${t("lum.flux")}`} /></td>
              <td><input style={{ width: 70 }} inputMode="decimal" defaultValue={e.power_w ?? ""} key={`p${id}${e.power_w ?? ""}`} onBlur={(ev) => set(id, { power_w: num(ev.target.value) })} aria-label={`${id} ${t("lum.power")}`} /></td>
              <td><input type="checkbox" checked={!!e.illustrative} onChange={(ev) => set(id, { illustrative: ev.target.checked })} aria-label={`${id} ${t("lum.typical")}`} /></td>
              <td><button onClick={() => remove(id)}>{t("solutions.remove")}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Wrap>
  );
}
