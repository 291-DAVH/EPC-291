import { useEffect, useState } from "react";
import { api, ApiError, JSON_HEADERS, LayerAttrs, LayersView, useApi } from "../api";
import { Badge, Page, State } from "../components";
import { Key, useI18n } from "../i18n";

/** The standard AutoCAD colour index as a CSS colour: 1-9 are the named ones, 10-249 are 24 hues in 10 shades, 250-255 are greys. An approximation to see what is chosen. */
function aci(n: number): string {
  const named = ["#ff0000", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ff00ff", "#ffffff", "#808080", "#c0c0c0"];
  if (n >= 1 && n <= 9) return named[n - 1];
  if (n >= 250 && n <= 255) return `hsl(0 0% ${20 + (n - 250) * 12}%)`;
  if (n < 10 || n > 249) return "transparent";
  const hue = Math.floor((n - 10) / 10) * 15, shade = (n - 10) % 10;
  const light = [50, 70, 40, 60, 30, 50, 25, 40, 20, 30][shade], sat = shade % 2 === 0 ? 100 : 50;
  return `hsl(${hue} ${sat}% ${light}%)`;
}

const FLAGS = ["on", "frozen", "locked", "plot"] as const;

/** The catalog of DXF layers every drawing is delivered with, at the level `path` serves (the MASTER's, the company's or a project's): names, colours and weights changed here reach the next DXF.
 *  Only what differs from the level above is stored; the level above is shown as the base to go back to. */
export function LayersEditor({ path, bare = false }: { path: string; bare?: boolean }) {
  const { t, lang } = useI18n();
  const [rev, setRev] = useState(0);
  const view = useApi<LayersView>(`${path}?rev=${rev}`);
  const [draft, setDraft] = useState<Record<string, LayerAttrs>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  useEffect(() => { if (view.data) { setDraft(view.data.layers); setErrors({}); } }, [view.data]);
  const Wrap = ({ children }: { children: React.ReactNode }) => (bare ? <>{children}</> : <Page title={t("layers.title")} help={t("layers.help")}>{children}</Page>);
  if (!view.data) return <Wrap><State loading={view.loading} error={view.error} /></Wrap>;

  const base = view.data.default, opts = view.data.options;
  const dirty = JSON.stringify(draft) !== JSON.stringify(view.data.layers);
  const differs = (role: string) => JSON.stringify({ ...draft[role], description: 0 }) !== JSON.stringify({ ...base[role], description: 0 });
  const set = (role: string, patch: Partial<LayerAttrs>) => { setDraft({ ...draft, [role]: { ...draft[role], ...patch } }); setState("idle"); };
  const send = async (reset: boolean) => {
    setState("saving"); setErrors({});
    try {
      const v = await api<LayersView>(path, reset ? { method: "DELETE" } : { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ layers: draft }) });
      setDraft(v.layers); setRev(rev + 1); setState("saved");
    } catch (e) {
      setErrors(e instanceof ApiError ? e.fieldErrors : {}); setState("idle");
    }
  };
  const groups = ["sld", "plan"].map((g) => ({ g, roles: Object.keys(draft).filter((r) => r.startsWith(g + ".")) }));
  const err = (role: string) => Object.entries(errors).filter(([k]) => k.startsWith(role + ".")).map(([k, v]) => `${k.slice(role.length + 1)}: ${v}`).join(" · ");

  return (
    <Wrap>
      {view.data.inherits && <p className="muted small">{t(`catalogs.inherits.${view.data.inherits}` as Key)}</p>}
      <div className="row" style={{ marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
        <button className="primary" disabled={!dirty || state === "saving"} onClick={() => send(false)}>{t("layers.save")}</button>
        <button disabled={!dirty} onClick={() => { setDraft(view.data!.layers); setErrors({}); }}>{t("layers.discard")}</button>
        <button disabled={view.data.changed.length === 0 || state === "saving"} onClick={() => { if (window.confirm(t("layers.resetConfirm"))) send(true); }}>{t("layers.reset")}</button>
        {state === "saved" && <Badge tone="ok">{t("layers.saved")}</Badge>}
        {Object.keys(errors).length > 0 && <Badge tone="bad">{t("layers.refused")}</Badge>}
      </div>
      {groups.map(({ g, roles }) => (
        <div key={g} className="card" style={{ marginBottom: 12 }}>
          <h2 style={{ marginTop: 0 }}>{t(`layers.group.${g}` as Key)}</h2>
          <div style={{ overflowX: "auto" }}>
            <table className="sldtable">
              <thead><tr>{(["layers.col.role", "layers.col.name", "layers.col.color", "layers.col.weight", "layers.col.linetype", "layers.col.on", "layers.col.frozen", "layers.col.locked", "layers.col.plot"] as Key[]).map((h) => <th key={h}>{t(h)}</th>)}<th /></tr></thead>
              <tbody>
                {roles.map((role) => {
                  const a = draft[role];
                  return (
                    <tr key={role} title={err(role)}>
                      <td><div><b>{role.slice(g.length + 1)}</b></div><div className="muted small">{a.description?.[lang] ?? a.description?.es ?? ""}</div></td>
                      <td><input value={a.name} onChange={(e) => set(role, { name: e.target.value })} style={{ width: 170 }} aria-label={t("layers.col.name")} /></td>
                      <td style={{ whiteSpace: "nowrap" }}>
                        <span style={{ display: "inline-block", width: 14, height: 14, border: "1px solid #999", background: aci(a.color), verticalAlign: "middle", marginRight: 4 }} />
                        <input type="number" min={1} max={255} value={a.color} onChange={(e) => set(role, { color: Number(e.target.value) })} style={{ width: 64 }} aria-label={t("layers.col.color")} />
                      </td>
                      <td>
                        <select value={a.lineweight ?? ""} onChange={(e) => set(role, { lineweight: e.target.value === "" ? null : Number(e.target.value) })} aria-label={t("layers.col.weight")}>
                          <option value="">{t("layers.weightDefault")}</option>
                          {opts.lineweights.map((w) => <option key={w} value={w}>{w.toFixed(2)} mm</option>)}
                        </select>
                      </td>
                      <td><select value={a.linetype} onChange={(e) => set(role, { linetype: e.target.value })} aria-label={t("layers.col.linetype")}>{opts.linetypes.map((l) => <option key={l}>{l}</option>)}</select></td>
                      {FLAGS.map((f) => <td key={f}><input type="checkbox" checked={a[f]} onChange={(e) => set(role, { [f]: e.target.checked })} aria-label={t(`layers.col.${f}` as Key)} /></td>)}
                      <td style={{ whiteSpace: "nowrap" }}>
                        {differs(role) && <><Badge tone="warn">{t("layers.changed")}</Badge>{" "}<button onClick={() => set(role, { ...base[role] })} title={t("layers.restore")}>↺</button></>}
                        {err(role) && <div style={{ color: "var(--bad, #d62728)" }} className="small">{err(role)}</div>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </Wrap>
  );
}
