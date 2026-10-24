import { FormEvent, useState } from "react";
import { ApiError, InvitationCreated, Me, OrgMember, OrgView, Page, State, api, useApi, useI18n } from "@epc/ui";

const json = { "Content-Type": "application/json" };

function errorText(x: unknown): string {
  return x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || String(x.status) : "error";
}

/** The signed-in person: account data, password and, for the owner of the organization, the people who share the subscription. */
export default function Account() {
  const { t } = useI18n();
  const me = useApi<Me>("/me");
  if (!me.data) return <State loading={me.loading} error={me.error} />;
  const m = me.data;
  return (
    <Page title={t("acc.title")} help={t("acc.help")}>
      <div className="grid" style={{ gap: 14 }}>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t("acc.person")}</h2>
          {m.auth !== "required" ? <div className="muted">{t("acc.simulated")}</div> : (
            <div className="fgrid">
              <div><div className="muted small">{t("auth.yourName")}</div>{m.name}</div>
              <div><div className="muted small">{t("auth.email")}</div>{m.email}</div>
              {m.role === "admin" ? <div><div className="muted small">{t("acc.role")}</div>{t("acc.staff")}</div> : (
                <>
                  <div><div className="muted small">{t("acc.org")}</div>{m.org}</div>
                  <div><div className="muted small">{t("acc.plan")}</div>{t(m.org_kind === "company" ? "auth.company" : "auth.individual")}</div>
                  <div><div className="muted small">{t("acc.role")}</div>{t(m.org_role === "owner" ? "org.owner" : m.org_role === "admin" ? "org.admin" : "org.member")}</div>
                </>
              )}
            </div>
          )}
        </div>
        {m.auth === "required" && <Password />}
        {m.auth === "required" && (m.org_role === "owner" || m.org_role === "admin") && <People meRole={m.org_role} />}
      </div>
    </Page>
  );
}

function Password() {
  const { t } = useI18n();
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/auth/password", { method: "POST", headers: json, body: JSON.stringify({ current_password: cur, new_password: next }) });
      setCur(""); setNext(""); setMsg({ ok: true, text: t("acc.pwChanged") });
    } catch (x) { setMsg({ ok: false, text: errorText(x) }); }
  };
  return (
    <form className="card" onSubmit={submit}>
      <h2 style={{ marginTop: 0 }}>{t("acc.password")}</h2>
      <div className="fgrid">
        <label className="field"><span>{t("acc.currentPw")}</span><input type="password" autoComplete="current-password" value={cur} onChange={(e) => setCur(e.target.value)} required /></label>
        <label className="field"><span>{t("acc.newPw")}</span><input type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} required /></label>
      </div>
      <div className="muted small" style={{ marginTop: 6 }}>{t("auth.minPw")}</div>
      <div className="row" style={{ marginTop: 10 }}><button className="primary" type="submit">{t("acc.changePw")}</button></div>
      {msg && <div className={"alert " + (msg.ok ? "ok" : "bad")} style={{ marginTop: 10 }}>{msg.text}</div>}
    </form>
  );
}

function People({ meRole }: { meRole: "owner" | "admin" }) {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const org = useApi<OrgView>(`/app/org?r=${rev}`);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"member" | "admin" | "owner">("member");
  const [created, setCreated] = useState<InvitationCreated | null>(null);
  const [copied, setCopied] = useState(false);
  const [err, setErr] = useState("");
  const reload = () => setRev((n) => n + 1);
  const act = async (fn: () => Promise<unknown>) => { try { await fn(); setErr(""); reload(); } catch (x) { setErr(errorText(x)); } };
  if (!org.data) return <State loading={org.loading} error={org.error} />;
  const o = org.data;
  const free = o.seats - o.seats_used - o.seats_pending;
  const invite = (e: FormEvent) => {
    e.preventDefault();
    act(async () => {
      setCreated(await api<InvitationCreated>("/app/org/invitations", { method: "POST", headers: json, body: JSON.stringify({ email, role }) }));
      setEmail(""); setCopied(false);
    });
  };
  const patch = (m: OrgMember, body: object) => act(() => api(`/app/org/members/${m.user_id}`, { method: "PATCH", headers: json, body: JSON.stringify(body) }));
  const copy = async (text: string) => { try { await navigator.clipboard.writeText(text); setCopied(true); } catch { /* the field stays selectable */ } };
  return (
    <div className="card">
      <div className="row between">
        <h2 style={{ margin: 0 }}>{t("org.people")}</h2>
        <span className="badge accent">{t("org.seats")}: {o.seats_used}/{o.seats} {t("org.used")}{o.seats_pending > 0 ? ` · ${o.seats_pending} ${t("org.pending")}` : ""}</span>
      </div>
      {err && <div className="alert bad" style={{ marginTop: 8 }}>{err}</div>}
      <table>
        <thead><tr><th>{t("org.name")}</th><th>{t("org.email")}</th><th>{t("org.role")}</th><th>{t("org.status")}</th><th>{t("org.lastLogin")}</th><th /></tr></thead>
        <tbody>
          {o.members.map((m) => (
            <tr key={m.user_id}>
              <td>{m.name} {m.me && <span className="muted small">({t("org.you")})</span>}</td>
              <td>{m.email}</td>
              <td>
                <select value={m.role} disabled={meRole !== "owner" && m.role === "owner"} onChange={(e) => patch(m, { role: e.target.value })}>
                  {(meRole === "owner" || m.role === "owner") && <option value="owner">{t("org.owner")}</option>}<option value="admin">{t("org.admin")}</option><option value="member">{t("org.member")}</option>
                </select>
              </td>
              <td><span className={"badge " + (m.active ? "ok" : "bad")}>{t(m.active ? "org.active" : "org.inactive")}</span></td>
              <td className="muted small">{m.last_login_at ? new Date(m.last_login_at).toLocaleString() : t("org.never")}</td>
              <td style={{ whiteSpace: "nowrap" }}>
                {(meRole === "owner" || m.role !== "owner") && <button onClick={() => patch(m, { active: !m.active })}>{t(m.active ? "org.deactivate" : "org.activate")}</button>}{" "}
                {!m.me && (meRole === "owner" || m.role !== "owner") && <button onClick={() => { if (window.confirm(t("org.confirmRemove"))) act(() => api(`/app/org/members/${m.user_id}`, { method: "DELETE" })); }}>{t("org.remove")}</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {o.invitations.length > 0 && (
        <>
          <h3>{t("org.pendingInv")}</h3>
          <table>
            <tbody>
              {o.invitations.map((i) => (
                <tr key={i.id}>
                  <td>{i.email}</td><td>{t(i.role === "owner" ? "org.owner" : i.role === "admin" ? "org.admin" : "org.member")}</td>
                  <td className="muted small">{t("org.expires")} {new Date(i.expires_at).toLocaleDateString()}</td>
                  <td><button onClick={() => act(() => api(`/app/org/invitations/${i.id}`, { method: "DELETE" }))}>{t("org.cancelInv")}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h3>{t("org.invite")}</h3>
      {o.kind === "individual" ? <div className="muted">{t("org.individualNote")}</div> : (
        <form onSubmit={invite}>
          <div className="row">
            <input type="email" placeholder={t("org.email")} value={email} onChange={(e) => setEmail(e.target.value)} required style={{ minWidth: 240 }} />
            <select value={role} onChange={(e) => setRole(e.target.value as "member" | "admin" | "owner")}>
              <option value="member">{t("org.member")}</option><option value="admin">{t("org.admin")}</option>{meRole === "owner" && <option value="owner">{t("org.owner")}</option>}
            </select>
            <button className="primary" type="submit" disabled={free < 1}>{t("org.inviteBtn")}</button>
          </div>
          <div className="muted small" style={{ marginTop: 6 }}>{t("org.inviteHelp")}</div>
        </form>
      )}
      {created && (
        <div className="alert ok" style={{ marginTop: 10 }}>
          <div><b>{t("org.link")}</b> · {created.email}</div>
          <div className="linkbox" style={{ marginTop: 6 }}>
            <input readOnly value={created.url} onFocus={(e) => e.target.select()} />
            <button onClick={() => copy(created.url)}>{copied ? t("org.copied") : t("org.copy")}</button>
          </div>
        </div>
      )}
    </div>
  );
}
