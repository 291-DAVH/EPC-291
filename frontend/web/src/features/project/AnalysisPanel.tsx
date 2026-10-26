import { useState } from "react";
import { AnalysisResult, AnalysisStatus, ApiError, api, useApi, useI18n } from "@epc/ui";

export default function AnalysisPanel({ client, code, onDone }: { client: string; code: string; onDone: () => void }) {
  const { t } = useI18n();
  const path = `/projects/${client}/${code}/analysis`;
  const [rev, setRev] = useState(0);
  const st = useApi<AnalysisStatus>(`${path}?r=${rev}`);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<AnalysisResult | null>(null);
  const [err, setErr] = useState("");
  if (!st.data) return null;
  const run = async () => {
    if (!window.confirm(t("an.confirm"))) return;
    setBusy(true); setErr(""); setRes(null);
    try {
      setRes(await api<AnalysisResult>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm: true }) }));
      setRev((n) => n + 1); onDone();
    } catch (x) {
      setErr(x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || String(x.status) : "error");
    } finally { setBusy(false); }
  };
  const d = st.data;
  return (
    <div className="card" style={{ marginBottom: 14 }}>
      <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
        <div>
          <b>{t("an.title")}</b> <span className="muted">· {d.pending} {t("an.pending")}</span>
          <div className="muted small">{t("an.help")}</div>
        </div>
        <button className="primary" disabled={busy || !d.configured || d.pending === 0} onClick={run}>{busy ? t("an.running") : t("an.run")}</button>
      </div>
      {!d.configured && <div className="alert" style={{ marginTop: 8 }}>{t("an.notConfigured")}</div>}
      {res && <div className="alert ok" style={{ marginTop: 8 }}><b>{t("an.done")}:</b> {res.created.length} {t("an.created")}, {res.merged.length} {t("an.merged")}, {res.open_questions} {t("an.questions")}</div>}
      {err && <div className="alert bad" style={{ marginTop: 8 }}><b>{t("an.failed")}:</b> {err}</div>}
      {d.usage.calls > 0 && <div className="muted small" style={{ marginTop: 6 }}>{t("an.usage")}: {d.usage.calls} {t("an.calls")} · {d.usage.input_tokens + d.usage.output_tokens} {t("an.tokens")} · {d.model}</div>}
    </div>
  );
}
