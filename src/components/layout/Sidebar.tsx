"use client";

import {
  LogOut,
  ShieldCheck,
} from "lucide-react";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { appNavItems, filterByRole } from "@/lib/permissions";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const items = filterByRole(appNavItems, user?.role);

  async function signOut() {
    await logout();
    router.replace("/login");
  }

  return (
    <aside className="app-sidebar hidden w-64 flex-col border-r shadow-2xl lg:flex">

      {/* Logo */}
      <Link
        href="/"
        className="flex h-16 items-center border-b border-white/10 px-6 transition hover:bg-white/5"
      >
        <div className="brand-mark flex h-9 w-9 items-center justify-center rounded-lg text-sm font-black">OS</div>
        <div className="ml-3">
          <h1 className="text-sm font-bold uppercase tracking-wide">Business OS</h1>
          <p className="text-xs text-slate-400">Enterprise cockpit</p>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="space-y-1 p-4">

        {items.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 transition ${
                active
                  ? "bg-white text-[var(--brand-strong)] shadow-sm"
                  : "text-[var(--sidebar-muted)] hover:bg-white/8 hover:text-white"
              }`}
            >
              <item.icon size={18} />
              <span className="text-sm">{item.label}</span>
            </Link>
          );
        })}

      </nav>

      <div className="mt-auto border-t border-white/10 p-4">
        <div className="mb-3 rounded-lg border border-white/10 bg-white/5 p-3">
          <div className="mb-2 flex items-center gap-2 text-xs text-emerald-200">
            <ShieldCheck size={14} />
            Active session
          </div>
          <p className="truncate text-sm font-semibold">{user?.full_name}</p>
          <p className="truncate text-xs capitalize text-[var(--sidebar-muted)]">{user?.role}</p>
        </div>
        <button
          onClick={signOut}
          className="focus-ring flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm text-[var(--sidebar-muted)] transition hover:bg-white/8 hover:text-white"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>

    </aside>
  );
}
