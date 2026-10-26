import { FormEvent, useState } from "react";
import { ApiError, Badge, Key, RequirementItem, State, api, useApi, useI18n } from "@epc/ui";

export default function Requirements({ canWrite, base, rev, onChange }: { canWrite: boolean; base: string; rev: number; onChange: () => void }) {
  const { t } = useI18n();
  const { data, loading, error } = useApi<RequirementItem[]>(base + "/requirements?r=" + rev);
  return (
    <>
      <p className="help">{t("u.r.help")}</p>
      <State loading={loading} error={error} />
      {data?.length === 0 && <div className="state">{t("u.r.none")}</div>}
      <div className="grid reqs">
        {data?.map((r) => (
          <div key={r.id} className="card">
            <div className="row between">
              <span className="mono muted">{r.id}</span>
              <div className="row">
                <Badge tone={r.priority === "alta" ? "bad" : r.priority === "media" ? "warn" : undefined}>{t(("u.r.prio." + r.priority) as Key)}</Badge>
                <Badge tone={r.status === "abierto" ? "warn" : "ok"}>{t(("u.r.status." + r.status) as Key)}</Badge>
              </div>
            </div>
            <p style={{ margin: "8px 0", fontWeight: 600 }}>{r.statement}</p>
            <div className="row small"><Badge>{r.type}</Badge>{r.discipline !== "general" && <Badge>{t(("projects.disc." + r.discipline) as Key)}</Badge>}</div>
            {r.acceptance.length > 0 && (<><h4>{t("u.r.acceptance")}</h4><ul>{r.acceptance.map((a) => <li key={a}>{a}</li>)}</ul></>)}
            {r.open_questions.length > 0 && (
              <>
                <h4 className="warnh">{t("u.r.questions")}</h4>
                <ul className="qlist">{r.open_questions.map((q) => <OpenQuestion key={q} canWrite={canWrite} base={base} reqId={r.id} question={q} onAnswered={onChange} />)}</ul>
              </>
            )}
            {(r.answered_questions ?? []).length > 0 && (
              <>
                <h4 className="okh">{t("u.r.answered")}</h4>
                <ul className="qlist">
                  {r.answered_questions!.map((a, i) => (
                    <li key={i}>
                      <div>{a.question}</div>
                      <div className="answer">{a.answer}</div>
                      <div className="muted small">{t("u.r.answeredBy")} {a.by} · {new Date(a.at).toLocaleString()}</div>
                    </li>
                  ))}
                </ul>
              </>
            )}
            <div className="muted small">{t("u.r.origin")}: {r.source_titles.join(", ")}</div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ---------------- reports ---------------- */

/** An open question: click "Responder", write the answer; it is stored with who answered and when. */
function OpenQuestion({ canWrite, base, reqId, question, onAnswered }: { canWrite: boolean; base: string; reqId: string; question: string; onAnswered: () => void }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const save = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      await api(`${base}/requirements/${reqId}/answer`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question, answer: text }) });
      onAnswered();
    } catch (x) { setErr(x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || String(x.status) : "error"); } finally { setBusy(false); }
  };
  return (
    <li>
      {!canWrite ? question : !open ? (
        <button className="qbtn" onClick={() => setOpen(true)} title={t("u.r.answer")}>{question} <span className="qhint">{t("u.r.answer")} →</span></button>
      ) : (
        <form onSubmit={save}>
          <div>{question}</div>
          <textarea autoFocus rows={3} value={text} onChange={(e) => setText(e.target.value)} placeholder={t("u.r.answerPlaceholder")} required style={{ width: "100%", marginTop: 6 }} />
          {err && <div className="small" style={{ color: "var(--bad)" }}>{err}</div>}
          <div className="row" style={{ marginTop: 6 }}>
            <button className="primary" type="submit" disabled={busy || !text.trim()}>{t("u.r.saveAnswer")}</button>
            <button type="button" onClick={() => { setOpen(false); setText(""); }}>{t("common.close")}</button>
          </div>
        </form>
      )}
    </li>
  );
}
