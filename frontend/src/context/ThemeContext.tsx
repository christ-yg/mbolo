import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ThemeContext, type ThemePreference } from "./themeContextValue";
const storageKey = "mbolo-theme";

function readPreference(): ThemePreference {
  const stored = window.localStorage.getItem(storageKey);
  return stored === "light" || stored === "dark" ? stored : "system";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, updatePreference] = useState<ThemePreference>(readPreference);
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const resolvedTheme = preference === "system" ? (systemDark ? "dark" : "light") : preference;

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const sync = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  const setPreference = useCallback((next: ThemePreference) => {
    updatePreference(next);
    if (next === "system") window.localStorage.removeItem(storageKey);
    else window.localStorage.setItem(storageKey, next);
  }, []);

  const value = useMemo(
    () => ({ preference, resolvedTheme, setPreference }),
    [preference, resolvedTheme, setPreference],
  );
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
