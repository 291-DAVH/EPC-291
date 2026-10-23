import { ScheduleView } from "../api";
import { Badge } from "../components";
import { useI18n } from "../i18n";

const day = (iso: string) => Date.parse(iso + "T00:00:00") / 86400000;

/** Gantt-style bars: critical activities highlighted, milestones as diamonds, today marker. */
export function Gantt({ schedule, today }: { schedule: ScheduleView; today?: string }) {
  const { t } = useI18n();
  if (!schedule.start || !schedule.end) return null;
  const s0 = day(schedule.start);
  const span = Math.max(1, day(schedule.end) - s0 + 1);
  const pos = (iso: string) => ((day(iso) - s0) / span) * 100;
  const todayPos = today ? pos(today) : null;
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 style={{ margin: 0 }}>{t("plan.schedule")}</h2>
        <span className="muted small">{schedule.start} → {schedule.end} · {schedule.span_days} {t("plan.days")}</span>
      </div>
      <div className="gantt">
        {schedule.activities.map((a) => {
          const left = pos(a.start);
          const width = a.milestone ? 0 : Math.max(0.8, ((day(a.end) - day(a.start) + 1) / span) * 100);
          return (
            <div key={a.id}>
              <div className="glabel">
                {a.name}
                {a.critical && <Badge tone="accent">{t("plan.critical")}</Badge>}
                {a.late && <Badge tone="bad">{t("plan.late")}</Badge>}
                {a.conflict && <Badge tone="warn">{t("plan.conflict")}</Badge>}
              </div>
              <div className="gtrack">
                {todayPos !== null && todayPos >= 0 && todayPos <= 100 && <i className="gtoday" style={{ left: `${todayPos}%` }} title={t("plan.today")} />}
                {a.milestone ? (
                  <span className={"gmile" + (a.critical ? " crit" : "")} style={{ left: `${left}%` }} title={`${t("plan.milestone")} ${a.start}`} />
                ) : (
                  <span className={"gbar" + (a.critical ? " crit" : "")} style={{ left: `${left}%`, width: `${width}%` }} title={`${a.start} → ${a.end} · ${t("plan.slack")}: ${a.slack_days} ${t("plan.days")}`}>
                    <i style={{ width: `${a.progress}%` }} />
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
