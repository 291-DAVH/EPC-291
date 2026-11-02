import { Key, useI18n } from "@epc/ui";
import Deliverables from "./Deliverables";
import Issuing from "./Issuing";
import Parties from "./Parties";
import Plan from "./Plan";
import Registers from "./Registers";

const SUBS = ["plan", "team", "issue", "deliverables", "registers"] as const;
const INTERNAL = ["team", "issue", "registers"];                        // the engineering team and the owner see them; the client sees the plan and what was delivered

/** Management of the project: its plan (schedule and breakdown), the team that signs the drawings, the issue of what engineering made (a transmittal), what was delivered and its registers (risks, changes, issues, decisions...). */
export default function Management({ base, client, code, engineer, sub, onSub }: { base: string; client: string; code: string; engineer: boolean; sub: string; onSub: (x: string) => void }) {
  const { t } = useI18n();
  const shown = SUBS.filter((x) => engineer || !INTERNAL.includes(x));
  const current = shown.find((x) => x === sub) ?? "plan";
  return (
    <>
      {shown.length > 1 && (
        <div className="subtabs" role="tablist">
          {shown.map((x) => <button key={x} role="tab" aria-selected={current === x} className={current === x ? "on" : ""} onClick={() => onSub(x)}>{t(("mgmt.sub." + x) as Key)}</button>)}
        </div>
      )}
      {current === "plan" && <Plan base={base} />}
      {current === "team" && <Parties client={client} code={code} />}
      {current === "issue" && <Issuing client={client} code={code} onOpenDeliverables={() => onSub("deliverables")} />}
      {current === "deliverables" && <Deliverables base={base} />}
      {current === "registers" && <Registers client={client} code={code} />}
    </>
  );
}
