import { useState } from "react";
import { ApiError, Badge, CriteriaView, Criterion, Key, Markdown, State, api, useApi, useI18n } from "@epc/ui";

const SOURCES = ["client", "standard", "project"] as const;

/** Quick editing of the design criteria of a project (e.g. socket height requested by the client). */
export default function DesignCriteria({ client, code }: { client: string; code: string }) {
  const { t, lang } = useI18n();
  const base = `/projects/${client}/${code}/engineering/criteria`;
  const [rev, setRev] = useState(0);
  const view = useApi<CriteriaView>(`${base}?r=${rev}`);
  const report = useApi<{ markdown: string }>(`${base}/report?lang=${lang}&r=${rev}`);
  if (!view.data) return <State loading={view.loading} error={view.error} />;
  const v = view.data;
  const reload = () => setRev((n) => n + 1);

  let group = "";
  const rows = v.items.flatMap((c) => {
    const g = c.group[lang];
    const head = g !== group ? [<tr key={"g" + g}><td colSpan={5} className="crit-group">{g}</td></tr>] : [];
    group = g;
    return [...head, <Row key={c.id} c={c} base={base} onSaved={reload} />];
  });

  return (
    <div className="grid" style={{ gap: 14 }}>
      <p className="muted small" style={{ margin: 0 }}>{t("crit.help")}</p>
      {!v.validated && <div className="alert">{t("crit.notValidated")}</div>}
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>{t("eng.sub.criteria")} · {v.jurisdiction} / {v.discipline}</h2>
          <span className="muted small">{v.changed} {t("crit.changed")}</span>
        </div>
        <table className="crit"><tbody>{rows}</tbody></table>
      </div>
      <div className="cols2">
        <div className="card">
          <h2>{t("crit.report")}</h2>
          {report.data ? <Markdown text={report.data.markdown} /> : <State loading />}
        </div>
        <div className="card">
          <h2>{t("crit.history")}</h2>
          {v.history.length === 0 && <div className="muted">{t("crit.noHistory")}</div>}
          {v.history.map((h, i) => {
            const spec = v.items.find((x) => x.id === h.key);
            return (
              <div className="item" key={i}>
                <b>{spec ? spec.label[lang] : h.key}</b>: {String(h.from)} → {String(h.to)} <span className="muted">· {t(("crit.s." + h.source) as Key)}</span>
                <div className="muted small">{h.at.replace("T", " ")}{h.note ? ` · ${h.note}` : ""}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Row({ c, base, onSaved }: { c: Criterion; base: string; onSaved: () => void }) {
  const { t, lang } = useI18n();
  const [value, setValue] = useState<string>(String(c.value));
  const [source, setSource] = useState<string>(c.overridden ? c.source : "client");
  const [note, setNote] = useState(c.note);
  const [err, setErr] = useState("");
  const dirty = value !== String(c.value) || (c.overridden && (source !== c.source || note !== c.note)) || (!c.overridden && note !== "");

  const send = async (method: "PUT" | "DELETE") => {
    try {
      await api(`${base}/${c.id}`, { method, headers: { "Content-Type": "application/json" }, body: method === "PUT" ? JSON.stringify({ value: c.type === "number" ? Number(value.replace(",", ".")) : value, source, note }) : undefined });
      setErr("");
      onSaved();
    } catch (x) {
      setErr(x instanceof ApiError ? Object.values(x.fieldErrors).join(", ") || String(x.status) : "error");
    }
  };

  return (
    <tr className={c.overridden ? "mod" : ""}>
      <td style={{ width: "34%" }}>{c.label[lang]}{c.overridden && <div className="muted small">{t("crit.default")}: {String(c.default)} {c.unit}</div>}</td>
      <td style={{ whiteSpace: "nowrap" }}>
        {c.type === "choice" ? (
          <select value={value} onChange={(e) => setValue(e.target.value)} aria-label={c.label[lang]}>
            {c.options!.map((o) => <option key={String(o)} value={String(o)}>{String(o)}</option>)}
          </select>
        ) : (
          <input type="number" step="any" min={c.min} max={c.max} value={value} onChange={(e) => setValue(e.target.value)} aria-label={c.label[lang]} />
        )}{" "}
        <span className="muted">{c.unit}</span>
      </td>
      <td>
        {c.overridden || dirty ? (
          <select value={source} onChange={(e) => setSource(e.target.value)} aria-label={t("crit.source")}>
            {SOURCES.map((s) => <option key={s} value={s}>{t(("crit.s." + s) as Key)}</option>)}
          </select>
        ) : <Badge>{t("crit.s.default")}</Badge>}
      </td>
      <td>
        {(c.overridden || dirty) && <input className="note" value={note} placeholder={t("crit.notePh")} onChange={(e) => setNote(e.target.value)} aria-label={t("crit.note")} />}
        {err && <div className="small" style={{ color: "var(--bad)" }}>{err}</div>}
      </td>
      <td style={{ whiteSpace: "nowrap", textAlign: "right" }}>
        {dirty && <button className="primary" onClick={() => send("PUT")}>{t("crit.save")}</button>}{" "}
        {c.overridden && <button onClick={() => send("DELETE")} title={t("crit.reset")} aria-label={t("crit.reset")}>↺</button>}
      </td>
    </tr>
  );
}
