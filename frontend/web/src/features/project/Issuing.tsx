import { useState } from "react";
import { ApiError, Badge, IssuingView, Key, State, api, useApi, useI18n } from "@epc/ui";

const json = { "Content-Type": "application/json" };

/** Issue engineering outputs to the client: prepare a transmittal (stamped DXF + PDF + workbooks), then confirm it was sent. */
export default function Issuing({ client, code, onOpenDeliverables }: { client: string; code: string; onOpenDeliverables: () => void }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/issuing`;
  const [rev, setRev] = useState(0);
  const view = useApi<IssuingView>(`${base}?r=${rev}`);
  const [pick, setPick] = useState<Set<string>>(new Set());
  const [emission, setEmission] = useState("ifa");
  const [clientRev, setClientRev] = useState("00");
  const [internalRev, setInternalRev] = useState("00.0.0");
  const [notes, setNotes] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [mail, setMail] = useState<{ id: string; subject: string; body: string } | null>(null);
  const [copied, setCopied] = useState("");
  if (!view.data) return <State loading={view.loading} error={view.error} />;
  const v = view.data;

  const toggle = (id: string) => { const n = new Set(pick); n.has(id) ? n.delete(id) : n.add(id); setPick(n); };
  const prepare = async () => {
    if (pick.size === 0) { setErr({ items: t("issue.pickOne") }); return; }
    setBusy(true);
    try {
      await api(base, { method: "POST", headers: json, body: JSON.stringify({ emission, client_rev: clientRev, internal_rev: internalRev, notes, items: [...pick].map((source) => ({ source })) }) });
      setPick(new Set()); setErr({}); setMsg(t("issue.prepared")); setRev((n) => n + 1);
    } catch (x) {
      setErr(x instanceof ApiError ? x.fieldErrors : { error: String(x) });
    } finally { setBusy(false); }
  };
  const showMail = async (id: string) => {
    if (mail?.id === id) { setMail(null); return; }
    try {
      const m = await api<{ subject: string; body: string }>(`${base}/${id}/message`);
      setMail({ id, ...m }); setCopied(""); setMsg("");
    } catch (x) {
      setMsg(`${t("issue.messageFailed")} (${x instanceof ApiError ? x.status : "error"})`);
    }
  };
  const copy = async (what: string, text: string) => { try { await navigator.clipboard.writeText(text); setCopied(what); } catch { /* the text stays selectable */ } };
  const markSent = async (id: string) => { await api(`${base}/${id}/sent`, { method: "POST" }); setMsg(t("issue.sentOk")); setRev((n) => n + 1); };

  return (
    <div className="grid" style={{ gap: 14 }}>
      <p className="muted small" style={{ margin: 0 }}>{t("issue.help")}</p>
      <div className="card">
        <h2>{t("issue.candidates")}</h2>
        {v.candidates.length === 0 ? <div className="state">{t("issue.none")}</div> : (
          <table>
            <tbody>
              {v.candidates.map((c) => (
                <tr key={c.id}>
                  <td style={{ width: 28 }}><input type="checkbox" checked={pick.has(c.id)} onChange={() => toggle(c.id)} aria-label={c.name} /></td>
                  <td><b>{c.name}</b><div className="muted small">{c.discipline} / {c.package}{c.pdf_will_be_rendered ? ` · ${t("issue.pdfRendered")}` : ""}</div></td>
                  <td><Badge>{t(("issue.k." + c.kind) as Key)}</Badge></td>
                  <td>{c.formats.map((f) => <Badge key={f}>.{f}</Badge>)}</td>
                  <td className="muted small">{t("issue.lastIssue")}: {c.last_issue ?? t("issue.never")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="fgrid">
          <label className="field"><span>{t("issue.emission")}</span><select value={emission} onChange={(e) => setEmission(e.target.value)}>{v.emissions.map((x) => <option key={x} value={x}>{x.toUpperCase()}</option>)}</select></label>
          <label className="field"><span>{t("issue.clientRev")}</span><input value={clientRev} onChange={(e) => setClientRev(e.target.value)} /></label>
          <label className="field"><span>{t("issue.internalRev")}</span><input value={internalRev} onChange={(e) => setInternalRev(e.target.value)} /></label>
          <label className="field"><span>{t("issue.notes")}</span><input value={notes} onChange={(e) => setNotes(e.target.value)} /></label>
        </div>
        <div className="row" style={{ marginTop: 12, flexWrap: "wrap" }}>
          <button className="primary" disabled={busy || v.candidates.length === 0} onClick={prepare}>{t("issue.prepare")} {v.next_transmittal}</button>
          <span className="muted small">{msg}</span>
        </div>
        <div className="muted small" style={{ marginTop: 6 }}>{t("issue.rule")}</div>
        {Object.keys(err).length > 0 && <ul className="errlist">{Object.entries(err).map(([k, x]) => <li key={k}><span className="mono">{k}</span>: {x}</li>)}</ul>}
      </div>

      {v.transmittals.length > 0 && (
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h2 style={{ margin: 0 }}>{t("issue.transmittals")}</h2>
            <button onClick={onOpenDeliverables}>{t("issue.openDeliverables")}</button>
          </div>
          {msg && <div className="alert" style={{ marginTop: 8 }}>{msg}</div>}
          <table>
            <tbody>
              {[...v.transmittals].reverse().map((tr) => (
                <tr key={tr.id}>
                  <td className="mono"><b>{tr.id}</b></td>
                  <td>{tr.emission.toUpperCase()} · Rev {tr.client_rev} <span className="muted small">({tr.internal_rev})</span></td>
                  <td>{tr.items} {t("issue.items")}</td>
                  <td><Badge tone={tr.status === "sent" ? "ok" : "warn"}>{t(("issue.status." + tr.status) as Key)}</Badge></td>
                  <td className="muted small">{tr.sent_on ?? tr.created.slice(0, 10)}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <a className="btn" href={`/api${base}/${tr.id}/package`} download>{t("issue.downloadPackage")}</a>{" "}
                    <button onClick={() => showMail(tr.id)}>{t("issue.message")}</button>{" "}
                    {tr.status === "prepared" && <button onClick={() => markSent(tr.id)}>{t("issue.markSent")}</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {mail && (
            <div className="mailbox">
              <div className="row between">
                <b>{t("issue.message")} · {mail.id}</b>
                <button onClick={() => setMail(null)}>{t("common.close")}</button>
              </div>
              <div className="muted small" style={{ margin: "4px 0" }}>{t("issue.messageHelp")}</div>
              <label className="field"><span>{t("issue.subject")}</span><input readOnly value={mail.subject} onFocus={(e) => e.target.select()} /></label>
              <label className="field" style={{ marginTop: 8 }}><span>{t("issue.body")}</span><textarea readOnly rows={14} value={mail.body} onFocus={(e) => e.target.select()} /></label>
              <div className="row" style={{ marginTop: 8 }}>
                <button onClick={() => copy("subject", mail.subject)}>{copied === "subject" ? t("org.copied") : t("issue.copySubject")}</button>
                <button className="primary" onClick={() => copy("body", mail.body)}>{copied === "body" ? t("org.copied") : t("issue.copyBody")}</button>
                <a className="btn" href={`mailto:?subject=${encodeURIComponent(mail.subject)}&body=${encodeURIComponent(mail.body)}`}>{t("issue.openMail")}</a>
                <a className="btn" href={`/api${base}/${mail.id}/package`} download>{t("issue.downloadPackage")}</a>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
