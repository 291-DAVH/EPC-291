import { useEffect, useMemo, useRef, useState } from "react";
import { Icon } from "@epc/ui";
import type { Drawing, Pt, Ref } from "./planEditing";
import { DEFAULT_KEYS, PlanPrefs } from "./planPrefs";
import type { SelectionStats, UnderlayOpts } from "./planTools";

/** The parts of the editor around the canvas: toolbox, selection strip, view panel, coordinates bar, minimap, context menu, command palette, shortcuts. They hold only their own open/closed state; what they do is handed in. */
type T = (key: string) => string;
export interface ToolDef { id: string; icon: string; write: boolean }
export interface Command { id: string; group: string; label: string; hint?: string; run: () => void; disabled?: boolean }
export interface MenuItem { label: string; icon?: string; run?: () => void; disabled?: boolean; danger?: boolean; sep?: boolean; sub?: MenuItem[] }

export function Toolbox({ tools, tool, readOnly, keys, t, onChoose, canUndo, canRedo, onUndo, onRedo, onFit, onSelection, onPalette, onExport }: {
  tools: ToolDef[]; tool: string; readOnly?: boolean; keys: Record<string, string>; t: T; onChoose: (id: string) => void; canUndo: boolean; canRedo: boolean;
  onUndo: () => void; onRedo: () => void; onFit: () => void; onSelection: () => void; onPalette: () => void; onExport: () => void;
}) {
  const hint = (id: string) => (keys[id] ? ` (${keys[id].replace("+", "")})` : "");
  return (
    <div className="wb-tools" role="toolbar" aria-orientation="vertical" aria-label={t("layout.toolbox")}>
      {tools.filter((x) => !readOnly || !x.write).map((x) => (
        <button key={x.id} className={"tool" + (tool === x.id ? " on" : "")} onClick={() => onChoose(x.id)} title={t("plan.tool." + x.id) + hint(x.id)} aria-pressed={tool === x.id}><Icon name={x.icon} size={20} /><span>{t("plan.tool." + x.id)}</span></button>
      ))}
      <span className="tool-sep" />
      {!readOnly && <>
        <button className="tool" onClick={onUndo} disabled={!canUndo} title={t("layout.undo") + " (Ctrl+Z)"}><Icon name="undo" size={20} /><span>{t("layout.undo")}</span></button>
        <button className="tool" onClick={onRedo} disabled={!canRedo} title={t("layout.redo") + " (Ctrl+Y)"}><Icon name="redo" size={20} /><span>{t("layout.redo")}</span></button>
      </>}
      <button className="tool" onClick={onFit} title={t("layout.fit") + " (F)"}><Icon name="fit" size={20} /><span>{t("layout.fit")}</span></button>
      <button className="tool" onClick={onSelection} title={t("plan.zoomSelection")}><Icon name="select" size={20} /><span>{t("plan.zoomSelection")}</span></button>
      <span className="tool-sep" />
      <button className="tool" onClick={onExport} title={t("plan.export")}><Icon name="image" size={20} /><span>{t("plan.export")}</span></button>
      <button className="tool" onClick={onPalette} title={t("plan.palette") + " (Ctrl+K)"}><Icon name="search" size={20} /><span>{t("plan.palette")}</span></button>
    </div>
  );
}

// ---------------------------------------------------------------- selection strip
export function SelectionStrip({ stats, write, t, run, onArray, onTransform, onTemplate, onLock, locked, onCopyLevels }: {
  stats: SelectionStats; write: boolean; t: T; run: (id: string) => void; onArray: () => void; onTransform: () => void; onTemplate: () => void; onLock: () => void; locked: boolean; onCopyLevels?: () => void;
}) {
  const multi = stats.nodes + stats.lines >= 2;
  const btn = (id: string, icon: string, enabled = true) => <button key={id} className="strip-btn" disabled={!enabled} onClick={() => run(id)} title={t("plan.act." + id)} aria-label={t("plan.act." + id)}><Icon name={icon} size={16} /></button>;
  return (
    <div className="wb-strip" role="toolbar" aria-label={t("plan.selectionActions")}>
      <b className="strip-count">{stats.nodes + stats.lines}</b>
      {btn("copy", "copy")}{write && btn("duplicate", "paste")}{write && <button className="strip-btn" onClick={onArray} title={t("plan.act.array")} aria-label={t("plan.act.array")}><Icon name="grid" size={16} /></button>}
      {write && <button className="strip-btn" onClick={onLock} title={t(locked ? "plan.act.unlock" : "plan.act.lock")} aria-label={t(locked ? "plan.act.unlock" : "plan.act.lock")} aria-pressed={locked}><Icon name={locked ? "unlock" : "lock"} size={16} /></button>}
      {write && multi && <><span className="strip-sep" />{btn("alignL", "alignL")}{btn("alignH", "alignH")}{btn("alignR", "alignR")}{btn("alignT", "alignT")}{btn("alignV", "alignV")}{btn("alignB", "alignB")}{btn("distH", "distH")}{btn("distV", "distV")}</>}
      {write && <><span className="strip-sep" /><button className="strip-btn" onClick={onTransform} title={t("plan.act.transform")} aria-label={t("plan.act.transform")}><Icon name="rotate" size={16} /></button>{btn("mirrorH", "mirror")}</>}
      {write && onCopyLevels && <button className="strip-btn" onClick={onCopyLevels} title={t("plan.act.copyLevels")} aria-label={t("plan.act.copyLevels")}><Icon name="layers" size={16} /></button>}
      {write && <button className="strip-btn" onClick={onTemplate} title={t("plan.act.template")} aria-label={t("plan.act.template")}><Icon name="template" size={16} /></button>}
      {write && btn("delete", "trash")}
    </div>
  );
}

// ---------------------------------------------------------------- the view panel
export function ViewPanel({ prefs, set, kinds, underlay, onUnderlay, hasUnderlay, onTool, onClose, t }: {
  prefs: PlanPrefs; set: (p: Partial<PlanPrefs>) => void; kinds: { id: string; name: string }[]; underlay: UnderlayOpts; onUnderlay: (o: UnderlayOpts) => void; hasUnderlay: boolean;
  onTool: (id: string) => void; onClose: () => void; t: T;
}) {
  const flag = (key: keyof PlanPrefs, label: string) => <label className="vp-row" key={key}><input type="checkbox" checked={!!prefs[key]} onChange={(e) => set({ [key]: e.target.checked } as Partial<PlanPrefs>)} /> {t(label)}</label>;
  return (
    <div className="wb-pop wb-viewpanel" role="dialog" aria-label={t("plan.view")}>
      <div className="pop-head"><b>{t("plan.view")}</b><button className="strip-btn" onClick={onClose} aria-label={t("layout.cancel")}><Icon name="close" size={14} /></button></div>
      <fieldset><legend>{t("plan.snap")}</legend>
        {flag("snap", "plan.snap.on")}{flag("mid", "plan.snap.mid")}{flag("ortho", "plan.snap.ortho")}{flag("chain", "plan.snap.chain")}
        <label className="vp-row">{t("plan.grid")} <select value={prefs.grid} onChange={(e) => set({ grid: parseFloat(e.target.value) })}>{[0, 0.1, 0.25, 0.5, 1, 2].map((g) => <option key={g} value={g}>{g === 0 ? t("plan.grid.off") : `${g} m`}</option>)}</select></label>
      </fieldset>
      <fieldset><legend>{t("plan.show")}</legend>
        {flag("labels", "plan.show.labels")}{flag("lengths", "plan.show.lengths")}{flag("coords", "plan.show.coords")}{flag("minimap", "plan.show.minimap")}{flag("refs", "plan.show.refs")}{flag("ghosts", "plan.show.ghosts")}{flag("pins", "plan.show.pins")}{flag("isolate", "plan.show.isolate")}
        <label className="vp-row">{t("plan.colorBy")} <select value={prefs.color} onChange={(e) => set({ color: e.target.value as PlanPrefs["color"] })}><option value="kind">{t("plan.colorBy.kind")}</option><option value="circuit">{t("plan.colorBy.circuit")}</option></select></label>
      </fieldset>
      {kinds.length > 0 && <fieldset><legend>{t("plan.kinds")}</legend>
        {kinds.map((k) => <label className="vp-row" key={k.id}><input type="checkbox" checked={!prefs.hidden.includes(k.id)} onChange={(e) => set({ hidden: e.target.checked ? prefs.hidden.filter((x) => x !== k.id) : [...prefs.hidden, k.id] })} /> <b>{k.id}</b> {k.name}</label>)}
      </fieldset>}
      {hasUnderlay && <fieldset><legend>{t("plan.underlay")}</legend>
        <label className="vp-row"><input type="checkbox" checked={!underlay.hidden} onChange={(e) => onUnderlay({ ...underlay, hidden: !e.target.checked })} /> {t("plan.underlay.show")}</label>
        <label className="vp-row">{t("plan.underlay.opacity")} <input type="range" min={0.1} max={1} step={0.05} value={underlay.opacity ?? 1} onChange={(e) => onUnderlay({ ...underlay, opacity: parseFloat(e.target.value) })} /></label>
        <label className="vp-row"><input type="checkbox" checked={!!underlay.locked} onChange={(e) => onUnderlay({ ...underlay, locked: e.target.checked })} /> {t("plan.underlay.lock")}</label>
        <div className="vp-row">
          <button onClick={() => onTool("alignUnderlay")} disabled={!!underlay.locked}><Icon name="rotate" size={14} /> {t("plan.underlay.align")}</button>
          <button onClick={() => onTool("cropUnderlay")} disabled={!!underlay.locked}><Icon name="crop" size={14} /> {t("plan.underlay.crop")}</button>
          <button onClick={() => onUnderlay({ ...underlay, rotation: 0, crop: null })} disabled={!!underlay.locked || (!underlay.rotation && !underlay.crop)}>{t("plan.underlay.reset")}</button>
        </div>
        {!!underlay.rotation && <small className="muted">{t("plan.underlay.turned")}: {underlay.rotation.toFixed(2)}°</small>}
      </fieldset>}
    </div>
  );
}

// ---------------------------------------------------------------- the bar under the canvas
export function CoordBar({ hint, cursor, zoom, snap, stats, scale, t, onTable }: {
  hint: string; cursor: Pt | null; zoom: number; snap: string; stats: SelectionStats | null; scale: number | null; t: T; onTable: () => void;
}) {
  const sel = stats && stats.nodes + stats.lines > 0 ? `${stats.nodes ? `${stats.nodes} ${t("plan.stat.nodes")}` : ""}${stats.nodes && stats.lines ? " · " : ""}${stats.lines ? `${stats.lines} ${t("plan.stat.lines")}` : ""}${stats.length_m !== null && stats.lines ? ` · ${stats.length_m} m` : ""}` : "";
  return (
    <div className="wb-hint">
      <span className="hint-text">{hint}</span>
      {sel && <button className="hint-btn" onClick={onTable} title={t("plan.stat.open")}>{sel}</button>}
      <span className="mono hint-right">
        {cursor && <>X {cursor[0].toFixed(2)} · Y {cursor[1].toFixed(2)} m · </>}
        {snap && <>{snap} · </>}
        {Math.round(zoom * 100)}%
        {scale === null ? <b style={{ color: "var(--bad)" }}> · {t("layout.notCalibrated")}</b> : <> · 1 u = {scale.toFixed(4)} m</>}
      </span>
    </div>
  );
}

export function SelectionTable({ stats, t, onClose }: { stats: SelectionStats; t: T; onClose: () => void }) {
  return (
    <div className="wb-pop wb-seltable" role="dialog" aria-label={t("plan.stat.title")}>
      <div className="pop-head"><b>{t("plan.stat.title")}</b><button className="strip-btn" onClick={onClose} aria-label={t("layout.cancel")}><Icon name="close" size={14} /></button></div>
      <table><tbody>
        <tr><td>{t("plan.stat.nodes")}</td><td className="mono">{stats.nodes}</td></tr><tr><td>{t("plan.stat.lines")}</td><td className="mono">{stats.lines}</td></tr>
        <tr><td>{t("plan.stat.length")}</td><td className="mono">{stats.length_m === null ? "–" : `${stats.length_m} m`}</td></tr>
        {Object.entries(stats.byKind).map(([k, n]) => <tr key={k}><td><b>{k}</b></td><td className="mono">{n}</td></tr>)}
        <tr><td>{t("plan.stat.circuits")}</td><td className="mono">{stats.circuits.join(", ") || "–"}</td></tr>
      </tbody></table>
    </div>
  );
}

// ---------------------------------------------------------------- legend
export function Legend({ entries, title }: { entries: { color: string; label: string }[]; title: string }) {
  if (!entries.length) return null;
  return (
    <div className="wb-legend" data-ui aria-label={title}>
      <b>{title}</b>
      {entries.map((e) => <span key={e.label}><i style={{ background: e.color }} />{e.label}</span>)}
    </div>
  );
}

// ---------------------------------------------------------------- minimap
export function MiniMap({ drawing, world, view, onCenter, t }: { drawing: Drawing; world: { x: number; y: number; w: number; h: number }; view: { x: number; y: number; w: number; h: number }; onCenter: (p: Pt) => void; t: T }) {
  const W = 150, H = Math.max(60, Math.min(110, (W * world.h) / world.w));
  const sx = W / world.w, sy = H / world.h, s = Math.min(sx, sy);
  const X = (x: number) => (x - world.x) * s, Y = (y: number) => (y - world.y) * s;
  const click = (e: React.PointerEvent<SVGSVGElement>) => { const r = e.currentTarget.getBoundingClientRect(); onCenter([world.x + (e.clientX - r.left) / s, world.y + (e.clientY - r.top) / s]); };
  return (
    <svg className="wb-minimap" width={W} height={H} onPointerDown={click} role="img" aria-label={t("plan.minimap")} data-ui>
      <rect width={W} height={H} fill="var(--panel)" fillOpacity={0.9} />
      {drawing.lines.map((l) => <polyline key={l.id} points={l.points.map((p) => `${X(p[0])},${Y(p[1])}`).join(" ")} fill="none" stroke="#4363d8" strokeWidth={1} />)}
      {drawing.nodes.map((n) => <rect key={n.id} x={X(n.x) - 1.5} y={Y(n.y) - 1.5} width={3} height={3} fill="#222" />)}
      <rect x={X(view.x)} y={Y(view.y)} width={view.w * s} height={view.h * s} fill="none" stroke="#d62728" strokeWidth={1.5} />
    </svg>
  );
}

// ---------------------------------------------------------------- context menu
export function ContextMenu({ at, items, onClose }: { at: [number, number]; items: MenuItem[]; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState<number | null>(null);
  useEffect(() => {
    const off = (e: Event) => { if (!ref.current?.contains(e.target as Node)) onClose(); };
    const key = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("pointerdown", off, true); window.addEventListener("keydown", key);
    return () => { window.removeEventListener("pointerdown", off, true); window.removeEventListener("keydown", key); };
  }, [onClose]);
  const go = (it: MenuItem) => { if (it.disabled || !it.run) return; onClose(); it.run(); };
  return (
    <div ref={ref} className="wb-menu" role="menu" style={{ left: at[0], top: at[1] }}>
      {items.map((it, i) => it.sep ? <hr key={i} /> : (
        <div key={i} className="menu-wrap" onMouseEnter={() => setOpen(it.sub ? i : null)}>
          <button role="menuitem" className={it.danger ? "danger" : ""} disabled={it.disabled} onClick={() => (it.sub ? setOpen(i) : go(it))}>{it.icon && <Icon name={it.icon} size={14} />}<span>{it.label}</span>{it.sub && <span className="menu-arrow">▸</span>}</button>
          {it.sub && open === i && <div className="wb-menu sub" role="menu">{it.sub.map((s, j) => <button key={j} role="menuitem" disabled={s.disabled} onClick={() => go(s)}>{s.label}</button>)}</div>}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- command palette
export function CommandPalette({ commands, onClose, t }: { commands: Command[]; onClose: () => void; t: T }) {
  const [q, setQ] = useState("");
  const [at, setAt] = useState(0);
  const list = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    return commands.filter((c) => !c.disabled && words.every((w) => `${c.group} ${c.label}`.toLowerCase().includes(w)));
  }, [q, commands]);
  useEffect(() => setAt(0), [q]);
  const run = (c?: Command) => { if (!c) return; onClose(); c.run(); };
  return (
    <div className="wb-palette" role="dialog" aria-label={t("plan.palette")} onPointerDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="palette-box">
        <input autoFocus value={q} placeholder={t("plan.palette.ph")} onChange={(e) => setQ(e.target.value)} aria-label={t("plan.palette")}
          onKeyDown={(e) => { e.stopPropagation(); if (e.key === "Escape") onClose(); else if (e.key === "ArrowDown") { e.preventDefault(); setAt((a) => Math.min(a + 1, list.length - 1)); } else if (e.key === "ArrowUp") { e.preventDefault(); setAt((a) => Math.max(a - 1, 0)); } else if (e.key === "Enter") run(list[at]); }} />
        <ul role="listbox">
          {list.slice(0, 12).map((c, i) => <li key={c.id} role="option" aria-selected={i === at} className={i === at ? "on" : ""} onMouseEnter={() => setAt(i)} onClick={() => run(c)}><span className="muted small">{c.group}</span> {c.label}{c.hint && <kbd>{c.hint}</kbd>}</li>)}
          {list.length === 0 && <li className="muted">{t("plan.palette.none")}</li>}
        </ul>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- shortcuts
export function ShortcutsPanel({ keys, set, fixed, t, onClose }: { keys: Record<string, string>; set: (k: Record<string, string>) => void; fixed: { keys: string; action: string }[]; t: T; onClose: () => void }) {
  const actions = Object.keys(DEFAULT_KEYS);
  const taken = (action: string, key: string) => !!key && actions.some((a) => a !== action && (keys[a] ?? DEFAULT_KEYS[a]) === key);
  return (
    <div className="wb-pop wb-shortcuts" role="dialog" aria-label={t("plan.keys")}>
      <div className="pop-head"><b>{t("plan.keys")}</b><button className="strip-btn" onClick={onClose} aria-label={t("layout.cancel")}><Icon name="close" size={14} /></button></div>
      <p className="muted small">{t("plan.keys.help")}</p>
      <table><tbody>
        {actions.map((a) => { const cur = keys[a] ?? DEFAULT_KEYS[a]; const bad = taken(a, cur);
          return <tr key={a}><td>{t("plan.tool." + a)}</td><td><input className="key-input" maxLength={1} value={cur.replace("+", "")} aria-invalid={bad} onChange={(e) => { const v = e.target.value.slice(-1).toLowerCase(); set({ ...keys, [a]: v }); }} />{bad && <span className="muted small"> {t("plan.keys.taken")}</span>}</td></tr>; })}
        {fixed.map((f) => <tr key={f.keys}><td>{f.action}</td><td><kbd>{f.keys}</kbd></td></tr>)}
      </tbody></table>
      <button onClick={() => set({})}>{t("plan.keys.reset")}</button>
    </div>
  );
}

// ---------------------------------------------------------------- small floating forms
export function NumberForm({ title, fields, onApply, onCancel, t }: { title: string; fields: { key: string; label: string; value: number; step?: number }[]; onApply: (v: Record<string, number>) => void; onCancel: () => void; t: T }) {
  const [vals, setVals] = useState<Record<string, string>>(Object.fromEntries(fields.map((f) => [f.key, String(f.value)])));
  const num = (k: string) => parseFloat((vals[k] ?? "").replace(",", "."));
  const ok = fields.every((f) => Number.isFinite(num(f.key)));
  const go = () => ok && onApply(Object.fromEntries(fields.map((f) => [f.key, num(f.key)])));
  return (
    <div className="wb-float" role="dialog" aria-label={title} onKeyDown={(e) => { e.stopPropagation(); if (e.key === "Enter") go(); if (e.key === "Escape") onCancel(); }}>
      <b>{title}</b>
      {fields.map((f, i) => <label key={f.key} className="vp-row">{f.label} <input autoFocus={i === 0} inputMode="decimal" value={vals[f.key]} onChange={(e) => setVals({ ...vals, [f.key]: e.target.value })} style={{ width: 72 }} /></label>)}
      <button className="primary" disabled={!ok} onClick={go}>{t("layout.apply")}</button><button onClick={onCancel}>{t("layout.cancel")}</button>
    </div>
  );
}

export function TextForm({ title, label, initial, onApply, onCancel, t }: { title: string; label: string; initial?: string; onApply: (v: string) => void; onCancel: () => void; t: T }) {
  const [v, setV] = useState(initial ?? "");
  return (
    <div className="wb-float" role="dialog" aria-label={title} onKeyDown={(e) => { e.stopPropagation(); if (e.key === "Enter" && v.trim()) onApply(v.trim()); if (e.key === "Escape") onCancel(); }}>
      <b>{title}</b><label className="vp-row">{label} <input autoFocus value={v} onChange={(e) => setV(e.target.value)} style={{ width: 160 }} /></label>
      <button className="primary" disabled={!v.trim()} onClick={() => onApply(v.trim())}>{t("layout.apply")}</button><button onClick={onCancel}>{t("layout.cancel")}</button>
    </div>
  );
}

export const refKey = (r: Ref) => `${r.type}:${r.id}`;
