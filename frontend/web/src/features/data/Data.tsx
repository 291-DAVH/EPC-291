import { FormEvent, ReactNode, useRef, useState } from "react";
import { api, Badge, ClientRecord, errorText, IssuerRecord, JSON_HEADERS, Key, LayersEditor, LuminairesEditor, Me, Page, PersonRecord, SolutionsEditor, State, useApi, useI18n } from "@epc/ui";

type Tab = "issuers" | "clients" | "people" | "layers" | "solutions" | "luminaires";

/** Information that does not change between projects, entered once (company, clients, people, logos). Admin/engineer role only. */
export default function Data() {
  const { t } = useI18n();
  const me = useApi<Me>("/me");
  const write = !me.data || !!me.data.abilities?.orgdata?.includes("write");          // members of an organization read its data; owners and administrators keep it
  const [tab, setTab] = useState<Tab>("issuers");
  return (
    <Page title={t("data.title")} help={t("data.help")}>
      <div className="subtabs" role="tablist">
        {(["issuers", "clients", "people", "layers", "solutions", "luminaires"] as Tab[]).map((x) => (
          <button key={x} role="tab" aria-selected={tab === x} className={tab === x ? "on" : ""} onClick={() => setTab(x)}>{t(("data.tab." + x) as Key)}</button>
        ))}
      </div>
      {tab === "issuers" && <Issuers write={write} />}
      {tab === "clients" && <Clients write={write} />}
      {tab === "people" && <People write={write} />}
      {tab === "layers" && <LayersEditor bare path="/data/drawing-layers" />}
      {tab === "solutions" && <SolutionsEditor bare path="/data/standard-solutions" />}
      {tab === "luminaires" && <LuminairesEditor bare path="/data/luminaires" />}
    </Page>
  );
}

function Field({ label, children }: { label: Key; children: ReactNode }) {
  const { t } = useI18n();
  return <label className="field"><span>{t(label)}</span>{children}</label>;
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

function Issuers({ write }: { write: boolean }) {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const list = useApi<IssuerRecord[]>(`/data/issuers?r=${rev}`);
  const blank = { id: "", legal_name: "", tax_id: "", email: "", website: "", address: "", phone: "", default_locale: "es-AR" };
  const [form, setForm] = useState<typeof blank | null>(null);
  const [err, setErr] = useState("");
  const reload = () => setRev((n) => n + 1);
  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    try {
      await api(form.id ? `/data/issuers/${form.id}` : "/data/issuers", { method: form.id ? "PUT" : "POST", headers: JSON_HEADERS, body: JSON.stringify(form) });
      setForm(null); setErr(""); reload();
    } catch (x) { setErr(errorText(x)); }
  };
  const del = async (id: string) => {
    if (!window.confirm(t("data.confirmDelete"))) return;
    try { await api(`/data/issuers/${id}`, { method: "DELETE" }); reload(); } catch (x) { setErr(errorText(x)); }
  };
  const makeDefault = async (id: string) => { await api(`/data/issuers/${id}/default`, { method: "POST" }); reload(); };
  const f = (k: keyof typeof blank, label: Key) => <Field label={label}><input value={form ? String(form[k] ?? "") : ""} onChange={(e) => form && setForm({ ...form, [k]: e.target.value })} /></Field>;
  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{t("data.tab.issuers")}</h2>
          {!form && write && <button className="primary" onClick={() => setForm(blank)}>+ {t("data.add")}</button>}
        </div>
        <p className="muted small" style={{ margin: "4px 0 8px" }}>{t("data.issuersHelp")}</p>
        {err && !form && <div className="small" style={{ color: "var(--bad)" }}>{err}</div>}
        {!list.data ? <State loading={list.loading} error={list.error} /> : list.data.length === 0 ? <div className="state">{t("data.issuersEmpty")}</div> : (
          <table>
            <thead><tr><th>{t("data.legalName")}</th><th>{t("data.taxId")}</th><th>{t("data.logo")}</th><th /></tr></thead>
            <tbody>
              {list.data.map((i) => (
                <tr key={i.id}>
                  <td><b>{i.legal_name}</b> {i.default && <Badge tone="accent">{t("data.default")}</Badge>}</td><td>{i.tax_id}</td>
                  <td><Logo kind={`issuer-${i.id}`} has={i.has_logo} onChange={reload} /></td>
                  <td style={{ whiteSpace: "nowrap" }}>{write && <>
                    <button onClick={() => setForm({ id: i.id, legal_name: i.legal_name, tax_id: i.tax_id, email: i.email, website: i.website, address: i.address, phone: i.phone, default_locale: i.default_locale })}>{t("data.edit")}</button>{" "}
                    {!i.default && <><button onClick={() => makeDefault(i.id)}>{t("data.makeDefault")}</button>{" "}</>}
                    <button onClick={() => del(i.id)}>{t("data.delete")}</button></>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {form && (
        <form className="card" onSubmit={save}>
          <div className="fgrid">{f("legal_name", "data.legalName")}{f("tax_id", "data.taxId")}{f("email", "data.email")}{f("website", "data.website")}{f("address", "data.address")}{f("phone", "data.phone")}</div>
          <div className="row" style={{ marginTop: 12 }}><button className="primary" type="submit">{t("data.save")}</button><button type="button" onClick={() => { setForm(null); setErr(""); }}>{t("data.cancel")}</button>{err && <span className="small" style={{ color: "var(--bad)" }}>{err}</span>}</div>
        </form>
      )}
    </div>
  );
}

function Clients({ write }: { write: boolean }) {
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
      await api(editing ? `/data/clients/${editing}` : "/data/clients", { method: editing ? "PUT" : "POST", headers: JSON_HEADERS, body: JSON.stringify(form) });
      setForm(null); setEditing(null); setErr(""); reload();
    } catch (x) { setErr(errorText(x)); }
  };
  const del = async (id: string) => { if (window.confirm(t("data.confirmDelete"))) { await api(`/data/clients/${id}`, { method: "DELETE" }); reload(); } };
  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{t("data.tab.clients")}</h2>
          {!form && write && <button className="primary" onClick={() => { setForm(blank); setEditing(null); }}>+ {t("data.add")}</button>}
        </div>
        {!list.data ? <State loading={list.loading} error={list.error} /> : list.data.length === 0 ? <div className="state">{t("data.empty")}</div> : (
          <table>
            <thead><tr><th>{t("data.code")}</th><th>{t("data.name")}</th><th>{t("data.taxId")}</th><th>{t("data.logo")}</th><th /></tr></thead>
            <tbody>
              {list.data.map((c) => (
                <tr key={c.id}>
                  <td className="mono">{c.id}</td><td>{c.name}</td><td>{c.tax_id}</td>
                  <td><Logo kind={`client-${c.id}`} has={c.has_logo} onChange={reload} /></td>
                  <td style={{ whiteSpace: "nowrap" }}>{write && <>
                    <button onClick={() => { setForm({ id: c.id, name: c.name, tax_id: c.tax_id, email: c.email, website: c.website, address: c.address }); setEditing(c.id); }}>{t("data.edit")}</button>{" "}
                    <button onClick={() => del(c.id)}>{t("data.delete")}</button></>}
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

function People({ write }: { write: boolean }) {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const list = useApi<PersonRecord[]>(`/data/people?r=${rev}`);
  const roleList = useApi<string[]>("/data/people/roles");
  const blank = { name: "", role: "", registration: "", roles: [] as string[] };
  const [form, setForm] = useState<typeof blank | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const reload = () => setRev((n) => n + 1);
  const save = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    try {
      await api(editing ? `/data/people/${editing}` : "/data/people", { method: editing ? "PUT" : "POST", headers: JSON_HEADERS, body: JSON.stringify(form) });
      setForm(null); setEditing(null); setErr(""); reload();
    } catch (x) { setErr(errorText(x)); }
  };
  const del = async (id: string) => { if (window.confirm(t("data.confirmDelete"))) { await api(`/data/people/${id}`, { method: "DELETE" }); reload(); } };
  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{t("data.tab.people")}</h2>
          {!form && write && <button className="primary" onClick={() => { setForm(blank); setEditing(null); }}>+ {t("data.add")}</button>}
        </div>
        {!list.data ? <State loading={list.loading} error={list.error} /> : list.data.length === 0 ? <div className="state">{t("data.empty")}</div> : (
          <table>
            <thead><tr><th>{t("data.name")}</th><th>{t("data.role")}</th><th>{t("data.functions")}</th><th>{t("data.registration")}</th><th /></tr></thead>
            <tbody>
              {list.data.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td><td>{p.role}</td><td>{(p.roles ?? []).map((r) => <Badge key={r}>{t(("data.pr." + r) as Key)}</Badge>)}</td><td>{p.registration}</td>
                  <td style={{ whiteSpace: "nowrap" }}>{write && <>
                    <button onClick={() => { setForm({ name: p.name, role: p.role, registration: p.registration, roles: p.roles ?? [] }); setEditing(p.id); }}>{t("data.edit")}</button>{" "}
                    <button onClick={() => del(p.id)}>{t("data.delete")}</button></>}
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
          <div style={{ marginTop: 10 }}>
            <div className="muted small">{t("data.functions")}</div>
            <div className="row" style={{ flexWrap: "wrap" }}>
              {(roleList.data ?? []).map((r) => (
                <label key={r} className="row chip">
                  <input type="checkbox" checked={form.roles.includes(r)} onChange={() => setForm({ ...form, roles: form.roles.includes(r) ? form.roles.filter((x) => x !== r) : [...form.roles, r] })} />
                  {t(("data.pr." + r) as Key)}
                </label>
              ))}
            </div>
          </div>
          <div className="row" style={{ marginTop: 12 }}><button className="primary" type="submit">{t("data.save")}</button><button type="button" onClick={() => { setForm(null); setEditing(null); setErr(""); }}>{t("data.cancel")}</button>{err && <span className="small" style={{ color: "var(--bad)" }}>{err}</span>}</div>
        </form>
      )}
    </div>
  );
}
