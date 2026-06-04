"use client";

import { useCallback, useEffect, useState } from "react";

export type ThemeMode = "light" | "dark";
export type ThemeTemplate = "forest" | "canopy" | "savanna";

export const themeTemplates: Array<{ id: ThemeTemplate; name: string; description: string; swatches: string[] }> = [
  { id: "forest", name: "Forest", description: "Jungle green, antique gold, and warm brown.", swatches: ["#145a38", "#c5962e", "#6b4b2a"] },
  { id: "canopy", name: "Canopy", description: "Brighter green with softer gold surfaces.", swatches: ["#1f6b43", "#b58b23", "#72502d"] },
  { id: "savanna", name: "Savanna", description: "Earth brown foundation with olive and gold accents.", swatches: ["#496b2e", "#d19a2a", "#7a4f28"] },
];

export interface ThemeState {
  mode: ThemeMode;
  theme: ThemeTemplate;
  templates: typeof themeTemplates;
  setMode: (mode: ThemeMode) => void;
  setTheme: (theme: ThemeTemplate) => void;
  toggleTheme: () => void;
}

function applyTheme(theme: ThemeTemplate, mode: ThemeMode) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.themeTemplate = theme;
  document.documentElement.dataset.themeMode = mode;
}

export function useThemeStore(): ThemeState {
  const [mode, setModeState] = useState<ThemeMode>("light");
  const [theme, setThemeState] = useState<ThemeTemplate>("forest");

  useEffect(() => {
    const saved = window.localStorage.getItem("business-os-theme") as ThemeTemplate | null;
    const savedMode = window.localStorage.getItem("business-os-theme-mode") as ThemeMode | null;
    const next: ThemeTemplate = themeTemplates.some((template) => template.id === saved) ? (saved as ThemeTemplate) : "forest";
    const nextMode: ThemeMode = savedMode === "dark" ? "dark" : "light";
    setThemeState(next);
    setModeState(nextMode);
    applyTheme(next, nextMode);
  }, []);

  const setMode = useCallback((next: ThemeMode) => {
    setModeState(next);
    applyTheme(theme, next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("business-os-theme-mode", next);
    }
  }, [theme]);

  const setTheme = useCallback((next: ThemeTemplate) => {
    setThemeState(next);
    applyTheme(next, mode);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("business-os-theme", next);
    }
  }, [mode]);

  const toggleTheme = useCallback(() => {
    setTheme(theme === "forest" ? "canopy" : theme === "canopy" ? "savanna" : "forest");
  }, [setTheme, theme]);

  return { mode, theme, templates: themeTemplates, setMode, setTheme, toggleTheme };
}
