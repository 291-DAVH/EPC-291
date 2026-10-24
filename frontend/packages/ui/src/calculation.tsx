import { Badge } from "./components";
import { CalcView } from "./api";
import { Key, useI18n } from "./i18n";

/** A calculation result as a readable table: criteria that governed it, a summary and one row per circuit. */
export function CalculationTable({ view }: { view: CalcView }) {
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
      <div style={{ overflowX: "auto" }}>
        <table className="sldtable">
          <thead><tr><th>{t("sld.tag")}</th><th>{t("sld.desc")}</th><th>{t("sld.col.type")}</th><th>{t("sld.col.ib")}</th><th>{t("sld.col.in")}</th><th>{t("sld.col.icu")}</th><th>{t("sld.col.s")}</th><th>{t("sld.col.du")}</th><th>{t("sld.col.limit")}</th><th>{t("sld.col.device")}</th><th>{t("sld.col.ok")}</th></tr></thead>
          <tbody>
            {view.rows.map((r) => (
              <tr key={r.tag}>
                <td className="mono">{r.tag}</td><td>{r.description}</td>
                <td>{r.tipo ? t(("sld.type." + r.tipo) as Key) : ""}</td>
                <td className="mono">{r.Ib}</td><td className="mono">{r.In}</td><td className="mono">{r.icu}</td><td className="mono">{r.S}</td>
                <td className="mono">{r.dU}</td><td className="mono">{r.limite_pct ?? ""}</td><td>{r.disp}</td>
                <td>{r.cumple == null ? "" : r.cumple ? <Badge tone="ok">✓</Badge> : <Badge tone="bad">✗</Badge>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
