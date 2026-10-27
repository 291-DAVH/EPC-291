import { useState } from "react";
import { Icon, Key, useI18n } from "@epc/ui";

/** The plans (sheets) a discipline has on the level. Each one is a drawing of its own over the same architecture. What the person types is the main description of the plan ("Iluminación planta baja");
 *  the secondary one is the type of plan (its subdiscipline: lighting, sockets, MV distribution...), which decides the symbols and kinds the editor offers. Adding a plan asks for that type. */
export interface PlanRow { level: string; name: string; sub: string }
export interface SubOption { id: string; name: string }
interface Props {
  discipline: string; plans: PlanRow[]; current: string; canWrite: boolean; subdisciplines: SubOption[]; currentSub: string;
  onOpen: (level: string) => void; onAdd: (name: string, subdiscipline: string) => void; onRename: (name: string) => void; onSub: (id: string) => void; onDelete: (level: string) => void;
}

export default function PlansPanel({ discipline, plans, current, canWrite, subdisciplines, currentSub, onOpen, onAdd, onRename, onSub, onDelete }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const [name, setName] = useState("");
  const [asking, setAsking] = useState(false);                         // the second step of adding a plan: which type of plan it is
  const [sub, setSub] = useState("");
  const text = name.trim().slice(0, 60);
  const start = () => { if (!text) return; if (subdisciplines.length) { setSub(""); setAsking(true); } else finish(""); };
  const finish = (id: string) => { onAdd(text, id); setName(""); setAsking(false); };
  return (
    <div className="plans">
      <p className="muted small" style={{ margin: "0 0 8px" }}>{tl("plan.plans.help")}</p>
      <h4 className="coord-h">{discipline}</h4>
      <ul className="plan-list">
        {plans.map((p) => (
          <li key={p.level} className={p.level === current ? "on" : ""}>
            <div className="plan-main">
              {p.level === current && canWrite
                ? <input defaultValue={p.name} key={p.level + p.name} placeholder={tl("plan.plans.main")} aria-label={tl("plan.plans.rename")} title={tl("plan.plans.rename")}
                    onBlur={(e) => e.target.value.trim() !== p.name && onRename(e.target.value.trim().slice(0, 60))} onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }} />
                : <button className="plan-open" onClick={() => onOpen(p.level)}>{p.name || tl("plan.plans.main")}</button>}
              {p.level === current && canWrite && subdisciplines.length > 0
                ? <select value={currentSub} onChange={(e) => onSub(e.target.value)} aria-label={tl("plan.plans.type")} title={tl("plan.plans.subHelp")}>
                    <option value="">{tl("plan.plans.allKinds")}</option>{subdisciplines.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                  </select>
                : <span className="plan-type muted small">{p.sub ? `${tl("plan.plans.type")}: ${p.sub}` : ""}</span>}
            </div>
            {canWrite && <button className="tool-ico" onClick={() => onDelete(p.level)} title={tl("layout.deleteLevel")} aria-label={tl("layout.deleteLevel")}><Icon name="trash" size={15} /></button>}
          </li>
        ))}
      </ul>
      {canWrite && (
        <div className="plan-add">
          <h4 className="coord-h">{tl("plan.plans.add")}</h4>
          {!asking ? (
            <div className="row" style={{ gap: 6 }}>
              <input value={name} placeholder={tl("plan.plans.ph")} aria-label={tl("plan.plans.ph")} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") start(); }} style={{ flex: 1, minWidth: 0 }} />
              <button className="primary" disabled={!text} onClick={start}>+ {tl("plan.plans.add")}</button>
            </div>
          ) : (
            <div className="plan-ask" role="group" aria-label={tl("plan.plans.askType")}>
              <b>{text}</b>
              <span className="muted small">{tl("plan.plans.askType")}</span>
              {subdisciplines.map((x) => <label key={x.id} className="vp-row"><input type="radio" name="plan-sub" checked={sub === x.id} onChange={() => setSub(x.id)} /> {x.name}</label>)}
              <div className="row" style={{ gap: 6 }}>
                <button className="primary" disabled={!sub} onClick={() => finish(sub)}>{tl("plan.plans.create")}</button>
                <button onClick={() => setAsking(false)}>{tl("layout.cancel")}</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
