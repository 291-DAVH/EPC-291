export const TABS = ["inputs", "requirements", "plan", "engineering", "reports", "overview"] as const;      // tab order: a project starts from its input data; Resumen is last but the default
export type Tab = (typeof TABS)[number];
export const ENGINEER_TABS: Tab[] = ["engineering"];          // internal work: admin/engineer role only

/** Where the screens that were tabs of their own now live: the drawings, the coordination and the catalogs of the project are sections of Engineering; the registers and the deliverables of Management
 * (the `plan` tab); the observations of Reports. Old links keep working. */
export const MOVED: Record<string, { tab: Tab; sub: string }> = {
  layout: { tab: "engineering", sub: "layout" }, coordination: { tab: "engineering", sub: "coordination" }, catalogs: { tab: "engineering", sub: "catalogs" },
  registers: { tab: "plan", sub: "registers" }, deliverables: { tab: "plan", sub: "deliverables" }, observations: { tab: "reports", sub: "observations" },
};

/** Sections of Engineering that went to Management: issuing is delivering, and the parties of the project are part of its setup. */
export const SUB_MOVED: Record<string, { tab: Tab; sub: string }> = { "engineering/issue": { tab: "plan", sub: "issue" }, "engineering/parties": { tab: "plan", sub: "team" } };

/** The tab and the section a link asks for: the tab of the link, or the one its screen moved to. */
export function placeOf(tab: string | null, sub: string | null): { tab: string | null; sub: string | null } {
  const moved = (tab && sub ? SUB_MOVED[`${tab}/${sub}`] : undefined) ?? (tab ? MOVED[tab] : undefined);
  return moved ? { tab: moved.tab, sub: moved.sub } : { tab, sub };
}
