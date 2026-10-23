import { FormEvent, useEffect, useState } from "react";
import { ApiError, NewProjectBody, Project, ProjectOptions, api, useApi } from "../api";
import { Badge, State } from "../components";
import { Key, useI18n } from "../i18n";

const slug = (s: string) =>
  s.normalize("NFD").replace(/[̀-ͯ]/g, "").toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 24);

export default function NewProject({ onCreated, onCancel }: { onCreated: (p: Project & { plugins_locked?: number }) => void; onCancel: () => void }) {
  const { t } = useI18n();
  const opts = useApi<ProjectOptions>("/projects/options");
  const [f, setF] = useState<NewProjectBody>({
    client_name: "", client_code: "", project_code: "", project_name: "", jurisdiction: "AR", methodology: "pm2",
    locale: "", disciplines: ["electrical"], phase: "IC",
  });
  const [codeTouched, setCodeTouched] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const jur = opts.data?.jurisdictions.find((j) => j.id === f.jurisdiction);
  useEffect(() => {
    if (jur) setF((x) => ({ ...x, locale: jur.default_locale, disciplines: x.disciplines.filter((d) => jur.disciplines.includes(d)) }));
  }, [jur?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (patch: Partial<NewProjectBody>) => setF((x) => ({ ...x, ...patch }));
  const toggle = (d: string) => set({ disciplines: f.disciplines.includes(d) ? f.disciplines.filter((x) => x !== d) : [...f.disciplines, d] });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const local: Record<string, string> = {};
    if (!f.client_name.trim()) local.client_name = t("projects.required");
    if (!f.client_code.trim()) local.client_code = t("projects.required");
    if (!f.project_code.trim()) local.project_code = t("projects.required");
    if (f.disciplines.length === 0) local.disciplines = t("projects.required");
    setErrors(local);
    setGeneral(null);
    if (Object.keys(local).length) return;
    setBusy(true);
    try {
      onCreated(await api<Project>("/projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(f) }));
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fieldErrors).length) setErrors(err.fieldErrors);
      else setGeneral(t("projects.error.generic"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card form" onSubmit={submit} noValidate>
      <div className="row between">
        <h2 style={{ margin: 0 }}>{t("projects.new")}</h2>
        <button type="button" onClick={onCancel}>{t("projects.cancel")}</button>
      </div>
      <State loading={opts.loading} error={opts.error} />
      {opts.data && (
        <>
          <div className="fields">
            <Field label={t("projects.clientName")} error={errors.client_name}>
              <input value={f.client_name} autoFocus onChange={(e) => set({ client_name: e.target.value, ...(codeTouched ? {} : { client_code: slug(e.target.value) }) })} />
            </Field>
            <Field label={t("projects.clientCode")} error={errors.client_code} hint={t("projects.clientCodeHelp")}>
              <input className="mono" value={f.client_code} onChange={(e) => { setCodeTouched(true); set({ client_code: e.target.value }); }} />
            </Field>
            <Field label={t("projects.projectCode")} error={errors.project_code}>
              <input className="mono" value={f.project_code} onChange={(e) => set({ project_code: e.target.value })} />
            </Field>
            <Field label={t("projects.projectName")} error={errors.project_name}>
              <input value={f.project_name} onChange={(e) => set({ project_name: e.target.value })} />
            </Field>
            <Field label={t("projects.jurisdiction")} error={errors.jurisdiction}>
              <select value={f.jurisdiction} onChange={(e) => set({ jurisdiction: e.target.value })}>
                {opts.data.jurisdictions.map((j) => <option key={j.id} value={j.id}>{j.id} · {j.name}</option>)}
              </select>
            </Field>
            <Field label={t("projects.methodology")} error={errors.methodology}>
              <select value={f.methodology} onChange={(e) => set({ methodology: e.target.value })}>
                {opts.data.methodologies.map((m) => (
                  <option key={m.id} value={m.id} disabled={!m.available}>{m.name}{m.available ? "" : ` (${t("projects.soon")})`}</option>
                ))}
              </select>
            </Field>
            <Field label={t("projects.locale")} error={errors.locale}>
              <select value={f.locale} onChange={(e) => set({ locale: e.target.value })}>
                {opts.data.locales.map((l) => <option key={l}>{l}</option>)}
              </select>
            </Field>
            <Field label={t("projects.phase")} error={errors.phase}>
              <select value={f.phase} onChange={(e) => set({ phase: e.target.value })}>
                {opts.data.phases.map((p) => <option key={p}>{p}</option>)}
              </select>
            </Field>
          </div>
          <Field label={t("projects.disciplines")} error={errors.disciplines}>
            <div className="row">
              {jur?.disciplines.map((d) => (
                <label key={d} className="row chip">
                  <input type="checkbox" checked={f.disciplines.includes(d)} onChange={() => toggle(d)} />
                  {t(("projects.disc." + d) as Key) === ("projects.disc." + d) ? d : t(("projects.disc." + d) as Key)}
                </label>
              ))}
            </div>
          </Field>
          {general && <div className="alert bad">{general}</div>}
          <div className="row" style={{ marginTop: 14 }}>
            <button className="primary" type="submit" disabled={busy}>{t("projects.create")}</button>
            <Badge>{f.client_code || "…"} / {f.project_code || "…"}</Badge>
          </div>
        </>
      )}
    </form>
  );
}

function Field({ label, error, hint, children }: { label: string; error?: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && !error && <small className="muted">{hint}</small>}
      {error && <small className="err">{error}</small>}
    </label>
  );
}
