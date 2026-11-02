import { useState } from "react";
import DesignCriteria from "./DesignCriteria";
import Layout from "./Layout";
import SldInput from "./SldInput";
import Memos from "./Memos";
import Catalogs from "./Catalogs";
import Coordination from "./Coordination";
import { Badge, CalcView, CalculationTable, EngFile, EngOverview, EngText, Key, Markdown, PdfViewer, State, docName, useApi, useI18n } from "@epc/ui";

type Sub = "criteria" | "sld" | "memos" | "layout" | "coordination" | "catalogs" | "files";

/** Engineering workspace of a project: in the order the work goes: the design criteria, the technical information (single-line data), the memos, the drawings (every discipline over the plan), the coordination between disciplines, the catalogs of the project and, at the end, the files. Engineer/admin only. */
export default function Engineering({ client, code, disciplines, onOpenTeam, sub: subParam, onSub, canWrite }: { client: string; code: string; disciplines: string[]; onOpenTeam: () => void; sub: string; onSub: (x: string) => void; canWrite: boolean }) {
  const { t } = useI18n();
  const [picked, setPicked] = useState("");
  const disc = disciplines.includes(picked) ? picked : disciplines.includes("electrical") ? "electrical" : disciplines[0] ?? "electrical";
  const SUBS = [...(disc === "electrical" ? ["criteria", "sld", "memos"] : ["criteria"]), "layout", "coordination", "catalogs", "files"] as Sub[];          // the tools of calculation are the electrical ones; the rest is of the whole project
  const sub = (SUBS as readonly string[]).includes(subParam) ? (subParam as Sub) : "criteria";
  const setSub = (x: Sub) => onSub(x);
  return (
    <>
      {disciplines.length > 1 && (
        <div className="filters" role="group" aria-label={t("eng.discipline")}>
          {disciplines.map((x) => <button key={x} className={"chipbtn" + (disc === x ? " on" : "")} onClick={() => setPicked(x)}>{t(("projects.disc." + x) as Key)}</button>)}
        </div>
      )}
      <div className="subtabs" role="tablist">
        {SUBS.map((x) => (
          <button key={x} role="tab" aria-selected={sub === x} className={sub === x ? "on" : ""} onClick={() => setSub(x)}>{t(("eng.sub." + x) as Key)}</button>
        ))}
      </div>
      {sub === "files" && <Files client={client} code={code} discipline={disciplines.length > 1 ? disc : ""} />}
      {sub === "layout" && <Layout client={client} code={code} canWrite={canWrite} />}
      {sub === "sld" && <SldInput client={client} code={code} onOpenFiles={() => setSub("files")} onOpenParties={onOpenTeam} onOpenMemos={() => setSub("memos")} />}
      {sub === "memos" && <Memos client={client} code={code} canWrite={canWrite} onOpenFiles={() => setSub("files")} />}
      {sub === "criteria" && <DesignCriteria key={disc} client={client} code={code} discipline={disc} />}
      {sub === "coordination" && <Coordination client={client} code={code} discipline="" canWrite={canWrite} standalone />}
      {sub === "catalogs" && <Catalogs client={client} code={code} />}
    </>
  );
}

function Files({ client, code, discipline }: { client: string; code: string; discipline: string }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/engineering`;
  const [tech, setTech] = useState(false);                // technical files of the software: administration only, hidden by default
  const ov = useApi<EngOverview>(base + (tech ? "?technical=true" : ""));
  const [sel, setSel] = useState<EngFile | null>(null);
  if (!ov.data) return <State loading={ov.loading} error={ov.error} />;
  const mine = (f: EngFile) => !discipline || f.discipline === discipline;                  // a project of several disciplines lists the files of the one chosen
  const diagrams = ov.data.diagrams.filter(mine), documents = ov.data.documents.filter(mine);
  const all = [...diagrams, ...documents];
  if (all.length === 0) return <div className="state">{t("eng.empty")}</div>;
  const current = all.find((f) => f.path === sel?.path) ?? diagrams[0] ?? documents[0];

  const item = (f: EngFile) => (
    <button key={f.path} className={current.path === f.path ? "on" : ""} onClick={() => setSel(f)} title={f.path}>
      <span>{docName(f, t)}<br /><small className="muted">{f.discipline}</small></span>
      <Badge>{t(("eng.k." + f.kind) as Key)}</Badge>
    </button>
  );
  return (
    <>
      <p className="muted small">{t("eng.internal")}</p>
      <label className="small muted" style={{ display: "block", marginBottom: 8 }}><input type="checkbox" checked={tech} onChange={(e) => { setTech(e.target.checked); setSel(null); }} /> {t("eng.showTech")}</label>
      <div className="eng">
        <div className="card eng-list">
          {diagrams.length > 0 && <h3>{t("eng.diagrams")}</h3>}
          {diagrams.map(item)}
          {documents.length > 0 && <h3>{t("eng.documents")}</h3>}
          {documents.map(item)}
        </div>
        <div className="card">
          <div className="muted small" style={{ marginBottom: 8 }}>{current.discipline} / {current.package} / <span className="mono">{current.name}{current.ext}</span></div>
          {current.what === "diagram" ? <SvgView base={base} f={current} /> : current.kind === "calculation" ? <CalcFile base={base} f={current} /> : current.kind === "pdf" ? <PdfView base={base} f={current} /> : <TextView base={base} f={current} />}
        </div>
      </div>
    </>
  );
}

/** A document made as a PDF (a calculation report), shown by the program's PDF reader. */
function PdfView({ base, f }: { base: string; f: EngFile }) {
  return <PdfViewer key={f.path} path={`${base}/pdf?path=${encodeURIComponent(f.path)}`} title={f.name} />;
}

function SvgView({ base, f }: { base: string; f: EngFile }) {
  const { t } = useI18n();
  const [zoom, setZoom] = useState(0);                       // 0 = fit to width
  const src = `/api${base}/svg?path=${encodeURIComponent(f.path)}`;
  return (
    <>
      <div className="row" style={{ marginBottom: 8 }}>
        <button onClick={() => setZoom((z) => (z || 100) + 25)}>{t("eng.zoomIn")}</button>
        <button onClick={() => setZoom((z) => Math.max(25, (z || 100) - 25))}>{t("eng.zoomOut")}</button>
        <button onClick={() => setZoom(0)}>{t("eng.fit")}</button>
      </div>
      <div className="eng-view">
        <img key={f.path} src={src} alt={f.name} style={zoom ? { width: `${zoom}%` } : { width: "100%", maxWidth: "100%" }} />
      </div>
    </>
  );
}

function CalcFile({ base, f }: { base: string; f: EngFile }) {
  const r = useApi<CalcView>(`${base}/calculation?path=${encodeURIComponent(f.path)}`);
  if (!r.data) return <State loading={r.loading} error={r.error} />;
  return <CalculationTable view={r.data} />;
}

function TextView({ base, f }: { base: string; f: EngFile }) {
  const { t } = useI18n();
  const r = useApi<EngText>(`${base}/text?path=${encodeURIComponent(f.path)}${f.kind === "technical" ? "&technical=true" : ""}`);
  if (!r.data) return <State loading={r.loading} error={r.error} />;
  const d = r.data;
  const table = (rows: string[][]) => (
    <div className="eng-view" style={{ background: "var(--panel)" }}>
      <table className="eng-table"><tbody>{rows.map((row, i) => <tr key={i}>{row.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody></table>
    </div>
  );
  return (
    <>
      {d.format === "text" && (f.ext === ".md" ? <div className="eng-view" style={{ background: "var(--panel)", padding: 12 }}><Markdown text={d.text} /></div> : <pre className="eng-text eng-view" style={{ background: "var(--panel)" }}>{d.text}</pre>)}
      {d.format === "table" && table(d.rows)}
      {d.format === "sheets" && Object.entries(d.sheets).map(([name, rows]) => <div key={name}><b>{name}</b>{table(rows)}</div>)}
      {d.format !== "sheets" && d.truncated && <p className="muted small">{t("eng.truncated")}</p>}
    </>
  );
}
