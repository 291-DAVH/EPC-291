import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { en } from "./dict/en";
import { es } from "./dict/es";

export type Lang = "es" | "en";

const dict = { es, en } as const;

export type Key = keyof (typeof dict)["es"];
type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (k: Key) => string };
const I18n = createContext<Ctx>(null as unknown as Ctx);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    try {
      return (localStorage.getItem("lang") as Lang) || "es";
    } catch {
      return "es";
    }
  });
  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem("lang", lang);
    } catch {
      /* storage unavailable */
    }
  }, [lang]);
  const t = (k: Key) => dict[lang][k] ?? k;
  return <I18n.Provider value={{ lang, setLang, t }}>{children}</I18n.Provider>;
}

export const useI18n = () => useContext(I18n);
