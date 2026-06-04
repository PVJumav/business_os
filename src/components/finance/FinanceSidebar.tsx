"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BookOpen, Building2, CreditCard, FileCheck, FileText, FolderKanban, Landmark, Receipt, ShieldCheck, Wallet } from "lucide-react";

const items = [
  { label: "Control Center", href: "/finance", icon: BarChart3 },
  { label: "Ledger", href: "/finance/chart-accounts", icon: BookOpen },
  { label: "Cost Centers", href: "/finance/cost-centers", icon: Building2 },
  { label: "Journals", href: "/finance/journal-entries", icon: FileText },
  { label: "Payables", href: "/finance/bills", icon: CreditCard },
  { label: "Receivables", href: "/finance/invoices", icon: Receipt },
  { label: "Expenses", href: "/finance/expense-claims", icon: Wallet },
  { label: "Budgets", href: "/finance/budgets", icon: BarChart3 },
  { label: "Procurement", href: "/finance/purchase-requests", icon: FileCheck },
  { label: "Bank & Cash", href: "/finance/bank-accounts", icon: Landmark },
  { label: "Tax", href: "/finance/tax-records", icon: ShieldCheck },
  { label: "Assets", href: "/finance/fixed-assets", icon: Building2 },
  { label: "Project Finance", href: "/finance/project-finance", icon: FolderKanban },
  { label: "Approvals", href: "/finance/approvals", icon: FileCheck },
  { label: "Documents", href: "/finance/documents", icon: FileText },
];

export default function FinanceSidebar() {
  const pathname = usePathname();

  return (
    <aside className="app-sidebar hidden border-r p-4 shadow-2xl lg:block">
      <Link href="/" className="mb-6 block rounded-lg border border-white/10 bg-white/5 p-4 transition hover:bg-white/10">
        <h2 className="text-lg font-bold text-white">Business OS</h2>
        <p className="text-sm text-slate-400">Executive dashboard</p>
      </Link>

      <nav className="space-y-1">
        {items.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition ${
                active ? "bg-white text-[var(--brand-strong)] shadow-sm" : "text-[var(--sidebar-muted)] hover:bg-white/8 hover:text-white"
              }`}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
