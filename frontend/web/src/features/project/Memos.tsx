import { useEffect, useRef, useState } from "react";
import { api, Badge, BoardMemoView, BoardRow, CalcView, errorText, Key, SldStatus, State, useApi, useI18n } from "@epc/ui";
import BoardMemo from "./BoardMemo";
import type { LightingStudy } from "./lightingApi";

interface Props { client: string; code: string; canWrite: boolean; onOpenFiles: () => void }
interface SheetRow { level: string; discipline: string }

/** A run that takes a while on the server: ask for its status in a moment until it is over, then say so. */
function useRun(running: () => Promise<boolean>, over: () => void) {
  const [busy, setBusy] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  const watch = () => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(async () => { if (await running().catch(() => false)) watch(); else { setBusy(false); over(); } }, 1500);
  };
  return { busy, start: () => { setBusy(true); watch(); } };
}

/** One board: the calculation of its cables and protections and its memo and summary, with the button for each. */
function BoardLine({ board, base, client, code, canWrite, rev, refresh }: { board: BoardRow; base: string; client: string; code: string; canWrite: boolean; rev: number; refresh: () => void }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const q = `board=${encodeURIComponent(board.id)}`;
  const memo = useApi<BoardMemoView>(`${base}/sld/memo?${q}&r=${rev}`);
  const calc = useApi<CalcView>(`${base}/sld/calculation?${q}&r=${rev}`);
  const [open, setOpen] = useState(false);
  const [err, setErr] = useState("");
  const run = useRun(async () => (await api<SldStatus>(`${base}/sld/status?${q}`)).state === "running", refresh);
  const ask = async (diagrams: "calc" | "none") => {
    setErr("");
    try { await api(`${base}/sld/generate?diagrams=${diagrams}&${q}`, { method: "POST" }); run.start(); } catch (x) { setErr(errorText(x)); }
  };
  const calculated = (calc.data?.rows.length ?? 0) > 0;
  const m = memo.data;
  const memoState = !m?.available ? "none" : m.stale ? "stale" : "fresh";
  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <b>{board.name}</b>
        <span className="muted small">{board.circuits} {tl("memos.circuits")}</span>
      </div>
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8, alignItems: "center" }}>
        <Badge tone={calculated ? "ok" : "warn"}>{tl(calculated ? "memos.calcDone" : "memos.calcNone")}</Badge>
        <button disabled={!canWrite || run.busy || board.circuits === 0} onClick={() => ask("calc")}>{tl("memos.calc")}</button>
        <span className="muted">·</span>
        <Badge tone={memoState === "fresh" ? "ok" : "warn"}>{tl(`memos.memo.${memoState}`)}</Badge>
        <button className={memoState === "fresh" ? "" : "primary"} disabled={!canWrite || run.busy || board.circuits === 0} onClick={() => ask("none")}>{tl("memos.memo")}</button>
        {m?.available && <button onClick={() => setOpen(!open)}>{tl(open ? "memos.hide" : "memos.view")}</button>}
        {run.busy && <span className="muted small" role="status">{tl("memos.running")}</span>}
      </div>
      {err && <p className="small" role="alert" style={{ margin: "6px 0 0", color: "var(--bad, #b3261e)" }}>{err}</p>}
      {open && m?.available && <div style={{ marginTop: 10 }}><BoardMemo client={client} code={code} v={m} /></div>}
    </div>
  );
}

/** One sheet with lighting: its study and its report, calculated again from the drawing as it is saved. */
function LightLine({ sheet, base, canWrite, lang, rev, refresh, onOpenFiles, what = "lighting" }: { sheet: string; base: string; canWrite: boolean; lang: string; rev: number; refresh: () => void; onOpenFiles: () => void; what?: "lighting" | "receptacles" }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const study = useApi<LightingStudy>(`${base}/${what}/study/${encodeURIComponent(sheet)}?r=${rev}`);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const remake = async () => {
    setBusy(true); setErr("");
    try { await api(`${base}/${what}/study/${encodeURIComponent(sheet)}/remake?lang=${lang}`, { method: "POST" }); refresh(); } catch (x) { setErr(errorText(x)); }
    setBusy(false);
  };
  const s = study.data;
  const state = !s?.exists ? "none" : s.stale ? "stale" : "fresh";
  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <b>{sheet}</b>
      <div className="row" style={{ gap: 8, flexWrap: "wrap", marginTop: 8, alignItems: "center" }}>
        <Badge tone={state === "fresh" ? "ok" : "warn"}>{tl(`memos.study.${state}`)}</Badge>
        <button className={state === "fresh" ? "" : "primary"} disabled={!canWrite || busy} onClick={remake}>{tl("memos.remake")}</button>
        {s?.report && <button onClick={onOpenFiles}>{tl("memos.openFiles")}</button>}
        {busy && <span className="muted small" role="status">{tl("memos.running")}</span>}
      </div>
      {s?.saved_at && <div className="muted small" style={{ marginTop: 4 }}>{s.saved_at}</div>}
      {err && <p className="small" role="alert" style={{ margin: "6px 0 0", color: "var(--bad, #b3261e)" }}>{err}</p>}
    </div>
  );
}

/** Every generator of memos of the project in one place: the cables and protections of each board, its memo and summary, and the lighting study of each plan. Issue turns them into PDF. */
export default function Memos({ client, code, canWrite, onOpenFiles }: Props) {
  const { t, lang } = useI18n();
  const tl = (k: string) => t(k as Key);
  const base = `/projects/${client}/${code}`;
  const [rev, setRev] = useState(0);
  const boards = useApi<BoardRow[]>(`${base}/sld/boards?r=${rev}`);
  const sheets = useApi<{ levels: SheetRow[] }>(`${base}/layout?r=${rev}`);
  const refresh = () => setRev((n) => n + 1);
  if (!boards.data || !sheets.data) return <State loading={boards.loading || sheets.loading} error={boards.error || sheets.error} />;
  const electrical = sheets.data.levels.filter((x) => x.discipline === "electrica_BT");
  return (
    <>
      <p className="muted small">{tl("memos.help")}</p>
      <h3>{tl("memos.boards")}</h3>
      {boards.data.length === 0 ? <div className="state">{tl("memos.noBoards")}</div>
        : boards.data.map((b) => <BoardLine key={b.id} board={b} base={base} client={client} code={code} canWrite={canWrite} rev={rev} refresh={refresh} />)}
      <h3>{tl("memos.lighting")}</h3>
      {electrical.length === 0 ? <div className="state">{tl("memos.noSheets")}</div>
        : electrical.map((x) => <LightLine key={x.level} sheet={x.level} base={base} canWrite={canWrite} lang={lang} rev={rev} refresh={refresh} onOpenFiles={onOpenFiles} />)}
      <h3>{tl("memos.receptacles")}</h3>
      {electrical.length === 0 ? <div className="state">{tl("memos.noSheets")}</div>
        : electrical.map((x) => <LightLine key={x.level} what="receptacles" sheet={x.level} base={base} canWrite={canWrite} lang={lang} rev={rev} refresh={refresh} onOpenFiles={onOpenFiles} />)}
      <p className="muted small" style={{ marginTop: 10 }}>{tl("memos.cablesNote")}</p>
    </>
  );
}
