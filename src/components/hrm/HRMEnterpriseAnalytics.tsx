"use client";

import { useEffect, useState } from "react";
import { BarChart3, Briefcase, CalendarDays, GraduationCap, PackageCheck, Users, Wallet } from "lucide-react";
import { api } from "@/services/api";

interface HRMEnterpriseAnalytics {
  headcount: { total: number; active: number; inactive: number };
  leave: { pending_requests: number };
  recruitment: { open_requisitions: number };
  training: { active_courses: number };
  assets: { assigned: number };
  payroll: { runs: number };
}

const cards = [
  { key: "headcount.active", label: "Active Employees", icon: Users, color: "rgba(37, 99, 235, 0.13)" },
  { key: "leave.pending_requests", label: "Pending Leave", icon: CalendarDays, color: "rgba(245, 158, 11, 0.15)" },
  { key: "recruitment.open_requisitions", label: "Open Requisitions", icon: Briefcase, color: "rgba(16, 185, 129, 0.14)" },
  { key: "training.active_courses", label: "Active Courses", icon: GraduationCap, color: "rgba(124, 58, 237, 0.13)" },
  { key: "assets.assigned", label: "Assigned Assets", icon: PackageCheck, color: "rgba(14, 165, 233, 0.13)" },
  { key: "payroll.runs", label: "Payroll Runs", icon: Wallet, color: "rgba(239, 68, 68, 0.11)" },
];

function readMetric(data: HRMEnterpriseAnalytics, path: string) {
  return path.split(".").reduce<unknown>((current, part) => {
    if (current && typeof current === "object" && part in current) {
      return (current as Record<string, unknown>)[part];
    }
    return 0;
  }, data) as number;
}

export default function HRMEnterpriseAnalytics() {
  const [data, setData] = useState<HRMEnterpriseAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<HRMEnterpriseAnalytics>("/api/hrm/enterprise/analytics")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load HRM analytics"));
  }, []);

  if (error) {
    return <div className="rounded-xl border bg-red-50 p-5 text-sm text-red-700">{error}</div>;
  }

  if (!data) {
    return <div className="rounded-xl border bg-white p-5 text-sm text-slate-500">Loading HRM analytics...</div>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Workforce Intelligence</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">HRM Analytics</h1>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
          A management view of HR operating health across workforce, leave, recruitment, learning, assets, and payroll.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => (
          <div key={card.key} className="rounded-2xl border p-5 shadow-sm" style={{ backgroundColor: card.color }}>
            <div className="flex items-center justify-between">
              <div className="rounded-xl bg-white/80 p-2 text-slate-950 shadow-sm">
                <card.icon size={18} />
              </div>
              <BarChart3 size={18} className="text-slate-500" />
            </div>
            <p className="mt-4 text-sm font-medium text-slate-600">{card.label}</p>
            <p className="mt-1 text-3xl font-bold text-slate-950">{readMetric(data, card.key).toLocaleString()}</p>
          </div>
        ))}
      </div>

      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Headcount Health</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {[
            ["Total", data.headcount.total],
            ["Active", data.headcount.active],
            ["Inactive", data.headcount.inactive],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl border bg-slate-50 p-4">
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-1 text-2xl font-semibold text-slate-950">{Number(value).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
