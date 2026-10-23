import { Link } from "react-router-dom";
import { Overview, StandardInfo, useApi } from "@epc/ui";
import { Badge, Page, State, statusTone } from "@epc/ui";
import { useI18n } from "@epc/ui";

export default function Dashboard() {
  const { t } = useI18n();
  const ov = useApi<Overview>("/overview");
  const stds = useApi<StandardInfo[]>("/rules/standards");
  const o = ov.data;
  const verified = o?.standards_by_status?.verified ?? 0;
  return (
    <Page title={t("dash.title")}>
      <State loading={ov.loading} error={ov.error} />
      {o && (
        <>
          <div className="grid stats">
            <Stat n={o.plugins} label={t("dash.plugins")} to="/plugins" />
            <Stat n={o.skills} label={t("dash.skills")} to="/skills" />
            <Stat n={o.standards} label={t("dash.standards")} to="/rules" />
            <Stat n={o.rules} label={t("dash.rules")} to="/rules" />
            <Stat n={o.rules_with_check} label={t("dash.checks")} to="/checker" />
            <Stat n={o.derived_checks} label={t("dash.derived")} to="/rules" />
            <Stat n={o.projects} label={t("dash.projects")} to="/files" />
          </div>
          <h2>{t("dash.alerts")}</h2>
          {verified === 0 && <div className="alert">{t("dash.alert.draft")}</div>}
          {o.derived_checks > 0 && <div className="alert">{o.derived_checks} {t("dash.alert.derived")}</div>}
          {o.plugins_pending > 0 && <div className="alert">{o.plugins_pending} {t("dash.alert.pending")}</div>}
          {o.skill_conflicts.length > 0 ? (
            <div className="alert bad">{o.skill_conflicts.length} {t("dash.alert.conflicts")}</div>
          ) : (
            <div className="alert ok">{t("dash.alert.ok")}</div>
          )}
          <p className="muted">{t("dash.env")}: <Badge>{o.env}</Badge></p>
        </>
      )}
      {stds.data && (
        <>
          <h2>{t("rules.standards")}</h2>
          <div className="grid cards">
            {stds.data.map((s) => (
              <Link key={s.id} to={`/rules?standard=${s.id}`} className="card">
                <div className="row between">
                  <b>{s.id}</b>
                  <Badge tone={statusTone(s.status)}>{s.status}</Badge>
                </div>
                <div className="muted">{s.body} · {s.edition}</div>
                <div className="row" style={{ marginTop: 8 }}>
                  <Badge>{s.rules} {t("rules.results")}</Badge>
                  <Badge tone="accent">{s.with_check} {t("common.check").toLowerCase()}</Badge>
                  {s.low_confidence > 0 && <Badge tone="warn">{s.low_confidence} {t("rules.lowConf")}</Badge>}
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </Page>
  );
}

function Stat({ n, label, to }: { n: number; label: string; to: string }) {
  return (
    <Link to={to} className="card stat">
      <b>{n}</b>
      <span>{label}</span>
    </Link>
  );
}
