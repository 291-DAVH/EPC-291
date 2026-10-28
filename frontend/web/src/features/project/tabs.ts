export const TABS = ["inputs", "requirements", "plan", "engineering", "coordination", "catalogs", "deliverables", "observations", "reports", "overview"] as const;      // tab order: a project starts from its input data; Resumen is last but the default
export type Tab = (typeof TABS)[number];
export const ENGINEER_TABS: Tab[] = ["engineering", "coordination", "catalogs"];          // internal work: admin/engineer role only

/** Where the screens that were tabs of their own now live: the drawings are a section of Engineering and the registers a section of Management (the `plan` tab). Old links keep working. */
export const MOVED: Record<string, { tab: Tab; sub: string }> = { layout: { tab: "engineering", sub: "layout" }, registers: { tab: "plan", sub: "registers" } };

/** The tab and the section a link asks for: the tab of the link, or the one its screen moved to. */
export function placeOf(tab: string | null, sub: string | null): { tab: string | null; sub: string | null } {
  const moved = tab ? MOVED[tab] : undefined;
  return moved ? { tab: moved.tab, sub: moved.sub } : { tab, sub };
}
