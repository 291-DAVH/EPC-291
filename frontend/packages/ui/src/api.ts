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
  const r = await fetch("/api" + path, init);
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
  disciplines: string[]; phase: string; workspace_files: number; deliverable_files: number; is_template: boolean;
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

export interface Me { role: string; name: string; org: string }
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
  due?: string; delivered_on?: string; downloadable: boolean; overdue: boolean;
}
export interface InputItem {
  id: string; kind: string; title: string; text: string; source: string; created: string; status: string; attachments: { name: string; size: number }[];
}
export interface RequirementItem {
  id: string; statement: string; type: string; priority: string; discipline: string; acceptance: string[]; open_questions: string[];
  source_titles: string[]; status: string;
}
export interface ReportItem { id: string; title: string; type: string; date: string; summary: string; downloadable: boolean }
