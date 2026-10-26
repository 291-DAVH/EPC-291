import { useEffect, useRef, useState } from "react";
import { api, Badge, errorText, JSON_HEADERS, Key, State, useApi, useI18n } from "@epc/ui";
import PlanEditor, { Derived, Profile } from "./PlanEditor";
import { BoardCircuit, Circuits, Properties } from "./PlanPanels";
import { blank, Drawing, nextLevel, Ref } from "./planEditing";

interface Overview { levels: { level: string; nodes: number; lines: number; underlay: boolean; has_files: boolean }[]; profiles: Profile[]; circuits: BoardCircuit[]; dxf_versions: string[]; default_dxf_version: string }
interface LevelView { level: string; saved: boolean; drawing: Drawing; result: Derived | null; underlay: { kind: string; version: number } | null; files: { dxf?: string; pdf?: string; dxf_version?: string } | null; generated_at?: string }

/** Layout of the routes over the architectural plan: one drawing per level (L0 ground, L1.. up, L-1.. down), the tables the engine derives from it, and the DXF and PDF. */
export default function Layout({ client, code, canWrite }: { client: string; code: string; canWrite: boolean }) {
  const { t, lang } = useI18n();
  const tl = (k: string) => t(k as Key);
  const root = `/projects/${client}/${code}/layout`;
  const [rev, setRev] = useState(0);
  const ov = useApi<Overview>(`${root}?r=${rev}`);
  const [level, setLevel] = useState("");
  const [lv, setLv] = useState<LevelView | null>(null);
  const [drawing, setDrawing] = useState<Drawing>(blank());
  const [derived, setDerived] = useState<Derived | null>(null);
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [err, setErr] = useState("");
  const [version, setVersion] = useState("");
  const [busy, setBusy] = useState(false);
  const [selection, setSelection] = useState<Ref[]>([]);
  const [focus, setFocus] = useState("");               // the circuit whose route is highlighted
  const [stale, setStale] = useState(false);          // the drawing changed after the files were made
  const timer = useRef<number | null>(null);
  const [stamp, setStamp] = useState(0);                 // bumps the underlay URL after an upload

  const levels = ov.data?.levels.map((x) => x.level) ?? [];
  useEffect(() => { if (ov.data && !level) setLevel(ov.data.levels[0]?.level ?? ""); }, [ov.data]);
  useEffect(() => {
    if (!level) { setLv(null); setDrawing(blank()); setDerived(null); return; }
    let live = true;
    api<LevelView>(`${root}/${level}`).then((v) => { if (live) { setLv(v); setDrawing(v.drawing); setDerived(v.result); setSelection([]); setFocus(""); setState("idle"); setStale(false); setErr(""); } }).catch((x) => live && setErr(errorText(x)));
    return () => { live = false; };
  }, [level, root]);

  const profile = ov.data?.profiles.find((p) => p.id === drawing.discipline);
  const send = async (next: Drawing) => {
    setState("saving");
    try { const v = await api<LevelView>(`${root}/${level}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(next) }); setLv(v); setDerived(v.result); setState("saved"); setErr(""); setRev((n) => n + 1); }
    catch (x) { setState("error"); setErr(errorText(x)); }
  };
  const change = (next: Drawing) => {
    setDrawing(next);
    setStale(true);
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => send(next), 700);                    // saved a moment after the last change
  };
  const createLevel = async (name: string) => {
    try { await api(`${root}/${name}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(blank()) }); setRev((n) => n + 1); setLevel(name); } catch (x) { setErr(errorText(x)); }
  };
  const deleteLevel = async () => {
    if (!window.confirm(tl("layout.confirmDelete"))) return;
    try { await api(`${root}/${level}`, { method: "DELETE" }); const rest = levels.filter((x) => x !== level); setLevel(rest[0] ?? ""); setRev((n) => n + 1); } catch (x) { setErr(errorText(x)); }
  };
  const upload = async (file?: File) => {
    if (!file) return;
    setBusy(true);
    const body = new FormData();
    body.append("file", file);
    try { const v = await api<LevelView>(`${root}/${level}/underlay`, { method: "POST", body }); setLv(v); setStamp((n) => n + 1); setErr(""); setRev((n) => n + 1); } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };
  const generate = async () => {
    setBusy(true);
    if (timer.current) { window.clearTimeout(timer.current); timer.current = null; await send(drawing); }       // what is on the screen is what gets drawn
    try { const v = await api<LevelView>(`${root}/${level}/generate${version ? `?version=${version}` : ""}`, { method: "POST" }); setLv(v); setDerived(v.result); setStale(false); setErr(""); } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };

  if (ov.error) return <div className="state err">{ov.error}</div>;
  if (!ov.data) return <State loading={ov.loading} />;
  const d = derived;
  const download = (name?: string) => (name ? `/api/projects/${client}/${code}/layout/${level}/files/${name}` : "");

  return (
    <div className="grid" style={{ gap: 12 }}>
      <div className="card">
        <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
          <b>{tl("layout.level")}</b>
          {levels.map((x) => <button key={x} className={x === level ? "primary" : ""} onClick={() => setLevel(x)}>{x}</button>)}
          {canWrite && (levels.length === 0
            ? <button className="primary" onClick={() => createLevel("L0")}>+ L0</button>
            : <><button onClick={() => createLevel(nextLevel(levels, "up"))}>+ {nextLevel(levels, "up")}</button><button onClick={() => createLevel(nextLevel(levels, "down"))}>+ {nextLevel(levels, "down")}</button></>)}
          {level && canWrite && <button onClick={deleteLevel}>{tl("layout.deleteLevel")}</button>}
          <span style={{ flex: 1 }} />
          {state === "saving" && <span className="muted small">{tl("layout.saving")}</span>}
          {state === "saved" && <span className="muted small">{tl("layout.saved")}</span>}
        </div>
        <p className="muted small" style={{ margin: "6px 0 0" }}>{tl("layout.help")}</p>
        {err && <div className="alert bad small" style={{ marginTop: 6 }}>{err}</div>}
      </div>

      {!level ? <div className="state">{tl("layout.empty")}</div> : (
        <>
          <div className="card">
            <div className="row" style={{ flexWrap: "wrap", gap: 12 }}>
              <label className="row"><span>{tl("layout.discipline")}</span>
                <select value={drawing.discipline} disabled={!canWrite} onChange={(e) => change({ ...drawing, discipline: e.target.value })}>
                  {ov.data.profiles.map((p) => <option key={p.id} value={p.id}>{p.name[lang] ?? p.name.es}</option>)}
                </select></label>
              {canWrite && <label className="row"><span>{tl("layout.underlay")}</span>
                <input type="file" accept=".png,.jpg,.jpeg,.svg,.dxf,.pdf" disabled={busy} onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }} /></label>}
              {!lv?.underlay && <span className="muted small">{tl("layout.noUnderlay")}</span>}
              {drawing.discipline !== "electrica_BT" && (
                <label className="row"><span>{tl("layout.outlet")}</span>
                  <select value={drawing.outlet} disabled={!canWrite} onChange={(e) => change({ ...drawing, outlet: e.target.value })}>
                    <option value="">–</option>{drawing.nodes.map((n) => <option key={n.id} value={n.id}>{d?.nodes?.find((x) => x.id === n.id)?.tag ?? n.id}</option>)}
                  </select>
                  <span>{tl("layout.outletInvert")}</span>
                  <input style={{ width: 80 }} disabled={!canWrite} value={drawing.outlet_invert_m ?? ""} onChange={(e) => change({ ...drawing, outlet_invert_m: e.target.value === "" ? null : parseFloat(e.target.value.replace(",", ".")) })} />
                </label>
              )}
            </div>
          </div>

          <PlanEditor drawing={drawing} onChange={change} derived={d?.ready ? d : null} profile={profile} lang={lang} readOnly={!canWrite}
            underlayUrl={lv?.underlay ? `/api${root}/${level}/underlay?v=${lv.underlay.version}-${stamp}` : null} t={tl}
            selection={selection} onSelect={setSelection} highlight={focus ? d?.circuits?.[focus]?.lines ?? [] : []} />

          <div className="grid" style={{ gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))" }}>
            <Properties drawing={drawing} selection={selection} derived={d?.ready ? d : null} profile={profile} lang={lang} boardCircuits={ov.data.circuits} readOnly={!canWrite} onChange={change} onSelect={setSelection} t={tl} />
            <Circuits drawing={drawing} derived={d?.ready ? d : null} boardCircuits={ov.data.circuits} profile={profile} onSelect={setSelection} readOnly={!canWrite} focus={focus} onFocus={setFocus} onChange={change} t={tl} />
          </div>

          <div className="card">
            <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
              <b>{tl("layout.generate")}</b>
              <label className="row"><span>{tl("layout.dxfVersion")}</span>
                <select value={version} onChange={(e) => setVersion(e.target.value)}>
                  <option value="">{tl("layout.latest")} ({ov.data.default_dxf_version})</option>
                  {ov.data.dxf_versions.map((v) => <option key={v} value={v}>{v}</option>)}
                </select></label>
              <button className="primary" disabled={busy || !drawing.scale || !canWrite} onClick={generate}>{tl("layout.makeFiles")}</button>
              {lv?.files?.dxf && <a href={download(lv.files.dxf)}>{tl("layout.downloadDxf")} ({lv.files.dxf_version})</a>}
              {lv?.files?.pdf && <a href={download(lv.files.pdf)}>{tl("layout.downloadPdf")}</a>}
              {lv?.files && stale && <Badge tone="warn">{tl("layout.filesOutdated")}</Badge>}
            </div>
            {!drawing.scale && <p className="muted small" style={{ margin: "6px 0 0" }}>{tl("layout.needScale")}</p>}
          </div>

          {d?.ready && d.schedule && (
            <div className="card">
              <b>{tl("layout.schedule")}</b>
              <div className="row small" style={{ flexWrap: "wrap", gap: 16, margin: "6px 0" }}>
                {Object.entries(d.schedule.lines).filter(([, v]) => v.stretches > 0).map(([kind, v]) => <span key={kind}><b>{kind}</b>: {v.lines} · {v.length_m} m</span>)}
                {Object.entries(d.schedule.nodes).filter(([, n]) => n > 0).map(([kind, n]) => <span key={kind}><b>{kind}</b>: {n}</span>)}
                <span><b>{tl("layout.total")}</b>: {d.schedule.total_length_m} m</span>
              </div>
              {Object.keys(d.schedule.circuit_routes).length > 0 && (
                <table><thead><tr><th>{tl("layout.col.circuit")}</th><th>{tl("layout.col.stretches")}</th><th>{tl("layout.col.length")}</th></tr></thead>
                  <tbody>{Object.entries(d.schedule.circuit_routes).map(([c, r]) => <tr key={c}><td className="mono">{c}</td><td className="mono">{r.stretches.join(", ")}</td><td className="mono">{r.length_m}</td></tr>)}</tbody></table>
              )}
              {d.schedule.containers.length > 0 && (
                <table style={{ marginTop: 8 }}><thead><tr><th>{tl("layout.col.tag")}</th><th>{tl("layout.col.kind")}</th><th>{tl("layout.circuits")}</th><th>{tl("layout.props.cables")}</th></tr></thead>
                  <tbody>{d.schedule.containers.map((c) => <tr key={c.tag}><td className="mono">{c.tag}</td><td>{c.kind}</td><td className="mono">{c.circuits.join(", ")}</td><td className="mono">{c.cables}</td></tr>)}</tbody></table>
              )}
              <table style={{ marginTop: 8 }}>
                <thead><tr><th>{tl("layout.col.tag")}</th><th>{tl("layout.col.kind")}</th><th>{tl("layout.col.from")}</th><th>{tl("layout.col.to")}</th><th>{tl("layout.col.length")}</th><th>{tl("layout.col.circuit")}</th></tr></thead>
                <tbody>
                  {(d.stretches ?? []).map((s) => <tr key={s.tag}><td className="mono">{s.tag}</td><td>{s.kind}</td><td className="mono">{d.nodes?.find((n) => n.id === s.from)?.tag}</td><td className="mono">{d.nodes?.find((n) => n.id === s.to)?.tag}</td><td className="mono">{s.length_m}</td><td className="mono">{s.circuit ?? ""}</td></tr>)}
                </tbody>
              </table>
              {d.network && <p className="small muted">{tl("layout.levels")}: {Object.entries(d.network.invert_m).map(([id, v]) => `${d.nodes?.find((n) => n.id === id)?.tag ?? id} ${v}`).join(" · ")}{d.network.validated ? "" : ` (${tl("layout.provisional")})`}</p>}
            </div>
          )}
          {d && d.ready === false && <div className="state">{tl("layout.needScale")}</div>}
          {d?.warnings && d.warnings.length > 0 && (
            <div className="card"><b>{tl("layout.warnings")}</b><ul className="small" style={{ margin: "6px 0 0", paddingLeft: 18 }}>{d.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></div>
          )}
        </>
      )}
    </div>
  );
}
