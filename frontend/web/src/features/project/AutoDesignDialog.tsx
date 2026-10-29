import { Key, useI18n } from "@epc/ui";
import { attention, sizeLabel, Sizing } from "./autoDesign";
import { Modal } from "./BoardPlenumDialogs";
import type { AutoStage } from "./useAutoDesign";

interface Props { stage: AutoStage; onRuns: () => void; onWiring: () => void; onApprove: () => void; onClose: () => void }

const num = (v: number | null | undefined, digits = 1): string => (v === null || v === undefined ? "–" : String(Math.round(v * 10 ** digits) / 10 ** digits));

/** A card at the bottom of the plan (the proposal stays visible behind it) for the steps that ask for an acceptance. */
function Step({ title, help, warnings = [], accept, acceptLabel, onClose, closeLabel }: { title: string; help: string; warnings?: string[]; accept: () => void; acceptLabel: string; onClose: () => void; closeLabel: string }) {
  return (
    <div role="dialog" aria-label={title} className="card" style={{ position: "fixed", left: "50%", bottom: 18, transform: "translateX(-50%)", width: "min(560px, 92vw)", zIndex: 40, padding: 14 }}>
      <b>{title}</b>
      <p className="muted small" style={{ margin: "6px 0 10px" }}>{help}</p>
      {warnings.map((w) => <div key={w} className="alert warn small" role="alert" style={{ margin: "0 0 8px" }}>{w}</div>)}
      <div className="row" style={{ gap: 8, justifyContent: "flex-end" }}>
        <button onClick={onClose}>{closeLabel}</button>
        <button className="primary" onClick={accept}>{acceptLabel}</button>
      </div>
    </div>
  );
}

function SizingDetail({ sizing }: { sizing: Sizing }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const look = attention(sizing);
  const cell = { padding: "3px 8px", textAlign: "left" as const };
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <p className="muted small" style={{ margin: 0 }}>{tl("auto.sizing.help")}</p>
      {(look.circuits.length > 0 || look.containers.length > 0) && (
        <p className="small" role="alert" style={{ margin: 0, color: "var(--bad, #b3261e)" }}>
          {look.circuits.length > 0 && <>{tl("auto.sizing.circuitsLook")}: {look.circuits.join(", ")}. </>}
          {look.containers.length > 0 && <>{tl("auto.sizing.boxesLook")}: {look.containers.join(", ")}.</>}
        </p>
      )}
      <table className="small" style={{ borderCollapse: "collapse", width: "100%" }}>
        <caption style={{ textAlign: "left", fontWeight: 600 }}>{tl("auto.sizing.circuits")}</caption>
        <thead><tr>{["circuit", "section", "in", "length", "du", "plenums"].map((k) => <th key={k} style={cell}>{tl(`auto.col.${k}`)}</th>)}</tr></thead>
        <tbody>{sizing.circuits.map((c) => (
          <tr key={c.tag}><td style={cell}><b>{c.tag}</b></td><td style={cell}>{num(c.section_mm2)} mm²</td><td style={cell}>{num(c.in_a, 0)} A</td><td style={cell}>{num(c.length_m)} m</td>
              <td style={cell}>{num(c.du_pct, 2)} %</td><td style={cell}>{c.plenums.length ? `${c.plenums.join(", ")} (+${num(c.rise_m)} m)` : "–"}</td></tr>
        ))}</tbody>
      </table>
      <table className="small" style={{ borderCollapse: "collapse", width: "100%" }}>
        <caption style={{ textAlign: "left", fontWeight: 600 }}>{tl("auto.sizing.boxes")}</caption>
        <thead><tr>{["stretch", "kind", "circuits", "cables", "size", "fill"].map((k) => <th key={k} style={cell}>{tl(`auto.col.${k}`)}</th>)}</tr></thead>
        <tbody>{sizing.containers.map((c) => (
          <tr key={c.line || c.tag}><td style={cell}><b>{c.tag}</b></td><td style={cell}>{c.kind}</td><td style={cell}>{c.circuits.join(", ")}</td><td style={cell}>{c.cables}</td>
              <td style={cell}><b>{sizeLabel(c.size)}</b> mm</td><td style={{ ...cell, color: c.fits ? undefined : "var(--bad, #b3261e)" }}>{num(c.used_pct)} % / {num(c.limit_pct, 0)} %</td></tr>
        ))}</tbody>
      </table>
      {sizing.warnings.length > 0 && <ul className="muted small" style={{ margin: 0 }}>{sizing.warnings.map((w) => <li key={w}>{w}</li>)}</ul>}
    </div>
  );
}

/** The guided steps after the luminaires are accepted: route of the conduits, circuits, and the detail of the sizing to approve. */
export default function AutoDesignDialog({ stage, onRuns, onWiring, onApprove, onClose }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  if (!stage) return null;
  if (stage.step === "busy") return <div role="status" className="card" style={{ position: "fixed", left: "50%", bottom: 18, transform: "translateX(-50%)", padding: 12, zIndex: 40 }}>{tl(`auto.busy.${stage.what}`)}</div>;
  if (stage.step === "runs") {
    const s = stage.proposal.stats as { trunks?: number; stubs?: number; trunk_length?: number; stub_length?: number };
    const closed = stage.proposal.closed ? ` ${tl("auto.runs.closed").replace("{n}", String(stage.proposal.closed))}` : "";
    const help = tl("auto.runs.help").replace("{trunks}", String(s.trunks ?? 0)).replace("{stubs}", String(s.stubs ?? 0)).replace("{m}", num((s.trunk_length ?? 0) + (s.stub_length ?? 0))) + closed;
    return <Step title={tl("auto.runs.title")} help={help} warnings={stage.proposal.warnings} accept={onRuns} acceptLabel={tl("auto.runs.accept")} onClose={onClose} closeLabel={tl("auto.stop")} />;
  }
  if (stage.step === "wiring") {
    const help = tl("auto.wiring.help").replace("{n}", String(stage.proposal.circuits.length));
    return <Step title={tl("auto.wiring.title")} help={help + (stage.proposal.warnings.length ? ` ${stage.proposal.warnings.join(" ")}` : "")} accept={onWiring} acceptLabel={tl("auto.wiring.accept")} onClose={onClose} closeLabel={tl("auto.stop")} />;
  }
  if (stage.step === "sizing") {
    return (
      <Modal title={tl("auto.sizing.title")} onClose={onClose} wide>
        <SizingDetail sizing={stage.sizing} />
        <div className="row" style={{ gap: 8, justifyContent: "flex-end", marginTop: 14, position: "sticky", bottom: -18, padding: "10px 0 0", background: "inherit" }}>
          <button onClick={onClose}>{tl("auto.cancel")}</button>
          <button className="primary" onClick={onApprove}>{tl("auto.sizing.approve")}</button>
        </div>
      </Modal>
    );
  }
  const text = stage.step === "done" ? tl("auto.done") : stage.why === "noBoard" ? tl("auto.noBoard") : `${tl("auto.stopped")} ${stage.why}`;
  return (
    <Modal title={tl("auto.title")} onClose={onClose}>
      <p style={{ marginTop: 0 }}>{text}</p>
      <div className="row" style={{ justifyContent: "flex-end" }}><button className="primary" onClick={onClose}>{tl("auto.close")}</button></div>
    </Modal>
  );
}
