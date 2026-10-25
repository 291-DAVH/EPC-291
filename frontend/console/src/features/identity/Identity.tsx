import { FormEvent, useState } from "react";
import { ApiError, AuditEvent, Page, Project, State, StaffOrg, StaffUser, api, useApi, useI18n } from "@epc/ui";

const json = { "Content-Type": "application/json" };

function errorText(x: unknown): string {
  return x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || String(x.status) : "error";
}

interface Created { org: StaffOrg; invitation: { email: string; url: string } }

/** Subscriptions (individual or company = a group of people), seats, the team's accounts and which organization owns each project. */
export default function Identity() {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const reload = () => setRev((n) => n + 1);
  const [err, setErr] = useState("");
  const orgs = useApi<StaffOrg[]>(`/identity/orgs?r=${rev}`);
  const users = useApi<StaffUser[]>(`/identity/users?r=${rev}`);
  const projects = useApi<Project[]>(`/projects?r=${rev}`);
  const act = async (fn: () => Promise<unknown>) => { try { await fn(); setErr(""); reload(); } catch (x) { setErr(errorText(x)); } };
  return (
    <Page title={t("ident.title")} help={t("ident.help")}>
      {err && <div className="alert bad">{err}</div>}
      <div className="grid" style={{ gap: 14 }}>
        <NewOrg onDone={reload} />
        <NewAccount onDone={reload} />
        <AuditLog />
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t("ident.orgs")}</h2>
          {!orgs.data ? <State loading={orgs.loading} error={orgs.error} /> : orgs.data.length === 0 ? <div className="state">{t("ident.noOrgs")}</div> : (
            <table>
              <thead><tr><th>{t("ident.name")}</th><th>{t("ident.kind")}</th><th>{t("ident.seats")}</th><th>{t("ident.members")}</th><th>{t("ident.validation")}</th><th>{t("ident.status")}</th><th /></tr></thead>
              <tbody>{orgs.data.map((o) => <OrgRow key={o.slug + o.seats + o.kind} o={o} act={act} />)}</tbody>
            </table>
          )}
        </div>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t("ident.users")}</h2>
          {!users.data ? <State loading={users.loading} error={users.error} /> : (
            <table>
              <thead><tr><th>{t("auth.email")}</th><th>{t("ident.name")}</th><th>{t("ident.orgsOf")}</th><th>{t("ident.status")}</th><th /></tr></thead>
              <tbody>
                {users.data.map((u) => (
                  <tr key={u.id}>
                    <td>{u.email} {u.platform_role === "admin" && <span className="badge accent">{t("ident.staff")}</span>}{(["standards", "inspector", "auditor"] as const).includes(u.platform_role as never) && <span className="badge accent">{t(("ident.role." + u.platform_role) as never)}</span>}</td>
                    <td>{u.name}</td>
                    <td className="small">{u.organizations.map((o) => `${o.name} (${o.role})`).join(", ")}{(u.platform_role === "inspector" || u.platform_role === "auditor") && orgs.data && <Assignments user={u} orgs={orgs.data} act={act} />}</td>
                    <td><span className={"badge " + (u.active ? "ok" : "bad")}>{t(u.active ? "org.active" : "org.inactive")}</span></td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button onClick={() => act(() => api(`/identity/users/${u.id}`, { method: "PATCH", headers: json, body: JSON.stringify({ active: !u.active }) }))}>{t(u.active ? "ident.disable" : "ident.enable")}</button>{" "}
                      {(u.platform_role === "admin" || u.platform_role === "user") && <button onClick={() => act(() => api(`/identity/users/${u.id}`, { method: "PATCH", headers: json, body: JSON.stringify({ platform_role: u.platform_role === "admin" ? "user" : "admin" }) }))}>{t(u.platform_role === "admin" ? "ident.removeStaff" : "ident.makeStaff")}</button>}{" "}
                      <button onClick={() => { const pw = window.prompt(t("ident.pwPrompt")); if (pw) act(async () => { await api(`/identity/users/${u.id}/password`, { method: "PUT", headers: json, body: JSON.stringify({ password: pw }) }); window.alert(t("ident.pwDone")); }); }}>{t("ident.setPw")}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t("ident.projects")}</h2>
          {!projects.data || !orgs.data ? <State loading={projects.loading} error={projects.error} /> : (
            <table>
              <thead><tr><th>{t("ident.project")}</th><th>{t("ident.owner")}</th></tr></thead>
              <tbody>
                {projects.data.filter((p) => !p.is_template).map((p) => (
                  <tr key={p.id}>
                    <td className="mono">{p.id} <span className="muted">· {p.name}</span></td>
                    <td>
                      <select value={p.org || ""} onChange={(e) => act(() => api(`/projects/${p.id}/org`, { method: "PUT", headers: json, body: JSON.stringify({ org: e.target.value }) }))}>
                        <option value="">{t("ident.unassigned")}</option>
                        {orgs.data!.map((o) => <option key={o.slug} value={o.slug}>{o.name}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Page>
  );
}

function OrgRow({ o, act }: { o: StaffOrg; act: (fn: () => Promise<unknown>) => void }) {
  const { t } = useI18n();
  const [seats, setSeats] = useState(String(o.seats));
  const [note, setNote] = useState(o.validation_note);
  const [open, setOpen] = useState(o.validation === "pending");                  // a registration waiting for the team opens by itself
  const patch = (body: object) => act(() => api(`/identity/orgs/${o.slug}`, { method: "PATCH", headers: json, body: JSON.stringify(body) }));
  const decide = (validation: string) => patch({ validation, validation_note: note });
  const a = o.address;
  const detail = o.kind === "company" && !!o.tax_id;
  return (
    <>
    <tr>
      <td>{o.name} <span className="muted small mono">{o.slug}</span></td>
      <td>{t(o.kind === "company" ? "auth.company" : "auth.individual")}</td>
      <td>
        {o.kind === "company" ? (
          <span className="row"><input type="number" min={1} value={seats} onChange={(e) => setSeats(e.target.value)} style={{ width: 70 }} />
            {seats !== String(o.seats) && <button onClick={() => patch({ seats: Number(seats) })}>{t("ident.save")}</button>}</span>
        ) : 1}
      </td>
      <td>{o.members}</td>
      <td><span className={"badge " + (o.validation === "validated" ? "ok" : o.validation === "pending" ? "warn" : "bad")}>{t(("ident.val." + o.validation) as never)}</span>{" "}
        {detail && <button className="linkbtn" onClick={() => setOpen(!open)}>{t("ident.fiscal")}</button>}</td>
      <td><span className={"badge " + (o.active ? "ok" : "bad")}>{t(o.active ? "ident.activeState" : "ident.suspended")}</span></td>
      <td><button onClick={() => patch({ active: !o.active })}>{t(o.active ? "ident.suspend" : "ident.reactivate")}</button></td>
    </tr>
    {detail && open && (
      <tr>
        <td colSpan={7}>
          <div className="row small" style={{ flexWrap: "wrap", gap: 16 }}>
            <span><b>{o.country}</b> · <span className="mono">{o.tax_id}</span></span>
            <span>{[`${a.street ?? ""} ${a.number ?? ""}`.trim(), a.locality, a.region, a.postal_code].filter(Boolean).join(", ")}</span>
            <span>{o.contact_email}</span>
            <span className="muted">{o.registered_by}</span>
          </div>
          <div className="row" style={{ marginTop: 8, flexWrap: "wrap" }}>
            <input value={note} placeholder={t("ident.valNote")} onChange={(e) => setNote(e.target.value)} style={{ minWidth: 280 }} />
            {o.validation !== "validated" && <button className="primary" onClick={() => decide("validated")}>{t("ident.validate")}</button>}
            {o.validation !== "rejected" && <button onClick={() => decide("rejected")}>{t("ident.reject")}</button>}
            {o.validation !== "pending" && <button onClick={() => decide("pending")}>{t("ident.revalidate")}</button>}
          </div>
        </td>
      </tr>
    )}
    </>
  );
}

function NewOrg({ onDone }: { onDone: () => void }) {
  const { t } = useI18n();
  const [name, setName] = useState("");
  const [kind, setKind] = useState<"individual" | "company">("company");
  const [seats, setSeats] = useState("5");
  const [email, setEmail] = useState("");
  const [res, setRes] = useState<Created | null>(null);
  const [err, setErr] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setRes(await api<Created>("/identity/orgs", { method: "POST", headers: json, body: JSON.stringify({ name, kind, seats: kind === "company" ? Number(seats) : 1, owner_email: email }) }));
      setName(""); setEmail(""); setErr(""); onDone();
    } catch (x) { setErr(errorText(x)); }
  };
  return (
    <form className="card" onSubmit={submit}>
      <h2 style={{ marginTop: 0 }}>{t("ident.new")}</h2>
      <div className="fgrid">
        <label className="field"><span>{t("ident.name")}</span><input value={name} onChange={(e) => setName(e.target.value)} required /></label>
        <label className="field"><span>{t("ident.kind")}</span>
          <select value={kind} onChange={(e) => setKind(e.target.value as "individual" | "company")}>
            <option value="company">{t("auth.company")}</option><option value="individual">{t("auth.individual")}</option>
          </select>
        </label>
        {kind === "company" && <label className="field"><span>{t("ident.seats")}</span><input type="number" min={1} value={seats} onChange={(e) => setSeats(e.target.value)} /></label>}
        <label className="field"><span>{t("ident.ownerEmail")}</span><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
      </div>
      <div className="row" style={{ marginTop: 12 }}><button className="primary" type="submit">{t("ident.create")}</button></div>
      {err && <div className="alert bad" style={{ marginTop: 10 }}>{err}</div>}
      {res && (
        <div className="alert ok" style={{ marginTop: 10 }}>
          <div>{t("ident.created")} <b>{res.invitation.email}</b></div>
          <div className="linkbox" style={{ marginTop: 6 }}>
            <input readOnly value={res.invitation.url} onFocus={(e) => e.target.select()} />
            <button type="button" onClick={() => navigator.clipboard?.writeText(res.invitation.url)}>{t("org.copy")}</button>
          </div>
        </div>
      )}
    </form>
  );
}

/** Accounts that belong to no customer organization: the norm reviewer (only sees the norms review) and engineering staff. */
function NewAccount({ onDone }: { onDone: () => void }) {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("standards");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/identity/users", { method: "POST", headers: json, body: JSON.stringify({ email, name, password, platform_role: role }) });
      setEmail(""); setName(""); setPassword(""); setMsg({ ok: true, text: t("ident.accountCreated") }); onDone();
    } catch (x) { setMsg({ ok: false, text: errorText(x) }); }
  };
  return (
    <form className="card" onSubmit={submit}>
      <h2 style={{ marginTop: 0 }}>{t("ident.newAccount")}</h2>
      <div className="fgrid">
        <label className="field"><span>{t("ident.accountRole")}</span>
          <select value={role} onChange={(e) => setRole(e.target.value)}><option value="standards">{t("ident.role.standards")}</option><option value="inspector">{t("ident.role.inspector")}</option><option value="auditor">{t("ident.role.auditor")}</option><option value="admin">{t("ident.role.admin")}</option></select>
        </label>
        <label className="field"><span>{t("ident.name")}</span><input value={name} onChange={(e) => setName(e.target.value)} required /></label>
        <label className="field"><span>{t("auth.email")}</span><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
        <label className="field"><span>{t("ident.tempPassword")}</span><input type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      </div>
      <div className="row" style={{ marginTop: 12 }}><button className="primary" type="submit">{t("ident.createAccount")}</button></div>
      {msg && <div className={"alert " + (msg.ok ? "ok" : "bad")} style={{ marginTop: 10 }}>{msg.text}</div>}
    </form>
  );
}

/** Organizations an inspector or an external auditor may see: exactly the ticked ones. */
function Assignments({ user, orgs, act }: { user: StaffUser; orgs: StaffOrg[]; act: (fn: () => Promise<unknown>) => void }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [sel, setSel] = useState<Set<string>>(new Set(user.assignments.map((a) => a.slug)));
  const toggle = (slug: string) => { const n = new Set(sel); n.has(slug) ? n.delete(slug) : n.add(slug); setSel(n); };
  return (
    <div style={{ marginTop: 6 }}>
      <b>{t("ident.assigned")}:</b> {user.assignments.length ? user.assignments.map((a) => a.name).join(", ") : <span className="muted">{t("ident.noAssigned")}</span>}{" "}
      <button onClick={() => setOpen(!open)}>{t("ident.assign")}</button>
      {open && (
        <div className="card" style={{ marginTop: 6 }}>
          {orgs.map((o) => <label key={o.slug} className="small" style={{ display: "block" }}><input type="checkbox" checked={sel.has(o.slug)} onChange={() => toggle(o.slug)} /> {o.name}</label>)}
          <div className="row" style={{ marginTop: 6 }}>
            <button className="primary" onClick={() => { act(() => api(`/identity/users/${user.id}/assignments`, { method: "PUT", headers: json, body: JSON.stringify({ orgs: [...sel] }) })); setOpen(false); }}>{t("ident.save")}</button>
          </div>
        </div>
      )}
    </div>
  );
}

/** Who did what, to what and when: sign-ins, failed sign-ins, accounts, roles, invitations, assignments, observations. */
function AuditLog() {
  const { t } = useI18n();
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");
  const log = useApi<AuditEvent[]>(`/identity/audit?limit=100&actor=${encodeURIComponent(actor)}&action=${encodeURIComponent(action)}`);
  return (
    <div className="card">
      <div className="row between">
        <h2 style={{ margin: 0 }}>{t("ident.audit")}</h2>
        <div className="row"><input placeholder={t("ident.auditActor")} value={actor} onChange={(e) => setActor(e.target.value)} /><input placeholder={t("ident.auditAction")} value={action} onChange={(e) => setAction(e.target.value)} /></div>
      </div>
      {!log.data ? <State loading={log.loading} error={log.error} /> : log.data.length === 0 ? <div className="state">{t("common.none")}</div> : (
        <div className="scroll">
          <table>
            <thead><tr><th>{t("ident.auditWhen")}</th><th>{t("ident.auditActor")}</th><th>{t("ident.auditAction")}</th><th>{t("ident.auditTarget")}</th></tr></thead>
            <tbody>
              {log.data.map((e, i) => (
                <tr key={i}>
                  <td className="small">{new Date(e.at).toLocaleString()}</td><td className="small">{e.actor || "—"}</td>
                  <td><span className={"badge" + (e.action === "login_failed" ? " bad" : "")}>{e.action}</span></td>
                  <td className="small">{e.target}{e.org ? ` · ${e.org}` : ""}{Object.keys(e.detail ?? {}).length ? <div className="muted mono">{JSON.stringify(e.detail)}</div> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

