import { useState } from "react";
import { Badge, DeliverableItem, Key, PackagesView, State, api, useApi, useFmt, useI18n } from "@epc/ui";

export default function Deliverables({ base }: { base: string }) {
  const { t } = useI18n();
  const fmt = useFmt();
  const { data, loading, error } = useApi<DeliverableItem[]>(base + "/deliverables");
  const pkgs = useApi<PackagesView>(base + "/deliverables/packages");
  const revLabel = (r: string) => r.replace(/Rev(\d+)/, "Rev $1");
  const [status, setStatus] = useState("");
  const order: Record<string, number> = { in_review: 0, in_progress: 1, planned: 2, delivered: 3 };
  const rows = (data ?? []).filter((x) => !status || x.status === status).sort((a, b) => order[a.status] - order[b.status] || (a.due ?? "").localeCompare(b.due ?? ""));
  const tone = (s: string) => (s === "delivered" ? "ok" : s === "in_review" ? "accent" : s === "in_progress" ? "warn" : undefined);
  return (
    <>
      <State loading={loading} error={error} empty={!!data && data.length === 0} />
      {data && data.length > 0 && (
        <>
          <div className="filters">
            {["", "delivered", "in_review", "in_progress", "planned"].map((s) => (
              <button key={s} className={"chipbtn" + (status === s ? " on" : "")} onClick={() => setStatus(s)}>
                {s ? t(("u.ds." + s) as Key) : t("u.f.all")} <span className="muted">{s ? data.filter((x) => x.status === s).length : data.length}</span>
              </button>
            ))}
          </div>
          {pkgs.data && pkgs.data.count > 0 && (
            <div className="card" style={{ marginBottom: 12 }}>
              <div className="row" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                <div>
                  <b>{t("u.d.package")} {revLabel(pkgs.data.rev)}</b> <span className="muted">· {pkgs.data.count} {t("u.d.packageFiles")}</span>
                  <div className="muted small">{t("u.d.packageHelp")}</div>
                </div>
                <a className="btn primary" href={`/api${base}/deliverables/package`}>{t("u.d.package")} (.zip)</a>
              </div>
              {pkgs.data.groups.length > 1 && (
                <div className="row" style={{ marginTop: 8, flexWrap: "wrap" }}>
                  <span className="muted small">{t("u.d.packageOne")}:</span>
                  {pkgs.data.groups.map((g) => (
                    <a key={g.id} className="btn" href={`/api${base}/deliverables/package?group=${encodeURIComponent(g.id)}`}>{g.emission} · {g.transmittal} · {revLabel(g.rev)} ({g.count})</a>
                  ))}
                </div>
              )}
            </div>
          )}
          <div className="card scroll">
            <table>
              <thead><tr><th>{t("u.d.name")}</th><th>{t("u.d.discipline")}</th><th>{t("u.d.format")}</th><th>{t("u.d.rev")}</th><th>{t("u.d.status")}</th><th>{t("u.d.due")}</th><th /></tr></thead>
              <tbody>
                {rows.map((x) => (
                  <tr key={x.id}>
                    <td><b>{x.name}</b><div className="muted mono small">{x.code}</div></td>
                    <td>{t(("projects.disc." + x.discipline) as Key)}</td>
                    <td><Badge>.{x.format}</Badge></td>
                    <td>{x.revision}</td>
                    <td><Badge tone={tone(x.status)}>{t(("u.ds." + x.status) as Key)}</Badge></td>
                    <td className={x.overdue ? "err" : ""}>{x.status === "delivered" ? `${t("u.d.deliveredOn")} ${fmt.date(x.delivered_on)}` : `${t("u.d.dueOn")} ${fmt.date(x.due)}`}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {x.downloadable && x.formats.length > 1 ? (
                        <span className="row" style={{ gap: 6 }}>
                          <span className="muted small">{t("u.d.downloadAs")}</span>
                          {x.formats.map((f) => <a key={f} className="btn" href={`/api${base}/deliverables/${x.id}/download?format=${f}`}>.{f}</a>)}
                        </span>
                      ) : x.downloadable ? <a className="btn" href={`/api${base}/deliverables/${x.id}/download`}>{t("u.d.download")}</a> : <span className="muted">{x.status === "delivered" ? t("u.d.na") : ""}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {data && data.length === 0 && <div className="state">{t("u.d.none")}</div>}
    </>
  );
}

/* ---------------- inputs ---------------- */
