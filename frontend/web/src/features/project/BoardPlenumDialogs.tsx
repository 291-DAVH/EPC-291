import { FormEvent, ReactNode, useState } from "react";
import { Key, useI18n } from "@epc/ui";
import { levelChoices, reachOf } from "./plenumFlow";

/** The two questions asked before the electrical drawing begins and before a level is added: where the board is, and the plenum (vertical shaft) that goes with it. */
export function Modal({ title, children, onClose, wide }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  return (
    <div role="dialog" aria-modal="true" aria-label={title} onKeyDown={(e) => e.key === "Escape" && onClose()}
         style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.45)", display: "grid", placeItems: "center", zIndex: 50 }}>
      <div className="card" style={{ width: wide ? "min(900px, 94vw)" : "min(520px, 92vw)", maxHeight: "90vh", overflow: "auto", padding: 18 }}>
        <h3 style={{ marginTop: 0 }}>{title}</h3>
        {children}
      </div>
    </div>
  );
}

export interface BoardAnswer { name: string; location: string; level: string }

/** Adding the first electrical sheet: the name of the board, where it is and on which level (not always the ground level: a board in the basement would be drawn on the wrong plan). */
export function ElectricalSetupDialog({ levels, onSubmit, onCancel, busy }: { levels: string[]; onSubmit: (a: BoardAnswer) => void; onCancel: () => void; busy: boolean }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const choices = levelChoices(levels);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [level, setLevel] = useState(choices.includes("L0") ? "L0" : choices[0]);
  const ok = name.trim().length > 0 && name.trim().length <= 60;
  const submit = (e: FormEvent) => { e.preventDefault(); if (ok && !busy) onSubmit({ name: name.trim(), location: location.trim(), level }); };
  const missing = choices.filter((c) => !levels.includes(c));
  return (
    <Modal title={tl("setup.title")} onClose={onCancel}>
      <form onSubmit={submit} className="fgrid" style={{ gap: 10 }}>
        <p className="muted small" style={{ gridColumn: "1 / -1", margin: 0 }}>{tl("setup.help")}</p>
        <label className="field" style={{ gridColumn: "1 / -1" }}><span>{tl("setup.name")}</span><input autoFocus maxLength={60} value={name} onChange={(e) => setName(e.target.value)} placeholder="TGBT" /></label>
        <label className="field" style={{ gridColumn: "1 / -1" }}><span>{tl("setup.location")}</span><input maxLength={120} value={location} onChange={(e) => setLocation(e.target.value)} placeholder={tl("setup.locationHint")} /></label>
        <label className="field"><span>{tl("setup.level")}</span>
          <select value={level} onChange={(e) => setLevel(e.target.value)}>{choices.map((c) => <option key={c} value={c}>{c}{levels.includes(c) ? "" : ` (${tl("setup.willMake")})`}</option>)}</select></label>
        {missing.includes(level) && <p className="muted small" style={{ gridColumn: "1 / -1", margin: 0 }}>{tl("setup.levelNote")}</p>}
        <div className="row" style={{ gridColumn: "1 / -1", gap: 8, justifyContent: "flex-end" }}>
          <button type="button" onClick={onCancel}>{tl("projects.cancel")}</button>
          <button type="submit" className="primary" disabled={!ok || busy}>{busy ? tl("design.working") : tl("setup.create")}</button>
        </div>
      </form>
    </Modal>
  );
}

export interface PlenumAnswer { code: string; x_m: number; y_m: number; altura_m: number; up: number | null; down: number | null }

/** The plenum of a level: its code, where it is and the height it adds, and how far it goes: all the levels, or some above and some below. Mandatory for the electrical one when a level is added. */
export function PlenumDialog({ title, help, level, nextLevel, defaults, onSubmit, onCancel, busy }: {
  title: string; help: string; level: string; nextLevel?: string; defaults: { x_m: number; y_m: number }; onSubmit: (a: PlenumAnswer) => void; onCancel: () => void; busy: boolean;
}) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const [code, setCode] = useState("PL-1");
  const [x, setX] = useState(String(defaults.x_m));
  const [y, setY] = useState(String(defaults.y_m));
  const [height, setHeight] = useState("3");
  const [all, setAll] = useState(true);
  const [up, setUp] = useState("1");
  const [down, setDown] = useState("0");
  const num = (s: string) => Number(s.replace(",", "."));
  const reach = reachOf(all, up, down);
  const ok = /^[A-Za-z0-9][A-Za-z0-9_-]{0,19}$/.test(code) && Number.isFinite(num(x)) && Number.isFinite(num(y)) && num(height) > 0 && num(height) <= 30 && reach !== null;
  const submit = (e: FormEvent) => { e.preventDefault(); if (ok && reach && !busy) onSubmit({ code, x_m: num(x), y_m: num(y), altura_m: num(height), ...reach }); };
  return (
    <Modal title={title} onClose={onCancel}>
      <form onSubmit={submit} className="fgrid" style={{ gap: 10 }}>
        <p className="muted small" style={{ gridColumn: "1 / -1", margin: 0 }}>{help}</p>
        <p className="small" style={{ gridColumn: "1 / -1", margin: 0 }}>{tl("plenum.startsAt")} <b>{level}</b>{nextLevel && <> · {tl("plenum.adding")} <b>{nextLevel}</b></>}</p>
        <label className="field"><span>{tl("plenum.code")}</span><input autoFocus value={code} onChange={(e) => setCode(e.target.value)} /></label>
        <label className="field"><span>{tl("plenum.height")}</span><input inputMode="decimal" value={height} onChange={(e) => setHeight(e.target.value)} /></label>
        <label className="field"><span>{tl("plenum.x")}</span><input inputMode="decimal" value={x} onChange={(e) => setX(e.target.value)} /></label>
        <label className="field"><span>{tl("plenum.y")}</span><input inputMode="decimal" value={y} onChange={(e) => setY(e.target.value)} /></label>
        <fieldset style={{ gridColumn: "1 / -1", border: "1px solid var(--line, #ccc)", borderRadius: 6 }}>
          <legend className="small">{tl("plenum.reach")}</legend>
          <label className="small" style={{ display: "block" }}><input type="radio" checked={all} onChange={() => setAll(true)} /> {tl("plenum.allLevels")}</label>
          <label className="small" style={{ display: "block" }}><input type="radio" checked={!all} onChange={() => setAll(false)} /> {tl("plenum.some")}</label>
          {!all && (
            <div className="row" style={{ gap: 10, marginTop: 6 }}>
              <label className="small">{tl("plenum.up")} <input style={{ width: 60 }} inputMode="numeric" value={up} onChange={(e) => setUp(e.target.value)} /></label>
              <label className="small">{tl("plenum.down")} <input style={{ width: 60 }} inputMode="numeric" value={down} onChange={(e) => setDown(e.target.value)} /></label>
            </div>
          )}
        </fieldset>
        <p className="muted small" style={{ gridColumn: "1 / -1", margin: 0 }}>{tl("plenum.note")}</p>
        <div className="row" style={{ gridColumn: "1 / -1", gap: 8, justifyContent: "flex-end" }}>
          <button type="button" onClick={onCancel}>{tl("projects.cancel")}</button>
          <button type="submit" className="primary" disabled={!ok || busy}>{busy ? tl("design.working") : tl("plenum.place")}</button>
        </div>
      </form>
    </Modal>
  );
}
