import { useState } from "react";
import { Project, TreeNode, useApi } from "../../api";
import NewProject from "../NewProject";
import { Badge, Page, State } from "../../components";
import { useI18n } from "../../i18n";

export default function Projects() {
  const { t } = useI18n();
  const [reload, setReload] = useState(0);
  const { data, loading, error } = useApi<Project[]>("/projects?r=" + reload);
  const [sel, setSel] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<(Project & { plugins_locked?: number }) | null>(null);
  return (
    <Page title={t("projects.title")} help={t("projects.help")}>
      <div className="row" style={{ marginBottom: 14 }}>
        {!creating && <button className="primary" onClick={() => { setCreating(true); setCreated(null); }}>+ {t("projects.new")}</button>}
      </div>
      {creating && (
        <div style={{ marginBottom: 18 }}>
          <NewProject
            onCancel={() => setCreating(false)}
            onCreated={(p) => { setCreating(false); setCreated(p); setSel(p.id); setReload((n) => n + 1); }}
          />
        </div>
      )}
      {created && (
        <div className="alert ok" role="status">
          <b>{t("projects.created")}: {created.client} / {created.project_code}</b>
          <div>{t("projects.created.detail")} {created.plugins_locked} {t("projects.plugins")}.</div>
          <div className="mono">{t("projects.location")}: projects/{created.id}</div>
        </div>
      )}
      <State loading={loading} error={error} empty={!!data && data.length === 0} />
      <div className="grid cards" style={{ marginBottom: 18 }}>
        {data?.map((p) => (
          <button key={p.id} className="card" style={{ textAlign: "left", outline: sel === p.id ? "2px solid var(--accent)" : undefined }} onClick={() => setSel(p.id)}>
            <div className="row between">
              <b>{p.is_template ? t("projects.template") : p.name}</b>
              {p.is_template && <Badge>_template</Badge>}
            </div>
            <div className="muted">{p.client || "—"} · {p.project_code || "—"}</div>
            <div className="row" style={{ marginTop: 8 }}>
              <Badge>{t("projects.jurisdiction")}: {p.jurisdiction}</Badge>
              <Badge>{p.methodology}</Badge>
              <Badge tone="accent">{p.workspace_files} {t("common.files")}</Badge>
              <Badge tone={p.deliverable_files ? "ok" : undefined}>{p.deliverable_files} {t("projects.deliverables").split(" ")[0].toLowerCase()}</Badge>
            </div>
          </button>
        ))}
      </div>
      {sel && <ProjectView id={sel} />}
    </Page>
  );
}

function ProjectView({ id }: { id: string }) {
  const { t } = useI18n();
  const ws = useApi<{ tree: TreeNode[] }>(`/projects/${id}/tree?area=workspace&depth=4`);
  const dl = useApi<{ tree: TreeNode[] }>(`/projects/${id}/tree?area=deliverables&depth=4`);
  return (
    <div className="cols2">
      <div className="card tree">
        <h2>{t("projects.workspace")}</h2>
        <State loading={ws.loading} error={ws.error} />
        {ws.data && <Tree nodes={ws.data.tree} open />}
      </div>
      <div className="card tree">
        <h2>{t("projects.deliverables")}</h2>
        <State loading={dl.loading} error={dl.error} />
        {dl.data && dl.data.tree.every((n) => n.type === "dir" && !n.files) && <p className="muted">{t("projects.empty")}</p>}
        {dl.data && <Tree nodes={dl.data.tree} open />}
      </div>
    </div>
  );
}

function Tree({ nodes, open }: { nodes: TreeNode[]; open?: boolean }) {
  const { t } = useI18n();
  return (
    <>
      {nodes.map((n) =>
        n.type === "dir" ? (
          <details key={n.name} open={open && (n.files ?? 0) > 0}>
            <summary>
              {n.name} <span className="muted">({n.files})</span>
            </summary>
            {n.children && <Tree nodes={n.children} />}
          </details>
        ) : (
          <div className="file" key={n.name}>
            <span className="mono">{n.name}</span>
            <Badge tone={n.deliver ? "ok" : undefined}>{n.deliver ? t("projects.delivered") : t("projects.internal")}</Badge>
          </div>
        ),
      )}
    </>
  );
}
