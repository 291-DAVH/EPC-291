import { useEffect, useState } from "react";

export class ApiError extends Error {
  constructor(public status: number, public body: any) {
    super(`${status}`);
  }
  get fieldErrors(): Record<string, string> {
    return this.body?.detail?.errors ?? {};
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch("/api" + path, { credentials: "same-origin", ...init });
  if (r.status === 401 && !path.startsWith("/auth/")) window.dispatchEvent(new Event("epc-unauthorized"));      // the session ended: show the sign-in again
  if (!r.ok) {
    let body: unknown = null;
    try {
      body = await r.json();
    } catch {
      /* no body */
    }
    throw new ApiError(r.status, body);
  }
  return r.json();
}

export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (path === null) return;
    let live = true;
    setLoading(true);
    setError(null);
    api<T>(path)
      .then((d) => live && setData(d))
      .catch((e) => live && setError(String(e)))
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [path]);
  return { data, error, loading };
}

export interface Overview {
  env: string; plugins: number; plugins_pending: number; skills: number; standards: number;
  standards_by_status: Record<string, number>; rules: number; rules_with_check: number; derived_checks: number;
  projects: number; skill_conflicts: { level: string; code: string; message: string }[];
}
export interface Plugin {
  id: string; version: string; kind: string; status: string; description: string; discipline: string[];
  requires: Record<string, string>; required_by: string[]; skills: { id: string; role: string }[];
  outputs: { format: string; channel: string }[]; entitlement?: string; python: string[]; readme?: string;
}
export interface Skill { id: string; owner: string | null; description: string; legacy_id?: string | null; active: boolean }
export interface StandardInfo {
  id: string; body: string; edition: string; domain: string; status: string; validated_by?: string | null;
  rules: number; with_check: number; derived: number; low_confidence: number;
}
export interface RuleView {
  id: string; standard: string; status: string; clause: string; part?: string | null; page?: number | string | null;
  topic: string; title: string; type: "mandatory" | "recommended" | "prohibited"; summary: Record<string, string>;
  has_check: boolean; derived: boolean; confidence?: string; verification?: string; installation_types: string[];
  params?: Record<string, unknown>; check?: { field: string; op: string; value: unknown; derived?: boolean } | null;
}
export interface Finding {
  rule_id: string; standard: string; clause: string; type: string; passed: boolean | null; message: string;
  field: string; expected: unknown; actual: unknown; source_status: string; reason: string;
}
export interface Project {
  id: string; name: string; client: string; project_code: string; jurisdiction: string; locale: string; methodology: string;
  disciplines: string[]; phase: string; workspace_files: number; deliverable_files: number; is_template: boolean; org?: string;
}
export interface TreeNode {
  name: string; type: "dir" | "file"; files?: number; children?: TreeNode[]; ext?: string; size?: number; deliver?: boolean; role?: string;
}
export interface ProjectOptions {
  jurisdictions: { id: string; name: string; default_locale: string; status: string; disciplines: string[] }[];
  methodologies: { id: string; name: string; available: boolean; default: boolean }[];
  locales: string[];
  phases: string[];
}
export interface NewProjectBody {
  client_name: string; client_code: string; project_code: string; project_name: string; jurisdiction: string;
  methodology: string; locale: string; disciplines: string[]; phase: string;
}

export type AccountType = "staff" | "reviewer" | "inspector" | "auditor" | "individual" | "corporate_owner" | "corporate_admin" | "corporate_member" | "";
export interface Me {
  role: string; name: string; org: string; auth?: "simulated" | "required"; authenticated?: boolean; email?: string;
  org_slug?: string; org_kind?: "individual" | "company" | ""; org_role?: "owner" | "admin" | "member" | ""; signup?: boolean;
  username?: string; has_password?: boolean; account_type?: AccountType; landing?: string; app_url?: string; console_url?: string; abilities?: Record<string, string[]>; assigned?: string[];
  organizations?: { slug: string; name: string; kind: "individual" | "company"; role: "owner" | "admin" | "member"; current: boolean }[];
}
export interface PortfolioProject {
  id: string; name: string; client: string; code: string; disciplines: string[]; state: string; phase: string; progress: number;
  health: "on_track" | "at_risk" | "delayed"; manager: string; location: string; start?: string; due?: string;
  next_milestone?: { name: string; date: string; done: boolean } | null; updated?: string;
  deliverables: { total: number; delivered: number; overdue: number }; inputs: { total: number; open: number };
  milestones?: { name: string; date: string; done: boolean }[]; requirements_count?: number;
}
export interface Portfolio {
  today: string; projects: PortfolioProject[];
  kpis: { total: number; active: number; closed: number; on_track: number; at_risk: number; delayed: number;
          deliverables_delivered: number; deliverables_total: number; deliverables_due_soon: number; inputs_open: number };
}
export interface DeliverableItem {
  id: string; code: string; name: string; discipline: string; format: string; revision: string; status: string;
  due?: string; delivered_on?: string; downloadable: boolean; overdue: boolean; formats: string[];
}
export interface PackageGroup { id: string; emission: string; transmittal: string; rev: string; count: number }
export interface PackagesView { count: number; rev: string; groups: PackageGroup[] }
export interface InputItem {
  id: string; kind: string; title: string; text: string; source: string; created: string; status: string; attachments: { name: string; size: number }[];
}
export interface RequirementItem {
  id: string; statement: string; type: string; priority: string; discipline: string; acceptance: string[]; open_questions: string[];
  source_titles: string[]; status: string;
  answered_questions?: { question: string; answer: string; by: string; by_email?: string; at: string }[];
}
export interface ReportItem { id: string; title: string; type: string; date: string; summary: string; downloadable: boolean }

/* ---- planning (WBS, schedule, backlog) ---- */
export interface WbsNode {
  id: string; name: string; parent: string; level: number; leaf: boolean; discipline: string; owner: string;
  weight: number; progress: number; status: "not_started" | "in_progress" | "done";
}
export interface WbsView { nodes: WbsNode[]; progress: number; counts: { nodes: number; leaves: number; done: number } }
export interface Activity {
  id: string; name: string; start: string; end: string; wbs_id: string; depends_on: string[]; milestone: boolean; progress: number;
  duration_days: number; slack_days: number; critical: boolean; conflict: boolean; late: boolean;
}
export interface ScheduleView {
  activities: Activity[]; start: string | null; end: string | null; span_days: number; critical_path: string[];
  counts: { activities: number; late: number; conflicts: number };
}
export interface BacklogItem {
  id: string; title: string; type: string; priority: string; status: string; estimate_h: number; wbs_id: string;
  requirement_id: string; owner: string; created: string;
}
export interface BacklogView { items: BacklogItem[]; counts: Record<string, number>; estimate_open_h: number }

/* ---- engineering workspace (admin/engineer role) ---- */
export interface EngFile {
  path: string; discipline: string; package: string; area: string; name: string; ext: string; what: "diagram" | "document";
  size: number; modified: string; kind: string;
}
export interface EngOverview { diagrams: EngFile[]; documents: EngFile[]; counts: { diagrams: number; documents: number; by_kind: Record<string, number> } }
export type EngText =
  | { name: string; format: "text"; text: string; truncated: boolean }
  | { name: string; format: "table"; rows: string[][]; truncated: boolean }
  | { name: string; format: "sheets"; sheets: Record<string, string[][]> };

/* ---- design criteria ---- */
export interface Criterion {
  id: string; group: { en: string; es: string }; label: { en: string; es: string }; unit: string; type: "number" | "choice" | "text";
  min?: number; max?: number; options?: (string | number)[]; default: string | number; value: string | number;
  overridden: boolean; source: string; note: string; updated: string | null;
}
export interface CriteriaHistory { key: string; from: string | number; to: string | number; source: string; note: string; at: string }
export interface CriteriaView {
  discipline: string; jurisdiction: string; validated: boolean; notice: string; items: Criterion[]; changed: number; history: CriteriaHistory[];
}

/* ---- single-line diagram input ---- */
export interface SldBoard { name: string; voltage_v: number; system: string; icc_ka: number; fp_default: number; frequency_hz: number; project: string; feeder_length_m: number; supplied_from: string; supply_tag: string }
export interface SldSegment { kind: string; length_m: number; label: string; ambient_c: number | null; soil_c: number | null; rho_kmw: number | null; circuits: number; depth_m: number | null }
export interface SldCircuit {
  tag: string; description: string; load: number | null; unit: string; destination: string; parent_tag: string; topology: string; phase: string;
  length_m: number; fp: number | null; efficiency: number | null; kind: string; notes: string; cable_type: string; route?: SldSegment[];
}
export interface SldTitleblock {
  company: string; company_cuit: string; client: string; client_cuit: string; drawn_by: string; checked_by: string; approved_by: string;
  description: string; location: string; scale: string; revision: string; status: string;
}
export interface SldData { board: SldBoard; circuits: SldCircuit[]; titleblock: SldTitleblock }
export interface SldStatus { state: "idle" | "running" | "done" | "failed"; name?: string; outputs: string[]; log: string[]; error?: string; started?: string; finished?: string }
export interface BoardRow { id: string; name: string; voltage_v: number; system: string; icc_ka: number; circuits: number; supplied_from: string; supply_tag: string; state: string; finished?: string }
export interface MemoCurve { curva: string; In: number; min: number[][]; max: number[][] }
export interface MemoSelectivity { aguas_arriba: string; aguas_abajo: string; relacion_termica: number | null; is_a: number; resultado: "total" | "parcial" | "revisar"; nota: string }
export interface BoardMemoView {
  available: boolean; stale: boolean; files: string[]; finished?: string;
  memo: {
    validated: boolean; board: { name: string; icc_ka: number };
    curvas: Record<string, MemoCurve>; selectividad: MemoSelectivity[];
    resumen: { circuits: number; cumplen: number; no_cumplen: number; transiciones: number; global: boolean; observaciones: string[] };
  } | null;
}
export interface SldView {
  input: SldData; saved: boolean; board_id: string; boards: { id: string; name: string }[]; status: SldStatus; people: string[]; logos: { company: boolean; client: boolean };
  options: { units: string[]; topologies: string[]; phases: string[]; kinds: string[]; cable_types: string[]; systems: string[]; route_kinds: string[] };
}

/* ---- master data ---- */
export interface OrganizationData { legal_name: string; tax_id: string; email: string; website: string; address: string; phone: string; default_locale: string; has_logo: boolean }
export interface ClientRecord { id: string; name: string; tax_id: string; email: string; website: string; address: string; has_logo: boolean }
export interface PersonRecord { id: string; name: string; role: string; registration: string }

/* ---- issuing (engineering -> deliverables) ---- */
export interface IssueCandidate { id: string; name: string; discipline: string; package: string; kind: "drawing" | "document"; formats: string[]; pdf_will_be_rendered: boolean; last_issue: string | null }
export interface TransmittalSummary { id: string; emission: string; client_rev: string; internal_rev: string; status: "prepared" | "sent"; created: string; sent_on: string | null; items: number }
export interface IssuingView { candidates: IssueCandidate[]; emissions: string[]; next_transmittal: string; transmittals: TransmittalSummary[] }
export interface CalcRow { tag: string; description: string; In: number; Ib: number; icu: number; S: number; dU: number; disp: string; tipo?: string; limite_pct?: number; du_propia_pct?: number; iz_a?: number; cumple?: boolean }
export interface CalcView { name?: string; summary?: { circuits: number; compliant: number; non_compliant: number }; rows: CalcRow[]; criteria: { limits_pct: { seccional: number; terminal: number; motor: number }; conductor: { material: string; aislacion: string }; rcd_ma: number } | null }

/* ---- automatic analysis of customer input (admin/engineer) ---- */
export interface AnalysisStatus { configured: boolean; model: string; pending: number; usage: { calls: number; input_tokens: number; output_tokens: number } }
export interface AnalysisResult { analyzed: number; created: string[]; merged: string[]; open_questions: number; usage: { input_tokens: number; output_tokens: number }; model: string; attempts: number }

/* ---- review of the norm data ---- */
export interface NormUnit { id: string; kind: "rule" | "table" | "criterion"; name: string; counts: { total: number; approved: number; rejected: number; pending: number; stale: number } }
export interface NormPointRow { key: string; title: string; group: string; ref: string; status: "pending" | "approved" | "rejected" | "stale"; by: string | null; at: string | null }
export interface NormPoint {
  unit: string; kind: "rule" | "table" | "criterion"; key: string; title: string; group: string; ref: string; value: unknown; editable: string[];
  status: "pending" | "approved" | "rejected" | "stale"; review: { status: string; by: string; at: string; note: string } | null;
  history: { at: string; by: string; action: string; note: string; changes?: [string, unknown, unknown][] }[];
}

/* ---- project registers (risks, changes, issues, decisions, assumptions, stakeholders) ---- */
export interface RegisterField {
  id: string; type: "text" | "longtext" | "number" | "date" | "enum"; required: boolean; label: string; min?: number; max?: number; default?: string;
  options?: { id: string; label: string }[];
}
export interface RegisterDef {
  id: string; prefix: string; name: string; columns: string[]; closed_states: string[]; fields: RegisterField[]; derived: string | null;
  counts: { total: number; active: number };
}
export interface RegistersView { methodology: string; available?: boolean; language: string; registers: RegisterDef[] }
export interface RegisterRecord {
  id: string; opened: string; created_by: string; updated_at: string; level?: number; level_name?: string;
  history: { at: string; by: string; action: string; changes?: Record<string, [unknown, unknown]> }[]; [field: string]: unknown;
}

/* ---- management reports (methodology: PM2) ---- */
export interface ReportType { id: string; code: string; name: string; audience: "client" | "internal"; command: string; next_number: number; last_period_end: string | null }
export interface GeneratedReport {
  id: string; type: string; code: string; nn: number; name: string; audience: "client" | "internal"; date: string; period: [string, string];
  language: string; prepared_by: string; summary: string; md: string; pdf: string; published: string | null;
}
export interface ReportingView { methodology: string; available?: boolean; language: string; types: ReportType[]; reports: GeneratedReport[] }

/* ---- sign-in with a provider ---- */
export interface SocialProvider { id: string; name: string; configured?: boolean }
export interface IdentitiesView { has_password: boolean; identities: { provider: string; email: string; created_at: string }[] }

/* ---- accounts and organizations ---- */
export interface OrgMember { user_id: string; email: string; name: string; role: "owner" | "admin" | "member"; active: boolean; last_login_at: string | null; me: boolean }
export interface OrgInvitation { id: string; email: string; role: "owner" | "admin" | "member"; expires_at: string }
export interface OrgView {
  slug: string; name: string; kind: "individual" | "company"; seats: number; seats_used: number; seats_pending: number;
  members: OrgMember[]; invitations: OrgInvitation[];
}
export interface InvitationCreated { id: string; email: string; role: string; expires_at: string; token: string; url: string }
export interface StaffOrg { slug: string; name: string; kind: "individual" | "company"; seats: number; active: boolean; members: number; created_at: string }
export interface StaffUser {
  id: string; email: string; name: string; active: boolean; platform_role: "user" | "admin" | "standards" | "inspector" | "auditor"; last_login_at: string | null;
  organizations: { slug: string; name: string; role: string }[]; assignments: { slug: string; name: string }[];
}
export interface AuditEvent { at: string; actor: string; action: string; target: string; org: string; detail: Record<string, unknown>; ip: string }
