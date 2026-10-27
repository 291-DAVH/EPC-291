import { useMemo, useRef, useState } from "react";
import { Key, State, useApi, useI18n } from "@epc/ui";
import { base, Clash } from "./coordApi";
import type { Pt } from "./planEditing";
import { colorOfDiscipline, RefItem } from "./planTypes";

/** The disciplines of one level seen together, as footprints in metres: a read-only view for coordinating. Each discipline is still edited on its own sheet; here nothing can be changed. */
interface Overlay { items: RefItem[]; clashes: Clash[]; sources: Record<string, string> }
interface View { x: number; y: number; w: number; h: number }

const bounds = (items: RefItem[]): View => {
  const pts = items.flatMap((i) => i.points);
  if (!pts.length) return { x: -5, y: -5, w: 10, h: 10 };
  const x0 = Math.min(...pts.map((p) => p[0])), x1 = Math.max(...pts.map((p) => p[0])), y0 = Math.min(...pts.map((p) => p[1])), y1 = Math.max(...pts.map((p) => p[1]));
  const w = Math.max(x1 - x0, 4), h = Math.max(y1 - y0, 4);
  return { x: x0 - w * 0.1, y: -(y1 + h * 0.1), w: w * 1.2, h: h * 1.2 };                // y up in metres, down on the screen
};

export default function CoordinationView({ client, code, onPick }: { client: string; code: string; onPick?: (clash: Clash) => void }) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const layout = useApi<{ levels: { base: string }[] }>(`/projects/${client}/${code}/layout`);
  const levels = [...new Set((layout.data?.levels ?? []).map((l) => l.base))];
  const [level, setLevel] = useState("");
  const [source, setSource] = useState("auto");
  const [hidden, setHidden] = useState<string[]>([]);
  const [view, setView] = useState<View | null>(null);
  const [picked, setPicked] = useState<Clash | null>(null);
  const svg = useRef<SVGSVGElement>(null);
  const pan = useRef<{ sx: number; sy: number; v: View; k: number } | null>(null);
  const current = level || levels[0] || "";
  const data = useApi<Overlay>(current ? `${base(client, code)}/overlay?level=${encodeURIComponent(current)}&source=${source}` : null);
  const items = useMemo(() => (data.data?.items ?? []).filter((i) => !hidden.includes(i.discipline)), [data.data, hidden]);
  const shown = view ?? bounds(data.data?.items ?? []);
  const disciplines = [...new Set((data.data?.items ?? []).map((i) => i.discipline))];
  if (!layout.data) return <State loading={layout.loading} />;
  if (!levels.length) return <div className="state">{tl("coord.view.none")}</div>;
  const unit = shown.w / Math.max(1, svg.current?.clientWidth ?? 600);                // metres per screen pixel
  const wheel = (e: React.WheelEvent) => {
    const f = e.deltaY > 0 ? 1.15 : 1 / 1.15, r = svg.current!.getBoundingClientRect();
    const px = shown.x + ((e.clientX - r.left) / r.width) * shown.w, py = shown.y + ((e.clientY - r.top) / r.height) * shown.h;
    setView({ x: px - (px - shown.x) * f, y: py - (py - shown.y) * f, w: shown.w * f, h: shown.h * f });
  };
  const centre = (p: Pt) => setView({ ...shown, x: p[0] - shown.w / 2, y: -p[1] - shown.h / 2 });
  return (
    <div>
      <p className="muted small" style={{ margin: "0 0 6px" }}>{tl("coord.view.help")}</p>
      <div className="row small" style={{ gap: 8, flexWrap: "wrap" }}>
        <label className="wb-field"><span>{tl("coord.view.level")}</span><select value={current} onChange={(e) => { setLevel(e.target.value); setView(null); setPicked(null); }}>{levels.map((l) => <option key={l}>{l}</option>)}</select></label>
        <label className="wb-field"><span>{tl("coord.source")}</span><select value={source} onChange={(e) => setSource(e.target.value)}>{["auto", "issued", "working"].map((s) => <option key={s} value={s}>{tl("coord.source." + s)}</option>)}</select></label>
        <button onClick={() => setView(null)}>{tl("coord.view.reset")}</button>
      </div>
      <div className="cview-legend">
        {disciplines.map((d) => <label key={d}><input type="checkbox" checked={!hidden.includes(d)} onChange={(e) => setHidden(e.target.checked ? hidden.filter((x) => x !== d) : [...hidden, d])} /><i style={{ width: 14, height: 4, background: colorOfDiscipline(d), display: "inline-block" }} /> {d} <span className="muted">({data.data?.sources[d] === "issued" ? tl("coord.source.issued") : tl("coord.source.working")})</span></label>)}
      </div>
      {data.loading && !data.data ? <State loading /> : !items.length ? <div className="state">{tl("coord.view.none")}</div> : (
        <div className="cview">
          <svg ref={svg} viewBox={`${shown.x} ${shown.y} ${shown.w} ${shown.h}`} preserveAspectRatio="xMidYMid meet" onWheel={wheel}
            onPointerDown={(e) => { (e.target as Element).setPointerCapture?.(e.pointerId); pan.current = { sx: e.clientX, sy: e.clientY, v: shown, k: unit }; }}
            onPointerMove={(e) => { const p = pan.current; if (p) setView({ ...p.v, x: p.v.x - (e.clientX - p.sx) * p.k, y: p.v.y - (e.clientY - p.sy) * p.k }); }} onPointerUp={() => { pan.current = null; }}>
            <g transform="scale(1,-1)">
              {items.map((i) => {
                const c = colorOfDiscipline(i.discipline), w = Math.max(i.width_m, unit * 2);
                return i.shape === "line"
                  ? <polyline key={i.sheet + i.id} points={i.points.map((p) => p.join(",")).join(" ")} fill="none" stroke={c} strokeOpacity={0.55} strokeWidth={w} strokeDasharray={i.origin === "reservation" ? `${unit * 8} ${unit * 5}` : undefined} strokeLinejoin="round"><title>{`${i.discipline} · ${i.kind} ${i.tag}`}</title></polyline>
                  : <rect key={i.sheet + i.id} x={i.points[0][0] - w / 2} y={i.points[0][1] - w / 2} width={w} height={w} fill={c} fillOpacity={0.45} stroke={c}><title>{`${i.discipline} · ${i.kind} ${i.tag}`}</title></rect>;
              })}
              {(data.data?.clashes ?? []).map((c) => (
                <g key={c.id} style={{ cursor: "pointer" }} onPointerDown={(e) => { e.stopPropagation(); setPicked(c); onPick?.(c); }}>
                  <circle cx={c.point_m[0]} cy={c.point_m[1]} r={unit * 9} fill={c.status === "accepted" ? "#7a8190" : c.type === "hard" ? "#d62728" : "#e08a00"} fillOpacity={0.35} stroke={c.status === "accepted" ? "#7a8190" : c.type === "hard" ? "#d62728" : "#e08a00"} strokeWidth={unit * 1.5}><title>{`${c.a.tag} ↔ ${c.b.tag}`}</title></circle>
                </g>
              ))}
            </g>
          </svg>
        </div>
      )}
      {picked && (
        <div className="coord-item" style={{ marginTop: 6 }}>
          <b>{tl("coord.clash." + picked.type)}</b> · {picked.a.tag} ({picked.a.discipline}) ↔ {picked.b.tag} ({picked.b.discipline}) · {picked.gap_m} m
          <button className="linkbtn" style={{ marginLeft: 8 }} onClick={() => centre(picked.point_m)}>{tl("coord.go")}</button>
        </div>
      )}
    </div>
  );
}
