import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { I18nProvider, useI18n } from "./i18n";

// The dictionary is not exported: its two blocks are read from the source, so a key added to one language and forgotten in the other is caught here.
const SRC = readFileSync(resolve(process.cwd(), "packages/ui/src/i18n.tsx"), "utf-8");
const START = SRC.indexOf("const dict = {");
const EN_AT = SRC.indexOf("\n  en: {", START);
const END = SRC.indexOf("} as const;", EN_AT);

function block(from: number, to: number): Map<string, string> {
  const out = new Map<string, string>();
  const re = /^\s{4}"([^"]+)":\s*("(?:[^"\\]|\\.)*"),?\s*$/gm;
  for (const m of SRC.slice(from, to).matchAll(re)) out.set(m[1], JSON.parse(m[2]));
  return out;
}
const es = block(START, EN_AT);
const en = block(EN_AT, END);
const placeholders = (s: string) => (s.match(/\{[a-zA-Z0-9_]+\}/g) ?? []).sort();

describe("i18n dictionary", () => {
  it("was read", () => {
    expect(es.size).toBeGreaterThan(500);
  });

  it("has the same keys in Spanish and English", () => {
    const missingEn = [...es.keys()].filter((k) => !en.has(k));
    const missingEs = [...en.keys()].filter((k) => !es.has(k));
    expect({ missingEn, missingEs }).toEqual({ missingEn: [], missingEs: [] });
  });

  it("has no empty text", () => {
    const empty = [...es, ...en].filter(([, v]) => !v.trim()).map(([k]) => k);
    expect(empty).toEqual([]);
  });

  it("uses the same placeholders in both languages", () => {
    const different = [...es.keys()].filter((k) => en.has(k) && placeholders(es.get(k)!).join() !== placeholders(en.get(k)!).join());
    expect(different).toEqual([]);
  });
});

describe("I18nProvider", () => {
  function Probe() {
    const { lang, t, setLang } = useI18n();
    return (
      <button onClick={() => setLang(lang === "es" ? "en" : "es")}>
        {lang}:{t("app.name")}:{t("no.such.key" as never)}
      </button>
    );
  }

  it("starts in Spanish, falls back to the key and switches language", () => {
    localStorage.removeItem("lang");
    const { getByRole } = render(<I18nProvider><Probe /></I18nProvider>);
    const b = getByRole("button");
    expect(b.textContent).toBe(`es:${es.get("app.name")}:no.such.key`);
    expect(document.documentElement.lang).toBe("es");
    b.click();
    return Promise.resolve().then(() => {
      expect(getByRole("button").textContent).toBe(`en:${en.get("app.name")}:no.such.key`);
      expect(localStorage.getItem("lang")).toBe("en");
    });
  });
});
