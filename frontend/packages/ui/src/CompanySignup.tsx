import { FormEvent, useEffect, useState } from "react";
import { ApiError, Me, api } from "./api";
import { Markdown } from "./markdown";
import { useI18n } from "./i18n";

interface Country {
  code: string; name: { es: string; en: string };
  tax: { id: string; example: string; hint: { es: string; en: string } };
  region: { es: string; en: string };
  postal: { label: { es: string; en: string }; example: string };
}
interface Started { registration: string; email: string; expires_minutes: number }
const json = { "Content-Type": "application/json" };

const blank = { country: "", org_name: "", tax_id: "", street: "", number: "", locality: "", region: "", postal_code: "", contact_email: "", name: "", username: "", password: "" };

/** Registration of a company: the country decides the fields, the whole form is checked, a code goes to the company's e-mail and the team validates the registration afterwards. */
export default function CompanySignup({ onDone, onBack }: { onDone: (m: Me) => void; onBack: () => void }) {
  const { t, lang } = useI18n();
  const [countries, setCountries] = useState<Country[]>([]);
  const [terms, setTerms] = useState<{ version: string; text: string } | null>(null);
  const [f, setF] = useState(blank);
  const [accept, setAccept] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [general, setGeneral] = useState("");
  const [busy, setBusy] = useState(false);
  const [started, setStarted] = useState<Started | null>(null);
  const [code, setCode] = useState("");
  const [wait, setWait] = useState(0);

  useEffect(() => {
    api<Country[]>("/auth/countries").then((c) => {
      setCountries(c);
      const region = (navigator.language.split("-")[1] || "").toUpperCase();
      setF((x) => ({ ...x, country: x.country || (c.some((k) => k.code === region) ? region : "AR") }));
    }).catch(() => setCountries([]));
  }, []);
  useEffect(() => { api<{ version: string; text: string }>(`/auth/terms?lang=${lang}`).then(setTerms).catch(() => setTerms(null)); }, [lang]);
  useEffect(() => {
    if (wait <= 0) return;
    const id = window.setTimeout(() => setWait((n) => n - 1), 1000);
    return () => window.clearTimeout(id);
  }, [wait]);

  const c = countries.find((k) => k.code === f.country);
  const set = (k: keyof typeof blank, v: string) => { setF({ ...f, [k]: v }); setErrors({ ...errors, [k]: "" }); };
  const fail = (x: unknown) => {
    if (x instanceof ApiError) { setErrors(x.fieldErrors); setGeneral(Object.keys(x.fieldErrors).length ? "" : String(x.status)); } else setGeneral("error");
  };

  const register = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setGeneral(""); setErrors({});
    try {
      const s = await api<Started>("/auth/company/register", { method: "POST", headers: json, body: JSON.stringify({ ...f, accept_terms: accept, terms_version: terms?.version ?? "", lang }) });
      setStarted(s); setWait(60); setCode("");
    } catch (x) { fail(x); } finally { setBusy(false); }
  };
  const verify = async (e: FormEvent) => {
    e.preventDefault();
    if (!started) return;
    setBusy(true); setGeneral(""); setErrors({});
    try {
      const m = await api<Me>("/auth/company/verify", { method: "POST", headers: json, body: JSON.stringify({ registration: started.registration, code }) });
      try { window.history.replaceState({}, "", m.landing || "/"); } catch { /* ignore */ }
      onDone(m);
    } catch (x) {
      if (x instanceof ApiError && (x.status === 404 || x.status === 429)) { setStarted(null); setGeneral(t(x.status === 404 ? "co.expired" : "co.tooMany")); } else fail(x);
    } finally { setBusy(false); }
  };
  const resend = async () => {
    if (!started) return;
    try { await api("/auth/company/resend", { method: "POST", headers: json, body: JSON.stringify({ registration: started.registration }) }); setWait(60); setGeneral(t("co.resent")); }
    catch (x) { fail(x); }
  };

  const field = (k: keyof typeof blank, label: string, opts: { type?: string; auto?: string; required?: boolean; hint?: string; placeholder?: string } = {}) => (
    <label className="field">
      <span>{label}</span>
      <input type={opts.type ?? "text"} value={f[k]} autoComplete={opts.auto} required={opts.required !== false} placeholder={opts.placeholder} onChange={(e) => set(k, e.target.value)} />
      {opts.hint && !errors[k] && <small className="muted">{opts.hint}</small>}
      {errors[k] && <small className="err">{errors[k]}</small>}
    </label>
  );

  if (started) {
    return (
      <form onSubmit={verify}>
        <h1 style={{ marginTop: 12 }}>{t("co.verifyTitle")}</h1>
        <p className="muted small">{t("co.codeSent")} <b>{started.email}</b>. {t("co.codeValid")} {started.expires_minutes} {t("co.minutes")}.</p>
        <label className="field"><span>{t("co.code")}</span>
          <input value={code} inputMode="numeric" autoComplete="one-time-code" maxLength={6} pattern="[0-9]{6}" required onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} autoFocus />
          {errors.code && <small className="err">{errors.code}</small>}
        </label>
        {general && <div className="alert bad">{general}</div>}
        <button className="primary" type="submit" disabled={busy || code.length !== 6}>{t("co.verify")}</button>
        <div className="row small" style={{ marginTop: 10 }}>
          <button type="button" className="linkbtn" disabled={wait > 0} onClick={resend}>{wait > 0 ? `${t("co.resend")} (${wait} s)` : t("co.resend")}</button>
          <button type="button" className="linkbtn" onClick={() => { setStarted(null); setGeneral(""); }}>{t("co.edit")}</button>
        </div>
      </form>
    );
  }

  return (
    <form onSubmit={register} noValidate={false}>
      <h1 style={{ marginTop: 12 }}>{t("co.title")}</h1>
      <div className="alert ok small" role="note">{t("co.notice")}</div>
      <label className="field"><span>{t("co.country")}</span>
        <select value={f.country} onChange={(e) => { setF({ ...f, country: e.target.value, tax_id: "" }); setErrors({}); }}>
          {countries.map((k) => <option key={k.code} value={k.code}>{k.name[lang]}</option>)}
        </select>
      </label>
      {field("org_name", t("co.orgName"), { auto: "organization" })}
      {c && field("tax_id", c.tax.id, { hint: `${c.tax.hint[lang]} · ${t("co.example")} ${c.tax.example}`, placeholder: c.tax.example })}
      <fieldset className="field" style={{ border: 0, padding: 0, margin: 0 }}>
        <legend className="muted small" style={{ marginBottom: 4 }}>{t("co.address")}</legend>
        <div className="fgrid" style={{ gridTemplateColumns: "2fr 1fr" }}>
          {field("street", t("co.street"), { auto: "address-line1" })}
          {field("number", t("co.number"))}
        </div>
        {field("locality", t("co.locality"), { auto: "address-level2" })}
        <div className="fgrid" style={{ gridTemplateColumns: "1fr 1fr" }}>
          {c && field("region", c.region[lang], { auto: "address-level1" })}
          {c && field("postal_code", c.postal.label[lang], { auto: "postal-code", placeholder: c.postal.example })}
        </div>
      </fieldset>
      {field("contact_email", t("co.email"), { type: "email", auto: "email", hint: t("co.emailHint") })}
      {field("name", t("co.person"), { auto: "name" })}
      {field("username", t("co.alias"), { auto: "username", required: false, hint: t("co.aliasHint") })}
      {field("password", t("co.password"), { type: "password", auto: "new-password", hint: t("auth.minPw") })}
      {errors.password && f.password === "" && <small className="err">{errors.password}</small>}
      <label className="row small" style={{ alignItems: "flex-start", gap: 8 }}>
        <input type="checkbox" checked={accept} onChange={(e) => { setAccept(e.target.checked); setErrors({ ...errors, accept_terms: "" }); }} />
        <span>{t("co.accept")} <button type="button" className="linkbtn" onClick={() => setShowTerms(!showTerms)}>{t("co.terms")}</button></span>
      </label>
      {errors.accept_terms && <small className="err">{errors.accept_terms}</small>}
      {showTerms && terms && <div className="card" style={{ maxHeight: 220, overflow: "auto", padding: 10 }}><Markdown text={terms.text} /></div>}
      {general && <div className="alert bad">{t("auth.failed")}: {general}</div>}
      <button className="primary" type="submit" disabled={busy || !accept}>{t("co.sendCode")}</button>
      <div className="switch small"><button type="button" className="linkbtn" onClick={onBack}>{t("co.back")}</button></div>
    </form>
  );
}

