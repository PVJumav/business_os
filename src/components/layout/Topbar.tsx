"use client";

import { Bell, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import GlobalSearchBox from "@/components/layout/GlobalSearchBox";
import ThemeSwitcher from "@/components/layout/ThemeSwitcher";
import { appNavItems, filterByRole } from "@/lib/permissions";

export default function Topbar() {
  const { user } = useAuth();
  const pathname = usePathname();
  const mobileNav = filterByRole(appNavItems, user?.role);

  return (
    <header className="app-topbar sticky top-0 z-30 border-b px-4 shadow-sm backdrop-blur-xl lg:px-6">
      <div className="flex h-16 items-center justify-between">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <div className="hidden items-center gap-2 rounded-full border border-blue-100 bg-blue-50/80 px-3 py-1 text-xs font-medium text-blue-800 xl:flex">
            <Sparkles size={14} />
            Command center
          </div>
          <GlobalSearchBox />
        </div>

        <div className="flex items-center gap-3 lg:gap-4">
          <ThemeSwitcher />

          <button className="focus-ring relative rounded-lg border border-slate-200 bg-white/80 p-2 text-slate-600 shadow-sm transition hover:bg-slate-50 hover:text-slate-950" aria-label="Notifications">

            <Bell size={20} />

            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-white"></span>

          </button>

          <div className="flex items-center gap-3 rounded-full border border-slate-200 bg-white/70 py-1 pl-1 pr-3 shadow-sm">

            <div className="brand-mark flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold">
              {(user?.full_name ?? "U").split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase()}
            </div>

            <div className="hidden text-sm sm:block">
              <p className="font-semibold">
                {user?.full_name ?? "User"}
              </p>

              <p className="text-xs capitalize text-slate-500">
                {user?.role ?? "user"}
              </p>
            </div>

          </div>

        </div>
      </div>
      <nav className="flex gap-2 overflow-x-auto pb-3 lg:hidden">
        {mobileNav.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex shrink-0 items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                isActive ? "border-blue-200 bg-blue-50 text-blue-800" : "border-slate-200 bg-white/70 text-slate-600"
              }`}
            >
              <item.icon size={14} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
