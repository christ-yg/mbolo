import { createContext, useContext } from "react";

export type ThemePreference = "light" | "dark" | "system";

export interface ThemeContextValue {
  preference: ThemePreference;
  resolvedTheme: "light" | "dark";
  setPreference: (preference: ThemePreference) => void;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (value === null) {
    throw new Error("useTheme doit être utilisé dans ThemeProvider.");
  }
  return value;
}
