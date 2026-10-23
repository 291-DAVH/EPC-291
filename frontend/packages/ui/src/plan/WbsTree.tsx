import { WbsView } from "../api";
import { Badge, Progress } from "../components";
import { useI18n } from "../i18n";

/** WBS as an indented list with rolled-up progress. */
export function WbsTree({ wbs }: { wbs: WbsView }) {
  const { t } = useI18n();
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 style={{ margin: 0 }}>{t("plan.wbs")}</h2>
        <span className="muted small">{wbs.counts.leaves} {t("plan.packages")} · {wbs.counts.done} {t("plan.done")} · <b className="mono">{wbs.progress}%</b></span>
      </div>
      <table className="wbs">
        <tbody>
          {wbs.nodes.map((n) => (
            <tr key={n.id} className={n.leaf ? "" : "wbs-group"}>
              <td className="mono wbs-id">{n.id}</td>
              <td style={{ paddingLeft: (n.level - 1) * 18 + 8 }}>{n.leaf ? n.name : <b>{n.name}</b>}</td>
              <td style={{ width: 160 }}><Progress pct={n.progress} /></td>
              <td className="mono" style={{ width: 56, textAlign: "right" }}>{n.progress}%</td>
              <td style={{ width: 40 }}>{n.status === "done" && <Badge tone="ok">✓</Badge>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
