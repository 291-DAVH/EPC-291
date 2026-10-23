import { useState } from "react";
import { Badge, EngFile, EngOverview, EngText, Key, State, useApi, useI18n } from "@epc/ui";

/** Engineering workspace of a project: SVG diagrams (single-line, multi-line, drawings) and lists/notes as text. Engineer/admin only. */
export default function Engineering({ client, code }: { client: string; code: string }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/engineering`;
  const ov = useApi<EngOverview>(base);
  const [sel, setSel] = useState<EngFile | null>(null);
  if (!ov.data) return <State loading={ov.loading} error={ov.error} />;
  const all = [...ov.data.diagrams, ...ov.data.documents];
  if (all.length === 0) return <div className="state">{t("eng.empty")}</div>;
  const current = sel ?? ov.data.diagrams[0] ?? ov.data.documents[0];

  const item = (f: EngFile) => (
    <button key={f.path} className={current.path === f.path ? "on" : ""} onClick={() => setSel(f)} title={f.path}>
      <span>{f.name}<br /><small className="muted">{f.discipline}</small></span>
      <Badge>{t(("eng.k." + f.kind) as Key)}</Badge>
    </button>
  );
  return (
    <>
      <p className="muted small">{t("eng.internal")}</p>
      <div className="eng">
        <div className="card eng-list">
          {ov.data.diagrams.length > 0 && <h3>{t("eng.diagrams")}</h3>}
          {ov.data.diagrams.map(item)}
          {ov.data.documents.length > 0 && <h3>{t("eng.documents")}</h3>}
          {ov.data.documents.map(item)}
        </div>
        <div className="card">
          <div className="muted small" style={{ marginBottom: 8 }}>{current.discipline} / {current.package} / <span className="mono">{current.name}{current.ext}</span></div>
          {current.what === "diagram" ? <SvgView base={base} f={current} /> : <TextView base={base} f={current} />}
        </div>
      </div>
    </>
  );
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

function TextView({ base, f }: { base: string; f: EngFile }) {
  const { t } = useI18n();
  const r = useApi<EngText>(`${base}/text?path=${encodeURIComponent(f.path)}`);
  if (!r.data) return <State loading={r.loading} error={r.error} />;
  const d = r.data;
  const table = (rows: string[][]) => (
    <div className="eng-view" style={{ background: "var(--panel)" }}>
      <table className="eng-table"><tbody>{rows.map((row, i) => <tr key={i}>{row.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody></table>
    </div>
  );
  return (
    <>
      {d.format === "text" && <pre className="eng-text eng-view" style={{ background: "var(--panel)" }}>{d.text}</pre>}
      {d.format === "table" && table(d.rows)}
      {d.format === "sheets" && Object.entries(d.sheets).map(([name, rows]) => <div key={name}><b>{name}</b>{table(rows)}</div>)}
      {d.format !== "sheets" && d.truncated && <p className="muted small">{t("eng.truncated")}</p>}
    </>
  );
}
