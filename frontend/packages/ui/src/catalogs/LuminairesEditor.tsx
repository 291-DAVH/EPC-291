import { useEffect, useState } from "react";
import { api, ApiError, JSON_HEADERS, useApi } from "../api";
import { Badge, Page, State } from "../components";
import { Key, useI18n } from "../i18n";
import { COLUMNS, parseLuminaires } from "./luminairesCsv";

export interface Luminaire { name: { es?: string; en?: string }; kind: "interior" | "exterior"; lamps: number; lamp_flux_lm: number; power_w?: number | null; power_factor?: number | null; favorite?: boolean; group?: string; illustrative?: boolean }
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

/** The ids of a catalogue that match what was typed (in the id or either name), and the group chosen ("" is every group); favourites first, then by id. */
export function visibleIds(draft: Record<string, Luminaire>, search: string, group: string): string[] {
  const q = search.trim().toLowerCase();
  return Object.keys(draft)
    .filter((id) => (!group || (draft[id].group ?? "") === group) && (!q || [id, draft[id].name?.es ?? "", draft[id].name?.en ?? ""].some((x) => x.toLowerCase().includes(q))))
    .sort((a, b) => Number(!!draft[b].favorite) - Number(!!draft[a].favorite) || a.localeCompare(b));
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
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("");
  const [paste, setPaste] = useState("");
  useEffect(() => { if (view.data) { setDraft(view.data.luminaires); setErrors([]); } }, [view.data]);
  const Wrap = ({ children }: { children: React.ReactNode }) => (bare ? <>{children}</> : <Page title={t("lum.title")} help={t("lum.help")}>{children}</Page>);
  if (!view.data) return <Wrap><State loading={view.loading} error={view.error} /></Wrap>;

  const data = view.data;
  const dirty = !same(draft, data.luminaires);
  const set = (id: string, patch: Partial<Luminaire>) => {
    const next: Record<string, unknown> = { ...draft[id], ...patch };
    for (const k of ["power_factor", "group"]) if (next[k] === null || next[k] === "" || next[k] === undefined) delete next[k];
    if (next.favorite === false) delete next.favorite;
    setDraft({ ...draft, [id]: next as unknown as Luminaire }); setState("idle");
  };
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
  const askId = (): string | undefined => {
    const id = window.prompt(t("lum.newId"))?.trim().toLowerCase().replace(/[^a-z0-9_.-]+/g, "_");
    return id && !draft[id] ? id : undefined;
  };
  const add = () => { const id = askId(); if (id) { setDraft({ ...draft, [id]: { ...NEW, name: { es: id, en: id } } }); setState("idle"); } };
  const duplicate = (from: string) => {
    const id = askId();
    if (!id) return;
    const { favorite: _f, ...rest } = draft[from];
    setDraft({ ...draft, [id]: { ...rest, name: { es: `${draft[from].name?.es ?? from} (copia)`, en: `${draft[from].name?.en ?? from} (copy)` }, illustrative: false } }); setState("idle");
  };
  const remove = (id: string) => { if (!window.confirm(t("lum.removeConfirm"))) return; const { [id]: _gone, ...rest } = draft; setDraft(rest); setState("idle"); };
  const own = (id: string) => id in data.own;
  const importText = (text: string) => {
    const found = parseLuminaires(text);
    setErrors(found.errors.map((e) => `${t("lum.importRow")} ${e}`));
    if (Object.keys(found.entries).length) { setDraft({ ...draft, ...found.entries }); setState("idle"); setPaste(""); }
  };
  const readFile = async (file: File | undefined) => { if (file) importText(await file.text()); };
  const groups = [...new Set(Object.values(draft).map((e) => e.group ?? "").filter(Boolean))].sort();
  const ids = visibleIds(draft, search, group);

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
      <div className="row" style={{ marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
        <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t("lum.search")} aria-label={t("lum.search")} style={{ minWidth: 200 }} />
        <select value={group} onChange={(e) => setGroup(e.target.value)} aria-label={t("lum.group")}>
          <option value="">{t("lum.allGroups")}</option>{groups.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
        <span className="muted small">{ids.length} / {Object.keys(draft).length}</span>
      </div>
      {errors.length > 0 && <ul className="alert" style={{ margin: "0 0 10px", paddingLeft: 24 }}>{errors.map((e, i) => <li key={i}>{e}</li>)}</ul>}
      <table className="table">
        <thead><tr><th /><th>ID</th><th>ES</th><th>EN</th><th>{t("lum.kind")}</th><th>{t("lum.lamps")}</th><th>{t("lum.flux")}</th><th>{t("lum.power")}</th><th>{t("lum.pf")}</th><th>{t("lum.group")}</th><th>{t("lum.typical")}</th><th /></tr></thead>
        <tbody>
          {ids.map((id) => {
            const e = draft[id];
            return (
              <tr key={id}>
                <td><button onClick={() => set(id, { favorite: !e.favorite })} aria-pressed={!!e.favorite} aria-label={`${t("lum.favorite")} ${id}`} title={t("lum.favorite")}>{e.favorite ? "★" : "☆"}</button></td>
                <td><b>{id}</b>{own(id) && <> <Badge tone="warn">{t("lum.changed")}</Badge></>}</td>
                <td><input value={e.name?.es ?? ""} onChange={(ev) => set(id, { name: { ...e.name, es: ev.target.value } })} aria-label={`${id} ES`} /></td>
                <td><input value={e.name?.en ?? ""} onChange={(ev) => set(id, { name: { ...e.name, en: ev.target.value } })} aria-label={`${id} EN`} /></td>
                <td><select value={e.kind} onChange={(ev) => set(id, { kind: ev.target.value === "exterior" ? "exterior" : "interior" })} aria-label={`${id} ${t("lum.kind")}`}>
                  <option value="interior">{t("lum.interior")}</option><option value="exterior">{t("lum.exterior")}</option></select></td>
                <td><input style={{ width: 56 }} inputMode="numeric" defaultValue={e.lamps} key={`l${id}${e.lamps}`} onBlur={(ev) => { const n = num(ev.target.value); if (n !== null) set(id, { lamps: n }); }} aria-label={`${id} ${t("lum.lamps")}`} /></td>
                <td><input style={{ width: 80 }} inputMode="decimal" defaultValue={e.lamp_flux_lm} key={`f${id}${e.lamp_flux_lm}`} onBlur={(ev) => { const n = num(ev.target.value); if (n !== null) set(id, { lamp_flux_lm: n }); }} aria-label={`${id} ${t("lum.flux")}`} /></td>
                <td><input style={{ width: 70 }} inputMode="decimal" defaultValue={e.power_w ?? ""} key={`p${id}${e.power_w ?? ""}`} onBlur={(ev) => set(id, { power_w: num(ev.target.value) })} aria-label={`${id} ${t("lum.power")}`} /></td>
                <td><input style={{ width: 56 }} inputMode="decimal" placeholder="1" defaultValue={e.power_factor ?? ""} key={`q${id}${e.power_factor ?? ""}`} onBlur={(ev) => set(id, { power_factor: num(ev.target.value) })} aria-label={`${id} ${t("lum.pf")}`} /></td>
                <td><input style={{ width: 90 }} list="lum-groups" value={e.group ?? ""} onChange={(ev) => set(id, { group: ev.target.value })} aria-label={`${id} ${t("lum.group")}`} /></td>
                <td><input type="checkbox" checked={!!e.illustrative} onChange={(ev) => set(id, { illustrative: ev.target.checked })} aria-label={`${id} ${t("lum.typical")}`} /></td>
                <td><button onClick={() => duplicate(id)}>{t("lum.duplicate")}</button> <button onClick={() => remove(id)}>{t("solutions.remove")}</button></td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <datalist id="lum-groups">{groups.map((g) => <option key={g} value={g} />)}</datalist>
      <details style={{ marginTop: 12 }}>
        <summary>{t("lum.import")}</summary>
        <p className="muted small">{t("lum.importHelp")} <code>{COLUMNS.join(", ")}</code></p>
        <textarea rows={5} className="mono" value={paste} onChange={(e) => setPaste(e.target.value)} style={{ width: "100%" }} aria-label={t("lum.import")} />
        <div className="row" style={{ gap: 8, marginTop: 6 }}>
          <button disabled={!paste.trim()} onClick={() => importText(paste)}>{t("lum.importPasted")}</button>
          <label className="small">{t("lum.importFile")} <input type="file" accept=".csv,.tsv,.txt,text/csv,text/plain" onChange={(e) => readFile(e.target.files?.[0])} /></label>
        </div>
      </details>
    </Wrap>
  );
}
