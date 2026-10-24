import { Fragment, ReactNode } from "react";

/** Small, safe Markdown view (headings, lists, quotes, bold, italics, code): nothing is injected as HTML, so text from files can never run. */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|_[^_]+_|`[^`]+`)/g).filter(Boolean).map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**") && p.length > 4) return <b key={i}>{p.slice(2, -2)}</b>;
    if (p.startsWith("_") && p.endsWith("_") && p.length > 2) return <i key={i}>{p.slice(1, -1)}</i>;
    if (p.startsWith("`") && p.endsWith("`") && p.length > 2) return <code key={i}>{p.slice(1, -1)}</code>;
    return <Fragment key={i}>{p}</Fragment>;
  });
}

export function Markdown({ text }: { text: string }) {
  const out: ReactNode[] = [];
  let list: string[] = [];
  const flush = () => {
    if (list.length) out.push(<ul key={"u" + out.length}>{list.map((x, i) => <li key={i}>{inline(x)}</li>)}</ul>);
    list = [];
  };
  for (const line of text.replace(/\r\n/g, "\n").split("\n")) {
    const li = /^\s*[-*]\s+(.*)$/.exec(line);
    if (li) { list.push(li[1]); continue; }
    flush();
    const h = /^(#{1,4})\s+(.*)$/.exec(line);
    if (h) { const L = Math.min(h[1].length + 1, 5); const H = ("h" + L) as "h2"; out.push(<H key={out.length}>{inline(h[2])}</H>); continue; }
    const q = /^>\s?(.*)$/.exec(line);
    if (q) { out.push(<blockquote key={out.length}>{inline(q[1])}</blockquote>); continue; }
    if (line.trim()) out.push(<p key={out.length}>{inline(line)}</p>);
  }
  flush();
  return <div className="md">{out}</div>;
}
