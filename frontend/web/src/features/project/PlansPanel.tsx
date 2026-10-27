import { useState } from "react";
import { Icon, Key, useI18n } from "@epc/ui";

/** The plans (sheets) a discipline has on the level: lighting, sockets, MV distribution... Each one is a drawing of its own over the same architecture, and each one is of a subdiscipline, which decides
 *  the symbols and kinds the editor offers in it. The person opens one, names and classifies the one being drawn, adds another or deletes one. */
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
  const [sub, setSub] = useState("");
  const chosen = subdisciplines.find((x) => x.id === sub);
  const final = (name.trim() || chosen?.name || "").slice(0, 60);
  const add = () => { if (final) { onAdd(final, sub); setName(""); } };
  return (
    <div className="plans">
      <p className="muted small" style={{ margin: "0 0 8px" }}>{tl("plan.plans.help")}</p>
      <h4 className="coord-h">{discipline}</h4>
      <ul className="plan-list">
        {plans.map((p) => (
          <li key={p.level} className={p.level === current ? "on" : ""}>
            {p.level === current && canWrite
              ? <input defaultValue={p.name} key={p.level + p.name} placeholder={p.sub || tl("plan.plans.main")} aria-label={tl("plan.plans.rename")} title={tl("plan.plans.rename")}
                  onBlur={(e) => e.target.value.trim() !== p.name && onRename(e.target.value.trim().slice(0, 60))} onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }} />
              : <button className="plan-open" onClick={() => onOpen(p.level)}>{p.name || p.sub || tl("plan.plans.main")}{p.name && p.sub && p.name !== p.sub && <span className="muted small"> · {p.sub}</span>}</button>}
            {canWrite && <button className="tool-ico" onClick={() => onDelete(p.level)} title={tl("layout.deleteLevel")} aria-label={tl("layout.deleteLevel")}><Icon name="trash" size={15} /></button>}
          </li>
        ))}
      </ul>
      {subdisciplines.length > 0 && (
        <label className="vp-row" style={{ marginTop: 8 }}>{tl("plan.plans.sub")}
          <select value={currentSub} disabled={!canWrite} onChange={(e) => onSub(e.target.value)} title={tl("plan.plans.subHelp")}>
            <option value="">{tl("plan.plans.allKinds")}</option>{subdisciplines.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
          </select>
        </label>
      )}
      {canWrite && (
        <div className="plan-add">
          <h4 className="coord-h">{tl("plan.plans.add")}</h4>
          {subdisciplines.length > 0 && (
            <select value={sub} aria-label={tl("plan.plans.sub")} onChange={(e) => setSub(e.target.value)}>
              <option value="">{tl("plan.plans.allKinds")}</option>{subdisciplines.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select>
          )}
          <div className="row" style={{ gap: 6 }}>
            <input value={name} placeholder={chosen?.name || tl("plan.plans.ph")} aria-label={tl("plan.plans.ph")} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") add(); }} style={{ flex: 1, minWidth: 0 }} />
            <button className="primary" disabled={!final} onClick={add}>+ {tl("plan.plans.add")}</button>
          </div>
        </div>
      )}
    </div>
  );
}
