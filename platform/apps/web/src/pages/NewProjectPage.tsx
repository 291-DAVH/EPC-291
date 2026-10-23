import { useNavigate } from "react-router-dom";
import { Page } from "../components";
import { useI18n } from "../i18n";
import NewProject from "./NewProject";

export default function NewProjectPage() {
  const { t } = useI18n();
  const nav = useNavigate();
  return (
    <Page title={t("u.nav.new")} help={t("u.np.help")}>
      <NewProject onCancel={() => nav("/")} onCreated={(p) => nav(`/projects/${p.id}`)} />
    </Page>
  );
}
