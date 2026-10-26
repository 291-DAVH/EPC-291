import { FormEvent, useState } from "react";
import { ApiError, Badge, InputItem, Key, State, api, useApi, useFmt, useI18n } from "@epc/ui";
import AnalysisPanel from "./AnalysisPanel";

export default function Inputs({ canWrite, base, rev, onSent, initialKind, engineer, client, code }: { canWrite: boolean; base: string; rev: number; onSent: () => void; initialKind: string; engineer: boolean; client: string; code: string }) {
  const { t } = useI18n();
  const fmt = useFmt();
  const [r, setR] = useState(0);
  const list = useApi<InputItem[]>(base + `/inputs?r=${rev}-${r}`);
  const [kind, setKind] = useState(initialKind);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setOk(false);
    setBusy(true);
    const fd = new FormData();
    fd.append("kind", kind);
    fd.append("title", title);
    fd.append("text", text);
    Array.from(files ?? []).forEach((f) => fd.append("files", f));
    try {
      const res = await fetch("/api" + base + "/inputs", { method: "POST", body: fd });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setErrs(new ApiError(res.status, body).fieldErrors);
        if (!Object.keys(new ApiError(res.status, body).fieldErrors).length) setErrs({ text: t("u.i.error") });
      } else {
        setErrs({}); setTitle(""); setText(""); setFiles(null); setOk(true); setR((n) => n + 1); onSent();
        (document.getElementById("input-files") as HTMLInputElement | null)?.setAttribute("value", "");
      }
    } finally {
      setBusy(false);
    }
  };
  const tone = (s: string) => (s === "structured" ? "ok" : s === "analyzing" ? "warn" : "accent");
  return (
    <>
      {engineer && <AnalysisPanel client={client} code={code} onDone={onSent} />}
    <div className="cols2">
      {canWrite && <form className="card form" onSubmit={submit} noValidate>
        <h2>{t("u.i.title")}</h2>
        <p className="muted">{t("u.i.help")}</p>
        <label className="field"><span>{t("u.i.kind")}</span>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            {["voice_of_customer", "user_story", "meeting_note", "document", "report"].map((k) => <option key={k} value={k}>{t(("u.k." + k) as Key)}</option>)}
          </select>
        </label>
        <label className="field"><span>{t("u.i.subject")}</span>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
          {errs.title && <small className="err">{errs.title}</small>}
        </label>
        <label className="field"><span>{t("u.i.text")}</span>
          <textarea rows={6} value={text} onChange={(e) => setText(e.target.value)} />
          {errs.text && <small className="err">{errs.text}</small>}
        </label>
        <label className="field"><span>{t("u.i.files")}</span>
          <input id="input-files" type="file" multiple onChange={(e) => setFiles(e.target.files)} />
          {errs.files && <small className="err">{errs.files}</small>}
        </label>
        {ok && <div className="alert ok" role="status">{t("u.i.sent")}</div>}
        <div className="row"><button className="primary" type="submit" disabled={busy}>{t("u.i.send")}</button></div>
      </form>}
      <div className="card">
        <h2>{t("u.i.list")}</h2>
        <State loading={list.loading && !list.data} error={list.error} />
        {list.data?.length === 0 && <p className="muted">{t("u.i.none")}</p>}
        <div className="scroll">
          {list.data?.map((x) => (
            <div key={x.id} className="item">
              <div className="row between">
                <b>{x.title}</b>
                <Badge tone={tone(x.status)}>{t(("u.is." + x.status) as Key)}</Badge>
              </div>
              <div className="muted small">{t(("u.k." + x.kind) as Key)} · {fmt.date(x.created)} · {x.source}</div>
              {x.text && <p style={{ margin: "6px 0" }}>{x.text}</p>}
              {x.attachments.length > 0 && <div className="muted small">{t("u.i.attachments")}: {x.attachments.map((a) => a.name).join(", ")}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
    </>
  );
}

/* ---------------- requirements ---------------- */
