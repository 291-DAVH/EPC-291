import { Skill, useApi } from "../../api";
import { Badge, Page, State } from "../../components";
import { useI18n } from "../../i18n";

export default function Skills() {
  const { t } = useI18n();
  const { data, loading, error } = useApi<Skill[]>("/skills");
  return (
    <Page title={t("skills.title")} help={t("skills.help")}>
      <State loading={loading} error={error} />
      {data && (
        <div className="card scroll">
          <table>
            <thead>
              <tr><th>Skill</th><th>{t("common.owner")}</th><th>{t("common.status")}</th><th>{t("common.summary")}</th></tr>
            </thead>
            <tbody>
              {data.map((s) => (
                <tr key={s.id}>
                  <td><b className="mono">{s.id}</b>{s.legacy_id && <div className="muted">{t("skills.legacy")}: {s.legacy_id}</div>}</td>
                  <td>{s.owner ? <Badge tone="accent">{s.owner}</Badge> : "—"}</td>
                  <td><Badge tone={s.active ? "ok" : "warn"}>{s.active ? t("skills.active") : t("skills.inactive")}</Badge></td>
                  <td className="muted">{s.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Page>
  );
}
