import { useEffect, useMemo, useState } from "react";
import { api, errorText, JSON_HEADERS, useApi } from "@epc/ui";
import type { Drawing } from "./planEditing";
import { applyReceptacles, ReceptaclesOptions, ReceptaclesProposal, requestOf } from "./receptaclesApi";

interface Args { client: string; code: string; lang: "es" | "en"; drawing: Drawing; onChange: (d: Drawing) => void; sheet: string }

/** The socket outlets of the sheet: the choices of the panel, the proposal of the last calculation (shown over the plan until the person decides) and what applying it does to the drawing. */
export function useReceptacles({ client, code, lang, drawing, onChange, sheet }: Args) {
  const [proposal, setProposal] = useState<ReceptaclesProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [applied, setApplied] = useState<{ added: number; removed: number } | null>(null);
  const options = useApi<ReceptaclesOptions>(`/projects/${client}/${code}/receptacles/options?lang=${lang}`);
  const key = useMemo(() => JSON.stringify(requestOf(drawing, lang)), [drawing, lang]);
  useEffect(() => { setProposal(null); setApplied(null); }, [sheet, key]);                       // a proposal is only good for the rooms and parameters it was calculated with

  const calc = async (drawn = false) => {
    setBusy(true);
    try {
      setProposal(await api<ReceptaclesProposal>(`/projects/${client}/${code}/receptacles/calc`, { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(requestOf(drawing, lang, { use_drawn: drawn })) }));
      setError(""); setApplied(null);
    } catch (x) { setError(errorText(x)); }
    setBusy(false);
  };
  const apply = () => {
    if (!proposal) return;
    const out = applyReceptacles(drawing, proposal);
    onChange(out.drawing);
    setProposal(null);
    setApplied({ added: out.added, removed: out.removed });
    api(`/projects/${client}/${code}/receptacles/study/${encodeURIComponent(sheet)}`, { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(requestOf(drawing, lang)) })       // what was applied is kept as the study of the sheet (the one its report is made from)
      .catch((x) => setError(errorText(x)));
  };
  return { options: options.data ?? undefined, proposal, busy, error, applied, calc, apply };
}
