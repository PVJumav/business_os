"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CheckCircle2, DollarSign, TrendingUp, Users } from "lucide-react";
import { api } from "@/services/api";

type Summary = Record<string, number>;

export default function KPICards() {
  const [summary, setSummary] = useState<Summary>({});

  useEffect(() => {
    api.get<Summary>("/api/analytics/summary").then(setSummary).catch(() => setSummary({}));
  }, []);

  const cards = [
    {
      title: "Pipeline",
      value: summary["crm.opportunities"] ?? 0,
      note: "Open sales opportunities",
      href: "/crm/opportunities",
      icon: TrendingUp,
    },
    {
      title: "Leads",
      value: summary["crm.leads"] ?? 0,
      note: "Prospects captured",
      href: "/crm/leads",
      icon: Users,
    },
    {
      title: "Quotes",
      value: summary["crm.quotes"] ?? 0,
      note: "Customer quotations",
      href: "/crm/quotes",
      icon: DollarSign,
    },
    {
      title: "Employees",
      value: summary["hrm.employees"] ?? 0,
      note: "Active employee records",
      href: "/hrm/employees",
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="grid gap-5 md:grid-cols-4">
      {cards.map((item) => (
        <Link
          href={item.href}
          key={item.title}
          className="soft-panel interactive-lift rounded-lg p-5"
        >
          <div className="mb-4 flex items-center justify-between">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[var(--brand-soft)] text-[var(--brand)]">
              <item.icon size={20} />
            </div>
            <span className="text-xs font-medium text-slate-500">View details</span>
          </div>

          <p className="text-sm text-slate-500">{item.title}</p>
          <h3 className="mt-1 text-2xl font-bold">{item.value.toLocaleString()}</h3>
          <p className="mt-1 text-xs text-slate-500">{item.note}</p>
        </Link>
      ))}
    </div>
  );
}
