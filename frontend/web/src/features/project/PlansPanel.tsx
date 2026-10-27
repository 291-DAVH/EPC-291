import { useState } from "react";
import { Icon, Key, useI18n } from "@epc/ui";

/** The plans (sheets) a discipline has on the level: lighting, sockets, power for HVAC... Each one is a drawing of its own over the same architecture. The person opens one, names the one
 *  being drawn, adds another or deletes one. */
export interface PlanRow { level: string; name: string }
interface Props {
  discipline: string; plans: PlanRow[]; current: string; canWrite: boolean;
  onOpen: (level: string) => void; onAdd: (name: string) => void; onRename: (name: string) => void; onDelete: (level: string) => void;
}

export default function PlansPanel({ discipline, plans, current, canWrite, onOpen, onAdd, onRename, onDelete }: Props) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const [name, setName] = useState("");
  const add = () => { const v = name.trim(); if (v) { onAdd(v.slice(0, 60)); setName(""); } };
  return (
    <div className="plans">
      <p className="muted small" style={{ margin: "0 0 8px" }}>{tl("plan.plans.help")}</p>
      <h4 className="coord-h">{discipline}</h4>
      <ul className="plan-list">
        {plans.map((p) => (
          <li key={p.level} className={p.level === current ? "on" : ""}>
            {p.level === current && canWrite
              ? <input defaultValue={p.name} key={p.level + p.name} placeholder={tl("plan.plans.main")} aria-label={tl("plan.plans.rename")} title={tl("plan.plans.rename")}
                  onBlur={(e) => e.target.value.trim() !== p.name && onRename(e.target.value.trim().slice(0, 60))} onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }} />
              : <button className="plan-open" onClick={() => onOpen(p.level)}>{p.name || tl("plan.plans.main")}</button>}
            {canWrite && <button className="tool-ico" onClick={() => onDelete(p.level)} title={tl("layout.deleteLevel")} aria-label={tl("layout.deleteLevel")}><Icon name="trash" size={15} /></button>}
          </li>
        ))}
      </ul>
      {canWrite && (
        <div className="row" style={{ gap: 6, marginTop: 8 }}>
          <input value={name} placeholder={tl("plan.plans.ph")} aria-label={tl("plan.plans.add")} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") add(); }} style={{ flex: 1, minWidth: 0 }} />
          <button className="primary" disabled={!name.trim()} onClick={add}>+ {tl("plan.plans.add")}</button>
        </div>
      )}
    </div>
  );
}
