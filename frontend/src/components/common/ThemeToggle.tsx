import { useTheme, type ThemePreference } from "../../context/themeContextValue";

import "./ThemeToggle.css";

const labels: Record<ThemePreference, string> = {
  light: "Mode clair",
  dark: "Mode sombre",
  system: "Thème du système",
};

export function ThemeToggle() {
  const { preference, resolvedTheme, setPreference } = useTheme();
  const next: ThemePreference = preference === "system" ? "light" : preference === "light" ? "dark" : "system";

  return (
    <button
      type="button"
      className="theme-toggle"
      aria-label={`${labels[preference]}. Changer l’apparence.`}
      title={`${labels[preference]} · Cliquer pour changer`}
      onClick={() => setPreference(next)}
    >
      <span className="theme-toggle__halo" aria-hidden="true" />
      <span className="theme-toggle__icon" aria-hidden="true">
        {preference === "system" ? "◐" : resolvedTheme === "dark" ? "☾" : "☀"}
      </span>
      <span className="theme-toggle__label">{labels[preference]}</span>
    </button>
  );
}
