import { Gantt, ScheduleView, State, WbsTree, WbsView, useApi, useI18n } from "@epc/ui";

export default function Plan({ base }: { base: string }) {
  const { t } = useI18n();
  const wbs = useApi<WbsView>(base + "/wbs");
  const sch = useApi<ScheduleView>(base + "/schedule");
  if (!wbs.data || !sch.data) return <State loading={wbs.loading || sch.loading} error={wbs.error || sch.error} />;
  if (wbs.data.nodes.length === 0 && sch.data.activities.length === 0) return <div className="state">{t("plan.empty")}</div>;
  return (
    <div className="grid" style={{ gap: 14 }}>
      <Gantt schedule={sch.data} today={new Date().toISOString().slice(0, 10)} />
      <WbsTree wbs={wbs.data} />
    </div>
  );
}

/* ---------------- automatic analysis (admin/engineer only) ---------------- */
