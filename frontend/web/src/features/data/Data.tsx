import { FormEvent, ReactNode, useRef, useState } from "react";
import { ApiError, ClientRecord, Key, OrganizationData, Page, PersonRecord, State, api, useApi, useI18n } from "@epc/ui";

type Tab = "organization" | "clients" | "people";
const json = { "Content-Type": "application/json" };

/** Information that does not change between projects, entered once (company, clients, people, logos). Admin/engineer role only. */
export default function Data() {
  const { t } = useI18n();
  const [tab, setTab] = useState<Tab>("organization");
  return (
    <Page title={t("data.title")} help={t("data.help")}>
      <div className="subtabs" role="tablist">
        {(["organization", "clients", "people"] as Tab[]).map((x) => (
          <button key={x} role="tab" aria-selected={tab === x} className={tab === x ? "on" : ""} onClick={() => setTab(x)}>{t(("data.tab." + x) as Key)}</button>
        ))}
      </div>
      {tab === "organization" && <Organization />}
      {tab === "clients" && <Clients />}
      {tab === "people" && <People />}
    </Page>
  );
}

function Field({ label, children }: { label: Key; children: ReactNode }) {
  const { t } = useI18n();
  return <label className="field"><span>{t(label)}</span>{children}</label>;
}

function errorText(x: unknown): string {
  return x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || String(x.status) : "error";
}

/** Logo of the company or of a client: preview, upload, remove. */
function Logo({ kind, has, onChange }: { kind: string; has: boolean; onChange: () => void }) {
  const { t } = useI18n();
  const input = useRef<HTMLInputElement>(null);
  const [err, setErr] = useState("");
  const [v, setV] = useState(0);
  const upload = async (file?: File) => {
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    try { await api(`/data/logos/${kind}`, { method: "POST", body }); setErr(""); setV((n) => n + 1); onChange(); } catch (x) { setErr(errorText(x)); }
    if (input.current) input.current.value = "";
  };
  const remove = async () => { await api(`/data/logos/${kind}`, { method: "DELETE" }); setV((n) => n + 1); onChange(); };
  return (
    <div className="logobox">
      <div className="thumb">{has ? <img src={`/api/data/logos/${kind}?v=${v}`} alt={t("data.logo")} /> : <span className="muted small">{t("data.noLogo")}</span>}</div>
      <div>
        <div className="row"><button onClick={() => input.current?.click()}>{t("data.logoUpload")}</button>{has && <button onClick={remove}>{t("data.logoRemove")}</button>}</div>
        <div className="muted small">{t("data.logoHelp")}</div>
        {err && <div className="small" style={{ color: "var(--bad)" }}>{err}</div>}
      </div>
      <input ref={input} type="file" accept=".svg,.png,image/svg+xml,image/png" hidden onChange={(e) => upload(e.target.files?.[0])} />
    </div>
  );
}

function Organization() {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const org = useApi<OrganizationData>(`/data/organization?r=${rev}`);
  const [edit, setEdit] = useState<Partial<OrganizationData>>({});
  const [msg, setMsg] = useState("");
  if (!org.data) return <State loading={org.loading} error={org.error} />;
  const v = { ...org.data, ...edit };
  const set = (k: keyof OrganizationData, val: string) => { setEdit({ ...edit, [k]: val }); setMsg(""); };
  const save = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/data/organization", { method: "PUT", headers: json, body: JSON.stringify({ legal_name: v.legal_name, tax_id: v.tax_id, email: v.email, website: v.website, address: v.address, phone: v.phone, default_locale: v.default_locale }) });
      setEdit({}); setRev((n) => n + 1); setMsg(t("data.saved"));
    } catch (x) { setMsg(errorText(x)); }
  };
  const text = (k: keyof OrganizationData, label: Key) => <Field label={label}><input value={String(v[k] ?? "")} onChange={(e) => set(k, e.target.value)} /></Field>;
  return (
    <form className="card" onSubmit={save}>
      <div className="fgrid">{text("legal_name", "data.legalName")}{text("tax_id", "data.taxId")}{text("email", "data.email")}{text("website", "data.website")}{text("address", "data.address")}{text("phone", "data.phone")}</div>
      <div className="row" style={{ marginTop: 14 }}><button className="primary" type="submit">{t("data.save")}</button><span className="muted small">{msg}</span></div>
      <h3 style={{ marginTop: 18 }}>{t("data.logo")}</h3>
      <Logo kind="organization" has={org.data.has_logo} onChange={() => setRev((n) => n + 1)} />
    </form>
  );
}

function Clients() {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const list = useApi<ClientRecord[]>(`/data/clients?r=${rev}`);
  const blank = { id: "", name: "", tax_id: "", email: "", website: "", address: "" };
  const [form, setForm] = useState<typeof blank | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const reload = () => setRev((n) => n + 1);
  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    try {
      await api(editing ? `/data/clients/${editing}` : "/data/clients", { method: editing ? "PUT" : "POST", headers: json, body: JSON.stringify(form) });
      setForm(null); setEditing(null); setErr(""); reload();
    } catch (x) { setErr(errorText(x)); }
  };
  const del = async (id: string) => { if (window.confirm(t("data.confirmDelete"))) { await api(`/data/clients/${id}`, { method: "DELETE" }); reload(); } };
  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{t("data.tab.clients")}</h2>
          {!form && <button className="primary" onClick={() => { setForm(blank); setEditing(null); }}>+ {t("data.add")}</button>}
        </div>
        {!list.data ? <State loading={list.loading} error={list.error} /> : list.data.length === 0 ? <div className="state">{t("data.empty")}</div> : (
          <table>
            <thead><tr><th>{t("data.code")}</th><th>{t("data.name")}</th><th>{t("data.taxId")}</th><th>{t("data.logo")}</th><th /></tr></thead>
            <tbody>
              {list.data.map((c) => (
                <tr key={c.id}>
                  <td className="mono">{c.id}</td><td>{c.name}</td><td>{c.tax_id}</td>
                  <td><Logo kind={`client-${c.id}`} has={c.has_logo} onChange={reload} /></td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <button onClick={() => { setForm({ id: c.id, name: c.name, tax_id: c.tax_id, email: c.email, website: c.website, address: c.address }); setEditing(c.id); }}>{t("data.edit")}</button>{" "}
                    <button onClick={() => del(c.id)}>{t("data.delete")}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {form && (
        <form className="card" onSubmit={save}>
          <div className="fgrid">
            <Field label="data.code"><input value={form.id} disabled={!!editing} onChange={(e) => setForm({ ...form, id: e.target.value.toUpperCase() })} /></Field>
            <Field label="data.name"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
            <Field label="data.taxId"><input value={form.tax_id} onChange={(e) => setForm({ ...form, tax_id: e.target.value })} /></Field>
            <Field label="data.email"><input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
            <Field label="data.website"><input value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} /></Field>
            <Field label="data.address"><input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></Field>
          </div>
          <div className="row" style={{ marginTop: 12 }}><button className="primary" type="submit">{t("data.save")}</button><button type="button" onClick={() => { setForm(null); setEditing(null); setErr(""); }}>{t("data.cancel")}</button>{err && <span className="small" style={{ color: "var(--bad)" }}>{err}</span>}</div>
        </form>
      )}
    </div>
  );
}

function People() {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const list = useApi<PersonRecord[]>(`/data/people?r=${rev}`);
  const blank = { name: "", role: "", registration: "" };
  const [form, setForm] = useState<typeof blank | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const reload = () => setRev((n) => n + 1);
  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    try {
      await api(editing ? `/data/people/${editing}` : "/data/people", { method: editing ? "PUT" : "POST", headers: json, body: JSON.stringify(form) });
      setForm(null); setEditing(null); setErr(""); reload();
    } catch (x) { setErr(errorText(x)); }
  };
  const del = async (id: string) => { if (window.confirm(t("data.confirmDelete"))) { await api(`/data/people/${id}`, { method: "DELETE" }); reload(); } };
  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{t("data.tab.people")}</h2>
          {!form && <button className="primary" onClick={() => { setForm(blank); setEditing(null); }}>+ {t("data.add")}</button>}
        </div>
        {!list.data ? <State loading={list.loading} error={list.error} /> : list.data.length === 0 ? <div className="state">{t("data.empty")}</div> : (
          <table>
            <thead><tr><th>{t("data.name")}</th><th>{t("data.role")}</th><th>{t("data.registration")}</th><th /></tr></thead>
            <tbody>
              {list.data.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td><td>{p.role}</td><td>{p.registration}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <button onClick={() => { setForm({ name: p.name, role: p.role, registration: p.registration }); setEditing(p.id); }}>{t("data.edit")}</button>{" "}
                    <button onClick={() => del(p.id)}>{t("data.delete")}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {form && (
        <form className="card" onSubmit={save}>
          <div className="fgrid">
            <Field label="data.name"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
            <Field label="data.role"><input value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} /></Field>
            <Field label="data.registration"><input value={form.registration} onChange={(e) => setForm({ ...form, registration: e.target.value })} /></Field>
          </div>
          <div className="row" style={{ marginTop: 12 }}><button className="primary" type="submit">{t("data.save")}</button><button type="button" onClick={() => { setForm(null); setEditing(null); setErr(""); }}>{t("data.cancel")}</button>{err && <span className="small" style={{ color: "var(--bad)" }}>{err}</span>}</div>
        </form>
      )}
    </div>
  );
}
