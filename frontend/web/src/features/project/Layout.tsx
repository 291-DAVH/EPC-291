import { useEffect, useMemo, useRef, useState } from "react";
import { api, Badge, errorText, Icon, JSON_HEADERS, Key, State, useApi, useI18n } from "@epc/ui";
import Coordination from "./Coordination";
import { base as coordBase, levelOf, pinsFor, useCoordination } from "./coordApi";
import DesignPanel from "./DesignPanel";
import LayersPanel from "./LayersPanel";
import LightingPanel from "./LightingPanel";
import type { CompareRow } from "./LightingExtras";
import { setRoomLighting } from "./lightingApi";
import { setSetting } from "./lightingTools";
import { applyLighting, emergencyMarksOf, LightingOptions, mapsOf, LightingStudy, LightingProposal, marksOf, requestOf } from "./lightingApi";
import PlansPanel from "./PlansPanel";
import { Changes, ChangesPanel, ChecksPanel, HistoryPanel, WarningsPanel } from "./LayoutPanels";
import PlanEditor, { Derived, Profile } from "./PlanEditor";
import { BoardCircuit, Properties } from "./PlanPanels";
import { blank, Drawing, levelNumber, metresPerUnit, nextLevel, Pt, Ref } from "./planEditing";
import { clearDraft, loadDraft, saveDraft, usePlanPrefs } from "./planPrefs";
import { applyProposal, applyRuns, Architecture, BoardRef, allowedKinds, newSheetKey, RunsProposal, Clip, convertClip, Limits, Proposal, fromMetres, generationChecks, linkProblems, LinkTarget, Problem, stampClip, toMetres, warningTargets } from "./planTools";
import type { Ghost } from "./planTypes";
import { BoardAnswer, ElectricalSetupDialog, PlenumAnswer, PlenumDialog } from "./BoardPlenumDialogs";
import { BoardPlace, ELECTRICAL, levelsToMake, otherShafts, plenumNear, plenumNeededAt, PlenumDef } from "./plenumFlow";

interface Sheet { level: string; base: string; discipline: string; plan: string; plan_name: string; subdiscipline: string; nodes: number; lines: number; underlay: boolean; has_files: boolean }
interface Overview { levels: Sheet[]; plenums: PlenumDef[]; profiles: Profile[]; circuits: BoardCircuit[]; boards: (BoardRef & BoardPlace)[]; dxf_versions: string[]; default_dxf_version: string }
interface ArchSummary { source: string; counts: Architecture["counts"]; wall_thickness: number | null; units_per_metre: number | null; scale_hint: Architecture["scale_hint"]; warnings: string[] }
interface LevelView { architecture?: ArchSummary | null; level: string; saved: boolean; drawing: Drawing; result: Derived | null; underlay: { kind: string; version: number } | null; files: { dxf?: string; pdf?: string; dxf_version?: string } | null; generated_at?: string }
interface Template { name: string; discipline: string; nodes: Clip["nodes"]; lines: Clip["lines"] }
type Panel = "props" | "plans" | "design" | "lighting" | "warnings" | "coord" | "layers" | "history";

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
  const [panel, setPanel] = useState<Panel | null>(null);        // the panels sit behind icons on the right and close when the person goes back to the canvas
  const [designBoard, setDesignBoard] = useState("");
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
  const [lighting, setLighting] = useState<LightingProposal | null>(null);          // luminaires proposed for the rooms, shown over the plan until the person decides
  const [lightBusy, setLightBusy] = useState(false);
  const [dialog, setDialog] = useState<null | { type: "setup" } | { type: "plenum"; level: string; next: string; discipline: string; mandatory: boolean; at: Pt }>(null);
  const [dialogBusy, setDialogBusy] = useState(false);
  const lightMap = !!drawing.lighting_settings?.map;                              // also draw the illuminance of the rooms over the plan: the sheet remembers it
  const [lightCompare, setLightCompare] = useState<{ room: string; options: CompareRow[]; best: string | null } | null>(null);
  const [studyError, setStudyError] = useState("");
  const [lightApplied, setLightApplied] = useState("");
  const [studyRev, setStudyRev] = useState(0);
  const [reported, setReported] = useState("");
  const study = useApi<LightingStudy>(panel === "lighting" && level ? `/projects/${client}/${code}/lighting/study/${encodeURIComponent(level)}?rev=${rev}&s=${studyRev}` : null);
  const lightOptions = useApi<LightingOptions>(`/projects/${client}/${code}/lighting/options?lang=${lang}`);
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
  const isArchitecture = discipline === "arquitectura";          // the plan is put in and recognized here; the other disciplines only draw over it
  const write = canWrite && !review;
  const coord = useCoordination(client, code, level, discipline);

  useEffect(() => { if (selection.length > 0) setPanel((p) => (p ? "props" : p)); }, [selection]);        // with a panel open, picking something shows its properties
  useEffect(() => {
    if (!panel) return;
    const away = (e: PointerEvent) => { if (!(e.target as Element | null)?.closest?.(".wb-side")) setPanel(null); };
    document.addEventListener("pointerdown", away);
    return () => document.removeEventListener("pointerdown", away);
  }, [panel]);
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
  const createSheet = async (name: string, discipline = "arquitectura", planName = "", subdiscipline = "") => {
    try { await api(`${root}/${name}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ ...blank(discipline), plan_name: planName, subdiscipline }) }); setRev((n) => n + 1); setLevel(name); } catch (x) { setErr(errorText(x)); }
  };
  /** A discipline is on a level once; what it draws there is split in plans (lighting, sockets...), each a sheet of its own: the first one has no name in its key, the next ones carry theirs. */
  const addDiscipline = (pid: string) => {
    if (pid === ELECTRICAL && !sheets.some((x) => x.discipline === ELECTRICAL)) { setDialog({ type: "setup" }); return; }            // the first electrical sheet asks where the board is
    createSheet(newSheetKey(base, pid, sheets.filter((x) => x.base === base).map((x) => x.level), "", false), pid);
  };
  const putSheet = (name: string, discipline: string) => api(`${root}/${name}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ ...blank(discipline), plan_name: "", subdiscipline: "" }) });
  /** The first electrical sheet: the levels the board needs (so it sits on its own, not on the ground level), the board with its place, and the sheet of its level. */
  const submitSetup = async (a: BoardAnswer) => {
    setDialogBusy(true);
    try {
      for (const key of levelsToMake(bases, a.level)) await putSheet(key, "arquitectura");
      await api(`/projects/${client}/${code}/sld/boards`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ name: a.name, level: a.level, location: a.location }) });
      await putSheet(`${a.level}@${ELECTRICAL}`, ELECTRICAL);
      setDialog(null); setRev((n) => n + 1); setLevel(`${a.level}@${ELECTRICAL}`); setErr("");
    } catch (x) { setErr(errorText(x)); }
    setDialogBusy(false);
  };
  /** Adding a level: where the board is there has to be a plenum for the cables to go through, so it is asked for (and the level waits for the answer); the other disciplines that can have one are asked whether they need it. */
  const requestLevel = async (direction: "up" | "down") => {
    const next = nextLevel(bases, direction);
    const needed = plenumNeededAt(ov.data?.boards ?? [], ov.data?.plenums ?? []);
    if (needed) {
      const board = await boardPosition(needed);
      setDialog({ type: "plenum", level: needed, next, discipline: ELECTRICAL, mandatory: true, at: plenumNear(board) });
      return;
    }
    const others = otherShafts(ov.data?.profiles ?? [], sheets.map((x) => x.discipline), ov.data?.plenums ?? [], base);
    const asked = others.find((pid) => window.confirm(tl("plenum.askOther").replace("{discipline}", profName(pid)).replace("{level}", base)));
    if (asked) setDialog({ type: "plenum", level: base, next, discipline: asked, mandatory: false, at: plenumNear(null) });
    else createSheet(next);
  };
  /** Where the board is on the plan of its level, in metres from the origin (null when it is not drawn yet). */
  const boardPosition = async (boardLevel: string): Promise<Pt | null> => {
    try {
      const v = await api<LevelView>(`${root}/${boardLevel}@${ELECTRICAL}`);
      const node = v.drawing.nodes.find((n) => n.kind === "TB"), k = metresPerUnit(v.drawing);
      return node && k ? toMetres([node.x, node.y], v.drawing.origin, k) : null;
    } catch { return null; }
  };
  const submitPlenum = async (a: PlenumAnswer) => {
    if (dialog?.type !== "plenum") return;
    setDialogBusy(true);
    try {
      await api(`${root}/plenums`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify({ ...a, discipline: dialog.discipline, level: dialog.level }) });
      const next = dialog.next;
      setDialog(null); setErr("");
      if (next) await createSheet(next); else setRev((n) => n + 1);
    } catch (x) { setErr(errorText(x)); }
    setDialogBusy(false);
  };
  const addPlan = (name: string, subdiscipline: string) => createSheet(newSheetKey(base, discipline, sheets.filter((x) => x.base === base).map((x) => x.level), name, true), discipline, name, subdiscipline);
  const renamePlan = (name: string) => { if (write) change({ ...drawing, plan_name: name }); };
  const setSubdiscipline = (id: string) => { if (write) change({ ...drawing, subdiscipline: id }); };
  const deleteSheet = async (target = level) => {
    if (!window.confirm(tl("layout.confirmDelete"))) return;
    try { await api(`${root}/${target}`, { method: "DELETE" }); const rest = levels.filter((x) => x !== target); if (target === level) setLevel(rest.find((x) => x.split("@")[0] === base) ?? rest[0] ?? ""); setRev((n) => n + 1); } catch (x) { setErr(errorText(x)); }
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
      then(await api<T>(`${root}/${level}/design/${step}`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ drawing, families, board: boardNode?.id ?? "" }) })); setErr("");
    } catch (x) { setErr(errorText(x)); }
    setDesignBusy(false);
  };
  const calcLighting = async (on?: boolean, drawn = false) => {
    setLightBusy(true);
    try { setLighting(await api<LightingProposal>(`/projects/${client}/${code}/lighting/calc`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(requestOf(drawing, lang, { map: on ?? lightMap, use_drawn: drawn })) })); setErr(""); } catch (x) { setErr(errorText(x)); }
    setLightBusy(false);
  };
  const lightKey = useMemo(() => JSON.stringify(requestOf(drawing, lang)), [drawing, lang]);
  useEffect(() => { setLighting(null); setLightApplied(""); }, [level, discipline, lightKey]);        // a proposal is only good for the rooms and parameters it was calculated with
  const verifyLighting = () => calcLighting(undefined, true);
  const compareLight = async (room: string) => {
    try { const r = await api<{ options: CompareRow[]; best: string | null }>(`/projects/${client}/${code}/lighting/compare`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ ...requestOf(drawing, lang), room }) }); setLightCompare({ room, options: r.options, best: r.best }); setErr(""); } catch (x) { setErr(errorText(x)); }
  };
  const useLuminaire = (room: string, luminaire: string) => { change(setRoomLighting(drawing, room, { luminaire })); setLightCompare(null); };
  const applyLight = () => {
    if (!lighting) return;
    const out = applyLighting(drawing, lighting);
    change(out.drawing);
    setLighting(null);
    setLightApplied(tl("light.applied").replace("{n}", String(out.added)).replace("{r}", String(out.removed)));
    keepStudy();
  };
  const keepStudy = async () => {                                      // what was applied is kept as the study of the sheet (the one its report is made from)
    try { const kept = await api<{ report_file?: string; report_error?: string }>(`/projects/${client}/${code}/lighting/study/${encodeURIComponent(level)}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(requestOf(drawing, lang)) }); setStudyRev((n) => n + 1); setReported(kept.report_file ? tl("light.reported").replace("{file}", kept.report_file) : ""); setStudyError(kept.report_error ? tl("light.reportError") + " " + kept.report_error : ""); } catch (x) { setStudyError(tl("light.studyError") + " " + errorText(x)); }
  };
  const makeReport = async () => {
    try { const r = await api<{ file: string }>(`/projects/${client}/${code}/lighting/study/${encodeURIComponent(level)}/report?lang=${lang}`, { method: "POST" }); setReported(tl("light.reported").replace("{file}", r.file)); setStudyRev((n) => n + 1); setStudyError(""); } catch (x) { setStudyError(tl("light.studyError") + " " + errorText(x)); }
  };
  const proposeRuns = () => designCall<RunsProposal>("runs", setRuns);
  const proposeWiring = () => designCall<Proposal>("wiring", setProposal);
  const applyDesignRuns = () => { if (runs) { change(applyRuns(drawing, runs)); setRuns(null); setRev((n) => n + 1); } };
  const applyDesign = async (inBoard: boolean) => {
    if (!proposal) return;
    setDesignBusy(true);
    try {
      if (inBoard) await api(`${root}/${level}/design/circuits`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ board: boardNode?.board ?? "", circuits: proposal.circuits.map((c) => ({ tag: c.tag, description: c.description, load: c.va, unit: "VA" })) }) });
      change(applyProposal(drawing, proposal)); setProposal(null); setRev((n) => n + 1); setErr("");
    } catch (x) { setErr(errorText(x)); }
    setDesignBusy(false);
  };
  const useHintedScale = () => {
    const h = lv?.architecture?.scale_hint;
    if (h && write && drawing.discipline === "arquitectura") change({ ...drawing, scale: { p1: [0, 0], p2: [h.units_per_metre, 0], distance_m: 1 } });
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
  const goProblem = (p: Problem) => { if (p.ref) look([p.ref]); else if (p.tag) setFocus(p.tag); };
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
  const order = ov.data.profiles.map((p) => p.id);                                    // the order a project is worked
  const disciplinesHere = [...usedHere].sort((a, b) => order.indexOf(a) - order.indexOf(b));
  const subs = ov.data.profiles.find((p) => p.id === discipline)?.subdisciplines ?? [];
  const subName = (id: string) => subs.find((x) => x.id === id)?.name[lang] ?? subs.find((x) => x.id === id)?.name.es ?? "";
  const plansHere = sameBase.filter((x) => x.discipline === discipline).map((x) => ({ level: x.level, name: x.level === level ? drawing.plan_name ?? x.plan_name : x.plan_name, sub: subName(x.level === level ? drawing.subdiscipline ?? x.subdiscipline : x.subdiscipline) }));
  const profName = (id: string) => ov.data!.profiles.find((p) => p.id === id)?.name[lang] ?? id;
  const ago = savedAt ? Math.max(0, Math.round((Date.now() - savedAt) / 1000)) : 0;
  const tabs: { id: Panel; label: string; icon: string; badge?: number }[] = [
    { id: "props", label: tl("layout.tab.props"), icon: "select", badge: selection.length }, { id: "plans", label: tl("plan.plans"), icon: "file", badge: plansHere.length > 1 ? plansHere.length : 0 }, { id: "warnings", label: tl("layout.tab.warnings"), icon: "warn", badge: warnings.length },
    { id: "design", label: tl("design.tab"), icon: "star" }, ...(discipline === "electrica_BT" ? [{ id: "lighting" as Panel, label: tl("light.tab"), icon: "sun" }] : []), { id: "layers", label: tl("layers.tab"), icon: "layers" }, { id: "coord", label: tl("coord.tab"), icon: "clash", badge: coord.count }, { id: "history", label: tl("plan.history"), icon: "history" },
  ];
  const boardNodes = drawing.nodes.filter((n) => (profile?.nodes ?? []).some((k) => k.id === n.kind && k.atributos?.includes("tablero")));
  const boardNode = boardNodes.find((n) => n.id === designBoard) ?? boardNodes[0];          // the board symbol the design starts from
  const layerOfKind = (id: string) => [...(profile?.lines ?? []), ...(profile?.nodes ?? [])].find((k) => k.id === id)?.capa_dxf ?? "";
  const layerCounts: Record<string, number> = {};
  [...drawing.nodes, ...drawing.lines].forEach((e) => { const l = layerOfKind(e.kind); if (l) layerCounts[l] = (layerCounts[l] ?? 0) + 1; });
  const found = lv?.architecture?.counts;                                      // what was recognized on the plan, by its layer
  if (lv?.underlay) layerCounts["ARQ-FONDO"] = 1;
  if (found) Object.assign(layerCounts, { "ARQ-MUROS": found.walls, "ARQ-PUERTAS": found.doors, "ARQ-VENTANAS": found.windows, "ARQ-HUECOS": found.openings ?? 0 });
  const tplHere = (templates.data ?? []).filter((x) => x.discipline === discipline);

  return (
    <div className="workbench">
      {dialog?.type === "setup" && <ElectricalSetupDialog levels={bases} busy={dialogBusy} onSubmit={submitSetup} onCancel={() => setDialog(null)} />}
      {dialog?.type === "plenum" && <PlenumDialog title={tl(dialog.mandatory ? "plenum.titleMandatory" : "plenum.title").replace("{discipline}", profName(dialog.discipline))} help={tl(dialog.mandatory ? "plenum.helpMandatory" : "plenum.help")}
        level={dialog.level} nextLevel={dialog.next} defaults={{ x_m: dialog.at[0], y_m: dialog.at[1] }} busy={dialogBusy} onSubmit={submitPlenum} onCancel={() => setDialog(null)} />}
      <div className="wb-top">
        <div className="wb-group" role="tablist" aria-label={tl("layout.level")}>
          {bases.map((x) => <button key={x} role="tab" aria-selected={x === base} className={"lvl" + (x === base ? " on" : "")} onClick={() => setLevel((sheets.find((s) => s.base === x && s.discipline === discipline) ?? sheets.find((s) => s.base === x))!.level)}>{x}</button>)}
          {canWrite && (bases.length === 0
            ? <button className="primary" onClick={() => createSheet("L0")}>+ L0</button>
            : <><button onClick={() => requestLevel("up")} title={tl("layout.addLevel")}>+ {nextLevel(bases, "up")}</button><button onClick={() => requestLevel("down")} title={tl("layout.addLevel")}>+ {nextLevel(bases, "down")}</button></>)}
        </div>
        {level && <div className="wb-group" role="tablist" aria-label={tl("plan.sheets")}>
          {disciplinesHere.map((pid) => { const first = sameBase.find((x) => x.discipline === pid)!; return <button key={pid} role="tab" aria-selected={pid === discipline} className={"lvl disc" + (pid === discipline ? " on" : "")} onClick={() => pid !== discipline && setLevel(first.level)} title={profName(pid)}>{profName(pid)}</button>; })}
          {canWrite && ov.data.profiles.some((p) => p.offered !== false && !usedHere.has(p.id)) && (
            <select className="add-sheet compact" value="" title={tl("plan.addSheet")} aria-label={tl("plan.addSheet")} onChange={(e) => e.target.value && addDiscipline(e.target.value)}>
              <option value="">+</option>{ov.data.profiles.filter((p) => p.offered !== false && !usedHere.has(p.id)).map((p) => <option key={p.id} value={p.id}>{p.name[lang] ?? p.name.es}</option>)}
            </select>)}
        </div>}
        {level && <>
          {write && isArchitecture && <label className="tool-ico wb-upload" title={lv?.underlay ? tl("layout.underlay") : tl("layout.noUnderlay")} aria-label={tl("layout.underlay")}><Icon name="upload" size={18} />
            <input type="file" accept=".png,.jpg,.jpeg,.svg,.dxf,.pdf" disabled={busy} onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }} /></label>}
          {write && isArchitecture && lv?.underlay && <button className="tool-ico" onClick={recognize} disabled={recognizing || busy} title={recognizing ? tl("plan.arch.working") : tl("plan.arch.recognize") + " — " + tl("plan.arch.help")} aria-label={tl("plan.arch.recognize")}><Icon name={recognizing ? "update" : "select"} size={18} /></button>}
          {isArchitecture && lv?.architecture && <span className="badge accent" title={[`${lv.architecture.counts.walls} ${tl("plan.arch.walls")}`, `${lv.architecture.counts.doors} ${tl("plan.arch.doors")}`, `${lv.architecture.counts.windows} ${tl("plan.arch.windows")}`, `${lv.architecture.counts.openings ?? 0} ${tl("plan.arch.openings")}`, ...lv.architecture.warnings].join("\n")}>{lv.architecture.counts.walls} {tl("plan.arch.walls")}</span>}
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
          <select className="compact-select" value={version} title={`${tl("layout.dxfVersion")}: ${tl("layout.latest")}`} aria-label={tl("layout.dxfVersion")} onChange={(e) => setVersion(e.target.value)}>
            <option value="">{ov.data.default_dxf_version}</option>
            {ov.data.dxf_versions.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
          <button className="tool-ico primary" disabled={busy || !drawing.scale || !write} onClick={beforeGenerate} title={!drawing.scale ? tl(drawing.discipline === "arquitectura" ? "layout.needScale" : "layout.needScalePlan") : tl("layout.makeFiles")} aria-label={tl("layout.makeFiles")}><Icon name="file" size={18} /></button>
          {lv?.files?.dxf && <a className="btn" href={download(lv.files.dxf)} title={`${tl("layout.downloadDxf")} (${lv.files.dxf_version})`}>DXF</a>}
          {lv?.files?.pdf && <a className="btn" href={download(lv.files.pdf)} title={tl("layout.downloadPdf")}>PDF</a>}
          {lv?.files && stale && <button className="badge warn" onClick={showChanges} title={tl("plan.changes")}>{tl("layout.filesOutdated")} ▸</button>}
          <button className="tool-ico" onClick={runChecks} title={`${tl("plan.check")} — ${tl("plan.check.help")}`} aria-label={tl("plan.check")}><Icon name="check" size={18} /></button>
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
            allowedKinds={allowedKinds(subs, drawing.subdiscipline)} sheetKey={level} sheetTitle={`${project}_${level}`} architecture={arch} prefs={[prefs, setPrefs]} proposal={runs} lightMarks={[...marksOf(lighting), ...emergencyMarksOf(lighting)]} lightMaps={mapsOf(lighting)} boards={ov.data.boards} roomRequest={roomRequest} ghosts={ghosts} pins={pins} onPin={onPin} problems={problems}
            freeCircuits={ov.data.circuits.map((c) => c.tag).filter((tag) => !drawing.circuits.some((c) => c.tag === tag))} circuitTags={ov.data.circuits.map((c) => c.tag)} focusRequest={focusReq}
            onCopyLevels={(c) => { setCopying(c); setTargets([]); }} onNewPin={(at) => { setPinAt(at); setPinText(""); }} onReserve={reserve} onTemplateSave={saveTemplate} pendingClip={clip} onClipUsed={() => setClip(null)} />
          <aside className="wb-side" aria-label={tl("layout.panel")}>
            <div className="wb-rail" role="tablist" aria-orientation="vertical">
              {tabs.map((x) => <button key={x.id} role="tab" aria-selected={panel === x.id} className={panel === x.id ? "on" : ""} title={x.label} aria-label={x.label} onClick={() => setPanel(panel === x.id ? null : x.id)}><Icon name={x.icon as never} size={20} />{!!x.badge && <span className="dot">{x.badge}</span>}</button>)}
            </div>
            {panel && <div className="wb-panel" role="tabpanel" aria-label={tabs.find((x) => x.id === panel)?.label}>
              <h3 className="wb-panel-h">{tabs.find((x) => x.id === panel)?.label}</h3>
              {pinAt && (
                <div className="coord-form" style={{ marginBottom: 8 }}>
                  <b>{tl("plan.pin.new")}</b>
                  <textarea autoFocus rows={2} value={pinText} onChange={(e) => setPinText(e.target.value)} placeholder={tl("coord.text")} />
                  <div className="row" style={{ gap: 6 }}><button className="primary" disabled={!pinText.trim()} onClick={sendPin}>{tl("coord.send")}</button><button onClick={() => setPinAt(null)}>{tl("layout.cancel")}</button></div>
                </div>
              )}
              {panel === "props" && <Properties drawing={drawing} selection={selection} derived={dp} profile={profile} lang={lang} boardCircuits={ov.data.circuits} readOnly={!write} onChange={change} onSelect={setSelection} t={tl} />}
              {panel === "warnings" && <WarningsPanel warnings={warnings} onJump={jump} tl={tl} />}
              {panel === "plans" && <PlansPanel discipline={profName(discipline)} plans={plansHere} current={level} canWrite={write} subdisciplines={subs.map((x) => ({ id: x.id, name: x.name[lang] ?? x.name.es }))} currentSub={drawing.subdiscipline ?? ""} onSub={setSubdiscipline} onOpen={setLevel} onAdd={addPlan} onRename={renamePlan} onDelete={deleteSheet} />}
              {panel === "lighting" && <LightingPanel drawing={drawing} options={lightOptions.data ?? undefined} proposal={lighting} busy={lightBusy} canWrite={write} onChange={change} onCalc={() => calcLighting()} showMap={lightMap} onMap={(on) => { change(setSetting(drawing, "map", on)); if (lighting) calcLighting(on); }} onVerify={verifyLighting} compare={lightCompare} onCompare={compareLight} onUse={useLuminaire} onCloseCompare={() => setLightCompare(null)} studyError={studyError || (study.error ? tl("light.studyError") + " " + String(study.error) : "")} onApply={applyLight} applied={lightApplied} study={study.data ?? undefined} onReport={makeReport} reported={reported} onDiscard={() => setLighting(null)} onNewRoom={() => setRoomRequest((n) => n + 1)} onLook={(at) => look(undefined, undefined, at)} />}
              {panel === "design" && <DesignPanel drawing={drawing} profile={profile} proposal={proposal} runs={runs} busy={designBusy} canWrite={write} limitsOverride={limits} onLimits={setLimits} onProposeRuns={proposeRuns} onApplyRuns={applyDesignRuns} onDiscardRuns={() => setRuns(null)} onPropose={proposeWiring} onApply={applyDesign} onDiscard={() => setProposal(null)}
                boards={boardNodes.map((n) => ({ id: n.id, name: n.tag || n.id }))} board={boardNode?.id ?? ""} onBoard={setDesignBoard} onChange={change} onNewRoom={() => setRoomRequest((n) => n + 1)} onLook={(at) => look(undefined, undefined, at)} derived={dp} />}
              {panel === "layers" && <LayersPanel client={client} code={code} rev={rev} current={discipline} prefs={prefs} setPrefs={setPrefs} counts={layerCounts} />}
              {panel === "coord" && <Coordination client={client} code={code} discipline={discipline} canWrite={canWrite} onChanged={coord.reload} onFocus={focusAt} />}
              {panel === "history" && <HistoryPanel root={root} level={level} rev={rev + hrev} canWrite={write} comparing={compare?.id ?? ""} onCompare={openCompare} onRestore={restore} tl={tl} />}
            </div>}
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
