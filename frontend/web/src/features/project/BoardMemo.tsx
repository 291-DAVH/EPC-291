import { useState } from "react";
import { Badge, BoardMemoView, Key, Markdown, State, useApi, useI18n } from "@epc/ui";

/** Calculation memo and summary of a board, plus the trip curves of its protections. The documents are the ones the engine writes (single source). */
export default function BoardMemo({ client, code, v }: { client: string; code: string; v: BoardMemoView }) {
  const { t } = useI18n();
  const [tab, setTab] = useState<"mc" | "sp" | "curves">("sp");
  if (!v.available || !v.memo) return <div className="state">{t("memo.none")}</div>;
  const r = v.memo.resumen;
  const file = (suffix: string) => v.files.find((f) => f.endsWith(suffix));
  return (
    <>
      <div className="row small" style={{ flexWrap: "wrap", margin: "0 0 8px" }}>
        <Badge tone={r.global ? "ok" : "bad"}>{r.global ? t("memo.ok") : t("memo.notOk")}</Badge>
        <Badge>{r.cumplen}/{r.circuits} {t("calc.compliant")}</Badge>
        {r.transiciones > 0 && <Badge tone="warn">{r.transiciones} {t("memo.transition")}</Badge>}
        {!v.memo.validated && <Badge tone="warn">{t("memo.unvalidated")}</Badge>}
        {v.stale && <Badge tone="bad">{t("memo.stale")}</Badge>}
      </div>
      <div className="subtabs" role="tablist">
        {(["sp", "mc", "curves"] as const).map((x) => (
          <button key={x} role="tab" aria-selected={tab === x} className={tab === x ? "on" : ""} onClick={() => setTab(x)}>{t(("memo.tab." + x) as Key)}</button>
        ))}
      </div>
      {tab === "sp" && <DocView client={client} code={code} path={file("_SP.md")} />}
      {tab === "mc" && <DocView client={client} code={code} path={file("_MC.md")} />}
      {tab === "curves" && <Curves memo={v.memo} />}
    </>
  );
}

function DocView({ client, code, path }: { client: string; code: string; path?: string }) {
  const r = useApi<{ text?: string }>(path ? `/projects/${client}/${code}/engineering/text?path=${encodeURIComponent("electrical/PQ-01/" + path)}` : null);
  if (!path) return null;
  if (!r.data) return <State loading={r.loading} error={r.error} />;
  return <div className="eng-view" style={{ background: "var(--panel)", padding: 12 }}><Markdown text={r.data.text ?? ""} /></div>;
}

const COLORS = ["#1f6fb2", "#c2410c", "#15803d", "#9333ea", "#b45309", "#0e7490"];

function Curves({ memo }: { memo: NonNullable<BoardMemoView["memo"]> }) {
  const { t } = useI18n();
  const tags = Object.keys(memo.curvas);
  const first = memo.selectividad[0];
  const [sel, setSel] = useState<string[]>(first ? [first.aguas_arriba, first.aguas_abajo].filter((x) => tags.includes(x)) : tags.slice(0, 2));
  const icc = (memo.board.icc_ka ?? 10) * 1000;
  const W = 640, H = 340, L = 52, B = 34, T = 10, Rr = 12;
  const xmin = 1, xmax = Math.max(icc * 1.5, 1000), ymin = 0.01, ymax = 10000;
  const X = (a: number) => L + ((Math.log10(Math.max(a, xmin)) - Math.log10(xmin)) / (Math.log10(xmax) - Math.log10(xmin))) * (W - L - Rr);
  const Y = (s: number) => T + (1 - (Math.log10(Math.max(s, ymin)) - Math.log10(ymin)) / (Math.log10(ymax) - Math.log10(ymin))) * (H - T - B);
  const path = (pts: number[][]) => pts.map(([a, s], i) => `${i ? "L" : "M"}${X(a).toFixed(1)},${Y(s).toFixed(1)}`).join(" ");
  const xt = [1, 10, 100, 1000, 10000, 100000].filter((v) => v <= xmax);
  const yt = [0.01, 0.1, 1, 10, 100, 1000, 10000];
  const toggle = (tag: string) => setSel(sel.includes(tag) ? sel.filter((x) => x !== tag) : [...sel, tag]);
  return (
    <>
      <p className="muted small" style={{ margin: "0 0 6px" }}>{t("memo.curvesHelp")}</p>
      <div className="row" style={{ marginBottom: 6 }}>
        <select value="" onChange={(e) => e.target.value && toggle(e.target.value)} aria-label={t("memo.addCurve")}>
          <option value="">{t("memo.addCurve")}</option>
          {tags.filter((x) => !sel.includes(x)).map((tag) => <option key={tag} value={tag}>{tag} ({memo.curvas[tag].curva} {memo.curvas[tag].In} A)</option>)}
        </select>
        {sel.map((tag, i) => <button key={tag} className="chip" style={{ borderColor: COLORS[i % COLORS.length], color: COLORS[i % COLORS.length] }} onClick={() => toggle(tag)} title={t("memo.removeCurve")}>{tag} ({memo.curvas[tag]?.curva} {memo.curvas[tag]?.In} A) ×</button>)}
      </div>
      <div style={{ overflowX: "auto" }}>
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", maxWidth: 760, background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 6 }} role="img" aria-label={t("memo.tab.curves")}>
          {xt.map((v) => <g key={"x" + v}><line x1={X(v)} x2={X(v)} y1={T} y2={H - B} stroke="var(--line)" /><text x={X(v)} y={H - B + 14} fontSize="10" textAnchor="middle" fill="var(--muted)">{v >= 1000 ? `${v / 1000}k` : v}</text></g>)}
          {yt.map((v) => <g key={"y" + v}><line x1={L} x2={W - Rr} y1={Y(v)} y2={Y(v)} stroke="var(--line)" /><text x={L - 4} y={Y(v) + 3} fontSize="10" textAnchor="end" fill="var(--muted)">{v}</text></g>)}
          <text x={(L + W - Rr) / 2} y={H - 4} fontSize="11" textAnchor="middle" fill="var(--muted)">{t("memo.axisI")}</text>
          <text x={12} y={(T + H - B) / 2} fontSize="11" textAnchor="middle" fill="var(--muted)" transform={`rotate(-90 12 ${(T + H - B) / 2})`}>{t("memo.axisT")}</text>
          <line x1={X(icc)} x2={X(icc)} y1={T} y2={H - B} stroke="#b00020" strokeDasharray="4 3" />
          <text x={X(icc) - 3} y={T + 11} fontSize="10" textAnchor="end" fill="#b00020">Icc {icc / 1000} kA</text>
          {sel.map((tag, i) => {
            const c = memo.curvas[tag];
            if (!c) return null;
            const col = COLORS[i % COLORS.length];
            const band = `${path(c.min)} ${[...c.max].reverse().map(([a, s]) => `L${X(a).toFixed(1)},${Y(s).toFixed(1)}`).join(" ")} Z`;
            return <g key={tag}><path d={band} fill={col} fillOpacity="0.18" stroke="none" /><path d={path(c.min)} fill="none" stroke={col} strokeWidth="1.5" /><path d={path(c.max)} fill="none" stroke={col} strokeWidth="1.5" />
              <text x={X(c.max[3][0]) + 3} y={Y(0.02) - 2 - i * 11} fontSize="10" fill={col}>{tag}</text></g>;
          })}
        </svg>
      </div>
      {memo.selectividad.length > 0 && (
        <div style={{ overflowX: "auto", marginTop: 8 }}>
          <table className="sldtable">
            <thead><tr><th>{t("memo.up")}</th><th>{t("memo.down")}</th><th>{t("memo.ratio")}</th><th>{t("memo.isA")}</th><th>{t("memo.result")}</th></tr></thead>
            <tbody>{memo.selectividad.map((s, i) => (
              <tr key={i} onClick={() => setSel([s.aguas_arriba, s.aguas_abajo].filter((x) => tags.includes(x)))} style={{ cursor: "pointer" }} title={s.nota}>
                <td className="mono">{s.aguas_arriba}</td><td className="mono">{s.aguas_abajo}</td><td className="mono">{s.relacion_termica ?? ""}</td><td className="mono">{s.is_a}</td>
                <td><Badge tone={s.resultado === "total" ? "ok" : s.resultado === "parcial" ? "warn" : "bad"}>{t(("memo.sel." + s.resultado) as Key)}</Badge></td>
              </tr>))}</tbody>
          </table>
        </div>
      )}
    </>
  );
}
