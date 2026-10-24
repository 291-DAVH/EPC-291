import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, Badge, Key, PartiesView, State, TeamRow, api, useApi, useI18n } from "@epc/ui";

const json = { "Content-Type": "application/json" };
const ROLES: (keyof TeamRow)[] = ["drawn_by", "checked_by", "approved_by"];
const FUNCTION: Record<keyof TeamRow, string> = { drawn_by: "designer", checked_by: "checker", approved_by: "approver" };           // who may be suggested for each

/** Who issues and who signs the project: set once here, every board's title block uses it. The issuer is chosen per project; the team per discipline. */
export default function Parties({ client, code }: { client: string; code: string }) {
  const { t } = useI18n();
  const [rev, setRev] = useState(0);
  const v = useApi<PartiesView>(`/projects/${client}/${code}/parties?r=${rev}`);
  const [issuer, setIssuer] = useState("");
  const [team, setTeam] = useState<Record<string, TeamRow>>({});
  const [msg, setMsg] = useState("");
  const [dirty, setDirty] = useState(false);
  useEffect(() => { if (v.data) { setIssuer(v.data.issuer_id); setTeam(v.data.team); setDirty(false); } }, [v.data]);
  if (!v.data) return <State loading={v.loading} error={v.error} />;
  const d = v.data;
  const setCell = (disc: string, k: keyof TeamRow, val: string) => { setTeam({ ...team, [disc]: { ...team[disc], [k]: val } }); setDirty(true); setMsg(""); };
  const save = async () => {
    try {
      await api(`/projects/${client}/${code}/parties`, { method: "PUT", headers: json, body: JSON.stringify({ issuer, team }) });
      setRev((n) => n + 1); setMsg(t("parties.saved"));
    } catch (x) { setMsg(x instanceof ApiError ? Object.values(x.fieldErrors).join(" · ") || String(x) : String(x)); }
  };
  const addClient = async () => {
    try { await api("/data/clients", { method: "POST", headers: json, body: JSON.stringify({ id: d.client.id, name: d.client.name }) }); setRev((n) => n + 1); } catch (x) { setMsg(x instanceof ApiError ? Object.values(x.fieldErrors).join(" · ") : String(x)); }
  };
  const chosen = d.issuers.find((i) => i.id === issuer);
  return (
    <div className="grid" style={{ gap: 14 }}>
      <p className="muted small" style={{ margin: 0 }}>{t("parties.help")}</p>
      <div className="cols2">
        <div className="card">
          <h2>{t("parties.issuer")}</h2>
          {d.issuers.length === 0 ? <div className="state">{t("parties.noIssuers")} <Link to="/data">{t("parties.goData")}</Link></div> : (
            <>
              <select value={issuer} onChange={(e) => { setIssuer(e.target.value); setDirty(true); setMsg(""); }} aria-label={t("parties.issuer")}>
                {d.issuers.map((i) => <option key={i.id} value={i.id}>{i.legal_name}{i.default ? ` · ${t("data.default")}` : ""}</option>)}
              </select>
              {d.issuer && chosen && <p className="small muted" style={{ margin: "8px 0 0" }}>{t("data.taxId")}: {d.issuer.id === issuer ? d.issuer.tax_id || "—" : "—"} · {t("data.logo")}: {d.issuer.id === issuer ? (d.issuer.has_logo ? "✓" : "—") : "…"}</p>}
              <p className="small muted" style={{ margin: "6px 0 0" }}>{t("parties.issuerHelp")} <Link to="/data">{t("parties.goData")}</Link></p>
            </>
          )}
        </div>
        <div className="card">
          <h2>{t("parties.client")}</h2>
          <p style={{ margin: "0 0 4px" }}><b>{d.client.name || d.client.id}</b> <span className="muted mono">{d.client.id}</span></p>
          <p className="small muted" style={{ margin: 0 }}>{t("data.taxId")}: {d.client.tax_id || "—"} · {t("data.logo")}: {d.client.has_logo ? "✓" : "—"}</p>
          {!d.client.in_directory && (
            <p className="small" style={{ margin: "8px 0 0" }}>{t("parties.clientNew")} <button onClick={addClient}>{t("parties.clientAdd")}</button></p>
          )}
          <p className="small muted" style={{ margin: "6px 0 0" }}>{t("parties.clientHelp")} <Link to="/data">{t("parties.goData")}</Link></p>
        </div>
      </div>
      <div className="card">
        <h2>{t("parties.team")}</h2>
        <p className="muted small" style={{ margin: "2px 0 8px" }}>{t("parties.teamHelp")}</p>
        {ROLES.map((r) => <datalist key={r} id={"parties-people-" + r}>{d.people.filter((p) => p.roles.length === 0 || p.roles.includes(FUNCTION[r])).map((p) => <option key={p.name} value={p.name} />)}</datalist>)}
        <div style={{ overflowX: "auto" }}>
          <table className="sldtable">
            <thead><tr><th>{t("u.f.discipline")}</th>{ROLES.map((r) => <th key={r}>{t(("parties.role." + r) as Key)}</th>)}</tr></thead>
            <tbody>
              {d.disciplines.map((disc) => (
                <tr key={disc}>
                  <td><b>{t(("projects.disc." + disc) as Key)}</b></td>
                  {ROLES.map((r) => <td key={r}><input list={"parties-people-" + r} className="w-desc" value={team[disc]?.[r] ?? ""} onChange={(e) => setCell(disc, r, e.target.value)} aria-label={`${disc} ${r}`} /></td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="row">
        <button className="primary" onClick={save} disabled={!dirty}>{t("data.save")}</button>
        {dirty && <Badge tone="warn">{t("sld.unsaved")}</Badge>}
        {msg && <span className="muted small">{msg}</span>}
      </div>
    </div>
  );
}
