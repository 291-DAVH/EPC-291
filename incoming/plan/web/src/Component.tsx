/** The screen of the module. It takes its data as props and reports changes through callbacks: it never calls the backend itself (the integration does).
 *  Text goes through a `t()` function with Spanish and English entries; here a minimal one so the demo runs alone. */
const TEXT: Record<string, string> = { title: "plan", items: "elementos" };
const t = (k: string) => TEXT[k] ?? k;

export interface Props { document: { items?: unknown[] }; onChange?: (next: unknown) => void }

export default function Component({ document }: Props) {
  return (
    <div style={{ fontFamily: "system-ui", padding: 16 }}>
      <h1>{t("title")}</h1>
      <p>{document.items?.length ?? 0} {t("items")}</p>
    </div>
  );
}
