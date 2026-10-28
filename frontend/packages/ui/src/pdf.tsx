import { useEffect, useState } from "react";
import { State } from "./components";
import { Key, useI18n } from "./i18n";

/** The PDF reader of the program: any screen that has a PDF to show gives the path of the file in the API and gets a viewer, a way to open it on its own and a way to download it.
 *  The file is fetched with the person's session and shown from a local copy, so it does not depend on how the server lets pages be framed. */
export function usePdfUrl(path: string | null): { url: string | null; loading: boolean; error: string } {
  const [state, setState] = useState<{ url: string | null; loading: boolean; error: string }>({ url: null, loading: !!path, error: "" });
  useEffect(() => {
    if (!path) { setState({ url: null, loading: false, error: "" }); return; }
    let url: string | null = null, gone = false;
    setState({ url: null, loading: true, error: "" });
    fetch("/api" + path, { credentials: "same-origin" })
      .then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.blob(); })
      .then((blob) => { if (gone) return; url = URL.createObjectURL(new Blob([blob], { type: "application/pdf" })); setState({ url, loading: false, error: "" }); })
      .catch((e: Error) => { if (!gone) setState({ url: null, loading: false, error: e.message }); });
    return () => { gone = true; if (url) URL.revokeObjectURL(url); };
  }, [path]);
  return state;
}

export interface PdfViewerProps {
  path: string | null;                  // where the file is in the API (without the /api prefix)
  title: string;                        // what the document is called: the title of the frame and the name of the download
  height?: string;
}

export function PdfViewer({ path, title, height = "75vh" }: PdfViewerProps) {
  const { t } = useI18n();
  const { url, loading, error } = usePdfUrl(path);
  if (!url) return <State loading={loading} error={error} />;
  return (
    <>
      <div className="row" style={{ marginBottom: 8, gap: 8 }}>
        <a className="btn" href={url} target="_blank" rel="noreferrer">{t("pdf.open" as Key)}</a>
        <a className="btn" href={url} download={title.toLowerCase().endsWith(".pdf") ? title : `${title}.pdf`}>{t("pdf.download" as Key)}</a>
      </div>
      <iframe src={`${url}#view=FitH`} title={title} style={{ width: "100%", height, border: "1px solid var(--line, #ccc)", borderRadius: 6 }} />
    </>
  );
}
