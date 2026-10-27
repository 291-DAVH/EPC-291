import { Badge, Icon, Key, State, useApi, useI18n } from "@epc/ui";
import type { PlanPrefs } from "./planPrefs";
import { colorOfDiscipline } from "./planTypes";

/** The drawing layers in force for the project that matter to this sheet: the architecture (one plan, seen in every discipline of the level) and the layers of the discipline being drawn. What each layer is
 *  called and looks like (from the catalog of layers of the company and the project), what the editor draws in it, how many elements the sheet has in it, and a switch to show or hide it. The other
 *  disciplines of the level are not listed by layer: only whether their footprint is shown and a way to open their sheet. */
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
  if (!data.data) return <State loading={data.loading} />;
  const groups = data.data.disciplines;
  const arq = groups.find((g) => g.prefix === "ARQ-");
  const mine = groups.find((g) => g.profile === current);
  const others = groups.filter((g) => g.profile && g.profile !== current);
  const hidden = prefs.hiddenLayers;
  const shown = (name: string) => !hidden.includes(name);
  const setMany = (names: string[], on: boolean) => setPrefs({ hiddenLayers: on ? hidden.filter((n) => !names.includes(n)) : [...new Set([...hidden, ...names])] });
  const table = (g: DisciplineLayers, own: boolean) => (
    <section key={g.id} aria-label={g.name[lang] ?? g.name.es}>
      <div className="row" style={{ justifyContent: "space-between", margin: "8px 0 6px", gap: 6, flexWrap: "wrap" }}>
        <b><i className="disc-dot" style={{ background: g.profile ? colorOfDiscipline(g.profile) : "#9aa3b5" }} /> {g.name[lang] ?? g.name.es}</b>
        <span className="row" style={{ gap: 6 }}>
          <button onClick={() => setMany(g.layers.map((x) => x.name), true)}>{tl("layers.showAll")}</button><button onClick={() => setMany(g.layers.map((x) => x.name), false)}>{tl("layers.hideAll")}</button>
        </span>
      </div>
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
                <td className="mono">{counts[l.name] ?? (own ? 0 : "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
  return (
    <div className="layers">
      {arq && <>{table(arq, false)}<p className="muted small" style={{ margin: "6px 0 0" }}>{tl("layers.archShared")}</p></>}
      {mine ? table(mine, true) : <p className="muted small">{tl("layers.noProfile")}</p>}
      {others.length > 0 && (
        <section aria-label={tl("layers.others")}>
          <h4 className="coord-h">{tl("layers.others")}</h4>
          {others.map((g) => {
            const sheet = sheetOf(g.profile!);
            return (
              <div key={g.id} className="row small" style={{ gap: 8, flexWrap: "wrap", margin: "4px 0", alignItems: "center" }}>
                <i className="disc-dot" style={{ background: colorOfDiscipline(g.profile!) }} /><span style={{ flex: 1, minWidth: 120 }}>{g.name[lang] ?? g.name.es}</span>
                <label className="vp-row"><input type="checkbox" checked={!prefs.hiddenDisc.includes(g.profile!)} onChange={(e) => setPrefs({ hiddenDisc: e.target.checked ? prefs.hiddenDisc.filter((p) => p !== g.profile) : [...prefs.hiddenDisc, g.profile!] })} /> {tl("layers.footprint")}</label>
                <button onClick={() => onOpen(g.profile!)} disabled={!sheet && !canWrite}><Icon name={sheet ? "eye" : "new"} size={14} /> {tl(sheet ? "layers.openSheet" : "layers.createSheet")}</button>
              </div>
            );
          })}
        </section>
      )}
      <p className="muted small" style={{ margin: "8px 0 0" }}>{tl("layers.help")}</p>
    </div>
  );
}
