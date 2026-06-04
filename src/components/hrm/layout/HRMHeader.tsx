"use client";

import { useAuth } from "@/hooks/useAuth";
import GlobalSearchBox from "@/components/layout/GlobalSearchBox";
import ThemeSwitcher from "@/components/layout/ThemeSwitcher";
import { Download, Plus } from "lucide-react";

export default function HRMHeader() {
  const { user } = useAuth();

  return (
    <header className="app-topbar sticky top-0 z-30 border-b px-6 py-3 shadow-sm backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <h1 className="text-lg font-semibold text-slate-950">
            Human Resource Management
          </h1>

          <p className="text-xs capitalize text-slate-500">
            {user?.full_name} - {user?.role}
          </p>
        </div>

        <div className="mx-6 hidden flex-1 xl:block">
          <GlobalSearchBox className="w-full max-w-2xl" />
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <ThemeSwitcher />
          <button className="focus-ring inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white/80 px-4 py-2 text-sm text-slate-700 shadow-sm hover:bg-slate-50">
            <Download size={16} />
            Export
          </button>

          <button className="focus-ring inline-flex items-center gap-2 rounded-lg bg-blue-700 px-4 py-2 text-sm text-white shadow-sm shadow-blue-900/20 hover:bg-blue-800">
            <Plus size={16} />
            Add Employee
          </button>
        </div>
      </div>
    </header>
  );
}
