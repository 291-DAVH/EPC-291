import { ReactNode } from "react";
import { Key, useI18n } from "./i18n";

export function Badge({ children, tone }: { children: ReactNode; tone?: "ok" | "warn" | "bad" | "accent" }) {
  return <span className={"badge " + (tone ?? "")}>{children}</span>;
}

export function State({ loading, error, empty }: { loading?: boolean; error?: string | null; empty?: boolean }) {
  const { t } = useI18n();
  if (loading) return <div className="state">{t("common.loading")}</div>;
  if (error) return <div className="state err">{t("common.error")} <span className="mono">{error}</span></div>;
  if (empty) return <div className="state">{t("common.none")}</div>;
  return null;
}

export function Page({ title, help, children }: { title: string; help?: string; children: ReactNode }) {
  return (
    <>
      <h1>{title}</h1>
      {help && <p className="help">{help}</p>}
      {children}
    </>
  );
}

export const statusTone = (s: string) => (s === "verified" || s === "active" ? "ok" : s === "draft" || s === "pending" ? "warn" : undefined);
export const typeTone = (ty: string) => (ty === "prohibited" ? "bad" : ty === "mandatory" ? "accent" : undefined);

/* ---- end-user helpers ---- */
export type Health = "on_track" | "at_risk" | "delayed";
export const healthTone = (h: string, closed?: boolean) => (closed ? undefined : h === "on_track" ? "ok" : h === "at_risk" ? "warn" : "bad");

export function HealthBadge({ health, closed }: { health: string; closed?: boolean }) {
  const { t } = useI18n();
  const k = (closed ? "u.health.closed" : "u.health." + health) as Key;
  return <Badge tone={healthTone(health, closed)}>{t(k)}</Badge>;
}

export function Progress({ pct, health, closed }: { pct: number; health?: string; closed?: boolean }) {
  const tone = closed ? "var(--muted)" : health === "delayed" ? "var(--bad)" : health === "at_risk" ? "var(--warn)" : "var(--ok)";
  return (
    <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div style={{ width: `${Math.max(0, Math.min(100, pct))}%`, background: tone }} />
    </div>
  );
}

export function useFmt() {
  const { lang } = useI18n();
  const loc = lang === "es" ? "es-AR" : "en-GB";
  return {
    date: (iso?: string | null) => (iso ? new Date(iso + "T00:00:00").toLocaleDateString(loc, { day: "2-digit", month: "short", year: "numeric" }) : "—"),
    short: (iso?: string | null) => (iso ? new Date(iso + "T00:00:00").toLocaleDateString(loc, { day: "2-digit", month: "short" }) : "—"),
  };
}

export const phaseKey = (p: string) => ("u.phase." + p) as Key;
