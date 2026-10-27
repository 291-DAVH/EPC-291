import { useEffect, useState } from "react";
import { api, Badge, errorText, Icon, JSON_HEADERS, Key, State, useApi, useI18n } from "@epc/ui";
import { base, Clash, ClashResult, CoordOverview, Exchange, Rule, RulesView, Thread } from "./coordApi";
import type { Pt } from "./planEditing";
import CoordinationView from "./CoordinationView";
import { colorOfDiscipline } from "./planTypes";

/** Coordination between disciplines that stay separate: each issues what it occupies, the others see only that; clashes are found on the issues; conversations and the data that cross
 *  go through threads and exchanges. One panel for the side of the layout editor and for the project tab. */
export interface CoordinationProps {
  client: string; code: string; discipline: string; canWrite: boolean; onChanged?: () => void; onFocus?: (at_m: Pt, level: string, sheet: string) => void; standalone?: boolean;
}
type Section = "plan" | "clashes" | "threads" | "data" | "team";
const THREAD_STATES: Record<string, string[]> = { comment: ["open", "resolved"], request: ["open", "review", "resolved", "rejected"], opening: ["open", "review", "resolved", "rejected"], reservation: ["open", "accepted", "released"] };
const TONE: Record<string, "ok" | "warn" | "bad" | "accent"> = { open: "warn", review: "accent", resolved: "ok", rejected: "bad", accepted: "ok", released: "ok", hard: "bad", clearance: "warn", maintenance: "warn" };

const Chip = ({ id }: { id: string }) => <span className="disc-chip" style={{ borderColor: colorOfDiscipline(id), color: colorOfDiscipline(id) }}>{id}</span>;

export default function Coordination(props: CoordinationProps) {
  const { t } = useI18n();
  const tl = (k: string) => t(k as Key);
  const b = base(props.client, props.code);
  const [rev, setRev] = useState(0);
  const [section, setSection] = useState<Section>(props.standalone ? "plan" : "clashes");
  const [me, setMe] = useState(props.discipline);
  const [err, setErr] = useState("");
  const ov = useApi<CoordOverview>(`${b}?r=${rev}`);
  useEffect(() => { if (props.discipline) setMe(props.discipline); }, [props.discipline]);
  useEffect(() => { if (!me && ov.data?.disciplines.length) setMe(ov.data.disciplines[0]); }, [ov.data]);
  const bump = () => { setRev((n) => n + 1); props.onChanged?.(); };
  const call = async <T,>(path: string, method: string, body?: unknown): Promise<T | null> => {
    try { const r = await api<T>(`${b}${path}`, { method, headers: JSON_HEADERS, body: body === undefined ? undefined : JSON.stringify(body) }); setErr(""); bump(); return r; }
    catch (x) { setErr(errorText(x)); return null; }
  };
  if (ov.error) return <div className="state err">{ov.error}</div>;
  if (!ov.data) return <State loading={ov.loading} />;
  const o = ov.data;
  const others = o.disciplines.filter((d) => d !== me);
  const sections: { id: Section; label: string; badge?: number }[] = [
    ...(props.standalone ? [{ id: "plan" as Section, label: tl("coord.view") }] : []),
    { id: "clashes", label: tl("coord.clashes"), badge: o.counts.open }, { id: "threads", label: tl("coord.threads"), badge: o.counts.threads }, { id: "data", label: tl("coord.data") }, { id: "team", label: tl("coord.team") },
  ];
  const shared = { b, me, others, canWrite: props.canWrite, tl, call, rev, onFocus: props.onFocus, setErr };
  return (
    <div className="coord">
      {props.standalone && (
        <div className="row" style={{ gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          <label className="wb-field"><span>{tl("coord.actingAs")}</span><select value={me} onChange={(e) => setMe(e.target.value)}>{o.disciplines.map((d) => <option key={d}>{d}</option>)}</select></label>
          <span className="muted small">{tl("coord.principle")}</span>
        </div>
      )}
      <div className="coord-summary">
        <span><b>{o.counts.hard}</b> {tl("coord.sum.hard")}</span><span><b>{o.counts.open}</b> {tl("coord.sum.open")}</span><span><b>{o.counts.accepted}</b> {tl("coord.sum.accepted")}</span><span><b>{o.counts.threads}</b> {tl("coord.sum.threads")}</span>
      </div>
      <div className="wb-tabs sub" role="tablist">
        {sections.map((s) => <button key={s.id} role="tab" aria-selected={section === s.id} className={section === s.id ? "on" : ""} onClick={() => setSection(s.id)}>{s.label}{!!s.badge && <span className="dot">{s.badge}</span>}</button>)}
      </div>
      {err && <div className="alert bad small" style={{ margin: "6px 0" }}>{err}</div>}
      {section === "plan" && <CoordinationView client={props.client} code={props.code} />}
      {section === "clashes" && <Clashes {...shared} />}
      {section === "threads" && <Threads {...shared} />}
      {section === "data" && <Data {...shared} overview={o} />}
      {section === "team" && <Team {...shared} overview={o} />}
    </div>
  );
}

interface Shared { b: string; me: string; others: string[]; canWrite: boolean; tl: (k: string) => string; call: <T>(path: string, method: string, body?: unknown) => Promise<T | null>; rev: number; onFocus?: CoordinationProps["onFocus"]; setErr: (s: string) => void }

// ---------------------------------------------------------------- clashes
function Clashes({ b, me, canWrite, tl, call, rev, onFocus }: Shared) {
  const [source, setSource] = useState("auto");
  const [show, setShow] = useState<"open" | "accepted" | "all">("open");
  const [mine, setMine] = useState(false);
  const [asking, setAsking] = useState("");
  const [reason, setReason] = useState("");
  const res = useApi<ClashResult>(`${b}/clashes?source=${source}&r=${rev}`);
  if (!res.data) return <State loading={res.loading} />;
  const list = res.data.clashes.filter((c) => (show === "all" || c.status === show) && (!mine || c.a.discipline === me || c.b.discipline === me));
  const ask = async (c: Clash) => {
    const other = c.a.discipline === me ? c.b : c.a;
    await call("/threads", "POST", { kind: "request", from_discipline: me, to_discipline: other.discipline === me ? c.b.discipline : other.discipline, title: `${c.a.tag} ↔ ${c.b.tag}`, text: `${tl("coord.clash." + c.type)}: ${c.gap_m} m`, level: c.level, point_m: c.point_m });
  };
  return (
    <div>
      <div className="row small" style={{ gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
        <label className="wb-field"><span>{tl("coord.source")}</span><select value={source} onChange={(e) => setSource(e.target.value)}>{["auto", "issued", "working"].map((s) => <option key={s} value={s}>{tl("coord.source." + s)}</option>)}</select></label>
        <label className="wb-field"><span>{tl("coord.show")}</span><select value={show} onChange={(e) => setShow(e.target.value as typeof show)}>{["open", "accepted", "all"].map((s) => <option key={s} value={s}>{tl("coord.status." + s)}</option>)}</select></label>
        <label className="vp-row"><input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} /> {tl("coord.mine")}</label>
      </div>
      <p className="muted small" style={{ margin: "0 0 6px" }}>{Object.entries(res.data.sources).map(([d, s]) => `${d}: ${tl("coord.source." + (s === "issued" ? "issued" : "working"))}`).join(" · ") || tl("coord.nothingDrawn")}</p>
      {list.length === 0 && <div className="state">{tl("coord.noClashes")}</div>}
      <ul className="coord-list">
        {list.map((c) => (
          <li key={c.id} className={"coord-item " + c.status}>
            <div className="row" style={{ justifyContent: "space-between", gap: 6 }}>
              <span><Badge tone={TONE[c.type]}>{tl("coord.clash." + c.type)}</Badge> <span className="mono small">{c.level}</span></span>
              <span className="mono small">{c.gap_m <= 0 ? `${tl("coord.overlap")} ${Math.abs(c.gap_m)} m` : `${c.gap_m} m < ${c.clearance_m} m`}</span>
            </div>
            <div className="small" style={{ margin: "4px 0" }}><Chip id={c.a.discipline} /> <b>{c.a.tag}</b> ({c.a.kind}) ↔ <Chip id={c.b.discipline} /> <b>{c.b.tag}</b> ({c.b.kind})</div>
            {c.status === "accepted" && <p className="small muted" style={{ margin: "0 0 4px" }}>{tl("coord.acceptedBy")} {c.by}: {c.reason}</p>}
            <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
              {onFocus && <button onClick={() => onFocus(c.point_m, c.level, c.a.discipline === me ? c.a.sheet : c.b.sheet)}><Icon name="fit" size={14} /> {tl("coord.go")}</button>}
              {canWrite && c.status === "open" && <button onClick={() => ask(c)}><Icon name="chat" size={14} /> {tl("coord.ask")}</button>}
              {canWrite && c.status === "open" && (asking === c.id
                ? <span className="row" style={{ gap: 4 }}><input autoFocus placeholder={tl("coord.reason")} value={reason} onChange={(e) => setReason(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && reason.trim()) { call(`/clashes/${c.id}`, "PUT", { status: "accepted", reason }); setAsking(""); setReason(""); } }} />
                  <button className="primary" disabled={!reason.trim()} onClick={() => { call(`/clashes/${c.id}`, "PUT", { status: "accepted", reason }); setAsking(""); setReason(""); }}>{tl("coord.accept")}</button></span>
                : <button onClick={() => setAsking(c.id)}><Icon name="check" size={14} /> {tl("coord.accept")}</button>)}
              {canWrite && c.status === "accepted" && <button onClick={() => call(`/clashes/${c.id}`, "PUT", { status: "open" })}>{tl("coord.reopen")}</button>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------- threads
function Threads({ b, me, others, canWrite, tl, call, rev, onFocus }: Shared) {
  const [scope, setScope] = useState<"all" | "mine">("all");
  const [open, setOpen] = useState("");
  const [form, setForm] = useState({ kind: "comment", to: "", title: "", text: "" });
  const list = useApi<Thread[]>(`${b}/threads${scope === "mine" ? `?discipline=${encodeURIComponent(me)}` : ""}${scope === "mine" ? "&" : "?"}r=${rev}`);
  const create = async () => {
    const made = await call<Thread>("/threads", "POST", { kind: form.kind, from_discipline: me, to_discipline: form.to, title: form.title, text: form.text });
    if (made) setForm({ ...form, title: "", text: "" });
  };
  const needsTo = form.kind === "request" || form.kind === "opening";
  return (
    <div>
      {canWrite && me && (
        <div className="coord-form">
          <b>{tl("coord.new")}</b>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>{["comment", "request", "opening"].map((k) => <option key={k} value={k}>{tl("coord.kind." + k)}</option>)}</select>
            {needsTo && <select value={form.to} onChange={(e) => setForm({ ...form, to: e.target.value })}><option value="">{tl("coord.to")}</option>{others.map((d) => <option key={d}>{d}</option>)}</select>}
          </div>
          <input placeholder={tl("coord.title")} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <textarea rows={2} placeholder={tl("coord.text")} value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} />
          <button className="primary" disabled={(!form.title.trim() && !form.text.trim()) || (needsTo && !form.to)} onClick={create}>{tl("coord.send")}</button>
        </div>
      )}
      <label className="wb-field" style={{ margin: "6px 0" }}><span>{tl("coord.show")}</span><select value={scope} onChange={(e) => setScope(e.target.value as typeof scope)}><option value="all">{tl("coord.status.all")}</option><option value="mine">{tl("coord.mine")}</option></select></label>
      {!list.data ? <State loading={list.loading} /> : list.data.length === 0 ? <div className="state">{tl("coord.noThreads")}</div> : (
        <ul className="coord-list">
          {list.data.map((x) => <ThreadCard key={x.id} x={x} open={open === x.id} toggle={() => setOpen(open === x.id ? "" : x.id)} me={me} canWrite={canWrite} tl={tl} call={call} onFocus={onFocus} />)}
        </ul>
      )}
    </div>
  );
}

function ThreadCard({ x, open, toggle, me, canWrite, tl, call, onFocus }: { x: Thread; open: boolean; toggle: () => void; me: string; canWrite: boolean; tl: (k: string) => string; call: Shared["call"]; onFocus?: Shared["onFocus"] }) {
  const [status, setStatus] = useState(x.status);
  const [comment, setComment] = useState("");
  const answer = async () => { await call(`/threads/${x.id}`, "PATCH", { status, comment }); setComment(""); };
  const asked = x.to_discipline === me;
  return (
    <li className={"coord-item " + x.status}>
      <button className="linkbtn coord-head" onClick={toggle} aria-expanded={open}>
        <span><Badge tone={TONE[x.status] ?? "accent"}>{tl("coord.state." + x.status)}</Badge> <span className="small muted">{tl("coord.kind." + x.kind)} · {x.id}</span></span>
        <b>{x.title || x.text.slice(0, 50)}</b>
      </button>
      <div className="small"><Chip id={x.from_discipline} />{x.to_discipline && <> → <Chip id={x.to_discipline} /></>} {asked && x.status === "open" && <Badge tone="warn">{tl("coord.asksYou")}</Badge>}</div>
      {open && (
        <div className="coord-body">
          {x.text && <p className="small" style={{ whiteSpace: "pre-wrap" }}>{x.text}</p>}
          <ol className="coord-history small">{x.history.map((h, i) => <li key={i}><span className="muted">{h.at.replace("T", " ")} · {h.by}</span> <b>{tl("coord.state." + h.status)}</b>{h.comment && i > 0 ? ` — ${h.comment}` : ""}</li>)}</ol>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            {x.point_m && onFocus && <button onClick={() => onFocus(x.point_m!, x.level, x.sheet)}><Icon name="fit" size={14} /> {tl("coord.go")}</button>}
            {canWrite && <>
              <select value={status} onChange={(e) => setStatus(e.target.value)}>{THREAD_STATES[x.kind].map((s) => <option key={s} value={s}>{tl("coord.state." + s)}</option>)}</select>
              <input placeholder={tl("coord.comment")} value={comment} onChange={(e) => setComment(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") answer(); }} />
              <button className="primary" disabled={status === x.status && !comment.trim()} onClick={answer}>{tl("coord.answer")}</button>
              <button onClick={() => { if (window.confirm(tl("coord.confirmDelete"))) call(`/threads/${x.id}`, "DELETE"); }} aria-label={tl("coord.delete")} title={tl("coord.delete")}><Icon name="trash" size={14} /></button>
            </>}
          </div>
        </div>
      )}
    </li>
  );
}

// ---------------------------------------------------------------- data that crosses
function Data({ b, me, others, canWrite, tl, call, rev, overview }: Shared & { overview: CoordOverview }) {
  const list = useApi<{ items: Exchange[]; matrix: CoordOverview["matrix"] }>(`${b}/exchanges?r=${rev}`);
  const [f, setF] = useState({ tag: "", field: "", value: "", unit: "", consumers: "" });
  if (!list.data) return <State loading={list.loading} />;
  const publish = async () => {
    const consumers = f.consumers.split(/[,\s]+/).filter(Boolean);
    const made = await call("/exchanges", "POST", { owner: me, consumers, tag: f.tag, field: f.field, value: isNaN(Number(f.value)) ? f.value : Number(f.value), unit: f.unit });
    if (made) setF({ ...f, value: "" });
  };
  return (
    <div>
      <p className="muted small" style={{ margin: "0 0 6px" }}>{tl("coord.data.help")}</p>
      {list.data.matrix.length > 0 && (
        <table className="coord-matrix"><thead><tr><th>{tl("coord.data.owner")}</th><th>{tl("coord.data.consumer")}</th><th>{tl("coord.state.delivered")}</th><th>{tl("coord.state.pending")}</th><th>{tl("coord.state.outdated")}</th></tr></thead>
          <tbody>{list.data.matrix.map((c) => <tr key={c.owner + c.consumer}><td><Chip id={c.owner} /></td><td><Chip id={c.consumer} /></td><td className="mono">{c.delivered}</td><td className="mono">{c.pending}</td><td className="mono" style={{ color: c.outdated ? "var(--bad)" : undefined }}>{c.outdated}</td></tr>)}</tbody></table>
      )}
      <ul className="coord-list">
        {list.data.items.map((x) => (
          <li key={x.id} className="coord-item">
            <div className="row" style={{ justifyContent: "space-between" }}><span><b className="mono">{x.tag}</b> · {x.field}</span><span className="mono">{String(x.value)} {x.unit} <span className="muted small">v{x.version}</span></span></div>
            <div className="small"><Chip id={x.owner} /> → {x.consumers.map((c) => (
              <span key={c} style={{ marginRight: 6 }}><Chip id={c} /> <Badge tone={x.states[c] === "delivered" ? "ok" : x.states[c] === "outdated" ? "bad" : "warn"}>{tl("coord.state." + x.states[c])}</Badge>{canWrite && c === me && x.states[c] !== "delivered" && <button className="linkbtn" onClick={() => call(`/exchanges/${x.id}/take`, "POST", { discipline: me })}> {tl("coord.take")}</button>}</span>
            ))}</div>
            {canWrite && x.owner === me && <button className="linkbtn small" onClick={() => { if (window.confirm(tl("coord.confirmDelete"))) call(`/exchanges/${x.id}`, "DELETE"); }}>{tl("coord.delete")}</button>}
          </li>
        ))}
      </ul>
      {canWrite && me && (
        <div className="coord-form">
          <b>{tl("coord.data.publish")} ({me})</b>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            <input placeholder={tl("coord.data.tag")} value={f.tag} onChange={(e) => setF({ ...f, tag: e.target.value })} style={{ width: 100 }} />
            <input placeholder={tl("coord.data.field")} value={f.field} onChange={(e) => setF({ ...f, field: e.target.value })} style={{ width: 110 }} />
            <input placeholder={tl("coord.data.value")} value={f.value} onChange={(e) => setF({ ...f, value: e.target.value })} style={{ width: 80 }} />
            <input placeholder={tl("coord.data.unit")} value={f.unit} onChange={(e) => setF({ ...f, unit: e.target.value })} style={{ width: 60 }} />
          </div>
          <input list="coord-others" placeholder={tl("coord.data.consumers")} value={f.consumers} onChange={(e) => setF({ ...f, consumers: e.target.value })} />
          <datalist id="coord-others">{[...others, ...overview.disciplines].map((d) => <option key={d} value={d} />)}</datalist>
          <button className="primary" disabled={!f.tag.trim() || !f.field.trim() || f.value === "" || !f.consumers.trim()} onClick={publish}>{tl("coord.data.send")}</button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- team: issues, members, settings, rules
function Team({ b, me, canWrite, tl, call, rev, overview, setErr }: Shared & { overview: CoordOverview }) {
  const [note, setNote] = useState("");
  const [members, setMembers] = useState<Record<string, string>>(Object.fromEntries(overview.disciplines.map((d) => [d, (overview.members[d] ?? []).join(", ")])));
  const [story, setStory] = useState(String(overview.settings.story_height_m));
  const emit = async () => { const r = await call<{ rev: number; new_clashes: Clash[] }>("/emit", "POST", { discipline: me, note }); if (r) { setNote(""); setErr(r.new_clashes.length ? `${tl("coord.emitted")} ${r.rev}: ${r.new_clashes.length} ${tl("coord.newClashes")}` : ""); } };
  return (
    <div>
      <h4 className="coord-h">{tl("coord.emissions")}</h4>
      {overview.emissions.length === 0 && <p className="muted small">{tl("coord.noEmissions")}</p>}
      <ul className="coord-list">{overview.emissions.map((e) => <li key={e.discipline} className="coord-item"><Chip id={e.discipline} /> <b>R{e.rev}</b> <span className="muted small">{e.at.replace("T", " ")} · {e.by} · {e.elements} {tl("coord.elements")}{e.note ? ` · ${e.note}` : ""}</span></li>)}</ul>
      {canWrite && me && <div className="row" style={{ gap: 6, flexWrap: "wrap", marginTop: 6 }}>
        <input placeholder={tl("coord.emit.note")} value={note} onChange={(e) => setNote(e.target.value)} style={{ flex: 1, minWidth: 140 }} />
        <button className="primary" onClick={emit}><Icon name="upload" size={14} /> {tl("coord.emit")} {me}</button>
      </div>}
      <p className="muted small">{tl("coord.emit.help")}</p>
      <h4 className="coord-h">{tl("coord.members")}</h4>
      <p className="muted small" style={{ margin: "0 0 4px" }}>{tl("coord.members.help")}</p>
      {overview.disciplines.map((d) => <label key={d} className="wb-field" style={{ marginBottom: 4 }}><Chip id={d} /><input disabled={!canWrite} placeholder="ana@empresa.com, luis@empresa.com" value={members[d] ?? ""} onChange={(e) => setMembers({ ...members, [d]: e.target.value })} style={{ flex: 1 }} /></label>)}
      {canWrite && <button onClick={() => call("/members", "PUT", { members: Object.fromEntries(Object.entries(members).map(([d, v]) => [d, v.split(/[,\s]+/).filter(Boolean)])) })}>{tl("coord.save")}</button>}
      <h4 className="coord-h">{tl("coord.story")}</h4>
      <label className="wb-field"><span>{tl("coord.story.label")}</span><input disabled={!canWrite} value={story} onChange={(e) => setStory(e.target.value)} style={{ width: 70 }} /> m
        {canWrite && <button onClick={() => { const v = parseFloat(story.replace(",", ".")); if (v > 0) call("/settings", "PUT", { story_height_m: v }); }}>{tl("coord.save")}</button>}</label>
      <Rules b={b} canWrite={canWrite} tl={tl} rev={rev} call={call} />
    </div>
  );
}

function Rules({ b, canWrite, tl, rev, call }: { b: string; canWrite: boolean; tl: (k: string) => string; rev: number; call: Shared["call"] }) {
  const [scope, setScope] = useState<"project" | "company">("project");
  const view = useApi<RulesView>(scope === "project" ? `${b}/rules?r=${rev}` : `/data/clash-rules?r=${rev}`);
  const [own, setOwn] = useState<Rule[]>([]);
  useEffect(() => { if (view.data) setOwn(view.data.own); }, [view.data]);
  const [msg, setMsg] = useState("");
  const path = scope === "project" ? `${b}/rules` : "/data/clash-rules";
  const send = async (method: string, body?: unknown) => {
    try { await api(path, { method, headers: JSON_HEADERS, body: body === undefined ? undefined : JSON.stringify(body) }); setMsg(""); call("/settings", "GET"); } catch (x) { setMsg(errorText(x)); }
  };
  const set = (i: number, patch: Partial<Rule>) => setOwn(own.map((r, k) => (k === i ? { ...r, ...patch } : r)));
  const list = (v: string | undefined) => (v ?? "").split(/[,\s]+/).filter(Boolean);
  return (
    <div>
      <h4 className="coord-h">{tl("coord.rules")}</h4>
      <div className="row" style={{ gap: 6 }}>
        <select value={scope} onChange={(e) => setScope(e.target.value as typeof scope)}><option value="project">{tl("coord.rules.project")}</option><option value="company">{tl("coord.rules.company")}</option></select>
        <span className="muted small">{tl("coord.rules.help")}</span>
      </div>
      {!view.data ? <State loading={view.loading} /> : <>
        <div style={{ overflowX: "auto" }}><table className="coord-rules"><thead><tr><th>A</th><th>B</th><th>{tl("coord.rules.kindsA")}</th><th>{tl("coord.rules.kindsB")}</th><th>{tl("coord.rules.clearance")}</th><th>{tl("coord.rules.ignore")}</th><th /></tr></thead>
          <tbody>
            {view.data.inherited.map((r, i) => <tr key={"i" + i} className="muted"><td>{r.a ?? "*"}</td><td>{r.b ?? "*"}</td><td>{(r.kinds_a ?? []).join(",")}</td><td>{(r.kinds_b ?? []).join(",")}</td><td className="mono">{r.clearance_m ?? 0}</td><td>{r.ignore ? "✓" : ""}</td><td /></tr>)}
            {own.map((r, i) => (
              <tr key={i}>
                <td><input disabled={!canWrite} value={r.a ?? "*"} onChange={(e) => set(i, { a: e.target.value })} style={{ width: 90 }} /></td><td><input disabled={!canWrite} value={r.b ?? "*"} onChange={(e) => set(i, { b: e.target.value })} style={{ width: 90 }} /></td>
                <td><input disabled={!canWrite} value={(r.kinds_a ?? []).join(",")} onChange={(e) => set(i, { kinds_a: list(e.target.value) })} style={{ width: 60 }} /></td><td><input disabled={!canWrite} value={(r.kinds_b ?? []).join(",")} onChange={(e) => set(i, { kinds_b: list(e.target.value) })} style={{ width: 60 }} /></td>
                <td><input disabled={!canWrite} value={r.clearance_m ?? 0} onChange={(e) => set(i, { clearance_m: parseFloat(e.target.value.replace(",", ".")) || 0 })} style={{ width: 54 }} /></td>
                <td><input type="checkbox" disabled={!canWrite} checked={!!r.ignore} onChange={(e) => set(i, { ignore: e.target.checked })} /></td>
                <td>{canWrite && <button onClick={() => setOwn(own.filter((_, k) => k !== i))} aria-label={tl("coord.delete")}>×</button>}</td>
              </tr>
            ))}
          </tbody></table></div>
        {msg && <div className="alert bad small">{msg}</div>}
        {canWrite && <div className="row" style={{ gap: 6, marginTop: 6 }}><button onClick={() => setOwn([...own, { a: "*", b: "*", clearance_m: 0.3 }])}>+ {tl("coord.rules.add")}</button><button className="primary" onClick={() => send("PUT", { rules: own })}>{tl("coord.save")}</button><button onClick={() => send("DELETE")}>{tl("coord.rules.reset")}</button></div>}
      </>}
    </div>
  );
}
