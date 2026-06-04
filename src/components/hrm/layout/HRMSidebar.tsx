"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { filterByRole, hrmNavItems } from "@/lib/permissions";

export default function HRMSidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const links = filterByRole(hrmNavItems, user?.role);

  return (
    <aside className="app-sidebar hidden border-r p-4 shadow-2xl lg:block">
      <Link href="/" className="mb-6 block rounded-lg border border-white/10 bg-white/5 p-4 transition hover:bg-white/10">
        <h2 className="text-lg font-bold text-white">Business OS</h2>
        <p className="text-sm text-slate-400">
          Executive dashboard
        </p>
      </Link>

      <nav className="space-y-1">
        {links.map((link) => {
          const isActive = pathname === link.href || (link.href !== "/hrm" && pathname.startsWith(`${link.href}/`));

          return (
            <Link
              key={link.label}
              href={link.href}
              className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition ${
                isActive
                  ? "bg-white text-[var(--brand-strong)] shadow-sm"
                  : "text-[var(--sidebar-muted)] hover:bg-white/8 hover:text-white"
              }`}
            >
              <link.icon className="h-5 w-5" />
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
