import { useNavigate } from "react-router-dom";
import { Page } from "@epc/ui";
import { useI18n } from "@epc/ui";
import { NewProject } from "@epc/ui";

export default function NewProjectPage() {
  const { t } = useI18n();
  const nav = useNavigate();
  return (
    <Page title={t("u.nav.new")} help={t("u.np.help")}>
      <NewProject onCancel={() => nav("/")} onCreated={(p) => nav(`/projects/${p.id}`)} />
    </Page>
  );
}
