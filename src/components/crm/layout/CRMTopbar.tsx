// src/components/crm/layout/CRMTopbar.tsx

"use client";

import { Bell, CalendarDays, Plus, Bot } from "lucide-react";
import GlobalSearchBox from "@/components/layout/GlobalSearchBox";
import ThemeSwitcher from "@/components/layout/ThemeSwitcher";

export default function CRMTopbar() {
  return (
    <header className="app-topbar sticky top-0 z-30 flex h-16 items-center justify-between border-b px-6 shadow-sm backdrop-blur-xl">
      <GlobalSearchBox className="w-full max-w-xl" />

      <div className="flex items-center gap-3">
        <ThemeSwitcher />
        <button className="focus-ring rounded-lg border border-slate-200 bg-white/80 p-2 text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-950" aria-label="Create">
          <Plus size={20} />
        </button>
        <button className="focus-ring rounded-lg border border-slate-200 bg-white/80 p-2 text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-950" aria-label="Calendar">
          <CalendarDays size={20} />
        </button>
        <button className="focus-ring rounded-lg border border-slate-200 bg-white/80 p-2 text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-950" aria-label="Assistant">
          <Bot size={20} />
        </button>
        <button className="focus-ring relative rounded-lg border border-slate-200 bg-white/80 p-2 text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-950" aria-label="Notifications">
          <Bell size={20} />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-white" />
        </button>
      </div>
    </header>
  );
}
