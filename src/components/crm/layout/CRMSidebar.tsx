"use client";

import Link from "next/link";
import {
  LogOut,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { crmNavItems, filterByRole } from "@/lib/permissions";


export default function CRMSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const menuItems = filterByRole(crmNavItems, user?.role);

  async function signOut() {
    await logout();
    router.replace("/login");
  }

  return (
    <aside className="app-sidebar hidden h-screen w-72 flex-col border-r shadow-2xl lg:flex">
      {/* Logo */}
      <Link
        href="/"
        className="flex h-16 items-center border-b border-white/10 px-6 transition hover:bg-white/5"
      >
        <div className="brand-mark flex h-9 w-9 items-center justify-center rounded-lg text-sm font-black">OS</div>
        <div className="ml-3">
          <h1 className="text-sm font-bold uppercase tracking-wide text-white">Business OS</h1>
          <p className="text-xs text-slate-400">CRM workspace</p>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <li key={item.label}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition ${
                    isActive ? "bg-white text-[var(--brand-strong)] shadow-sm" : "text-[var(--sidebar-muted)] hover:bg-white/8 hover:text-white"
                  }`}
                >
                  <Icon size={20} />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="mb-3 rounded-lg border border-white/10 bg-white/5 p-3">
          <p className="truncate text-sm font-semibold text-white">{user?.full_name}</p>
          <p className="truncate text-xs capitalize text-[var(--sidebar-muted)]">{user?.role}</p>
        </div>
        <button
          onClick={signOut}
          className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm text-[var(--sidebar-muted)] transition hover:bg-white/8 hover:text-white"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
}
