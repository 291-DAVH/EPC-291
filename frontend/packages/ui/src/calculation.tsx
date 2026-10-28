import { Badge } from "./components";
import { CalcRow, CalcView } from "./api";
import { Key, useI18n } from "./i18n";

/** The columns of a calculation result, after the tag and the description. */
export const CALC_HEADS = ["sld.col.type", "sld.col.ib", "sld.col.in", "sld.col.icu", "sld.col.s", "sld.col.du", "sld.col.limit", "sld.col.device", "sld.col.ok"] as Key[];

/** What a calculation gave for one circuit, as the cells of a table row (empty cells when there is no result for it yet). */
export function CalcCells({ row }: { row?: CalcRow }) {
  const { t } = useI18n();
  if (!row) return <>{CALC_HEADS.map((h) => <td key={h} />)}</>;
  return (
    <>
      <td>{row.tipo ? t(("sld.type." + row.tipo) as Key) : ""}</td>
      <td className="mono">{row.Ib}</td><td className="mono">{row.In}</td><td className="mono">{row.icu}</td><td className="mono">{row.S}</td>
      <td className="mono">{row.dU}</td><td className="mono">{row.limite_pct ?? ""}</td><td>{row.disp}</td>
      <td>{row.cumple == null ? "" : row.cumple ? <Badge tone="ok">✓</Badge> : <Badge tone="bad">✗</Badge>}</td>
    </>
  );
}

/** The summary of a calculation and the criteria that governed it. */
export function CalcHeader({ view }: { view: CalcView }) {
  const { t } = useI18n();
  const c = view.criteria;
  const s = view.summary;
  return (
    <>
      {s && (
        <p className="row small" style={{ margin: "0 0 8px", flexWrap: "wrap" }}>
          <Badge>{s.circuits} {t("calc.circuits")}</Badge>
          <Badge tone="ok">{s.compliant} {t("calc.compliant")}</Badge>
          {s.non_compliant > 0 && <Badge tone="bad">{s.non_compliant} {t("calc.nonCompliant")}</Badge>}
        </p>
      )}
      {c?.limits_pct && (
        <p className="small" style={{ margin: "0 0 8px" }}>
          <b>{t("sld.calcLimits")}:</b> {t("sld.calcSectional")} {c.limits_pct.seccional} % · {t("sld.calcTerminal")} {c.limits_pct.terminal} % · {t("sld.calcMotor")} {c.limits_pct.motor} %
          {c.conductor && <>{" · "}<b>{t("sld.calcConductor")}:</b> {c.conductor.material === "cu" ? "Cu" : "Al"} {c.conductor.aislacion.toUpperCase()}</>}
        </p>
      )}
    </>
  );
}

/** A calculation result as a readable table: criteria that governed it, a summary and one row per circuit. */
export function CalculationTable({ view }: { view: CalcView }) {
  const { t } = useI18n();
  return (
    <>
      <CalcHeader view={view} />
      <div style={{ overflowX: "auto" }}>
        <table className="sldtable">
          <thead><tr><th>{t("sld.tag")}</th><th>{t("sld.desc")}</th>{CALC_HEADS.map((h) => <th key={h}>{t(h)}</th>)}</tr></thead>
          <tbody>
            {view.rows.map((r) => (
              <tr key={r.tag}><td className="mono">{r.tag}</td><td>{r.description}</td><CalcCells row={r} /></tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
