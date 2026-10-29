import { ReactNode, useEffect, useRef, useState } from "react";
import BoardMemo from "./BoardMemo";
import FeedersCard from "./FeedersCard";
import RouteEditor from "./RouteEditor";
import { api, ApiError, Badge, BoardMemoView, BoardRow, CALC_HEADS, CalcCells, CalcHeader, CalcView, JSON_HEADERS, Key, LengthInfo, SldCircuit, SldData, SldStatus, SldView, State, WiringDefaults, useApi, useI18n } from "@epc/ui";

/** How a circuit is wired, in a few words: the method of installation, the conductor and the insulation (what it leaves to the design criteria is read from them). */
const wiringOf = (c: SldCircuit, crit?: { material: string; aislacion: string }): string =>
  `${c.method || "–"} · ${(c.material || crit?.material || "").replace(/^./, (x) => x.toUpperCase())} ${(c.insulation || crit?.aislacion || "").toUpperCase()}`.trim();

const blankCircuit = (): SldCircuit => ({
  tag: "", description: "", load: null, unit: "kW", destination: "", parent_tag: "", topology: "single", phase: "3F",
  length_m: 0, length_source: "auto", fp: null, efficiency: null, kind: "auto", notes: "", cable_type: "tetra_sep",
});
interface Editing { index: number | null; draft: SldCircuit }
/** The usual nominal voltages as line / phase pairs (V): a board is typed by its line voltage, the phase voltage is what a single-phase circuit sees. */
const VOLTAGES: [number, number][] = [[380, 220], [400, 230], [220, 127], [440, 254], [690, 400]];
const OTHER_VOLTAGE = "other";
const num = (v: string): number | null => (v.trim() === "" ? null : Number(v.replace(",", ".")));

type Options = SldView["options"];

/** The data cells of a circuit (everything but its length, which the caller draws, and the delete button): the same for a circuit of the board and for the one being added. */
function CircuitInputs({ c, set, parents, o, lengthCell, t, focus, defaults }: { c: SldCircuit; set: (patch: Partial<SldCircuit>) => void; parents: string[]; o: Options; lengthCell: ReactNode; t: (k: Key) => string; focus?: boolean; defaults?: WiringDefaults }) {
  const sel = (value: string, items: string[], on: (v: string) => void) => <select value={value} onChange={(e) => on(e.target.value)}>{items.map((x) => <option key={x}>{x}</option>)}</select>;
  /** A choice that may be left to the design criteria of the project (empty). */
  const pick = (value: string, items: string[], on: (v: string) => void, label: (v: string) => string, byDefault?: string) =>
    <select value={value} onChange={(e) => on(e.target.value)}><option value="">{t("sld.byCriteria")}{byDefault ? ` (${label(byDefault)})` : ""}</option>{items.map((x) => <option key={x} value={x}>{label(x)}</option>)}</select>;
  return (
    <>
      <td><input className="w-tag" value={c.tag} autoFocus={focus} onChange={(e) => set({ tag: e.target.value })} aria-label={t("sld.tag")} /></td>
      <td><input className="w-desc" value={c.description} onChange={(e) => set({ description: e.target.value })} aria-label={t("sld.desc")} /></td>
      <td><input className="w-num" type="number" step="any" value={c.load ?? ""} onChange={(e) => set({ load: num(e.target.value) })} aria-label={t("sld.load")} /></td>
      <td>{sel(c.unit, o.units, (v) => set({ unit: v }))}</td>
      <td><input className="w-desc" value={c.destination} onChange={(e) => set({ destination: e.target.value })} aria-label={t("sld.dest")} /></td>
      <td>
        <select value={c.parent_tag} onChange={(e) => set({ parent_tag: e.target.value })} aria-label={t("sld.parent")}>
          <option value="">{t("sld.parentRoot")}</option>
          {parents.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </td>
      <td>{sel(c.topology, o.topologies, (v) => set({ topology: v }))}</td>
      <td>{sel(c.phase, o.phases, (v) => set({ phase: v }))}</td>
      <td style={{ whiteSpace: "nowrap" }}>{lengthCell}</td>
      <td><input className="w-num" type="number" step="0.01" value={c.fp ?? ""} onChange={(e) => set({ fp: num(e.target.value) })} aria-label={t("sld.fp")} /></td>
      <td><input className="w-num" type="number" step="0.01" value={c.efficiency ?? ""} onChange={(e) => set({ efficiency: num(e.target.value) })} aria-label={t("sld.eff")} /></td>
      <td>{sel(c.kind, o.kinds, (v) => set({ kind: v }))}</td>
      <td>{sel(c.cable_type, o.cable_types, (v) => set({ cable_type: v }))}</td>
      <td>{pick(c.method ?? "", o.methods ?? [], (v) => set({ method: v }), (m) => `${m} · ${t(("sld.method." + m) as Key)}`, defaults?.method)}</td>
      <td>{pick(c.insulation ?? "", o.insulations ?? [], (v) => set({ insulation: v }), (m) => m.toUpperCase(), defaults?.insulation)}</td>
      <td>{pick(c.material ?? "", o.materials ?? [], (v) => set({ material: v }), (m) => t(("sld.material." + m) as Key), defaults?.material)}</td>
    </>
  );
}

/** Under the length of a circuit: where it comes from (plan, data or automatic) and what each one says, so it is clear what the calculation takes. */
function LengthSource({ c, info, sources, onChange, t }: { c: SldCircuit; info?: LengthInfo; sources: string[]; onChange: (v: string) => void; t: (k: Key) => string }) {
  if ((c.route?.length ?? 0) > 0 || !c.tag.trim()) return null;
  const plan = info?.plan_m != null;
  const differs = plan && info!.data_m > 0 && Math.abs(info!.plan_m! - info!.data_m) / info!.data_m > 0.1;
  return (
    <div className="muted small" style={{ marginTop: 3 }}>
      <select value={c.length_source ?? "auto"} onChange={(e) => onChange(e.target.value)} aria-label={t("sld.lenSource")} title={t("sld.lenSource")}>
        {sources.map((s) => <option key={s} value={s}>{t(("sld.len." + s) as Key)}</option>)}
      </select>
      {" "}{info && <Badge tone={info.used === "plan" ? "ok" : undefined}>{t(info.used === "plan" ? "sld.lenUsesPlan" : "sld.lenUsesData")}</Badge>}
      {plan && <div>{t("sld.lenPlan")}: <b className="mono">{info!.plan_m}</b> m{info!.moments ? ` · ${t("sld.lenMoments")}, ${t("sld.lenMax")} ${info!.plan_max_m} m` : ""}</div>}
      {info?.fallback && <div style={{ color: "var(--bad)" }}>{t("sld.lenFallback")}</div>}
      {differs && <div style={{ color: "var(--warn, #b26a00)" }}>{t("sld.lenDiffers")}</div>}
    </div>
  );
}

/** The boards of the project: each one has its own data, calculation and diagrams, and a project can start with one and add others later. */
export default function SldInput({ client, code, onOpenFiles, onOpenParties }: { client: string; code: string; onOpenFiles: () => void; onOpenParties: () => void }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/sld`;
  const [tick, setTick] = useState(0);
  const list = useApi<BoardRow[]>(`${base}/boards?t=${tick}`);
  const [cur, setCur] = useState("");
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", from: "", tag: "" });
  const [err, setErr] = useState("");
  if (!list.data) return <State loading={list.loading} error={list.error} />;
  const boards = list.data;
  const id = boards.some((b) => b.id === cur) ? cur : boards[0]?.id ?? "";
  const add = async () => {
    try {
      const v = await api<SldView>(`${base}/boards`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ name: form.name, supplied_from: form.from, supply_tag: form.tag }) });
      setCur(v.board_id); setAdding(false); setForm({ name: "", from: "", tag: "" }); setErr(""); setTick((n) => n + 1);
    } catch (x) { setErr(x instanceof ApiError ? Object.values(x.fieldErrors).join(" · ") || String(x) : String(x)); }
  };
  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
        <b className="small">{t("sld.boards")}</b>
        {boards.map((b) => (
          <button key={b.id} className={"chip" + (b.id === id ? " on" : "")} style={b.id === id ? { borderColor: "var(--accent)", color: "var(--accent)", fontWeight: 600 } : undefined} onClick={() => { setCur(b.id); setAdding(false); }}>
            {b.name} <span className="muted small">· {b.circuits} {t("calc.circuits")}{b.supplied_from ? ` · ← ${boards.find((x) => x.id === b.supplied_from)?.name ?? b.supplied_from}` : ""}</span>
          </button>
        ))}
        <button onClick={() => { setAdding(!adding); setErr(""); }}>{adding ? t("projects.cancel") : t("sld.addBoard")}</button>
      </div>
      {adding && (
        <div className="card">
          <div className="fgrid">
            <label className="field"><span>{t("sld.name")}</span><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label className="field"><span>{t("sld.suppliedFrom")}</span>
              <select value={form.from} onChange={(e) => setForm({ ...form, from: e.target.value })}><option value="">{t("sld.suppliedNone")}</option>{boards.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select></label>
            {form.from && <label className="field"><span>{t("sld.supplyTag")}</span><input value={form.tag} onChange={(e) => setForm({ ...form, tag: e.target.value })} /></label>}
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            <button className="primary" onClick={add} disabled={!form.name.trim()}>{t("sld.createBoard")}</button>
            {err && <span className="muted small" style={{ color: "var(--bad, #b00020)" }}>{err}</span>}
          </div>
        </div>
      )}
      <BoardEditor key={id} client={client} code={code} board={id} boards={boards} onOpenFiles={onOpenFiles} onOpenParties={onOpenParties}
        onSaved={(bid) => { if (bid !== id) setCur(bid); setTick((n) => n + 1); }}
        onDeleted={() => { setCur(""); setTick((n) => n + 1); }} />
    </div>
  );
}

function BoardEditor({ client, code, board, boards, onOpenFiles, onOpenParties, onSaved, onDeleted }:
  { client: string; code: string; board: string; boards: BoardRow[]; onOpenFiles: () => void; onOpenParties: () => void; onSaved: (id: string) => void; onDeleted: () => void }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/sld`;
  const q = board ? `board=${encodeURIComponent(board)}` : "";
  const view = useApi<SldView>(`${base}?${q}`);
  const [data, setData] = useState<SldData | null>(null);
  const [dirty, setDirty] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<SldStatus | null>(null);
  const memo = useApi<BoardMemoView>(`${base}/memo?${q}&s=${status?.finished ?? ""}`);
  const calc = useApi<CalcView>(`${base}/calculation?${q}&s=${status?.finished ?? ""}`);
  const [msg, setMsg] = useState("");
  const [editing, setEditing] = useState<Editing | null>(null);          // the circuit being added (index null) or edited, in the form under the table
  const [routeOpen, setRouteOpen] = useState(false);                       // its real route is being edited
  const [customVoltage, setCustomVoltage] = useState(false);               // the voltage is typed, not one of the usual pairs
  const timer = useRef<number | undefined>(undefined);

  /** Ask for the status again in a moment while a calculation runs. Declared before the early return below: the effect that resumes a run found at load time uses it. */
  const poll = () => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(async () => {
      const st = await api<SldStatus>(`${base}/status?${q}`);
      setStatus(st);
      if (st.state === "running") poll();
    }, 1500);
  };
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

  const fail = (x: unknown) => { if (x instanceof ApiError) setErrors(x.fieldErrors); else setErrors({ error: String(x) }); };
  const save = async (payload: SldData = data): Promise<boolean> => {
    try {
      const v = await api<SldView>(`${base}?${q}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(payload) });
      setErrors({}); setDirty(false); setMsg(t("sld.saved"));
      onSaved(v.board_id);
      return true;
    } catch (x) { fail(x); return false; }
  };
  const generate = async (diagrams: "sld" | "mld" | "none" = "sld") => {
    if (dirty && !(await save())) return;
    try {
      const st = await api<SldStatus>(`${base}/generate?diagrams=${diagrams}&${q}`, { method: "POST" });
      setStatus(st);
      setErrors({});
      poll();
    } catch (x) { fail(x); }
  };
  /** The calculation alone (sections, protections, drops): no memo, no diagrams. It follows the data that were just saved. */
  const calculate = async (payload: SldData = data) => {
    if (!(await save(payload))) return;
    try {
      const st = await api<SldStatus>(`${base}/generate?diagrams=calc&${q}`, { method: "POST" });
      setStatus(st); setErrors({}); poll();
    } catch (x) { fail(x); }
  };
  const draftSet = (patch: Partial<SldCircuit>) => setEditing((e) => (e ? { ...e, draft: { ...e.draft, ...patch } } : e));
  const closeForm = () => { setEditing(null); setRouteOpen(false); setErrors({}); };
  /** Accept the circuit being typed or edited: it joins the board (or replaces its older self), is saved and calculated at once. */
  const accept = async () => {
    if (!editing) return;
    const tag = editing.draft.tag.trim();
    if (!tag) { setErrors({ tag: t("sld.tagNeeded") }); return; }
    if (data.circuits.some((c, i) => i !== editing.index && c.tag.trim() === tag)) { setErrors({ tag: t("sld.tagTaken") }); return; }
    const circuit = { ...editing.draft, tag };
    const next = { ...data, circuits: editing.index === null ? [...data.circuits, circuit] : data.circuits.map((c, i) => (i === editing.index ? circuit : c)) };
    setData(next); closeForm();
    await calculate(next);
  };
  const removeCircuit = async (i: number) => {
    const next = { ...data, circuits: data.circuits.filter((_, j) => j !== i) };
    setData(next); closeForm();
    if (next.circuits.length) await calculate(next); else { setDirty(true); setMsg(""); }
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
  const memoReady = !!memo.data?.available && !memo.data.stale && !dirty;                // the diagram is drawn only from a memo calculated on the current data
  const errList = Object.entries(errors);
  const hasBoard = data.board.name.trim().length > 0;                                      // a circuit belongs to a board: without one there is nothing to add it to
  const calcOf = new Map((calc.data?.rows ?? []).map((r) => [r.tag, r]));
  const inputTags = new Set(data.circuits.map((c) => c.tag.trim()));
  const extra = (calc.data?.rows ?? []).filter((r) => data.circuits.length > 0 && !inputTags.has(r.tag));              // groups the standard solutions added: calculated, not typed

  const remove = async () => {
    if (!window.confirm(t("sld.deleteConfirm"))) return;
    try { await api(`${base}/boards/${encodeURIComponent(board)}`, { method: "DELETE" }); onDeleted(); } catch (x) { fail(x); }
  };

  return (
    <div className="grid" style={{ gap: 14 }}>
      <p className="muted small" style={{ margin: 0 }}>{t("sld.help")}</p>
      <div className="alert ok">{t("sld.notCriteria2")}</div>

      <div className="card">
        <h2>{t("sld.board")}</h2>
        <div className="fgrid">
          {text("name", "board", "sld.name")}
          {field("sld.voltage", <>
            <select value={VOLTAGES.some(([l]) => l === data.board.voltage_v) && !customVoltage ? String(data.board.voltage_v) : OTHER_VOLTAGE}
              onChange={(e) => { if (e.target.value === OTHER_VOLTAGE) setCustomVoltage(true); else { setCustomVoltage(false); set("board", { voltage_v: Number(e.target.value) }); } }}>
              {VOLTAGES.map(([l, p]) => <option key={l} value={l}>{l} / {p} V</option>)}
              <option value={OTHER_VOLTAGE}>{t("sld.voltageOther")}</option>
            </select>
            {(customVoltage || !VOLTAGES.some(([l]) => l === data.board.voltage_v)) && <input type="number" step="any" value={String(data.board.voltage_v)} onChange={(e) => set("board", { voltage_v: Number(e.target.value) })} aria-label={t("sld.voltage")} />}
          </>)}
          {field("sld.system", sel(data.board.system, o.systems, (v) => set("board", { system: v })))}
          {numeric("icc_ka", "sld.icc")}
          {numeric("fp_default", "sld.fp", "0.01")}
          {field("sld.freq", sel(String(data.board.frequency_hz), ["50", "60"], (v) => set("board", { frequency_hz: Number(v) })))}
          {text("project", "board", "sld.project")}
          {numeric("feeder_length_m", "sld.feeder")}
          {field("sld.suppliedFrom", <select value={data.board.supplied_from} onChange={(e) => set("board", { supplied_from: e.target.value, supply_tag: e.target.value ? data.board.supply_tag : "" })}>
            <option value="">{t("sld.suppliedNone")}</option>{boards.filter((b) => b.id !== board).map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select>)}
          {data.board.supplied_from && text("supply_tag", "board", "sld.supplyTag")}
          {!data.board.supplied_from && field("sld.supplyName", <input maxLength={80} value={data.board.supply_name ?? ""} onChange={(e) => set("board", { supply_name: e.target.value })} placeholder={t("sld.supplyNameHint")} />)}
        </div>
        {board && <div className="row" style={{ marginTop: 8 }}><button onClick={remove}>{t("sld.deleteBoard")}</button></div>}
      </div>

      <FeedersCard feeders={data.feeders ?? []} rows={calc.data?.feeders ?? []} phases={o.phases} methods={o.methods ?? []} insulations={o.insulations ?? []} materials={o.materials ?? []} defaults={view.data.wiring_defaults}
        blocked={!hasBoard ? t("sld.needBoard") : data.circuits.length === 0 ? t("feeder.needCircuits") : ""} busy={running} onChange={(next) => { const nd = { ...data, feeders: next }; setData(nd); calculate(nd); }} />

      <div className="card">
        <h2>{t("sld.titleblock")}</h2>
        {view.data.parties && (
          <p className="small" style={{ margin: "4px 0 8px" }}>
            <b>{t("parties.issuer")}:</b> {view.data.parties.issuer || "—"} · <b>{t("parties.client")}:</b> {view.data.parties.client || "—"} · <b>{t("parties.role.drawn_by")}:</b> {view.data.parties.team.drawn_by || "—"} · <b>{t("parties.role.checked_by")}:</b> {view.data.parties.team.checked_by || "—"} · <b>{t("parties.role.approved_by")}:</b> {view.data.parties.team.approved_by || "—"}
            {" "}<button onClick={onOpenParties}>{t("sld.changeParties")}</button>
          </p>
        )}
        <p className="muted small" style={{ margin: "0 0 4px" }}>{t("sld.logos")}: {view.data.logos.company ? "✓" : "—"} {t("sld.logoCompany")} · {view.data.logos.client ? "✓" : "—"} {t("sld.logoClient")}</p>
        <div className="fgrid">
          {text("description", "titleblock", "sld.description")}{text("location", "titleblock", "sld.location")}
          {text("scale", "titleblock", "sld.scale")}{text("revision", "titleblock", "sld.revision")}{text("status", "titleblock", "sld.status")}
          {text("drawing_type", "titleblock", "sld.drawingType")}{text("replaces", "titleblock", "sld.replaces")}{text("replaced_by", "titleblock", "sld.replacedBy")}{text("internal_code", "titleblock", "sld.internalCode")}
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
          <h2 style={{ margin: 0 }}>{t("sld.circuits")} <span className="muted small">({data.circuits.length})</span></h2>
          <div className="row">
            <button onClick={loadExample}>{t("sld.loadExample")}</button>
            <button onClick={() => calculate(data)} disabled={running || !hasBoard || data.circuits.length === 0} title={t("sld.calcHelp")}>{t("sld.calcNow")}</button>
            <button className={editing?.index === null ? "" : "primary"} disabled={!hasBoard} title={hasBoard ? "" : t("sld.needBoard")} onClick={() => { if (editing?.index === null) closeForm(); else { setEditing({ index: null, draft: blankCircuit() }); setRouteOpen(false); setErrors({}); } }}>{editing?.index === null ? t("projects.cancel") : `+ ${t("sld.addRow")}`}</button>
          </div>
        </div>
        {!hasBoard && <p className="small" role="alert" style={{ margin: "6px 0 8px", color: "var(--bad, #b3261e)" }}>{t("sld.needBoard")}</p>}
        <p className="muted small" style={{ margin: "6px 0 8px" }}>{running ? t("sld.calcRunning") : dirty ? t("sld.calcPending") : t("sld.calcHelp")}</p>
        {calc.data && calc.data.rows.length > 0 && <CalcHeader view={calc.data} />}
        {data.circuits.length > 0 && (
          <div style={{ overflowX: "auto", marginTop: 6 }}>
            <table className="sldtable">
              <thead>
                <tr>{(["sld.tag", "sld.desc", "sld.load", "sld.length", "sld.install"] as Key[]).map((h) => <th key={h}>{t(h)}</th>)}{CALC_HEADS.map((h) => <th key={h}>{t(h)}</th>)}<th /></tr>
              </thead>
              <tbody>
                {data.circuits.map((c, i) => (
                  <tr key={i} className={editing?.index === i ? "draft" : undefined}>
                    <td className="mono">{c.tag}</td><td>{c.description}</td>
                    <td className="mono" style={{ whiteSpace: "nowrap" }}>{c.load ?? ""} {c.unit}</td>
                    <td className="mono">{(c.route?.length ?? 0) > 0 ? Math.round(c.route!.reduce((a, s) => a + (Number(s.length_m) || 0), 0) * 100) / 100 : c.length_m}</td>
                    <td style={{ whiteSpace: "nowrap" }}>{wiringOf(c, calc.data?.criteria?.conductor)}</td>
                    <CalcCells row={calcOf.get(c.tag.trim())} />
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button onClick={() => { setEditing({ index: i, draft: JSON.parse(JSON.stringify(c)) }); setRouteOpen(false); setErrors({}); }} title={t("sld.editRow")} aria-label={t("sld.editRow")} disabled={running}>✎</button>{" "}
                      <button onClick={() => removeCircuit(i)} title={t("sld.removeRow")} aria-label={t("sld.removeRow")} disabled={running}>✕</button>
                    </td>
                  </tr>
                ))}
                {extra.map((r) => (
                  <tr key={"auto-" + r.tag} className="muted">
                    <td className="mono">{r.tag}</td><td colSpan={4}>{r.description} · {t("sld.autoGroup")}</td><CalcCells row={r} /><td />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data.circuits.length === 0 && !editing && <div className="state">{t("sld.calcNone")}</div>}
        {editing && (
          <div style={{ overflowX: "auto", marginTop: 12 }}>
            <p className="small" style={{ margin: "0 0 4px" }}><b>{editing.index === null ? t("sld.newCircuit") : `${t("sld.editing")} ${data.circuits[editing.index]?.tag ?? ""}`}</b></p>
            <table className="sldtable">
              <thead>
                <tr>{(["sld.tag", "sld.desc", "sld.load", "sld.unit", "sld.dest", "sld.parent", "sld.topology", "sld.phase", "sld.length", "sld.fp", "sld.eff", "sld.kind", "sld.cable", "sld.install", "sld.insulation", "sld.conductor"] as Key[]).map((h) => <th key={h}>{t(h)}</th>)}<th /></tr>
              </thead>
              <tbody>
                <tr className="draft" onKeyDown={(e) => { if (e.key === "Enter" && (e.target as HTMLElement).tagName !== "BUTTON") { e.preventDefault(); accept(); } else if (e.key === "Escape") closeForm(); }}>
                  <CircuitInputs focus defaults={view.data.wiring_defaults} c={editing.draft} set={draftSet} parents={data.circuits.filter((p, j) => j !== editing.index && p.tag.trim()).map((p) => p.tag)} o={o} t={t} lengthCell={<>
                    {(editing.draft.route?.length ?? 0) > 0
                      ? <b className="mono" title={t("route.totalHint")}>{Math.round(editing.draft.route!.reduce((a, s) => a + (Number(s.length_m) || 0), 0) * 100) / 100}</b>
                      : <input className="w-num" type="number" step="any" value={editing.draft.length_m} onChange={(e) => draftSet({ length_m: Number(e.target.value) })} title={t("sld.lenData")} aria-label={t("sld.length")} />}
                    {" "}<button className={routeOpen ? "primary" : ""} onClick={() => setRouteOpen(!routeOpen)} title={t("route.title")}>{t("route.button")}{(editing.draft.route?.length ?? 0) > 0 ? ` (${editing.draft.route!.length})` : ""}</button>
                    {editing.index !== null && <LengthSource c={editing.draft} info={view.data?.lengths?.[editing.draft.tag.trim()]} sources={o.length_sources ?? ["auto", "plan", "data"]} onChange={(v) => draftSet({ length_source: v })} t={t} />}
                  </>} />
                  <td style={{ whiteSpace: "nowrap" }}>
                    <button className="primary" onClick={accept} disabled={running}>{t("sld.accept")}</button>{" "}
                    <button onClick={closeForm}>{t("projects.cancel")}</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <p className="muted small" style={{ margin: "6px 0 0" }}>{t("sld.installHelp")}</p>
          </div>
        )}
      </div>
      {editing && routeOpen && (
        <RouteEditor tag={editing.draft.tag} route={editing.draft.route ?? []} kinds={o.route_kinds} fallbackLength={editing.draft.length_m}
          onChange={(r) => draftSet({ route: r, ...(r.length ? { length_m: Math.round(r.reduce((a, s) => a + (Number(s.length_m) || 0), 0) * 100) / 100 } : {}) })} onClose={() => setRouteOpen(false)} />
      )}

      <div className="card">
        <h2>{t("memo.title")}</h2>
        <p className="muted small" style={{ margin: "2px 0 8px" }}>{t("memo.help")}</p>
        <div className="row" style={{ marginBottom: 8 }}>
          <button className={memoReady ? "" : "primary"} onClick={() => generate("none")} disabled={running || data.circuits.length === 0}>{t("memo.run")}</button>
        </div>
        {memo.data ? <BoardMemo client={client} code={code} v={memo.data} /> : <State loading={memo.loading} error={memo.error} />}
      </div>

      <div className="card">
        <div className="row" style={{ flexWrap: "wrap" }}>
          <button onClick={() => save()} disabled={!dirty || running}>{t("sld.save")}</button>
          <button className="primary" onClick={() => generate("sld")} disabled={running || !memoReady} title={memoReady ? "" : t("memo.needFirst")}>{t("sld.generateSldStep")}</button>
          <button onClick={() => generate("mld")} disabled={running || !memoReady} title={memoReady ? "" : t("memo.needFirst")}>{t("sld.generateMldStep")}</button>
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
            {status.state === "done" && status.outputs.some((f) => /\.(svg|dxf)$/i.test(f)) && (
              <>
                <div className={memo.data?.outdated ? "alert warn" : "alert ok"}>{memo.data?.outdated ? t("sld.outdated") : t("sld.done")} <button onClick={onOpenFiles} style={{ marginLeft: 8 }}>{t("sld.openFiles")}</button></div>
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
