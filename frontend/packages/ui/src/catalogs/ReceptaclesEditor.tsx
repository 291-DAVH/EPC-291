import { useEffect, useState } from "react";
import { api, ApiError, JSON_HEADERS, useApi } from "../api";
import { Badge, Page, State } from "../components";
import { Key, useI18n } from "../i18n";

export interface Receptacle { name: { es?: string; en?: string }; kind: "general" | "special"; poles?: number | null; rated_a?: number | null; power_va?: number | null; height_m?: number | null; ip?: string; illustrative?: boolean }
interface ReceptaclesView { receptacles: Record<string, Receptacle>; own: Record<string, unknown>; default: Record<string, Receptacle>; inherits: string }

const NEW: Receptacle = { name: { es: "", en: "" }, kind: "general", poles: 2, rated_a: 10, power_va: 100, height_m: 0.3, ip: "IP20", illustrative: false };
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

/** What a level changes: the entries that differ from what it has now, and `{"disabled": true}` for the ones it took out. The server keeps only what differs from the level below. */
export function receptacleChanges(current: Record<string, Receptacle>, draft: Record<string, Receptacle>): Record<string, unknown> {
  const changes: Record<string, unknown> = {};
  for (const [id, entry] of Object.entries(draft)) if (!same(entry, current[id])) changes[id] = entry;
  for (const id of Object.keys(current)) if (!(id in draft)) changes[id] = { disabled: true };
  return changes;
}

/** The catalogue of socket outlets at the level `path` serves (the company's or a project's): the ones the receptacles panel offers. Only what differs from the level above is stored; a factory outlet
 *  can be changed or taken out here without touching the list itself. */
export function ReceptaclesEditor({ path, bare = false }: { path: string; bare?: boolean }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const [rev, setRev] = useState(0);
  const view = useApi<ReceptaclesView>(`${path}?rev=${rev}`);
  const [draft, setDraft] = useState<Record<string, Receptacle>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  useEffect(() => { if (view.data) { setDraft(view.data.receptacles); setErrors([]); } }, [view.data]);
  const Wrap = ({ children }: { children: React.ReactNode }) => (bare ? <>{children}</> : <Page title={tl("rec.title")} help={tl("rec.catalogHelp")}>{children}</Page>);
  if (!view.data) return <Wrap><State loading={view.loading} error={view.error} /></Wrap>;

  const data = view.data;
  const dirty = !same(draft, data.receptacles);
  const set = (id: string, patch: Partial<Receptacle>) => { setDraft({ ...draft, [id]: { ...draft[id], ...patch } }); setState("idle"); };
  const num = (v: string): number | null => (v.trim() === "" || Number.isNaN(Number(v.replace(",", "."))) ? null : Number(v.replace(",", ".")));
  const send = async (reset: boolean) => {
    setState("saving"); setErrors([]);
    try {
      const v = await api<ReceptaclesView>(path, reset ? { method: "DELETE" } : { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ receptacles: receptacleChanges(data.receptacles, draft) }) });
      setDraft(v.receptacles); setRev(rev + 1); setState("saved");
    } catch (e) {
      const text = e instanceof ApiError ? Object.values(e.fieldErrors).flatMap((x) => (Array.isArray(x) ? x : [x])).map(String) : [String(e)];
      setErrors(text.length ? text : [String(e)]); setState("idle");
    }
  };
  const askId = (): string | undefined => {
    const id = window.prompt(tl("rec.newId"))?.trim().toLowerCase().replace(/[^a-z0-9_.-]+/g, "_");
    return id && !draft[id] ? id : undefined;
  };
  const add = () => { const id = askId(); if (id) { setDraft({ ...draft, [id]: { ...NEW, name: { es: id, en: id } } }); setState("idle"); } };
  const duplicate = (from: string) => {
    const id = askId();
    if (id) { setDraft({ ...draft, [id]: { ...draft[from], name: { es: `${draft[from].name?.es ?? from} (copia)`, en: `${draft[from].name?.en ?? from} (copy)` }, illustrative: false } }); setState("idle"); }
  };
  const remove = (id: string) => { if (!window.confirm(tl("rec.removeConfirm"))) return; const { [id]: _gone, ...rest } = draft; setDraft(rest); setState("idle"); };
  const ids = Object.keys(draft).sort();

  return (
    <Wrap>
      {data.inherits && <p className="muted small">{t(`catalogs.inherits.${data.inherits}` as Key)}</p>}
      <div className="row" style={{ marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
        <button className="primary" disabled={!dirty || state === "saving"} onClick={() => send(false)}>{t("layers.save")}</button>
        <button disabled={!dirty} onClick={() => { setDraft(data.receptacles); setErrors([]); }}>{t("layers.discard")}</button>
        <button onClick={add}>{tl("rec.add")}</button>
        <button disabled={Object.keys(data.own).length === 0} onClick={() => { if (window.confirm(tl("rec.resetConfirm"))) send(true); }}>{t("layers.reset")}</button>
        {state === "saved" && <Badge tone="ok">{t("layers.saved")}</Badge>}
      </div>
      {errors.length > 0 && <ul className="alert" style={{ margin: "0 0 10px", paddingLeft: 24 }}>{errors.map((e, i) => <li key={i}>{e}</li>)}</ul>}
      <table className="table">
        <thead><tr><th>ID</th><th>ES</th><th>EN</th><th>{tl("rec.kind")}</th><th>{tl("rec.poles")}</th><th>{tl("rec.rated")}</th><th>{tl("rec.power")}</th><th>{tl("rec.mount")}</th><th>{tl("rec.ip")}</th><th>{tl("rec.typical")}</th><th /></tr></thead>
        <tbody>
          {ids.map((id) => {
            const e = draft[id];
            const field = (key: "poles" | "rated_a" | "power_va" | "height_m", width: number) => (
              <input style={{ width }} inputMode="decimal" defaultValue={e[key] ?? ""} key={`${key}${id}${e[key] ?? ""}`} onBlur={(ev) => set(id, { [key]: num(ev.target.value) })} aria-label={`${id} ${key}`} />
            );
            return (
              <tr key={id}>
                <td><b>{id}</b>{id in data.own && <> <Badge tone="warn">{tl("rec.changed")}</Badge></>}</td>
                <td><input value={e.name?.es ?? ""} onChange={(ev) => set(id, { name: { ...e.name, es: ev.target.value } })} aria-label={`${id} ES`} /></td>
                <td><input value={e.name?.en ?? ""} onChange={(ev) => set(id, { name: { ...e.name, en: ev.target.value } })} aria-label={`${id} EN`} /></td>
                <td><select value={e.kind} onChange={(ev) => set(id, { kind: ev.target.value === "special" ? "special" : "general" })} aria-label={`${id} ${tl("rec.kind")}`}>
                  <option value="general">{tl("rec.general")}</option><option value="special">{tl("rec.special")}</option></select></td>
                <td>{field("poles", 44)}</td><td>{field("rated_a", 56)}</td><td>{field("power_va", 70)}</td><td>{field("height_m", 56)}</td>
                <td><input style={{ width: 64 }} value={e.ip ?? ""} onChange={(ev) => set(id, { ip: ev.target.value })} aria-label={`${id} IP`} /></td>
                <td><input type="checkbox" checked={!!e.illustrative} onChange={(ev) => set(id, { illustrative: ev.target.checked })} aria-label={`${id} ${tl("rec.typical")}`} /></td>
                <td><button onClick={() => duplicate(id)}>{tl("rec.duplicate")}</button> <button onClick={() => remove(id)}>{t("solutions.remove")}</button></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Wrap>
  );
}
