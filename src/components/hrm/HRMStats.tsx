"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/services/api";

type Summary = Record<string, number>;

export default function HRMStats() {
  const [summary, setSummary] = useState<Summary>({});

  useEffect(() => {
    api.get<Summary>("/api/analytics/summary").then(setSummary).catch(() => setSummary({}));
  }, []);

  const cards = [
    { label: "Employees", value: summary["hrm.employees"] ?? 0, href: "/hrm/employees" },
    { label: "Departments", value: summary["hrm.departments"] ?? 0, href: "/hrm/departments" },
    { label: "Payroll", value: summary["hrm.payroll"] ?? 0, href: "/hrm/payroll" },
    { label: "Leave", value: summary["hrm.leave"] ?? 0, href: "/hrm/leave" },
  ];

  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="text-xl font-semibold">HRM Summary</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Click a card to drill into the live HRM records behind the metric.
      </p>
      <div className="mt-5 grid gap-3 md:grid-cols-4">
        {cards.map((card) => (
          <Link key={card.label} href={card.href} className="rounded-xl border bg-white p-4 hover:shadow-sm">
            <p className="text-sm text-slate-500">{card.label}</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{card.value.toLocaleString()}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
