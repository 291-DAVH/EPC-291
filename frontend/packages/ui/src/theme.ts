import { useEffect, useState } from "react";

export function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark" | "">(() => {
    try {
      return (localStorage.getItem("theme") as "light" | "dark") || "";
    } catch {
      return "";
    }
  });
  useEffect(() => {
    const el = document.documentElement;
    if (theme) el.setAttribute("data-theme", theme);
    else el.removeAttribute("data-theme");
    try {
      theme ? localStorage.setItem("theme", theme) : localStorage.removeItem("theme");
    } catch {
      /* storage unavailable */
    }
  }, [theme]);
  const isDark = theme ? theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  return { toggle: () => setTheme(isDark ? "light" : "dark"), isDark };
}
