export const TABS = ["inputs", "requirements", "plan", "registers", "engineering", "layout", "deliverables", "observations", "reports", "overview"] as const;      // tab order: a project starts from its input data; Resumen is last but the default
export type Tab = (typeof TABS)[number];
export const ENGINEER_TABS: Tab[] = ["engineering", "layout", "registers"];          // internal work: admin/engineer role only
