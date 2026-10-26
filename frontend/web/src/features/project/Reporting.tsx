import { FormEvent, useState } from "react";
import { api, ApiError, Badge, GeneratedReport, JSON_HEADERS, ReportingView, State, useApi, useI18n } from "@epc/ui";


/** Management reports of the project's methodology (PM²): choose one, generate it from the project's data, review it, publish it to the client. Engineer only. */
export default function Reporting({ client, code, onPublished }: { client: string; code: string; onPublished: () => void }) {
  const { t } = useI18n();
  const base = `/projects/${client}/${code}/reporting`;
  const [rev, setRev] = useState(0);
  const view = useApi<ReportingView>(`${base}?r=${rev}`);
  const [type, setType] = useState("status");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  if (!view.data) return <State loading={view.loading} error={view.error} />;
  const v = view.data;
  if (v.available === false) return <div className="card" style={{ marginBottom: 14 }}><div className="state">{t("rep.unavailable")} ({v.methodology.toUpperCase()})</div></div>;
  const cur = v.types.find((x) => x.id === type) ?? v.types[0];
  const fail = (x: unknown) => setMsg({ ok: false, text: `${t("rep.failed")}: ${x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || x.status : "error"}` });

  const generate = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setMsg(null);
    try {
      const r = await api<GeneratedReport>(base, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ type, period_start: from || null, period_end: to || null }) });
      setMsg({ ok: true, text: `${t("rep.generated")}: ${r.id}` }); setRev((n) => n + 1);
    } catch (x) { fail(x); } finally { setBusy(false); }
  };
  const publish = async (r: GeneratedReport) => {
    if (!window.confirm(t("rep.confirmPublish"))) return;
    try { await api(`${base}/${r.id}/publish`, { method: "POST" }); setMsg({ ok: true, text: t("rep.publishedOk") }); setRev((n) => n + 1); onPublished(); } catch (x) { fail(x); }
  };

  return (
    <div className="card" style={{ marginBottom: 14 }}>
      <div className="row between">
        <h2 style={{ margin: 0 }}>{t("rep.title")}</h2>
        <Badge tone="accent">{v.methodology.toUpperCase()}</Badge>
      </div>
      <p className="muted small" style={{ margin: "4px 0 10px" }}>{t("rep.help")}</p>
      <form onSubmit={generate}>
        <div className="fgrid">
          <label className="field"><span>{t("rep.type")}</span>
            <select value={type} onChange={(e) => setType(e.target.value)}>
              {v.types.map((x) => <option key={x.id} value={x.id}>{x.code} · {x.name}</option>)}
            </select>
          </label>
          <label className="field"><span>{t("rep.from")}</span><input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
          <label className="field"><span>{t("rep.to")}</span><input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></label>
        </div>
        <div className="muted small" style={{ marginTop: 6 }}>
          {t(cur.audience === "client" ? "rep.aud.client" : "rep.aud.internal")}
          {cur.last_period_end ? ` · ${t("rep.continues")} ${cur.last_period_end}` : ""}
        </div>
        <div className="row" style={{ marginTop: 10 }}>
          <button className="primary" type="submit" disabled={busy}>{busy ? t("rep.generating") : `${t("rep.generate")} ${cur.code}-${String(cur.next_number).padStart(2, "0")}`}</button>
        </div>
      </form>
      {msg && <div className={"alert " + (msg.ok ? "ok" : "bad")} style={{ marginTop: 10 }}>{msg.text}</div>}

      <h3 style={{ marginBottom: 4 }}>{t("rep.list")}</h3>
      {v.reports.length === 0 ? <div className="muted">{t("rep.none")}</div> : (
        <table>
          <thead><tr><th>{t("rep.id")}</th><th>{t("rep.period")}</th><th>{t("rep.by")}</th><th>{t("rep.state")}</th><th /></tr></thead>
          <tbody>
            {v.reports.map((r) => (
              <tr key={r.id}>
                <td><b className="mono">{r.id}</b><div className="muted small">{r.code} · {r.name}</div></td>
                <td className="small">{r.period[0]} → {r.period[1]}<div className="muted">{r.date}</div></td>
                <td className="small">{r.prepared_by}</td>
                <td>{r.published ? <Badge tone="ok">{t("rep.published")} · {r.published}</Badge> : <Badge>{t("rep.internal")}</Badge>}</td>
                <td style={{ whiteSpace: "nowrap" }}>
                  <a className="btn" href={`/api${base}/${r.id}/file?format=pdf`} download>PDF</a>{" "}
                  {!r.published && <button onClick={() => publish(r)}>{t("rep.publish")}</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
