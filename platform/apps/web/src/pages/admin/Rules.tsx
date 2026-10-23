import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { RuleView, StandardInfo, useApi } from "../../api";
import { Badge, Page, State, statusTone, typeTone } from "../../components";
import { Key, useI18n } from "../../i18n";

const INSTALLATIONS = ["dwellings", "offices", "commercial_premises", "industrial", "garages", "ev_charging", "educational", "outdoor_lighting", "non_flammable_storage"];

export default function Rules() {
  const { t, lang } = useI18n();
  const [sp, setSp] = useSearchParams();
  const standard = sp.get("standard") ?? "";
  const [q, setQ] = useState("");
  const [dq, setDq] = useState("");
  const [topic, setTopic] = useState("");
  const [type, setType] = useState("");
  const [inst, setInst] = useState("");
  const [onlyChecks, setOnlyChecks] = useState(false);
  const [sel, setSel] = useState<string | null>(null);

  useEffect(() => {
    const h = setTimeout(() => setDq(q), 250);
    return () => clearTimeout(h);
  }, [q]);

  const stds = useApi<StandardInfo[]>("/rules/standards");
  const topics = useApi<string[]>("/rules/topics");
  const path = useMemo(() => {
    const p = new URLSearchParams();
    if (standard) p.set("standard", standard);
    if (dq) p.set("q", dq);
    if (topic) p.set("topic", topic);
    if (type) p.set("type", type);
    if (inst) p.set("installation", inst);
    if (onlyChecks) p.set("only_checks", "true");
    return "/rules?" + p.toString();
  }, [standard, dq, topic, type, inst, onlyChecks]);
  const list = useApi<{ total: number; items: RuleView[] }>(path);
  const detail = useApi<RuleView>(sel ? `/rules/${encodeURIComponent(sel)}` : null);
  const summary = (r: RuleView) => r.summary[lang] ?? r.summary.es ?? Object.values(r.summary)[0] ?? "";

  return (
    <Page title={t("rules.title")} help={t("rules.help")}>
      <div className="filters">
        <select value={standard} onChange={(e) => (e.target.value ? setSp({ standard: e.target.value }) : setSp({}))} aria-label={t("common.standard")}>
          <option value="">{t("common.standard")}: {t("common.all")}</option>
          {stds.data?.map((s) => <option key={s.id} value={s.id}>{s.id} ({s.rules})</option>)}
        </select>
        <select value={topic} onChange={(e) => setTopic(e.target.value)} aria-label={t("common.topic")}>
          <option value="">{t("common.topic")}: {t("common.all")}</option>
          {topics.data?.map((x) => <option key={x}>{x}</option>)}
        </select>
        <select value={type} onChange={(e) => setType(e.target.value)} aria-label={t("common.type")}>
          <option value="">{t("common.type")}: {t("common.all")}</option>
          {["mandatory", "recommended", "prohibited"].map((x) => <option key={x} value={x}>{t(("type." + x) as Key)}</option>)}
        </select>
        <select value={inst} onChange={(e) => setInst(e.target.value)} aria-label={t("rules.installation")}>
          <option value="">{t("rules.installation")}: {t("common.all")}</option>
          {INSTALLATIONS.map((x) => <option key={x}>{x}</option>)}
        </select>
        <input type="search" placeholder={t("common.search") + "…"} value={q} onChange={(e) => setQ(e.target.value)} />
        <label className="row"><input type="checkbox" checked={onlyChecks} onChange={(e) => setOnlyChecks(e.target.checked)} /> {t("rules.onlyChecks")}</label>
        {list.data && <span className="muted">{list.data.total} {t("rules.results")}</span>}
      </div>
      <State loading={list.loading && !list.data} error={list.error} empty={!!list.data && list.data.items.length === 0} />
      <div className="split">
        <div className="card scroll">
          <table>
            <thead>
              <tr><th>{t("common.clause")}</th><th>{t("common.summary")}</th><th>{t("common.type")}</th></tr>
            </thead>
            <tbody>
              {list.data?.items.map((r) => (
                <tr key={r.id} className={"click" + (sel === r.id ? " sel" : "")} onClick={() => setSel(r.id)}>
                  <td className="mono" style={{ whiteSpace: "nowrap" }}>{r.clause}<div className="muted">{r.page ? `${t("common.page")} ${r.page}` : ""}</div></td>
                  <td>
                    {summary(r)}
                    <div className="row" style={{ marginTop: 4 }}>
                      <Badge>{r.topic}</Badge>
                      {r.has_check && <Badge tone={r.derived ? "warn" : "ok"}>{r.derived ? t("rules.derivedWarn") : t("common.check")}</Badge>}
                      {r.confidence === "low" && <Badge tone="warn">{t("rules.lowConf")}</Badge>}
                    </div>
                  </td>
                  <td><Badge tone={typeTone(r.type)}>{t(("type." + r.type) as Key)}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          {!sel && <p className="muted">{t("rules.select")}</p>}
          {sel && <State loading={detail.loading} error={detail.error} />}
          {detail.data && sel && (
            <>
              <div className="row between">
                <h2 style={{ margin: 0 }} className="mono">{detail.data.id}</h2>
                <button onClick={() => setSel(null)}>{t("common.close")}</button>
              </div>
              <p>{summary(detail.data)}</p>
              <dl className="kv">
                <dt>{t("common.standard")}</dt><dd>{detail.data.standard} <Badge tone={statusTone(detail.data.status)}>{detail.data.status}</Badge></dd>
                <dt>{t("common.clause")}</dt><dd className="mono">{detail.data.clause}{detail.data.part ? ` (${detail.data.part})` : ""}</dd>
                <dt>{t("common.page")}</dt><dd>{detail.data.page ?? "—"}</dd>
                <dt>{t("common.type")}</dt><dd><Badge tone={typeTone(detail.data.type)}>{t(("type." + detail.data.type) as Key)}</Badge></dd>
                <dt>{t("rules.installation")}</dt><dd>{detail.data.installation_types.map((x) => <Badge key={x}>{x}</Badge>)}</dd>
                <dt>{t("common.topic")}</dt><dd>{detail.data.topic}</dd>
              </dl>
              {detail.data.check && (
                <>
                  <h2>{t("common.check")} {detail.data.check.derived && <Badge tone="warn">{t("rules.derivedWarn")}</Badge>}</h2>
                  <pre>{`${detail.data.check.field} ${detail.data.check.op} ${JSON.stringify(detail.data.check.value)}`}</pre>
                </>
              )}
              <h2>{t("common.params")}</h2>
              <pre>{JSON.stringify(detail.data.params ?? {}, null, 2)}</pre>
            </>
          )}
        </div>
      </div>
    </Page>
  );
}
