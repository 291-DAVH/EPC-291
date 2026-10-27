import { useEffect, useMemo, useRef, useState } from "react";
import { api, Badge, errorText, Icon, JSON_HEADERS, Key, State, useApi, useI18n } from "@epc/ui";
import Coordination from "./Coordination";
import { base as coordBase, levelOf, pinsFor, useCoordination } from "./coordApi";
import DesignPanel from "./DesignPanel";
import LayersPanel from "./LayersPanel";
import { Changes, ChangesPanel, ChecksPanel, HistoryPanel, TablePanel, WarningsPanel } from "./LayoutPanels";
import PlanEditor, { Derived, Profile } from "./PlanEditor";
import { BoardCircuit, Circuits, Properties } from "./PlanPanels";
import { blank, Drawing, levelNumber, metresPerUnit, nextLevel, Pt, Ref } from "./planEditing";
import { clearDraft, loadDraft, saveDraft, usePlanPrefs } from "./planPrefs";
import { applyProposal, applyRuns, Architecture, RunsProposal, Clip, convertClip, Limits, Proposal, fromMetres, generationChecks, linkProblems, LinkTarget, Problem, stampClip, toMetres, warningTargets } from "./planTools";
import type { Ghost } from "./planTypes";

interface Sheet { level: string; base: string; discipline: string; nodes: number; lines: number; underlay: boolean; has_files: boolean }
interface Overview { levels: Sheet[]; profiles: Profile[]; circuits: BoardCircuit[]; dxf_versions: string[]; default_dxf_version: string }
interface ArchSummary { source: string; counts: Architecture["counts"]; wall_thickness: number | null; units_per_metre: number | null; scale_hint: Architecture["scale_hint"]; warnings: string[] }
interface LevelView { architecture?: ArchSummary | null; level: string; saved: boolean; drawing: Drawing; result: Derived | null; underlay: { kind: string; version: number } | null; files: { dxf?: string; pdf?: string; dxf_version?: string } | null; generated_at?: string }
interface Template { name: string; discipline: string; nodes: Clip["nodes"]; lines: Clip["lines"] }
type Panel = "props" | "circuits" | "design" | "table" | "warnings" | "coord" | "layers" | "history";

const SNAP_TOL_M = 0.15;                                                       // what the engine joins as one point (params.json, geometry.snap_tolerance_m)

/** Layout of the routes over the architectural plan: one drawing per level and discipline (L0 ground, L1.. up, L-1.. down), the tables the engine derives from it, the DXF and PDF,
 *  and the coordination with the drawings of the other disciplines, which stay separate: they are seen as footprints only. */
export default function Layout({ client, code, canWrite }: { client: string; code: string; canWrite: boolean }) {
  const { t, lang } = useI18n();
  const tl = (k: string) => t(k as Key);
  const root = `/projects/${client}/${code}/layout`;
  const project = `${client}/${code}`;
  const [rev, setRev] = useState(0);
  const ov = useApi<Overview>(`${root}?r=${rev}`);
  const templates = useApi<Template[]>(`/projects/${client}/${code}/layout-templates?r=${rev}`);
  const [level, setLevel] = useState("");
  const [lv, setLv] = useState<LevelView | null>(null);
  const [drawing, setDrawing] = useState<Drawing>(blank());
  const [derived, setDerived] = useState<Derived | null>(null);
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [savedAt, setSavedAt] = useState(0);
  const [, tick] = useState(0);
  const [err, setErr] = useState("");
  const [version, setVersion] = useState("");
  const [busy, setBusy] = useState(false);
  const [selection, setSelection] = useState<Ref[]>([]);
  const [focus, setFocus] = useState("");               // the circuit whose route is highlighted
  const [stale, setStale] = useState(false);          // the drawing changed after the files were made
  const timer = useRef<number | null>(null);
  const [stamp, setStamp] = useState(0);                 // bumps the underlay URL after an upload
  const [panel, setPanel] = useState<Panel>("props");
  const [help, setHelp] = useState(false);
  const [review, setReview] = useState(false);            // read-only look at the drawing, even for someone who may edit it
  const [checks, setChecks] = useState<Problem[] | null>(null);
  const [draft, setDraft] = useState<{ at: string; value: Drawing } | null>(null);
  const [clip, setClip] = useState<Clip | null>(null);
  const [focusReq, setFocusReq] = useState<{ n: number; refs?: Ref[]; at_m?: Pt; at?: Pt }>({ n: 0 });
  const [compare, setCompare] = useState<{ id: string; drawing: Drawing } | null>(null);
  const [others, setOthers] = useState<{ level: string; drawing: Drawing }[]>([]);
  const [pinAt, setPinAt] = useState<Pt | null>(null);
  const [pinText, setPinText] = useState("");
  const [hrev, setHrev] = useState(0);
  const [copying, setCopying] = useState<Clip | null>(null);
  const [targets, setTargets] = useState<string[]>([]);
  const [changes, setChanges] = useState<Changes | null>(null);
  const [arch, setArch] = useState<Architecture | null>(null);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [runs, setRuns] = useState<RunsProposal | null>(null);
  const [designBusy, setDesignBusy] = useState(false);
  const [limits, setLimits] = useState<Record<string, Partial<Limits>>>({});
  const [roomRequest, setRoomRequest] = useState(0);
  const [recognizing, setRecognizing] = useState(false);

  const [prefs, setPrefs] = usePlanPrefs();
  const sheets = ov.data?.levels ?? [];
  const levels = sheets.map((x) => x.level);
  const base = levelOf(level);
  const mine = sheets.find((x) => x.level === level);
  const discipline = drawing.discipline;
  const write = canWrite && !review;
  const coord = useCoordination(client, code, level, discipline);

  useEffect(() => { if (selection.length > 0) setPanel("props"); }, [selection]);        // picking something on the canvas brings its properties forward
  useEffect(() => { if (ov.data && !level) setLevel(ov.data.levels[0]?.level ?? ""); }, [ov.data]);
  useEffect(() => { const id = window.setInterval(() => tick((n) => n + 1), 15000); return () => window.clearInterval(id); }, []);
  useEffect(() => {
    if (!level) { setLv(null); setDrawing(blank()); setDerived(null); return; }
    let live = true;
    setCompare(null);
    api<LevelView>(`${root}/${level}`).then((v) => {
      if (!live) return;
      setLv(v); setDrawing(v.drawing); setDerived(v.result); setSelection([]); setFocus(""); setState("idle"); setStale(false); setErr(""); setSavedAt(0);
      const d = loadDraft<Drawing>(project, level);                                // changes of an earlier session that never reached the server
      setDraft(d && JSON.stringify(d.value) !== JSON.stringify(v.drawing) ? d : null);
    }).catch((x) => live && setErr(errorText(x)));
    return () => { live = false; };
  }, [level, root]);
  useEffect(() => {                                    // the same discipline on the level above and below, to line things up
    const n = levelNumber(base || "L0");
    const near = sheets.filter((x) => x.discipline === discipline && x.level !== level && Number.isFinite(levelNumber(x.base)) && Math.abs(levelNumber(x.base) - n) === 1);
    let live = true;
    Promise.all(near.map((x) => api<LevelView>(`${root}/${x.level}`).then((v) => ({ level: x.base, drawing: v.drawing })).catch(() => null))).then((r) => live && setOthers(r.filter((x): x is { level: string; drawing: Drawing } => !!x)));
    return () => { live = false; };
  }, [level, discipline, rev, sheets.length]);

  useEffect(() => {                                    // what was recognized in the plan of this sheet (walls, doors, windows)
    if (!level || !lv?.architecture) { setArch(null); return; }
    let live = true;
    api<Architecture>(`${root}/${level}/architecture`).then((a) => live && setArch(a)).catch(() => live && setArch(null));
    return () => { live = false; };
  }, [level, lv?.architecture?.counts?.walls, lv?.architecture?.source, stamp]);

  const profile = ov.data?.profiles.find((p) => p.id === discipline);
  const k = metresPerUnit(drawing);
  const ghosts = useMemo<Ghost[]>(() => {
    if (!k) return [];
    const out: Ghost[] = [];
    others.forEach((o) => {
      const k2 = metresPerUnit(o.drawing);
      if (!k2) return;
      const conv = (p: Pt): Pt => fromMetres(toMetres(p, o.drawing.origin, k2), drawing.origin, k);
      out.push({ key: o.level, level: o.level, nodes: o.drawing.nodes.map((n) => conv([n.x, n.y])), lines: o.drawing.lines.map((l) => l.points.map(conv)) });
    });
    if (compare) out.push({ key: "history", level: tl("plan.history.before"), nodes: compare.drawing.nodes.map((n) => [n.x, n.y] as Pt), lines: compare.drawing.lines.map((l) => l.points) });
    return out;
  }, [others, compare, drawing.origin, k]);
  const pins = useMemo(() => pinsFor(coord.clashes, coord.threads, discipline, base, tl), [coord.clashes, coord.threads, discipline, base, lang]);
  const problems = useMemo(() => (checks ?? []).filter((p) => p.at), [checks]);

  const send = async (next: Drawing) => {
    setState("saving");
    try { const v = await api<LevelView>(`${root}/${level}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(next) }); setLv(v); setDerived(v.result); setState("saved"); setSavedAt(Date.now()); clearDraft(project, level); setErr(""); setRev((n) => n + 1); coord.reload(); }
    catch (x) { setState("error"); setErr(errorText(x)); }
  };
  const change = (next: Drawing) => {
    if (!write) return;
    setDrawing(next);
    setStale(true);
    setChecks(null);
    saveDraft(project, level, next);                                              // kept on this computer until the server has it
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => send(next), 700);                    // saved a moment after the last change
  };
  const createSheet = async (name: string, discipline = "electrica_BT") => {
    try { await api(`${root}/${name}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(blank(discipline)) }); setRev((n) => n + 1); setLevel(name); } catch (x) { setErr(errorText(x)); }
  };
  const deleteSheet = async () => {
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
    setChecks(null);
    if (timer.current) { window.clearTimeout(timer.current); timer.current = null; await send(drawing); }       // what is on the screen is what gets drawn
    try { const v = await api<LevelView>(`${root}/${level}/generate${version ? `?version=${version}` : ""}`, { method: "POST" }); setLv(v); setDerived(v.result); setStale(false); setErr(""); } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };
  /** Everything worth a look before making files: the checks of the drawing and the links of its shafts with their twins on other levels. */
  const collectProblems = async (): Promise<Problem[]> => {
    const found = generationChecks(drawing, derived?.circuits, k ? SNAP_TOL_M / k : 3);
    const wanted = [...new Set(drawing.nodes.map((n) => (typeof n.attrs?.enlace === "string" ? /^(L-?\d+):/.exec(n.attrs.enlace.trim())?.[1] : undefined)).filter((x): x is string => !!x))];
    const fetched: Record<string, LinkTarget | undefined> = {};
    await Promise.all(wanted.map(async (lvl) => {
      const sheet = sheets.find((x) => x.base === lvl && x.discipline === discipline);
      if (sheet) { const v = await api<LevelView>(`${root}/${sheet.level}`).catch(() => null); if (v) fetched[lvl] = { drawing: v.drawing, k: metresPerUnit(v.drawing) }; }
    }));
    return [...found, ...linkProblems(drawing, base, k, (lvl) => fetched[lvl])];
  };
  const runChecks = async () => setChecks(await collectProblems());
  const beforeGenerate = async () => {
    const found = await collectProblems();
    if (found.length) setChecks(found); else generate();
  };
  const showChanges = async () => { try { setChanges(await api<Changes>(`${root}/${level}/changes`)); } catch (x) { setErr(errorText(x)); } };
  const copyTo = async () => {
    if (!copying || !k) return;
    try {
      for (const sheet of targets) {
        const v = await api<LevelView>(`${root}/${sheet}`);
        const k2 = metresPerUnit(v.drawing);
        if (!k2) continue;                                                      // a sheet without scale cannot take it: positions are in metres
        const put = stampClip(v.drawing, convertClip(copying, { origin: drawing.origin, k }, { origin: v.drawing.origin, k: k2 }));
        await api(`${root}/${sheet}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(put) });
      }
      setRev((n) => n + 1); setCopying(null); setTargets([]); setErr("");
    } catch (x) { setErr(errorText(x)); }
  };
  const recognize = async () => {
    if (!level || recognizing) return;
    const vector = lv?.underlay && lv.underlay.kind !== "png" && lv.underlay.kind !== "jpg" && lv.underlay.kind !== "jpeg";
    if (vector && (drawing.nodes.length || drawing.lines.length) && !window.confirm(tl("plan.arch.confirm"))) return;
    setRecognizing(true);
    try {
      const r = await api<{ view: LevelView; underlay_replaced: boolean }>(`${root}/${level}/architecture`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({}) });
      setLv(r.view); setStamp((n) => n + 1); setErr(""); setRev((n) => n + 1);
    } catch (x) { setErr(errorText(x)); }
    setRecognizing(false);
  };
  const designCall = async <T,>(step: "runs" | "wiring", then: (r: T) => void) => {
    setDesignBusy(true);
    try {
      const families = Object.fromEntries(Object.entries(limits).map(([f, v]) => [f, Object.fromEntries(Object.entries(v).filter(([, x]) => typeof x === "number"))]));
      then(await api<T>(`${root}/${level}/design/${step}`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ drawing, families }) })); setErr("");
    } catch (x) { setErr(errorText(x)); }
    setDesignBusy(false);
  };
  const proposeRuns = () => designCall<RunsProposal>("runs", setRuns);
  const proposeWiring = () => designCall<Proposal>("wiring", setProposal);
  const applyDesignRuns = () => { if (runs) { change(applyRuns(drawing, runs)); setRuns(null); setRev((n) => n + 1); } };
  const applyDesign = async (inBoard: boolean) => {
    if (!proposal) return;
    setDesignBusy(true);
    try {
      if (inBoard) await api(`${root}/${level}/design/circuits`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ circuits: proposal.circuits.map((c) => ({ tag: c.tag, description: c.description, load: c.va, unit: "VA" })) }) });
      change(applyProposal(drawing, proposal)); setProposal(null); setRev((n) => n + 1); setErr("");
    } catch (x) { setErr(errorText(x)); }
    setDesignBusy(false);
  };
  const useHintedScale = () => {
    const h = lv?.architecture?.scale_hint;
    if (h && write) change({ ...drawing, scale: { p1: [0, 0], p2: [h.units_per_metre, 0], distance_m: 1 } });
  };
  const restore = async (id: string) => {
    try { const v = await api<LevelView>(`${root}/${level}/history/${id}/restore`, { method: "POST" }); setLv(v); setDrawing(v.drawing); setDerived(v.result); setCompare(null); setHrev((n) => n + 1); setRev((n) => n + 1); setStale(true); } catch (x) { setErr(errorText(x)); }
  };
  const openCompare = async (id: string) => {
    if (!id) { setCompare(null); return; }
    try { setCompare({ id, drawing: await api<Drawing>(`${root}/${level}/history/${id}`) }); } catch (x) { setErr(errorText(x)); }
  };
  const look = (refs?: Ref[], at_m?: Pt, at?: Pt) => { if (refs) setSelection(refs); setFocusReq((r) => ({ n: r.n + 1, refs, at_m, at })); };
  const jump = (w: string) => { const r = warningTargets(w, derived?.nodes ?? [], derived?.stretches ?? []); if (r.length) look(r); };
  const goProblem = (p: Problem) => { if (p.ref) look([p.ref]); else if (p.tag) { setPanel("circuits"); setFocus(p.tag); } };
  const describeProblem = (p: Problem) => {
    const what = p.ref ? (p.ref.type === "node" ? derived?.nodes?.find((n) => n.id === p.ref!.id)?.tag ?? p.ref.id : derived?.stretches?.find((s) => s.line === p.ref!.id)?.line_tag ?? p.ref.id) : p.tag ?? "";
    return `${tl("layout.problem." + p.code)}${what ? `: ${what}` : ""}`;
  };
  const focusAt = (at_m: Pt, lvl: string, sheet: string) => { if (sheet && sheet !== level && levels.includes(sheet)) setLevel(sheet); else if (lvl && lvl !== base) { const s = sheets.find((x) => x.base === lvl && x.discipline === discipline); if (s) setLevel(s.level); } look(undefined, at_m); };
  const saveTemplate = async (name: string, c: Clip) => {
    try { await api(`/projects/${client}/${code}/layout-templates/${encodeURIComponent(name)}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ discipline, nodes: c.nodes, lines: c.lines }) }); setRev((n) => n + 1); setErr(""); } catch (x) { setErr(errorText(x)); }
  };
  const newThread = async (body: object) => {
    try { await api(`${coordBase(client, code)}/threads`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(body) }); coord.reload(); setErr(""); return true; } catch (x) { setErr(errorText(x)); return false; }
  };
  const reserve = async (lineId: string) => {
    const l = drawing.lines.find((x) => x.id === lineId);
    if (!l || !k || !profile) return;
    const kind = profile.lines.find((x) => x.id === l.kind);
    const g = { z_m: 0, ancho_m: 0.1, alto_m: 0.1, ...(kind?.geom ?? {}), ...Object.fromEntries(Object.entries(l.attrs ?? {}).filter(([key, v]) => ["z_m", "ancho_m", "alto_m"].includes(key) && typeof v === "number")) } as Record<string, number>;
    const story = (await api<{ story_height_m: number }>(`${coordBase(client, code)}/settings`).catch(() => ({ story_height_m: 3 }))).story_height_m;
    const floor = levelNumber(base) * story;
    const ok = await newThread({ kind: "reservation", from_discipline: discipline, title: `${tl("plan.act.reserve")} ${derived?.stretches?.find((s) => s.line === lineId)?.line_tag ?? lineId}`, sheet: level, level: base, point_m: toMetres(l.points[0], drawing.origin, k),
      geom: { points_m: l.points.map((p) => toMetres(p, drawing.origin, k)), width_m: Math.round((g.ancho_m + 0.1) * 1000) / 1000, z0: floor + g.z_m - g.alto_m / 2 - 0.05, z1: floor + g.z_m + g.alto_m / 2 + 0.05, level: base, sheet: level } });
    if (ok) setPanel("coord");
  };
  const onPin = (id: string) => { setPanel("coord"); if (id.startsWith("clash:")) { const c = coord.clashes.find((x) => "clash:" + x.id === id); if (c) look(undefined, c.point_m); } };
  const sendPin = async () => {
    if (!pinAt || !pinText.trim()) return;
    if (await newThread({ kind: "comment", from_discipline: discipline, text: pinText.trim(), sheet: level, level: base, point_m: pinAt })) { setPinAt(null); setPinText(""); setPanel("coord"); }
  };

  if (ov.error) return <div className="state err">{ov.error}</div>;
  if (!ov.data) return <State loading={ov.loading} />;
  const d = derived;
  const download = (name?: string) => (name ? `/api/projects/${client}/${code}/layout/${level}/files/${name}` : "");
  const dp = d?.ready ? d : null;
  const warnings = d?.warnings ?? [];
  const bases = [...new Set(sheets.map((x) => x.base))];
  const sameBase = sheets.filter((x) => x.base === base);
  const usedHere = new Set(sameBase.map((x) => x.discipline));
  const profName = (id: string) => ov.data!.profiles.find((p) => p.id === id)?.name[lang] ?? id;
  const ago = savedAt ? Math.max(0, Math.round((Date.now() - savedAt) / 1000)) : 0;
  const tabs: { id: Panel; label: string; badge?: number }[] = [
    { id: "props", label: tl("layout.tab.props") }, { id: "circuits", label: tl("layout.tab.circuits") }, { id: "table", label: tl("layout.tab.table") }, { id: "warnings", label: tl("layout.tab.warnings"), badge: warnings.length },
    { id: "design", label: tl("design.tab") }, { id: "layers", label: tl("layers.tab") }, { id: "coord", label: tl("coord.tab"), badge: coord.count }, { id: "history", label: tl("plan.history") },
  ];
  const layerOfKind = (id: string) => [...(profile?.lines ?? []), ...(profile?.nodes ?? [])].find((k) => k.id === id)?.capa_dxf ?? "";
  const layerCounts: Record<string, number> = {};
  [...drawing.nodes, ...drawing.lines].forEach((e) => { const l = layerOfKind(e.kind); if (l) layerCounts[l] = (layerCounts[l] ?? 0) + 1; });
  const tplHere = (templates.data ?? []).filter((x) => x.discipline === discipline);

  return (
    <div className="workbench">
      <div className="wb-top">
        <div className="wb-group" role="tablist" aria-label={tl("layout.level")}>
          {bases.map((x) => <button key={x} role="tab" aria-selected={x === base} className={"lvl" + (x === base ? " on" : "")} onClick={() => setLevel((sheets.find((s) => s.base === x && s.discipline === discipline) ?? sheets.find((s) => s.base === x))!.level)}>{x}</button>)}
          {canWrite && (bases.length === 0
            ? <button className="primary" onClick={() => createSheet("L0")}>+ L0</button>
            : <><button onClick={() => createSheet(nextLevel(bases, "up"))} title={tl("layout.addLevel")}>+ {nextLevel(bases, "up")}</button><button onClick={() => createSheet(nextLevel(bases, "down"))} title={tl("layout.addLevel")}>+ {nextLevel(bases, "down")}</button></>)}
        </div>
        {level && <div className="wb-group" role="tablist" aria-label={tl("plan.sheets")}>
          {sameBase.map((x) => <button key={x.level} role="tab" aria-selected={x.level === level} className={"lvl disc" + (x.level === level ? " on" : "")} onClick={() => setLevel(x.level)} title={profName(x.discipline)}>{profName(x.discipline)}</button>)}
          {canWrite && ov.data.profiles.some((p) => !usedHere.has(p.id)) && (
            <select className="add-sheet" value="" aria-label={tl("plan.addSheet")} onChange={(e) => e.target.value && createSheet(`${base}@${e.target.value}`, e.target.value)}>
              <option value="">+ {tl("plan.addSheet")}</option>{ov.data.profiles.filter((p) => !usedHere.has(p.id)).map((p) => <option key={p.id} value={p.id}>{p.name[lang] ?? p.name.es}</option>)}
            </select>)}
          {level && canWrite && <button onClick={deleteSheet} title={tl("layout.deleteLevel")} aria-label={tl("layout.deleteLevel")}><Icon name="trash" size={16} /></button>}
        </div>}
        {level && <>
          <label className="wb-field"><span>{tl("layout.discipline")}</span>
            <select value={discipline} disabled={!write || level.includes("@")} onChange={(e) => change({ ...drawing, discipline: e.target.value })}>
              {ov.data.profiles.map((p) => <option key={p.id} value={p.id} disabled={usedHere.has(p.id) && p.id !== discipline}>{p.name[lang] ?? p.name.es}</option>)}
            </select></label>
          {write && <label className="btn wb-upload" title={tl("layout.noUnderlay")}><Icon name="upload" size={16} /> {tl("layout.underlay")}
            <input type="file" accept=".png,.jpg,.jpeg,.svg,.dxf,.pdf" disabled={busy} onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }} /></label>}
          {!lv?.underlay && <span className="muted small wb-note">{tl("layout.noUnderlay")}</span>}
          {write && lv?.underlay && <button onClick={recognize} disabled={recognizing || busy} title={tl("plan.arch.help")}><Icon name="select" size={16} /> {recognizing ? tl("plan.arch.working") : tl("plan.arch.recognize")}</button>}
          {lv?.architecture && <span className="badge accent" title={lv.architecture.warnings.join("\n")}>{lv.architecture.counts.walls} {tl("plan.arch.walls")} · {lv.architecture.counts.doors} {tl("plan.arch.doors")} · {lv.architecture.counts.windows} {tl("plan.arch.windows")}{lv.architecture.counts.openings ? ` · ${lv.architecture.counts.openings} ${tl("plan.arch.openings")}` : ""}</span>}
          {write && !drawing.scale && lv?.architecture?.scale_hint && <button onClick={useHintedScale} title={lv.architecture.scale_hint.basis}>{tl("plan.arch.useScale")}</button>}
          {discipline !== "electrica_BT" && (
            <label className="wb-field"><span>{tl("layout.outlet")}</span>
              <select value={drawing.outlet} disabled={!write} onChange={(e) => change({ ...drawing, outlet: e.target.value })}>
                <option value="">–</option>{drawing.nodes.map((n) => <option key={n.id} value={n.id}>{d?.nodes?.find((x) => x.id === n.id)?.tag ?? n.id}</option>)}
              </select>
              <span>{tl("layout.outletInvert")}</span>
              <input style={{ width: 70 }} disabled={!write} value={drawing.outlet_invert_m ?? ""} onChange={(e) => change({ ...drawing, outlet_invert_m: e.target.value === "" ? null : parseFloat(e.target.value.replace(",", ".")) })} />
            </label>
          )}
          {write && tplHere.length > 0 && (
            <select className="add-sheet" value="" aria-label={tl("plan.templates")} onChange={(e) => { const x = tplHere.find((y) => y.name === e.target.value); if (x) setClip({ nodes: x.nodes, lines: x.lines }); }}>
              <option value="">{tl("plan.templates")}</option>{tplHere.map((x) => <option key={x.name} value={x.name}>{x.name}</option>)}
            </select>)}
        </>}
        <span className="grow" />
        {state === "saving" && <span className="muted small">{tl("layout.saving")}</span>}
        {state === "saved" && <span className="muted small" title={tl("plan.savedAgo")}>{tl("layout.saved")} {ago < 60 ? `${ago}s` : `${Math.round(ago / 60)} min`}</span>}
        {state === "error" && <Badge tone="bad">{tl("plan.notSaved")}</Badge>}
        {level && <>
          <label className="wb-field"><span>{tl("layout.dxfVersion")}</span>
            <select value={version} onChange={(e) => setVersion(e.target.value)}>
              <option value="">{tl("layout.latest")} ({ov.data.default_dxf_version})</option>
              {ov.data.dxf_versions.map((v) => <option key={v} value={v}>{v}</option>)}
            </select></label>
          <button className="primary" disabled={busy || !drawing.scale || !write} onClick={beforeGenerate} title={!drawing.scale ? tl("layout.needScale") : ""}><Icon name="file" size={16} /> {tl("layout.makeFiles")}</button>
          {lv?.files?.dxf && <a className="btn" href={download(lv.files.dxf)}>{tl("layout.downloadDxf")} ({lv.files.dxf_version})</a>}
          {lv?.files?.pdf && <a className="btn" href={download(lv.files.pdf)}>{tl("layout.downloadPdf")}</a>}
          {lv?.files && stale && <button className="badge warn" onClick={showChanges} title={tl("plan.changes")}>{tl("layout.filesOutdated")} ▸</button>}
          <button onClick={runChecks} title={tl("plan.check.help")}><Icon name="check" size={16} /> {tl("plan.check")}</button>
        </>}
        {canWrite && <button className="tool-ico" onClick={() => setReview(!review)} aria-pressed={review} aria-label={tl("plan.review")} title={tl("plan.review")}><Icon name="eye" size={18} /></button>}
        <button className="tool-ico" onClick={() => setHelp(!help)} aria-pressed={help} aria-label={tl("layout.helpToggle")} title={tl("layout.helpToggle")}><Icon name="help" size={18} /></button>
      </div>
      {help && <p className="wb-help">{tl("layout.help")}</p>}
      {review && <p className="wb-help review"><Icon name="eye" size={16} /> {tl("plan.review.on")} <button onClick={() => setReview(false)}>{tl("plan.review.exit")}</button></p>}
      {draft && write && (
        <p className="wb-help draft"><Icon name="warn" size={16} /> {tl("plan.draft")} ({draft.at.replace("T", " ").slice(0, 16)}).
          <button className="primary" onClick={() => { change(draft.value); setDraft(null); }}>{tl("plan.draft.restore")}</button><button onClick={() => { clearDraft(project, level); setDraft(null); }}>{tl("plan.draft.discard")}</button></p>
      )}
      {err && <div className="alert bad small" style={{ margin: 0 }}>{err}</div>}

      {!level ? <div className="state wb-empty">{tl("layout.empty")}</div> : (
        <div className="wb-body">
          <PlanEditor drawing={drawing} onChange={change} derived={dp} profile={profile} lang={lang} readOnly={!write}
            underlayUrl={lv?.underlay ? `/api${root}/${level}/underlay?v=${lv.underlay.version}-${stamp}` : null} underlayKind={lv?.underlay?.kind} t={tl}
            selection={selection} onSelect={setSelection} highlight={focus ? d?.circuits?.[focus]?.lines ?? [] : []} focusCircuit={focus}
            sheetKey={level} sheetTitle={`${project}_${level}`} architecture={arch} prefs={[prefs, setPrefs]} proposal={runs} roomRequest={roomRequest} reference={coord.reference} ghosts={ghosts} pins={pins} onPin={onPin} problems={problems}
            freeCircuits={ov.data.circuits.map((c) => c.tag).filter((tag) => !drawing.circuits.some((c) => c.tag === tag))} circuitTags={ov.data.circuits.map((c) => c.tag)} focusRequest={focusReq}
            onCopyLevels={(c) => { setCopying(c); setTargets([]); }} onNewPin={(at) => { setPinAt(at); setPinText(""); }} onReserve={reserve} onTemplateSave={saveTemplate} pendingClip={clip} onClipUsed={() => setClip(null)} />
          <aside className="wb-side" aria-label={tl("layout.panel")}>
            <div className="wb-tabs" role="tablist">
              {tabs.map((x) => <button key={x.id} role="tab" aria-selected={panel === x.id} className={panel === x.id ? "on" : ""} onClick={() => setPanel(x.id)}>{x.label}{!!x.badge && <span className="dot">{x.badge}</span>}</button>)}
            </div>
            <div className="wb-panel" role="tabpanel">
              {pinAt && (
                <div className="coord-form" style={{ marginBottom: 8 }}>
                  <b>{tl("plan.pin.new")}</b>
                  <textarea autoFocus rows={2} value={pinText} onChange={(e) => setPinText(e.target.value)} placeholder={tl("coord.text")} />
                  <div className="row" style={{ gap: 6 }}><button className="primary" disabled={!pinText.trim()} onClick={sendPin}>{tl("coord.send")}</button><button onClick={() => setPinAt(null)}>{tl("layout.cancel")}</button></div>
                </div>
              )}
              {panel === "props" && <Properties drawing={drawing} selection={selection} derived={dp} profile={profile} lang={lang} boardCircuits={ov.data.circuits} readOnly={!write} onChange={change} onSelect={setSelection} t={tl} />}
              {panel === "circuits" && <Circuits drawing={drawing} derived={dp} boardCircuits={ov.data.circuits} profile={profile} onSelect={setSelection} readOnly={!write} focus={focus} onFocus={setFocus} onChange={change} t={tl} />}
              {panel === "table" && <TablePanel d={d} tl={tl} />}
              {panel === "warnings" && <WarningsPanel warnings={warnings} onJump={jump} tl={tl} />}
              {panel === "design" && <DesignPanel drawing={drawing} profile={profile} proposal={proposal} runs={runs} busy={designBusy} canWrite={write} limitsOverride={limits} onLimits={setLimits} onProposeRuns={proposeRuns} onApplyRuns={applyDesignRuns} onDiscardRuns={() => setRuns(null)} onPropose={proposeWiring} onApply={applyDesign} onDiscard={() => setProposal(null)}
                onChange={change} onNewRoom={() => setRoomRequest((n) => n + 1)} onLook={(at) => look(undefined, undefined, at)} derived={dp} />}
              {panel === "layers" && <LayersPanel client={client} code={code} rev={rev} current={discipline} prefs={prefs} setPrefs={setPrefs} counts={layerCounts} canWrite={canWrite}
                sheetOf={(pid) => sameBase.find((x) => x.discipline === pid)?.level ?? null} onOpen={(pid) => { const s = sameBase.find((x) => x.discipline === pid); if (s) setLevel(s.level); else createSheet(sheets.length ? `${base}@${pid}` : base, pid); }} />}
              {panel === "coord" && <Coordination client={client} code={code} discipline={discipline} canWrite={canWrite} onChanged={coord.reload} onFocus={focusAt} />}
              {panel === "history" && <HistoryPanel root={root} level={level} rev={rev + hrev} canWrite={write} comparing={compare?.id ?? ""} onCompare={openCompare} onRestore={restore} tl={tl} />}
            </div>
          </aside>
          {copying && (
            <div className="wb-float wb-checks" role="dialog" aria-label={tl("plan.act.copyLevels")}>
              <b>{tl("plan.act.copyLevels")}</b><p className="small muted" style={{ margin: 0 }}>{tl("plan.copyLevels.help")}</p>
              {sheets.filter((x) => x.discipline === discipline && x.level !== level).map((x) => <label key={x.level} className="vp-row"><input type="checkbox" checked={targets.includes(x.level)} onChange={(e) => setTargets(e.target.checked ? [...targets, x.level] : targets.filter((y) => y !== x.level))} /> {x.base}</label>)}
              {!sheets.some((x) => x.discipline === discipline && x.level !== level) && <p className="small">{tl("plan.copyLevels.none")}</p>}
              <div className="row" style={{ gap: 6 }}><button className="primary" disabled={!targets.length} onClick={copyTo}>{tl("plan.copyLevels.go")}</button><button onClick={() => setCopying(null)}>{tl("layout.cancel")}</button></div>
            </div>
          )}
          {changes && <ChangesPanel data={changes} tl={tl} onClose={() => setChanges(null)} onGo={(r) => { look([r]); setChanges(null); }} />}
          {checks && <ChecksPanel problems={checks} describe={describeProblem} onGo={goProblem} onForce={generate} onClose={() => setChecks(null)} tl={tl} />}
        </div>
      )}
    </div>
  );
}
