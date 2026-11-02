import { Key } from "./i18n";

/** What a file is called for people: its kind of document and what it is about ("Single-line diagram (SLD) · TGBT"); a name that is not of a known kind is shown as it is. */
export const docName = (x: { name: string; doc_type?: string; subject?: string }, t: (k: Key) => string): string =>
  !x.doc_type || x.doc_type === "other" ? x.name : `${t(("u.d.type." + x.doc_type) as Key)} · ${x.subject}`;
