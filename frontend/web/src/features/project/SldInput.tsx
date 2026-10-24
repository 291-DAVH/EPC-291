import { ReactNode, useEffect, useRef, useState } from "react";
import { ApiError, Badge, CalcView, CalculationTable, Key, SldCircuit, SldData, SldStatus, SldView, State, api, useApi, useI18n } from "@epc/ui";

const blankCircuit = (): SldCircuit => ({
  tag: "", description: "", load: null, unit: "kW", destination: "", parent_tag: "", topology: "single", phase: "3F",
  length_m: 0, fp: null, efficiency: null, kind: "auto", notes: "", cable_type: "tetra_sep",
});
const num = (v: string): number | null => (v.trim() === "" ? null : Number(v.replace(",", ".")));
const json = { "Content-Type": "application/json" };

/** Data that feeds the single-line diagram. The sld plugin generator runs on it unchanged and its outputs land in the Files tab. */
export default function SldInput({ client, code, onOpenFiles }: { client: string; code: string; onOpenFiles: () => void }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/sld`;
  const view = useApi<SldView>(base);
  const [data, setData] = useState<SldData | null>(null);
  const [dirty, setDirty] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<SldStatus | null>(null);
  const calc = useApi<CalcView>(`${base}/calculation?s=${status?.finished ?? ""}`);
  const [msg, setMsg] = useState("");
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (view.data) {
      setData((d) => d ?? view.data!.input);
      setStatus((s) => s ?? view.data!.status);
    }
  }, [view.data]);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  useEffect(() => {
    if (view.data?.status.state === "running") poll();
  }, [view.data]);                                                      // eslint-disable-line react-hooks/exhaustive-deps

  if (!view.data || !data) return <State loading={view.loading} error={view.error} />;
  const o = view.data.options;

  const set = <K extends keyof SldData>(k: K, patch: Partial<SldData[K]>) => { setData({ ...data, [k]: { ...(data[k] as object), ...patch } } as SldData); setDirty(true); setMsg(""); };
  const setRow = (i: number, patch: Partial<SldCircuit>) => { setData({ ...data, circuits: data.circuits.map((c, j) => (j === i ? { ...c, ...patch } : c)) }); setDirty(true); setMsg(""); };
  const addRow = () => { setData({ ...data, circuits: [...data.circuits, blankCircuit()] }); setDirty(true); };
  const delRow = (i: number) => { setData({ ...data, circuits: data.circuits.filter((_, j) => j !== i) }); setDirty(true); };

  const fail = (x: unknown) => { if (x instanceof ApiError) setErrors(x.fieldErrors); else setErrors({ error: String(x) }); };
  const save = async (): Promise<boolean> => {
    try {
      await api(base, { method: "PUT", headers: json, body: JSON.stringify(data) });
      setErrors({}); setDirty(false); setMsg(t("sld.saved"));
      return true;
    } catch (x) { fail(x); return false; }
  };
  const poll = () => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(async () => {
      const st = await api<SldStatus>(`${base}/status`);
      setStatus(st);
      if (st.state === "running") poll();
    }, 1500);
  };
  const generate = async (diagrams: "sld" | "mld" = "sld") => {
    if (dirty && !(await save())) return;
    try {
      const st = await api<SldStatus>(`${base}/generate?diagrams=${diagrams}`, { method: "POST" });
      setStatus(st);
      setErrors({});
      poll();
    } catch (x) { fail(x); }
  };
  const loadExample = async () => {
    if (data.circuits.length > 0 && !window.confirm(t("sld.exampleConfirm"))) return;
    const ex = await api<{ board: SldData["board"]; circuits: SldCircuit[] }>(`${base}/example`);
    setData({ ...data, board: { ...data.board, ...ex.board, project: data.board.project || ex.board.project }, circuits: ex.circuits });
    setDirty(true);
  };

  const field = (label: Key, node: ReactNode) => <label className="field"><span>{t(label)}</span>{node}</label>;
  const text = (k: keyof SldData["board"] | keyof SldData["titleblock"], group: "board" | "titleblock", label: Key) =>
    field(label, <input list={group === "titleblock" && ["drawn_by", "checked_by", "approved_by"].includes(k as string) ? "sld-people" : undefined}
      value={String((data[group] as unknown as Record<string, unknown>)[k] ?? "")} onChange={(e) => set(group, { [k]: e.target.value } as never)} />);
  const numeric = (k: keyof SldData["board"], label: Key, step = "any") =>
    field(label, <input type="number" step={step} value={String(data.board[k])} onChange={(e) => set("board", { [k]: Number(e.target.value) } as never)} />);
  const sel = (value: string, items: string[], on: (v: string) => void) => <select value={value} onChange={(e) => on(e.target.value)}>{items.map((x) => <option key={x}>{x}</option>)}</select>;
  const running = status?.state === "running";
  const errList = Object.entries(errors);

  return (
    <div className="grid" style={{ gap: 14 }}>
      <p className="muted small" style={{ margin: 0 }}>{t("sld.help")}</p>
      <div className="alert ok">{t("sld.notCriteria2")}</div>

      <div className="card">
        <h2>{t("sld.board")}</h2>
        <div className="fgrid">
          {text("name", "board", "sld.name")}
          {numeric("voltage_v", "sld.voltage")}
          {field("sld.system", sel(data.board.system, o.systems, (v) => set("board", { system: v })))}
          {numeric("icc_ka", "sld.icc")}
          {numeric("fp_default", "sld.fp", "0.01")}
          {field("sld.freq", sel(String(data.board.frequency_hz), ["50", "60"], (v) => set("board", { frequency_hz: Number(v) })))}
          {text("project", "board", "sld.project")}
          {numeric("feeder_length_m", "sld.feeder")}
        </div>
      </div>

      <div className="card">
        <h2>{t("sld.titleblock")}</h2>
        <datalist id="sld-people">{view.data.people.map((n) => <option key={n} value={n} />)}</datalist>
        <p className="muted small" style={{ margin: "4px 0 0" }}>
          {t("sld.fromData")} · {t("sld.logos")}: {view.data.logos.company ? "✓" : "—"} {t("sld.logoCompany")} · {view.data.logos.client ? "✓" : "—"} {t("sld.logoClient")}
        </p>
        <div className="fgrid">
          {text("company", "titleblock", "sld.company")}{text("company_cuit", "titleblock", "sld.companyCuit")}
          {text("client", "titleblock", "sld.client")}{text("client_cuit", "titleblock", "sld.clientCuit")}
          {text("drawn_by", "titleblock", "sld.drawnBy")}{text("checked_by", "titleblock", "sld.checkedBy")}{text("approved_by", "titleblock", "sld.approvedBy")}
          {text("description", "titleblock", "sld.description")}{text("location", "titleblock", "sld.location")}
          {text("scale", "titleblock", "sld.scale")}{text("revision", "titleblock", "sld.revision")}{text("status", "titleblock", "sld.status")}
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
          <h2 style={{ margin: 0 }}>{t("sld.circuits")} <span className="muted small">({data.circuits.length})</span></h2>
          <div className="row"><button onClick={loadExample}>{t("sld.loadExample")}</button><button onClick={addRow}>+ {t("sld.addRow")}</button></div>
        </div>
        <div style={{ overflowX: "auto", marginTop: 10 }}>
          <table className="sldtable">
            <thead>
              <tr>{(["sld.tag", "sld.desc", "sld.load", "sld.unit", "sld.dest", "sld.parent", "sld.topology", "sld.phase", "sld.length", "sld.fp", "sld.eff", "sld.kind", "sld.cable"] as Key[]).map((h) => <th key={h}>{t(h)}</th>)}<th /></tr>
            </thead>
            <tbody>
              {data.circuits.map((c, i) => (
                <tr key={i}>
                  <td><input className="w-tag" value={c.tag} onChange={(e) => setRow(i, { tag: e.target.value })} aria-label={t("sld.tag")} /></td>
                  <td><input className="w-desc" value={c.description} onChange={(e) => setRow(i, { description: e.target.value })} /></td>
                  <td><input className="w-num" type="number" step="any" value={c.load ?? ""} onChange={(e) => setRow(i, { load: num(e.target.value) })} /></td>
                  <td>{sel(c.unit, o.units, (v) => setRow(i, { unit: v }))}</td>
                  <td><input className="w-desc" value={c.destination} onChange={(e) => setRow(i, { destination: e.target.value })} /></td>
                  <td>
                    <select value={c.parent_tag} onChange={(e) => setRow(i, { parent_tag: e.target.value })}>
                      <option value="">{t("sld.parentRoot")}</option>
                      {data.circuits.filter((p, j) => j !== i && p.tag.trim()).map((p) => <option key={p.tag} value={p.tag}>{p.tag}</option>)}
                    </select>
                  </td>
                  <td>{sel(c.topology, o.topologies, (v) => setRow(i, { topology: v }))}</td>
                  <td>{sel(c.phase, o.phases, (v) => setRow(i, { phase: v }))}</td>
                  <td><input className="w-num" type="number" step="any" value={c.length_m} onChange={(e) => setRow(i, { length_m: Number(e.target.value) })} /></td>
                  <td><input className="w-num" type="number" step="0.01" value={c.fp ?? ""} onChange={(e) => setRow(i, { fp: num(e.target.value) })} /></td>
                  <td><input className="w-num" type="number" step="0.01" value={c.efficiency ?? ""} onChange={(e) => setRow(i, { efficiency: num(e.target.value) })} /></td>
                  <td>{sel(c.kind, o.kinds, (v) => setRow(i, { kind: v }))}</td>
                  <td>{sel(c.cable_type, o.cable_types, (v) => setRow(i, { cable_type: v }))}</td>
                  <td><button onClick={() => delRow(i)} title={t("sld.removeRow")} aria-label={t("sld.removeRow")}>✕</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h2>{t("sld.calc")}</h2>
        <p className="muted small" style={{ margin: "2px 0 8px" }}>{t("sld.calcHelp")}</p>
        {!calc.data || calc.data.rows.length === 0 ? <div className="state">{t("sld.calcNone")}</div> : (
          <>
            <CalculationTable view={calc.data} />
          </>
        )}
      </div>

      <div className="card">
        <div className="row" style={{ flexWrap: "wrap" }}>
          <button onClick={save} disabled={!dirty || running}>{t("sld.save")}</button>
          <button className="primary" onClick={() => generate("sld")} disabled={running || data.circuits.length === 0}>{t("sld.generate")}</button>
          <button onClick={() => generate("mld")} disabled={running || data.circuits.length === 0}>{t("sld.generateMld")}</button>
          {dirty && <span className="muted small">{t("sld.unsaved")}</span>}
          {!dirty && msg && <span className="muted small">{msg}</span>}
        </div>
        {errList.length > 0 && (
          <div><b className="small">{t("sld.errors")}</b><ul className="errlist">{errList.map(([k, v]) => <li key={k}><span className="mono">{k}</span>: {v}</li>)}</ul></div>
        )}
        {status && status.state !== "idle" && (
          <div style={{ marginTop: 12 }}>
            {status.state === "running" && <div className="alert">{t("sld.running")}</div>}
            {status.state === "failed" && <div className="alert bad"><b>{t("sld.failed")}</b><pre className="eng-text" style={{ padding: 0 }}>{status.error}</pre></div>}
            {status.state === "done" && (
              <>
                <div className="alert ok">{t("sld.done")} <button onClick={onOpenFiles} style={{ marginLeft: 8 }}>{t("sld.openFiles")}</button></div>
                <div className="muted small" style={{ marginTop: 6 }}>{t("sld.outputs")}: {status.outputs.map((f) => <Badge key={f}>{f.split("/").pop()}</Badge>)}</div>
              </>
            )}
            {status.log.filter((l) => l.startsWith("AVISO")).length > 0 && <div className="muted small" style={{ marginTop: 6 }}><b>{t("sld.log")}</b>: {status.log.filter((l) => l.startsWith("AVISO")).join(" · ")}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
