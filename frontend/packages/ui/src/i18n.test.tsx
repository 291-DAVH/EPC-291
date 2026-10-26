import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { en as enDict } from "./dict/en";
import { es as esDict } from "./dict/es";
import { I18nProvider, useI18n } from "./i18n";

// A key added to one language and forgotten in the other is caught here.
const es = new Map<string, string>(Object.entries(esDict));
const en = new Map<string, string>(Object.entries(enDict));
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
