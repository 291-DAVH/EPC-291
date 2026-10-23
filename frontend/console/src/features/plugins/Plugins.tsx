import { useState } from "react";
import { Plugin, useApi } from "@epc/ui";
import { Badge, Page, State, statusTone } from "@epc/ui";
import { useI18n } from "@epc/ui";

export default function Plugins() {
  const { t } = useI18n();
  const { data, loading, error } = useApi<Plugin[]>("/plugins");
  const [sel, setSel] = useState<string | null>(null);
  const detail = useApi<Plugin>(sel ? `/plugins/${sel}` : null);
  return (
    <Page title={t("plugins.title")} help={t("plugins.help")}>
      <State loading={loading} error={error} />
      <div className="split">
        <div className="grid cards" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
          {data?.map((p) => (
            <button key={p.id} className="card" style={{ textAlign: "left", outline: sel === p.id ? "2px solid var(--accent)" : undefined }} onClick={() => setSel(p.id)}>
              <div className="row between">
                <b>{p.id}</b>
                <Badge tone={statusTone(p.status)}>{p.status}</Badge>
              </div>
              <div className="muted mono">v{p.version} · {p.kind}</div>
              <p style={{ margin: "8px 0", display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{p.description}</p>
              <div className="row">
                {p.skills.length > 0 && <Badge>{p.skills.length} skills</Badge>}
                {Object.keys(p.requires).length > 0 && <Badge tone="accent">→ {Object.keys(p.requires).length}</Badge>}
                {p.required_by.length > 0 && <Badge>← {p.required_by.length}</Badge>}
              </div>
            </button>
          ))}
        </div>
        <div className="card">
          {!sel && <p className="muted">{t("plugins.detail")}</p>}
          {sel && <State loading={detail.loading} error={detail.error} />}
          {detail.data && sel && (
            <>
              <div className="row between">
                <h2 style={{ margin: 0 }}>{detail.data.id}</h2>
                <button onClick={() => setSel(null)}>{t("common.close")}</button>
              </div>
              <p>{detail.data.description}</p>
              <dl className="kv">
                <dt>{t("common.version")}</dt><dd className="mono">{detail.data.version}</dd>
                <dt>{t("common.kind")}</dt><dd>{detail.data.kind}</dd>
                <dt>{t("common.requires")}</dt>
                <dd>{Object.entries(detail.data.requires).map(([k, v]) => <Badge key={k} tone="accent">{k} {v}</Badge>)}{Object.keys(detail.data.requires).length === 0 && "—"}</dd>
                <dt>{t("common.requiredBy")}</dt>
                <dd>{detail.data.required_by.map((k) => <Badge key={k}>{k}</Badge>)}{detail.data.required_by.length === 0 && "—"}</dd>
                <dt>{t("common.skills")}</dt>
                <dd>{detail.data.skills.map((s) => <Badge key={s.id} tone={s.role === "owner" ? "ok" : undefined}>{s.id}</Badge>)}{detail.data.skills.length === 0 && "—"}</dd>
                <dt>{t("common.outputs")}</dt>
                <dd>{detail.data.outputs.map((o) => <Badge key={o.format} tone={o.channel.includes("deliverable") ? "ok" : undefined}>.{o.format} · {o.channel}</Badge>)}{detail.data.outputs.length === 0 && "—"}</dd>
                <dt>Python</dt><dd className="mono">{detail.data.python.join(", ") || "stdlib"}</dd>
              </dl>
              {detail.data.readme && <pre>{detail.data.readme}</pre>}
            </>
          )}
        </div>
      </div>
    </Page>
  );
}
