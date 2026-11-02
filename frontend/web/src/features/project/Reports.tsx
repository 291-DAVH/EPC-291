import { useState } from "react";
import { Key, ReportItem, State, api, useApi, useFmt, useI18n } from "@epc/ui";
import Observations from "./Observations";
import Reporting from "./Reporting";
import type { Tab } from "./tabs";

export default function Reports({ base, go, engineer, client, code, sub, onSub, can }: { base: string; go: (t: Tab, x?: Record<string, string>) => void; engineer: boolean; client: string; code: string; sub: string; onSub: (x: string) => void; can: (subject: string, action: string) => boolean }) {
  const { t } = useI18n();
  const current = sub === "observations" ? "observations" : "reports";
  const fmt = useFmt();
  const [rev, setRev] = useState(0);
  const { data, loading, error } = useApi<ReportItem[]>(base + "/reports?r=" + rev);
  return (
    <>
    <div className="subtabs" role="tablist">
      {(["reports", "observations"] as const).map((x) => <button key={x} role="tab" aria-selected={current === x} className={current === x ? "on" : ""} onClick={() => onSub(x)}>{t(("rep.sub." + x) as Key)}</button>)}
    </div>
    {current === "observations" && <Observations base={base} can={can} />}
    {current === "reports" && <>
    {engineer && <Reporting client={client} code={code} onPublished={() => setRev((n) => n + 1)} />}
    <div className="cols2">
      <div className="card">
        <h2>{t("u.rp.title")}</h2>
        <State loading={loading} error={error} />
        {data?.length === 0 && <p className="muted">{t("u.rp.none")}</p>}
        {data?.map((r) => (
          <div key={r.id} className="item">
            <div className="row between">
              <b>{r.title}</b>
              {r.downloadable && <a className="btn" href={`/api${base}/reports/${r.id}/download`}>{t("u.d.download")}</a>}
            </div>
            <div className="muted small">{fmt.date(r.date)} · {r.type}</div>
            <p style={{ margin: "6px 0" }}>{r.summary}</p>
          </div>
        ))}
      </div>
      <div className="card">
        <h2>{t("u.rp.report")}</h2>
        <p className="muted">{t("u.rp.reportHelp")}</p>
        <button className="primary" onClick={() => go("inputs", { kind: "report" })}>{t("u.rp.report")}</button>
      </div>
    </div>
    </>}
    </>
  );
}

/* ---------------- plan (read-only view of the WBS and the schedule) ---------------- */
