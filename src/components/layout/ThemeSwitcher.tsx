"use client";

import { Palette } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

export default function ThemeSwitcher() {
  const { mode, theme, templates, setMode, setTheme } = useTheme();

  return (
    <div className="theme-swatch hidden items-center gap-2 rounded-lg px-2 py-1.5 shadow-sm md:flex">
      <Palette size={16} className="text-[var(--brand)]" />
      <select
        value={mode}
        onChange={(event) => setMode(event.target.value === "dark" ? "dark" : "light")}
        className="focus-ring h-8 rounded-md bg-transparent px-1 text-xs font-medium text-[var(--foreground)] outline-none"
        aria-label="Theme mode"
      >
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
      <select
        value={theme}
        onChange={(event) => setTheme(event.target.value as typeof theme)}
        className="focus-ring h-8 rounded-md bg-transparent px-1 text-xs font-medium text-[var(--foreground)] outline-none"
        aria-label="Theme template"
      >
        {templates.map((template) => (
          <option key={template.id} value={template.id}>
            {template.name}
          </option>
        ))}
      </select>
      <div className="flex gap-1">
        {templates.find((template) => template.id === theme)?.swatches.map((color) => (
          <span key={color} className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
        ))}
      </div>
    </div>
  );
}
