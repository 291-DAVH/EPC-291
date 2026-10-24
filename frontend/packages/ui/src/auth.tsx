import { FormEvent, ReactNode, useCallback, useEffect, useState } from "react";
import { ApiError, Me, SocialProvider, api } from "./api";
import { Key, useI18n } from "./i18n";

const json = { "Content-Type": "application/json" };

interface InvitationInfo { email: string; role: string; org: string; kind: string; existing_account: boolean }

function inviteToken(): string {
  try { return new URLSearchParams(window.location.search).get("invite") || ""; } catch { return ""; }
}

function clearInvite() {
  try { window.history.replaceState({}, "", window.location.pathname); } catch { /* ignore */ }
}

function queryParam(name: string): string {
  try { return new URLSearchParams(window.location.search).get(name) || ""; } catch { return ""; }
}

/** One button per configured provider; the same button signs in and registers (a new person is asked what kind of account they want next). */
function SocialButtons({ providers, invite }: { providers: SocialProvider[]; invite?: string }) {
  const { t } = useI18n();
  if (providers.length === 0) return null;
  return (
    <div className="social">
      <div className="muted small social-or"><span>{t("auth.or")}</span></div>
      {providers.map((p) => p.configured === false ? (
        <span key={p.id} className={"socialbtn disabled " + p.id} title={t("auth.notConfiguredHint")} aria-disabled="true">
          <span className="socialmark" aria-hidden>{p.name[0]}</span>{p.name} · {t("auth.notConfigured")}
        </span>
      ) : (
        <a key={p.id} className={"socialbtn " + p.id} href={`/api/auth/oauth/${p.id}/start${invite ? `?invite=${encodeURIComponent(invite)}` : ""}`}>
          <span className="socialmark" aria-hidden>{p.name[0]}</span>{t("auth.continueWith")} {p.name}
        </a>
      ))}
    </div>
  );
}

/** A person authenticated by a provider who has no account yet chooses the kind of subscription; then the account is created. */
function SocialComplete({ onDone }: { onDone: (m: Me) => void }) {
  const { t } = useI18n();
  const [who, setWho] = useState<{ provider: string; email: string; name: string } | null>(null);
  const [gone, setGone] = useState(false);
  const [kind, setKind] = useState<"individual" | "company">("individual");
  const [orgName, setOrgName] = useState("");
  const [username, setUsername] = useState("");
  const [err, setErr] = useState("");
  useEffect(() => { api<{ provider: string; email: string; name: string }>("/auth/oauth/pending").then(setWho).catch(() => setGone(true)); }, []);
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setErr("");
    try {
      const m = await api<Me>("/auth/oauth/complete", { method: "POST", headers: json, body: JSON.stringify({ kind, org_name: orgName, username }) });
      try { window.history.replaceState({}, "", "/"); } catch { /* ignore */ }
      onDone(m);
    } catch (x) { setErr(x instanceof ApiError ? Object.entries(x.fieldErrors).map(([k, v]) => `${k}: ${v}`).join(", ") || String(x.status) : "error"); }
  };
  return (
    <div className="authwrap">
      <div className="authbox card">
        <b>{t("app.name")}</b>
        {gone ? <div className="alert bad" style={{ marginTop: 12 }}>{t("auth.err.expired")}</div> : !who ? <div className="state">{t("common.loading")}</div> : (
          <>
            <h1 style={{ marginTop: 12 }}>{t("auth.finishSignup")}</h1>
            <div className="muted small">{who.name} · {who.email} · {who.provider}</div>
            <form onSubmit={submit}>
              <label className="field"><span>{t("auth.kind")}</span>
                <select value={kind} onChange={(e) => setKind(e.target.value as "individual" | "company")}>
                  <option value="individual">{t("auth.individual")}</option><option value="company">{t("auth.company")}</option>
                </select>
              </label>
              {kind === "company" && <label className="field"><span>{t("auth.orgName")}</span><input value={orgName} onChange={(e) => setOrgName(e.target.value)} required /></label>}
              <label className="field"><span>{t("auth.username")}</span><input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" /></label>
              {err && <div className="alert bad">{t("auth.failed")}: {err}</div>}
              <button className="primary" type="submit">{t("auth.signup")}</button>
            </form>
          </>
        )}
        <div className="switch small"><button className="linkbtn" onClick={() => { window.location.assign("/"); }}>{t("auth.toLogin")}</button></div>
      </div>
    </div>
  );
}

/** Shows the sign-in / sign-up / invitation screen while the API requires an account and there is no session; otherwise renders the app. */
export function AuthGate({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const [me, setMe] = useState<Me | null>(null);
  const [failed, setFailed] = useState(false);
  const refresh = useCallback(() => {
    api<Me>("/me").then((m) => { setMe(m); setFailed(false); }).catch(() => setFailed(true));
  }, []);
  useEffect(() => {
    refresh();
    window.addEventListener("epc-unauthorized", refresh);
    return () => window.removeEventListener("epc-unauthorized", refresh);
  }, [refresh]);
  if (failed) return <div className="authwrap"><div className="state">{t("common.error")}</div></div>;
  if (!me) return <div className="authwrap"><div className="state">{t("common.loading")}</div></div>;
  if (me.auth === "required" && !me.authenticated) return queryParam("social") === "pending" ? <SocialComplete onDone={setMe} /> : <AuthScreen me={me} onDone={setMe} />;
  return <>{children}</>;
}

function reason(x: unknown, t: (k: Key) => string): string {
  if (x instanceof ApiError) {
    if (x.status === 429) return t("auth.many");
    if (x.status === 401) return t("auth.wrong");
    if (x.status === 403) return t("auth.noOrg");
    const f = Object.entries(x.fieldErrors).map(([k, v]) => `${k}: ${v}`).join(", ");
    return f || String(x.status);
  }
  return "error";
}

function AuthScreen({ me, onDone }: { me: Me; onDone: (m: Me) => void }) {
  const { t, lang, setLang } = useI18n();
  const token = inviteToken();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [inv, setInv] = useState<InvitationInfo | null>(null);
  const [invBad, setInvBad] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [kind, setKind] = useState<"individual" | "company">("individual");
  const [username, setUsername] = useState("");
  const [providers, setProviders] = useState<SocialProvider[]>([]);
  const [err, setErr] = useState(() => (queryParam("auth_error") ? "auth.err." + queryParam("auth_error") : ""));
  const [busy, setBusy] = useState(false);

  useEffect(() => { api<SocialProvider[]>("/auth/providers").then(setProviders).catch(() => setProviders([])); }, []);
  useEffect(() => {
    if (!token) return;
    api<InvitationInfo>("/auth/invitation", { method: "POST", headers: json, body: JSON.stringify({ token }) }).then(setInv).catch(() => setInvBad(true));
  }, [token]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      let path = "/auth/login";
      let body: Record<string, unknown> = { login: email, password };
      if (token && inv) { path = "/auth/accept-invitation"; body = { token, name, password, username }; }
      else if (mode === "signup") { path = "/auth/signup"; body = { kind, org_name: orgName, name, email, password, username }; }
      const m = await api<Me>(path, { method: "POST", headers: json, body: JSON.stringify(body) });
      if (token) clearInvite();
      try { window.history.replaceState({}, "", m.landing || "/"); } catch { /* ignore */ }      // each kind of account starts where its work is
      onDone(m);
    } catch (x) { setErr(reason(x, t)); } finally { setBusy(false); }
  };

  const inviting = !!token;
  const field = (label: Key, value: string, set: (v: string) => void, type = "text", auto?: string) => (
    <label className="field"><span>{t(label)}</span><input type={type} value={value} autoComplete={auto} onChange={(e) => set(e.target.value)} required /></label>
  );
  return (
    <div className="authwrap">
      <div className="authbox card">
        <div className="row between">
          <b>{t("app.name")}</b>
          <button onClick={() => setLang(lang === "es" ? "en" : "es")} aria-label="Language">{lang === "es" ? "EN" : "ES"}</button>
        </div>
        {inviting && invBad && <div className="alert bad" style={{ marginTop: 12 }}>{t("auth.invalidInvite")}</div>}
        {inviting && inv && (
          <>
            <h1 style={{ marginTop: 12 }}>{t("auth.acceptInvite")}</h1>
            <div className="muted small">{t("auth.invitedTo")} <b>{inv.org}</b> {t("auth.asRole")} {t(inv.role === "owner" ? "org.owner" : "org.member")} · {inv.email}</div>
            {inv.existing_account && <div className="muted small" style={{ marginTop: 6 }}>{t("auth.existing")}</div>}
            <form onSubmit={submit}>
              {!inv.existing_account && field("auth.yourName", name, setName, "text", "name")}
              {!inv.existing_account && <label className="field"><span>{t("auth.username")}</span><input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" /></label>}
              {field("auth.password", password, setPassword, "password", inv.existing_account ? "current-password" : "new-password")}
              {!inv.existing_account && <div className="muted small">{t("auth.minPw")}</div>}
              {err && <div className="alert bad">{t("auth.failed")}: {err}</div>}
              <button className="primary" type="submit" disabled={busy}>{t("auth.acceptInvite")}</button>
            </form>
            <SocialButtons providers={providers} invite={token} />
          </>
        )}
        {!inviting && mode === "login" && (
          <>
            <h1 style={{ marginTop: 12 }}>{t("auth.title")}</h1>
            <form onSubmit={submit}>
              {field("auth.loginField", email, setEmail, "text", "username")}
              {field("auth.password", password, setPassword, "password", "current-password")}
              {err && <div className="alert bad">{err.startsWith("auth.err.") ? t(err as never) : err}</div>}
              <button className="primary" type="submit" disabled={busy}>{t("auth.login")}</button>
            </form>
            <SocialButtons providers={providers} />
            <div className="switch small">
              {me.signup ? <button className="linkbtn" onClick={() => { setMode("signup"); setErr(""); }}>{t("auth.toSignup")}</button> : <span className="muted">{t("auth.closedHint")}</span>}
            </div>
          </>
        )}
        {!inviting && mode === "signup" && (
          <>
            <h1 style={{ marginTop: 12 }}>{t("auth.signupTitle")}</h1>
            <form onSubmit={submit}>
              <label className="field"><span>{t("auth.kind")}</span>
                <select value={kind} onChange={(e) => setKind(e.target.value as "individual" | "company")}>
                  <option value="individual">{t("auth.individual")}</option>
                  <option value="company">{t("auth.company")}</option>
                </select>
              </label>
              {kind === "company" && field("auth.orgName", orgName, setOrgName)}
              {field("auth.yourName", name, setName, "text", "name")}
              {field("auth.email", email, setEmail, "email", "email")}
              <label className="field"><span>{t("auth.username")}</span><input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" /></label>
              {field("auth.password", password, setPassword, "password", "new-password")}
              <div className="muted small">{t("auth.minPw")}</div>
              {err && <div className="alert bad">{t("auth.failed")}: {err}</div>}
              <button className="primary" type="submit" disabled={busy}>{t("auth.signup")}</button>
            </form>
            <SocialButtons providers={providers} />
            <div className="switch small"><button className="linkbtn" onClick={() => { setMode("login"); setErr(""); }}>{t("auth.toLogin")}</button></div>
          </>
        )}
        {inviting && (invBad || inv) && (
          <div className="switch small"><button className="linkbtn" onClick={() => { clearInvite(); window.location.reload(); }}>{t("auth.toLogin")}</button></div>
        )}
      </div>
    </div>
  );
}

/** Ends the session and returns to the sign-in screen. */
export async function signOut() {
  try { await api("/auth/logout", { method: "POST" }); } finally { window.location.assign("/"); }
}
