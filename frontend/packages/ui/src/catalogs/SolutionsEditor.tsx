import { useEffect, useState } from "react";
import { api, ApiError, GroupRule, JSON_HEADERS, Solution, SolutionItem, SolutionsView, SolutionWhen, useApi } from "../api";
import { Badge, Page, State } from "../components";
import { Key, useI18n } from "../i18n";

const TOPOLOGIES = ["single", "dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd"];
const KINDS = ["auto", "mcb", "mccb", "mccb_motorized", "rcbo", "rccb"];
const TYPES = ["seccional", "motor", "iluminacion", "tomacorrientes"];
const PHASES = ["1F", "3F", "3F+N"];
const RANGES = ["gt", "ge", "lt", "le"] as const;

type Part = "solutions" | "add_ons" | "groups";
type Doc = { solutions: Record<string, Solution>; add_ons: Record<string, Solution>; groups: Record<string, GroupRule> };
const BY = ["type", "phase", "kind", "topology"];

const list = (v: string) => v.split(",").map((x) => x.trim()).filter(Boolean);
const num = (v: string): number | undefined => (v.trim() === "" || Number.isNaN(Number(v)) ? undefined : Number(v));

/** A value that is one for every phase or one per phase (poles and the label the single-line shows). */
function PhaseValue({ value, onChange, number, label }: { value: unknown; onChange: (v: unknown) => void; number: boolean; label: string }) {
  const { t } = useI18n();
  const byPhase = typeof value === "object" && value !== null;
  const map = (byPhase ? value : {}) as Record<string, string | number>;
  const parse = (s: string): unknown => (s === "" ? undefined : number ? Number(s) : s);
  return (
    <span className="row" style={{ gap: 4, flexWrap: "wrap", alignItems: "center" }} aria-label={label}>
      <select value={byPhase ? "phase" : "all"} onChange={(e) => onChange(e.target.value === "phase" ? { "*": value ?? "" } : (map["*"] ?? undefined))}>
        <option value="all">{t("solutions.sameForAll")}</option><option value="phase">{t("solutions.byPhase")}</option>
      </select>
      {byPhase ? [...PHASES, "*"].map((ph) => <span key={ph} className="small">{ph} <input style={{ width: 54 }} value={map[ph] ?? ""} onChange={(e) => onChange({ ...map, [ph]: parse(e.target.value) })} /></span>)
        : <input style={{ width: 80 }} value={(value as string | number | undefined) ?? ""} onChange={(e) => onChange(parse(e.target.value))} aria-label={label} />}
    </span>
  );
}

function Tri({ value, onChange, label }: { value: boolean | undefined; onChange: (v: boolean | undefined) => void; label: string }) {
  const { t } = useI18n();
  return (
    <select value={value === undefined ? "" : String(value)} onChange={(e) => onChange(e.target.value === "" ? undefined : e.target.value === "true")} aria-label={label}>
      <option value="">{t("solutions.any")}</option><option value="true">{t("solutions.yes")}</option><option value="false">{t("solutions.no")}</option>
    </select>
  );
}

/** The conditions of a solution (or of one of its items): everything left empty does not restrict. */
function WhenEditor({ when, onChange, only }: { when: SolutionWhen; onChange: (w: SolutionWhen) => void; only?: boolean }) {
  const { t } = useI18n();
  const set = (patch: Partial<SolutionWhen>) => {
    const next = { ...when, ...patch } as Record<string, unknown>;
    Object.keys(next).forEach((k) => { const v = next[k]; if (v === undefined || (Array.isArray(v) && v.length === 0) || (typeof v === "object" && v !== null && !Array.isArray(v) && Object.keys(v).length === 0)) delete next[k]; });
    onChange(next as SolutionWhen);
  };
  const chips = (key: "topology" | "kind" | "phase" | "type", options: string[]) => (
    <label className="small" style={{ display: "block" }}>{t(`solutions.when.${key}` as Key)}{" "}
      <input list={`opt-${key}`} value={(when[key] ?? []).join(", ")} onChange={(e) => set({ [key]: list(e.target.value) })} style={{ width: 230 }} placeholder={options.join(", ")} />
      <datalist id={`opt-${key}`}>{options.map((o) => <option key={o} value={o} />)}</datalist>
    </label>
  );
  return (
    <div style={{ display: "grid", gap: 4 }}>
      {!only && <>{chips("topology", TOPOLOGIES)}{chips("kind", KINDS)}{chips("phase", PHASES)}{chips("type", TYPES)}
        <label className="small">{t("solutions.when.has_children")} <Tri value={when.has_children} onChange={(v) => set({ has_children: v })} label={t("solutions.when.has_children")} /></label>
        <label className="small">{t("solutions.when.motor")} <Tri value={when.motor} onChange={(v) => set({ motor: v })} label={t("solutions.when.motor")} /></label>
        <label className="small">{t("solutions.when.text")} <input value={(when.text_contains ?? []).join(", ")} onChange={(e) => set({ text_contains: list(e.target.value) })} style={{ width: 200 }} /></label></>}
      <span className="small">{t("solutions.when.in_a")} {RANGES.map((r) => <span key={r}>{" "}{r} <input style={{ width: 56 }} value={when.in_a?.[r] ?? ""} onChange={(e) => set({ in_a: { ...(when.in_a ?? {}), [r]: num(e.target.value) } as Record<string, number> })} /></span>)}</span>
    </div>
  );
}

/** A rule of automatic groups: which circuits, how they are split and how many each differential serves. */
function GroupEditor({ id, rule, onChange, onRemove, error }: { id: string; rule: GroupRule; onChange: (p: Partial<GroupRule>) => void; onRemove: () => void; error: string }) {
  const { t } = useI18n();
  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
        <b>{id}</b>
        <label className="small">ES <input value={rule.name?.es ?? ""} onChange={(e) => onChange({ name: { ...rule.name, es: e.target.value } })} style={{ width: 220 }} /></label>
        <label className="small">EN <input value={rule.name?.en ?? ""} onChange={(e) => onChange({ name: { ...rule.name, en: e.target.value } })} style={{ width: 220 }} /></label>
        <label className="small"><input type="checkbox" checked={rule.enabled !== false} onChange={(e) => onChange({ enabled: e.target.checked })} /> {t("solutions.enabled")}</label>
        <button onClick={onRemove}>{t("solutions.remove")}</button>
      </div>
      <div className="muted small">{t("solutions.groups.help")}</div>
      <div><b className="small">{t("solutions.groups.which")}</b><WhenEditor when={rule.when ?? {}} onChange={(w) => onChange({ when: w })} /></div>
      <div className="small"><b>{t("solutions.groups.by")}</b> {BY.map((k) => <label key={k} style={{ marginRight: 10 }}><input type="checkbox" checked={(rule.by ?? []).includes(k)} onChange={(e) => onChange({ by: e.target.checked ? [...(rule.by ?? []), k] : (rule.by ?? []).filter((x) => x !== k) })} /> {k}</label>)}</div>
      <div className="row small" style={{ gap: 12, flexWrap: "wrap" }}>
        <label>{t("solutions.groups.maxCircuits")} <input type="number" min={1} value={rule.max_circuits ?? 6} onChange={(e) => onChange({ max_circuits: Number(e.target.value) })} style={{ width: 70 }} /></label>
        <label>{t("solutions.groups.maxIb")} <input type="number" min={1} value={rule.max_ib_a ?? 40} onChange={(e) => onChange({ max_ib_a: Number(e.target.value) })} style={{ width: 80 }} /></label>
        <label>{t("solutions.groups.tag")} <input value={rule.tag ?? ""} onChange={(e) => onChange({ tag: e.target.value })} style={{ width: 110 }} placeholder="GD-L{n:02d}" /></label>
      </div>
      <div className="row small" style={{ gap: 12, flexWrap: "wrap" }}>
        <label>{t("solutions.groups.description")} ES <input value={rule.description?.es ?? ""} onChange={(e) => onChange({ description: { ...rule.description, es: e.target.value } })} style={{ width: 240 }} /></label>
        <label>EN <input value={rule.description?.en ?? ""} onChange={(e) => onChange({ description: { ...rule.description, en: e.target.value } })} style={{ width: 240 }} /></label>
      </div>
      {error && <p style={{ color: "var(--bad, #d62728)" }} className="small">{error}</p>}
    </div>
  );
}

/** The document of standard solutions at the level `path` serves (the MASTER's, the company's or a project's). Only what differs from the level above is stored. */
export function SolutionsEditor({ path, bare = false }: { path: string; bare?: boolean }) {
  const { t, lang } = useI18n();
  const [rev, setRev] = useState(0);
  const view = useApi<SolutionsView>(`${path}?rev=${rev}`);
  const [draft, setDraft] = useState<Doc>({ solutions: {}, add_ons: {}, groups: {} });
  const [sel, setSel] = useState<{ part: Part; id: string } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  useEffect(() => { if (view.data) { setDraft({ solutions: view.data.solutions, add_ons: view.data.add_ons, groups: view.data.groups ?? {} }); setErrors({}); } }, [view.data]);
  const Wrap = ({ children }: { children: React.ReactNode }) => (bare ? <>{children}</> : <Page title={t("solutions.title")} help={t("solutions.help")}>{children}</Page>);
  if (!view.data) return <Wrap><State loading={view.loading} error={view.error} /></Wrap>;

  const data = view.data;
  const saved: Doc = { solutions: data.solutions, add_ons: data.add_ons, groups: data.groups ?? {} };
  const dirty = JSON.stringify(draft) !== JSON.stringify(saved);
  const edit = (part: "solutions" | "add_ons", id: string, patch: Partial<Solution>) => { setDraft({ ...draft, [part]: { ...draft[part], [id]: { ...draft[part][id], ...patch } } }); setState("idle"); };
  const editGroup = (id: string, patch: Partial<GroupRule>) => { setDraft({ ...draft, groups: { ...draft.groups, [id]: { ...draft.groups[id], ...patch } } }); setState("idle"); };
  const send = async (reset: boolean) => {
    setState("saving"); setErrors({});
    try {
      const v = await api<SolutionsView>(path, reset ? { method: "DELETE" } : { method: "PUT", headers: JSON_HEADERS, body: JSON.stringify(draft) });
      setDraft({ solutions: v.solutions, add_ons: v.add_ons, groups: v.groups ?? {} }); setRev(rev + 1); setState("saved");
    } catch (e) { setErrors(e instanceof ApiError ? e.fieldErrors : {}); setState("idle"); }
  };
  const addSolution = (part: Part) => {
    const id = window.prompt(t("solutions.newId"))?.trim().toLowerCase().replace(/[^a-z0-9-]+/g, "-");
    if (!id || draft[part][id]) return;
    if (part === "groups") setDraft({ ...draft, groups: { ...draft.groups, [id]: { name: { es: id, en: id }, enabled: false, when: {}, by: ["type", "phase"], max_circuits: 6, max_ib_a: 40, tag: "G{n:02d}", description: { es: "Diferencial de grupo {n}", en: "Group differential {n}" } } } });
    else setDraft({ ...draft, [part]: { ...draft[part], [id]: { name: { es: id, en: id }, enabled: true, priority: 20, when: {}, chain: [{ symbol: data.symbols[0]?.id ?? "lv_mcb", short: "", slots: {} }] } } });
    setSel({ part, id });
  };
  const remove = (part: Part, id: string) => {
    if (!window.confirm(t("solutions.removeConfirm"))) return;
    const { [id]: _gone, ...rest } = draft[part] as Record<string, unknown>;
    setDraft({ ...draft, [part]: rest } as Doc); setSel(null);
  };
  const symbolOf = (id: string) => data.symbols.find((s) => s.id === id);
  const nameOf = (s: { name?: { es?: string; en?: string } }, id: string) => s.name?.[lang] ?? s.name?.es ?? id;
  const err = (part: Part, id: string) => Object.entries(errors).filter(([k]) => k.startsWith(`${part}.${id}`)).map(([k, v]) => `${k.slice(part.length + id.length + 2)}: ${v}`).join(" · ");
  const ordered = (part: "solutions" | "add_ons") => Object.entries(draft[part]).sort((a, b) => (b[1].priority ?? 0) - (a[1].priority ?? 0));
  const cur = sel && sel.part !== "groups" ? draft[sel.part][sel.id] ?? null : null;
  const sp = (sel?.part ?? "solutions") as "solutions" | "add_ons";          // the part a solution or add-on lives in (a rule of groups has its own editor)
  const curGroup = sel?.part === "groups" ? draft.groups[sel.id] ?? null : null;
  const setItem = (n: number, patch: Partial<SolutionItem>) => cur && sel && sel.part !== "groups" && edit(sp, sel.id, { chain: cur.chain.map((it, i) => (i === n ? { ...it, ...patch } : it)) });
  const move = (n: number, d: number) => { if (!cur || !sel || sel.part === "groups") return; const c = cur.chain.slice(); const [x] = c.splice(n, 1); c.splice(n + d, 0, x); edit(sp, sel.id, { chain: c }); };

  return (
    <Wrap>
      {data.inherits && <p className="muted small">{t(`catalogs.inherits.${data.inherits}` as Key)}</p>}
      <div className="row" style={{ marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
        <button className="primary" disabled={!dirty || state === "saving"} onClick={() => send(false)}>{t("layers.save")}</button>
        <button disabled={!dirty} onClick={() => { setDraft(saved); setErrors({}); }}>{t("layers.discard")}</button>
        <button disabled={data.changed.length === 0 || state === "saving"} onClick={() => { if (window.confirm(t("solutions.resetConfirm"))) send(true); }}>{t("layers.reset")}</button>
        {state === "saved" && <Badge tone="ok">{t("layers.saved")}</Badge>}
        {Object.keys(errors).length > 0 && <Badge tone="bad">{t("layers.refused")}</Badge>}
      </div>
      {errors.solutions && <p style={{ color: "var(--bad, #d62728)" }}>{errors.solutions}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(240px, 320px) 1fr", gap: 14, alignItems: "start" }}>
        <div className="card">
          {(["solutions", "add_ons"] as const).map((part) => (
            <div key={part} style={{ marginBottom: 10 }}>
              <div className="row" style={{ justifyContent: "space-between" }}><b>{t(`solutions.group.${part}` as Key)}</b><button onClick={() => addSolution(part)}>+</button></div>
              {ordered(part).map(([id, s]) => (
                <div key={id} onClick={() => setSel({ part, id })} style={{ padding: "4px 6px", cursor: "pointer", borderRadius: 4, background: sel?.part === part && sel.id === id ? "var(--accent-soft, rgba(80,120,255,.15))" : undefined, opacity: s.enabled === false ? 0.55 : 1 }} title={err(part, id)}>
                  <div>{nameOf(s, id)} {err(part, id) && <Badge tone="bad">!</Badge>}{data.changed.includes(id) && <> <Badge tone="warn">{t("layers.changed")}</Badge></>}{s.enabled === false && <> <Badge>{t("solutions.off")}</Badge></>}</div>
                  <div className="muted small">{id} · {(s.chain ?? []).map((it) => it.short || it.symbol).join(" › ")}</div>
                </div>
              ))}
            </div>
          ))}
          <div style={{ marginBottom: 10 }}>
            <div className="row" style={{ justifyContent: "space-between" }}><b>{t("solutions.group.groups")}</b><button onClick={() => addSolution("groups")}>+</button></div>
            {Object.entries(draft.groups).map(([id, g]) => (
              <div key={id} onClick={() => setSel({ part: "groups", id })} style={{ padding: "4px 6px", cursor: "pointer", borderRadius: 4, background: sel?.part === "groups" && sel.id === id ? "var(--accent-soft, rgba(80,120,255,.15))" : undefined, opacity: g.enabled === false ? 0.55 : 1 }} title={err("groups", id)}>
                <div>{nameOf(g, id)} {err("groups", id) && <Badge tone="bad">!</Badge>}{data.changed.includes(id) && <> <Badge tone="warn">{t("layers.changed")}</Badge></>}{g.enabled === false && <> <Badge>{t("solutions.off")}</Badge></>}</div>
                <div className="muted small">{id} · ≤ {g.max_circuits} · ≤ {g.max_ib_a} A</div>
              </div>
            ))}
          </div>
        </div>
        <div className="card">
          {curGroup && sel ? <GroupEditor id={sel.id} rule={curGroup} onChange={(patch) => editGroup(sel.id, patch)} onRemove={() => remove("groups", sel.id)} error={err("groups", sel.id)} /> : !cur || !sel ? <p className="muted">{t("solutions.pick")}</p> : (
            <div style={{ display: "grid", gap: 10 }}>
              <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
                <b>{sel.id}</b>
                <label className="small">ES <input value={cur.name?.es ?? ""} onChange={(e) => edit(sp, sel.id, { name: { ...cur.name, es: e.target.value } })} style={{ width: 200 }} /></label>
                <label className="small">EN <input value={cur.name?.en ?? ""} onChange={(e) => edit(sp, sel.id, { name: { ...cur.name, en: e.target.value } })} style={{ width: 200 }} /></label>
                {sel.part === "solutions" && <label className="small">{t("solutions.priority")} <input type="number" value={cur.priority ?? 0} onChange={(e) => edit(sp, sel.id, { priority: Number(e.target.value) })} style={{ width: 70 }} /></label>}
                <label className="small"><input type="checkbox" checked={cur.enabled !== false} onChange={(e) => edit(sp, sel.id, { enabled: e.target.checked })} /> {t("solutions.enabled")}</label>
                <button onClick={() => remove(sel.part, sel.id)}>{t("solutions.remove")}</button>
              </div>
              <div><b className="small">{t("solutions.when.title")}</b><div className="muted small">{t("solutions.when.help")}</div><WhenEditor when={cur.when ?? {}} onChange={(w) => edit(sp, sel.id, { when: w })} /></div>
              <div>
                <b className="small">{t("solutions.chain")}</b>
                {cur.chain.map((it, n) => (
                  <div key={n} className="card" style={{ margin: "6px 0", padding: 8, display: "grid", gap: 4 }}>
                    <div className="row" style={{ gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                      <span className="muted">{n + 1}</span>
                      <select value={it.symbol} onChange={(e) => setItem(n, { symbol: e.target.value })} aria-label={t("solutions.item.symbol")}>
                        {!symbolOf(it.symbol) && <option value={it.symbol}>{it.symbol} ⚠</option>}
                        {data.symbols.map((s) => <option key={s.id} value={s.id}>{s.id} — {s.name[lang] || s.name.es}</option>)}
                      </select>
                      <label className="small">{t("solutions.item.short")} <input value={it.short ?? ""} onChange={(e) => setItem(n, { short: e.target.value })} style={{ width: 80 }} /></label>
                      <label className="small">{t("solutions.item.count")} <input value={it.count ?? ""} onChange={(e) => setItem(n, { count: e.target.value === "" ? undefined : (num(e.target.value) ?? e.target.value) })} style={{ width: 120 }} placeholder="1" /></label>
                      <button disabled={n === 0} onClick={() => move(n, -1)}>↑</button><button disabled={n === cur.chain.length - 1} onClick={() => move(n, 1)}>↓</button>
                      <button onClick={() => edit(sp, sel.id, { chain: cur.chain.filter((_, i) => i !== n) })}>✕</button>
                    </div>
                    <div className="small">{t("solutions.item.poles")} <PhaseValue value={it.poles} number onChange={(v) => setItem(n, { poles: v as SolutionItem["poles"] })} label={t("solutions.item.poles")} />{" · "}
                      {t("solutions.item.label")} <PhaseValue value={it.label} number={false} onChange={(v) => setItem(n, { label: v as SolutionItem["label"] })} label={t("solutions.item.label")} /></div>
                    <div className="small">{t("solutions.item.slots")}
                      {Object.entries(it.slots ?? {}).map(([k, v]) => (
                        <div key={k} className="row" style={{ gap: 4 }}>
                          <select value={k} onChange={(e) => { const { [k]: val, ...rest } = it.slots ?? {}; setItem(n, { slots: { ...rest, [e.target.value]: val } }); }}>
                            {[...new Set([k, ...(symbolOf(it.symbol)?.slots ?? []).map((s) => s.key)])].map((o) => <option key={o}>{o}</option>)}
                          </select>
                          <input value={v} onChange={(e) => setItem(n, { slots: { ...(it.slots ?? {}), [k]: e.target.value } })} style={{ width: 220 }} />
                          <button onClick={() => { const { [k]: _x, ...rest } = it.slots ?? {}; setItem(n, { slots: rest }); }}>✕</button>
                        </div>
                      ))}
                      <button onClick={() => { const free = (symbolOf(it.symbol)?.slots ?? []).map((s) => s.key).find((k) => !(k in (it.slots ?? {}))) ?? "tag"; setItem(n, { slots: { ...(it.slots ?? {}), [free]: "" } }); }}>+ {t("solutions.item.slot")}</button>
                      <span className="muted"> {"{in_a:g} {icu_ka:g} {rcd_ma:g} {tag}"}</span>
                    </div>
                    <div className="small">{t("solutions.item.if")} <WhenEditor only when={it.if ?? {}} onChange={(w) => setItem(n, { if: Object.keys(w).length ? w : undefined })} /></div>
                  </div>
                ))}
                <button onClick={() => cur && edit(sp, sel.id, { chain: [...cur.chain, { symbol: data.symbols[0]?.id ?? "lv_mcb", short: "", slots: {} }] })}>+ {t("solutions.item.add")}</button>
              </div>
              {sel.part === "solutions" && <label className="small">{t("solutions.disp")} <input value={cur.disp ?? ""} onChange={(e) => edit(sp, sel.id, { disp: e.target.value || undefined })} style={{ width: 360 }} placeholder={t("solutions.dispAuto")} /></label>}
              {err(sel.part, sel.id) && <p style={{ color: "var(--bad, #d62728)" }} className="small">{err(sel.part, sel.id)}</p>}
            </div>
          )}
        </div>
      </div>
    </Wrap>
  );
}
