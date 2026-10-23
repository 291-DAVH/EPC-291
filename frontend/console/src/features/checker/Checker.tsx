import { useState } from "react";
import { Finding, api } from "@epc/ui";
import { Badge, Page } from "@epc/ui";
import { useI18n } from "@epc/ui";

interface Row { field: string; value: string }
const EXAMPLE: Row[] = [
  { field: "reserva_pct", value: "10" },
  { field: "capas", value: "1" },
  { field: "bocas", value: "12" },
  { field: "profundidad_m", value: "0.5" },
];

function parse(v: string): unknown {
  const s = v.trim();
  if (s === "true") return true;
  if (s === "false") return false;
  if (s !== "" && !isNaN(Number(s.replace(",", ".")))) return Number(s.replace(",", "."));
  return s;
}

export default function Checker() {
  const { t } = useI18n();
  const [rows, setRows] = useState<Row[]>(EXAMPLE);
  const [inst, setInst] = useState("dwellings");
  const [res, setRes] = useState<{ summary: Record<string, number>; findings: Finding[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    setErr(null);
    try {
      const context: Record<string, unknown> = {};
      rows.filter((r) => r.field.trim()).forEach((r) => (context[r.field.trim()] = parse(r.value)));
      setRes(await api("/rules/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ context, installation_type: inst || null }) }));
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };
  const set = (i: number, patch: Partial<Row>) => setRows(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const shown = res?.findings.filter((f) => f.passed !== null || true) ?? [];
  const order = (f: Finding) => (f.passed === false ? 0 : f.passed === null ? 2 : 1);

  return (
    <Page title={t("checker.title")} help={t("checker.help")}>
      <div className="cols2">
        <div className="card">
          <div className="filters">
            <select value={inst} onChange={(e) => setInst(e.target.value)} aria-label={t("rules.installation")}>
              {["dwellings", "offices", "commercial_premises", "industrial", "garages", "ev_charging"].map((x) => <option key={x}>{x}</option>)}
            </select>
            <button onClick={() => setRows(EXAMPLE)}>{t("checker.example")}</button>
          </div>
          {rows.map((r, i) => (
            <div className="row" key={i} style={{ marginBottom: 6 }}>
              <input aria-label={t("checker.field")} placeholder={t("checker.field")} value={r.field} onChange={(e) => set(i, { field: e.target.value })} className="mono" />
              <input aria-label={t("checker.value")} placeholder={t("checker.value")} value={r.value} onChange={(e) => set(i, { value: e.target.value })} className="mono" />
              <button onClick={() => setRows(rows.filter((_, j) => j !== i))} aria-label="remove">×</button>
            </div>
          ))}
          <div className="row" style={{ marginTop: 10 }}>
            <button onClick={() => setRows([...rows, { field: "", value: "" }])}>+ {t("checker.addField")}</button>
            <button className="primary" onClick={run} disabled={busy}>{t("checker.run")}</button>
          </div>
          {err && <p className="err">{err}</p>}
        </div>
        <div className="card">
          {!res && <p className="muted">—</p>}
          {res && (
            <>
              <div className="row" style={{ marginBottom: 8 }}>
                <Badge tone="ok">{t("checker.pass")}: {res.summary.passed}</Badge>
                <Badge tone="bad">{t("checker.fail")}: {res.summary.failed}</Badge>
                <Badge>{t("checker.skip")}: {res.summary.not_evaluated}</Badge>
              </div>
              {shown.some((f) => f.source_status !== "verified") && <div className="alert">{t("checker.draftNote")}</div>}
              <div className="scroll">
                {[...shown].sort((a, b) => order(a) - order(b)).map((f) => (
                  <div className="finding" key={f.rule_id}>
                    <div>
                      <Badge tone={f.passed === true ? "ok" : f.passed === false ? "bad" : undefined}>
                        {f.passed === true ? t("checker.pass") : f.passed === false ? t("checker.fail") : t("checker.skip")}
                      </Badge>
                    </div>
                    <div>
                      <div className="mono">{f.rule_id} · cl. {f.clause}</div>
                      <div className="muted">{f.message}</div>
                      {f.passed === false && <div className="err mono">{f.field}: {t("checker.expected")} {JSON.stringify(f.expected)} · {t("checker.actual")} {JSON.stringify(f.actual)}</div>}
                      {f.passed === null && <div className="muted mono">{f.reason}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </Page>
  );
}
