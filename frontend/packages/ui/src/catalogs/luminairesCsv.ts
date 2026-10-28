import type { Luminaire } from "./LuminairesEditor";

/** Luminaires from a spreadsheet: text copied from it (tabs) or saved as CSV (commas or semicolons), with a first row that names the columns. */
export const COLUMNS = ["id", "name_es", "name_en", "kind", "lamps", "lamp_flux_lm", "power_w", "power_factor", "group"] as const;

const ID = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/;

function splitLine(line: string, sep: string): string[] {
  const cells: string[] = [];
  let cell = "", quoted = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (quoted) {
      if (ch === '"' && line[i + 1] === '"') { cell += '"'; i++; } else if (ch === '"') quoted = false; else cell += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === sep) { cells.push(cell.trim()); cell = ""; } else cell += ch;
  }
  cells.push(cell.trim());
  return cells;
}

const separatorOf = (header: string): string => ([",", ";", "\t"].map((s) => [s, header.split(s).length] as const).sort((a, b) => b[1] - a[1])[0][0]);

const number = (text: string): number | undefined => {
  if (text === "") return undefined;
  const n = Number(text.replace(",", "."));
  return Number.isFinite(n) ? n : NaN;
};

export interface Imported { entries: Record<string, Luminaire>; errors: string[] }

/** The luminaires of the text and, for each row that cannot be used, a message that says which row and what to correct. Rows that can be used are returned even when others are not. */
export function parseLuminaires(text: string): Imported {
  const lines = text.replace(/^﻿/, "").split(/\r?\n/).filter((l) => l.trim() !== "");
  if (!lines.length) return { entries: {}, errors: ["empty"] };
  const sep = separatorOf(lines[0]);
  const header = splitLine(lines[0], sep).map((h) => h.toLowerCase());
  const missing = ["id", "name_es", "name_en", "lamp_flux_lm"].filter((c) => !header.includes(c));
  if (missing.length) return { entries: {}, errors: [`columns: ${missing.join(", ")}`] };
  const at = (cells: string[], col: string) => cells[header.indexOf(col)]?.trim() ?? "";
  const entries: Record<string, Luminaire> = {}, errors: string[] = [];
  lines.slice(1).forEach((line, n) => {
    const cells = splitLine(line, sep), row = n + 2;
    const id = at(cells, "id");
    const [lamps, flux, watts, pf] = ["lamps", "lamp_flux_lm", "power_w", "power_factor"].map((c) => number(at(cells, c)));
    const problem = !ID.test(id) ? "id" : !at(cells, "name_es") || !at(cells, "name_en") ? "name_es / name_en"
      : flux === undefined || Number.isNaN(flux) || flux <= 0 ? "lamp_flux_lm" : lamps !== undefined && (Number.isNaN(lamps) || lamps < 1 || !Number.isInteger(lamps)) ? "lamps"
      : watts !== undefined && (Number.isNaN(watts) || watts < 0) ? "power_w" : pf !== undefined && (Number.isNaN(pf) || pf <= 0 || pf > 1) ? "power_factor" : entries[id] ? "id (repeated)" : "";
    if (problem) { errors.push(`${row}: ${problem}`); return; }
    const kind = at(cells, "kind").toLowerCase() === "exterior" ? "exterior" : "interior";
    const group = at(cells, "group");
    entries[id] = { name: { es: at(cells, "name_es"), en: at(cells, "name_en") }, kind, lamps: lamps ?? 1, lamp_flux_lm: flux as number, power_w: watts ?? null, ...(pf !== undefined ? { power_factor: pf } : {}), ...(group ? { group } : {}), illustrative: false };
  });
  return { entries, errors };
}
