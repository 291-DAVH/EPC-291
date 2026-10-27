import { useEffect, useState } from "react";
import { Badge, Icon, Key, State, useApi, useI18n } from "@epc/ui";
import type { PlanPrefs } from "./planPrefs";
import { colorOfDiscipline } from "./planTypes";

/** The drawing layers in force for the project, one tab per discipline (Electricidad, HVAC, Protección contra incendios...): what each layer is called and looks like (from the catalog of layers of
 *  the company and the project), what the editor draws in it, how many elements the sheet has in it, and a switch to show or hide it. */
export interface LayerKind { profile: string; id: string; type: "line" | "node"; name: { es: string; en: string } }
export interface LayerItem { role: string; name: string; color: number; hex: string; linetype: string; lineweight: number | null; on: boolean; description: { es?: string; en?: string }; kinds: LayerKind[] }
export interface DisciplineLayers { id: string; prefix: string; profile: string | null; name: { es: string; en: string }; drawn: boolean; layers: LayerItem[] }

interface Props {
  client: string; code: string; rev: number; current: string; prefs: PlanPrefs; setPrefs: (p: Partial<PlanPrefs>) => void; counts: Record<string, number>; canWrite: boolean;
  sheetOf: (profile: string) => string | null; onOpen: (profile: string) => void;
}

export default function LayersPanel({ client, code, rev, current, prefs, setPrefs, counts, canWrite, sheetOf, onOpen }: Props) {
  const { t, lang } = useI18n();
  const tl = (k: string) => t(k as Key);
  const data = useApi<{ disciplines: DisciplineLayers[] }>(`/projects/${client}/${code}/layout-layers?r=${rev}`);
  const groups = data.data?.disciplines ?? [];
  const [tab, setTab] = useState("");
  useEffect(() => { if (!tab && groups.length) setTab(groups.find((g) => g.profile === current)?.id ?? groups.find((g) => g.layers.length)?.id ?? groups[0].id); }, [groups.length, current]);
  useEffect(() => { const g = groups.find((x) => x.profile === current); if (g) setTab(g.id); }, [current]);
  if (!data.data) return <State loading={data.loading} />;
  const g = groups.find((x) => x.id === tab) ?? groups[0];
  const hidden = prefs.hiddenLayers;
  const shown = (name: string) => !hidden.includes(name);
  const setMany = (names: string[], on: boolean) => setPrefs({ hiddenLayers: on ? hidden.filter((n) => !names.includes(n)) : [...new Set([...hidden, ...names])] });
  const names = g.layers.map((x) => x.name);
  const mine = g.profile === current;
  const footprintShown = !!g.profile && !prefs.hiddenDisc.includes(g.profile);
  const sheet = g.profile ? sheetOf(g.profile) : null;
  return (
    <div className="layers">
      <div className="wb-tabs sub" role="tablist" aria-label={tl("layers.disciplines")}>
        {groups.map((x) => {
          const off = x.layers.length > 0 && x.layers.every((l) => hidden.includes(l.name));
          return <button key={x.id} role="tab" aria-selected={tab === x.id} className={tab === x.id ? "on" : ""} onClick={() => setTab(x.id)} title={x.name[lang] ?? x.name.es}>
            <i className="disc-dot" style={{ background: x.profile ? colorOfDiscipline(x.profile) : "#9aa3b5", opacity: off ? 0.3 : 1 }} />{x.name[lang] ?? x.name.es}</button>;
        })}
      </div>
      <div className="row" style={{ justifyContent: "space-between", margin: "6px 0", gap: 6, flexWrap: "wrap" }}>
        <b>{g.name[lang] ?? g.name.es}</b>
        <span className="row" style={{ gap: 6 }}>
          <button onClick={() => setMany(names, true)}>{tl("layers.showAll")}</button><button onClick={() => setMany(names, false)}>{tl("layers.hideAll")}</button>
        </span>
      </div>
      {g.profile ? (
        <div className="row small" style={{ gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
          {mine ? <Badge tone="ok">{tl("layers.thisSheet")}</Badge> : <>
            <button onClick={() => onOpen(g.profile!)} disabled={!sheet && !canWrite}><Icon name={sheet ? "eye" : "new"} size={14} /> {tl(sheet ? "layers.openSheet" : "layers.createSheet")}</button>
            <label className="vp-row"><input type="checkbox" checked={footprintShown} onChange={(e) => setPrefs({ hiddenDisc: e.target.checked ? prefs.hiddenDisc.filter((p) => p !== g.profile) : [...prefs.hiddenDisc, g.profile!] })} /> {tl("layers.footprint")}</label></>}
        </div>
      ) : <p className="muted small" style={{ margin: "0 0 6px" }}>{tl("layers.noProfile")}</p>}
      {g.layers.length === 0 ? <div className="state">{tl("layers.none")}</div> : (
        <table className="layer-table">
          <thead><tr><th /><th>{tl("layers.name")}</th><th>{tl("layers.draws")}</th><th>{tl("layers.count")}</th></tr></thead>
          <tbody>
            {g.layers.map((l) => (
              <tr key={l.role} className={shown(l.name) ? "" : "off"}>
                <td><input type="checkbox" aria-label={`${tl("layers.show")} ${l.name}`} checked={shown(l.name)} onChange={(e) => setMany([l.name], e.target.checked)} /></td>
                <td title={l.description[lang] ?? l.description.es}><i className="layer-swatch" style={{ background: l.hex }} /><b className="mono">{l.name}</b><div className="muted small">{l.description[lang] ?? l.description.es}</div>
                  <div className="muted small mono">{l.linetype}{l.lineweight !== null ? ` · ${l.lineweight} mm` : ""}{l.on ? "" : ` · ${tl("layers.off")}`}</div></td>
                <td className="small">{l.kinds.length ? l.kinds.map((k) => <span key={k.profile + k.id} className="kind-chip" title={k.name[lang] ?? k.name.es}>{k.id}</span>) : <span className="muted">–</span>}</td>
                <td className="mono">{counts[l.name] ?? (mine ? 0 : "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="muted small" style={{ margin: "8px 0 0" }}>{tl("layers.help")}</p>
    </div>
  );
}
