import { Key, useI18n } from "@epc/ui";
import Plan from "./Plan";
import Registers from "./Registers";

const SUBS = ["plan", "registers"] as const;

/** Management of the project: its plan (schedule and breakdown) and its registers (risks, changes, issues, decisions...). The registers are internal work: the engineering team and the owner see them. */
export default function Management({ base, client, code, engineer, sub, onSub }: { base: string; client: string; code: string; engineer: boolean; sub: string; onSub: (x: string) => void }) {
  const { t } = useI18n();
  const shown = SUBS.filter((x) => x === "plan" || engineer);
  const current = shown.find((x) => x === sub) ?? "plan";
  return (
    <>
      {shown.length > 1 && (
        <div className="subtabs" role="tablist">
          {shown.map((x) => <button key={x} role="tab" aria-selected={current === x} className={current === x ? "on" : ""} onClick={() => onSub(x)}>{t(("mgmt.sub." + x) as Key)}</button>)}
        </div>
      )}
      {current === "plan" && <Plan base={base} />}
      {current === "registers" && <Registers client={client} code={code} />}
    </>
  );
}
