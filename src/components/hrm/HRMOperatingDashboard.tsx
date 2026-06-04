"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Briefcase,
  CalendarDays,
  CheckCircle2,
  Clock,
  GitBranch,
  GraduationCap,
  PackageCheck,
  ShieldCheck,
  Users,
  Wallet,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/services/api";

interface HRMOverview {
  company_profile: {
    name: string;
    structure: string[];
    departments: string[];
  };
  kpis: Record<string, number>;
  alerts: Array<{ label: string; value: number; severity: string; href: string }>;
  processes: Array<{ name: string; steps: string[]; href: string; open_items: number }>;
  department_distribution: Array<{ name: string; employees: number }>;
}

interface HRMEnterpriseSummary {
  headcount: { total: number; active: number; inactive: number };
  leave: { pending_requests: number };
  recruitment: { open_requisitions: number };
  training: { active_courses: number };
  assets: { assigned: number };
  payroll: { runs: number };
}

const enterpriseModules = [
  { label: "Organization", href: "/hrm/organization", icon: GitBranch, description: "Companies, branches, cost centers, grades, contracts, and emergency contacts." },
  { label: "Leave", href: "/hrm/leave", icon: CalendarDays, description: "Policies, balances, requests, approvals, accrual, and blackout controls." },
  { label: "Attendance", href: "/hrm/attendance", icon: Clock, description: "Shifts, attendance logs, overtime, holidays, approvals, and locked periods." },
  { label: "Payroll", href: "/hrm/payroll", icon: Wallet, description: "Salary structures, components, payroll runs, payslips, approvals, and adjustments." },
  { label: "Recruitment", href: "/hrm/recruitment", icon: Briefcase, description: "Requisitions, openings, candidates, interviews, feedback, and offers." },
  { label: "Performance", href: "/hrm/performance", icon: BarChart3, description: "Goals, KPIs, cycles, competencies, reviews, and improvement plans." },
  { label: "Training", href: "/hrm/training", icon: GraduationCap, description: "Courses, sessions, certifications, expiry tracking, and mandatory policies." },
  { label: "Assets & Exit", href: "/hrm/assets", icon: PackageCheck, description: "Assets, assignments, clearance, exits, terminations, and approvals." },
  { label: "Access & Audit", href: "/hrm/security", icon: ShieldCheck, description: "Roles, permissions, user links, manager visibility, and audit trails." },
];

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function formatNumber(value: number | string | undefined) {
  if (typeof value === "string") return value;
  return Number(value ?? 0).toLocaleString();
}

function statusTone(severity: string) {
  if (severity === "good") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (severity === "critical" || severity === "high") return "border-rose-200 bg-rose-50 text-rose-700";
  return "border-amber-200 bg-amber-50 text-amber-700";
}

export default function HRMOperatingDashboard() {
  const [data, setData] = useState<HRMOverview | null>(null);
  const [enterprise, setEnterprise] = useState<HRMEnterpriseSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<HRMOverview>("/api/hrm/overview"),
      api.get<HRMEnterpriseSummary>("/api/hrm/enterprise/analytics").catch(() => null),
    ])
      .then(([overview, enterpriseSummary]) => {
        setData(overview);
        setEnterprise(enterpriseSummary);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load HRM dashboard"))
      .finally(() => setLoading(false));
  }, []);

  const kpis = useMemo(() => {
    if (!data) return [];
    return [
      { label: "Active Employees", value: data.kpis.active_employees, href: "/hrm/employees", icon: Users },
      { label: "Data Quality", value: `${data.kpis.data_quality_score}%`, href: "/hrm/employees", icon: ShieldCheck },
      { label: "Open Positions", value: data.kpis.open_positions, href: "/hrm/positions", icon: GitBranch },
      { label: "Recruitment", value: data.kpis.open_recruitment, href: "/hrm/recruitment", icon: Briefcase },
      { label: "Onboarding", value: data.kpis.pending_onboarding, href: "/hrm/onboarding", icon: CheckCircle2 },
      { label: "Pending Leave", value: data.kpis.pending_leave, href: "/hrm/leave", icon: CalendarDays },
    ];
  }, [data]);

  const operatingSummary = useMemo(() => {
    if (!enterprise) return [];
    return [
      ["Headcount", enterprise.headcount.active, "/hrm/employees"],
      ["Pending Leave", enterprise.leave.pending_requests, "/hrm/leave"],
      ["Open Requisitions", enterprise.recruitment.open_requisitions, "/hrm/recruitment"],
      ["Training Courses", enterprise.training.active_courses, "/hrm/training"],
      ["Assigned Assets", enterprise.assets.assigned, "/hrm/assets"],
      ["Payroll Runs", enterprise.payroll.runs, "/hrm/payroll"],
    ] as const;
  }, [enterprise]);

  if (loading) {
    return <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">Loading HRM dashboard...</div>;
  }

  if (error || !data) {
    return <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">{error ?? "HRM dashboard unavailable"}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">BusinessOS HRM v5.5</p>
            <div className="mt-3 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950">HRM Control Center</h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                  A single operating view for staff records, organization structure, recruitment, leave, payroll, compliance, performance, training, and offboarding.
                </p>
              </div>
              <Link href="/hrm/employees" className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800">
                Open Employees
                <ArrowRight size={16} />
              </Link>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              {data.company_profile.departments.slice(0, 9).map((department) => (
                <span key={department} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                  {department}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Company Structure</p>
            <div className="mt-4 space-y-2">
              {data.company_profile.structure.slice(0, 7).map((level, index) => (
                <div key={level} className="flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs font-semibold text-slate-600 ring-1 ring-slate-200">
                    {index + 1}
                  </span>
                  <span className="text-sm text-slate-700">{level}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
        {kpis.map((item) => (
          <Link key={item.label} href={item.href} className="group rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-slate-700">
                <item.icon size={18} />
              </span>
              <ArrowRight size={16} className="text-slate-400 transition group-hover:text-blue-700" />
            </div>
            <p className="mt-4 text-xs font-medium uppercase tracking-wide text-slate-500">{item.label}</p>
            <p className="mt-1 text-3xl font-semibold text-slate-950">{formatNumber(item.value)}</p>
          </Link>
        ))}
      </section>

      {operatingSummary.length > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
            {operatingSummary.map(([label, value, href]) => (
              <Link key={label} href={href} className="rounded-lg px-3 py-3 transition hover:bg-slate-50">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
                <p className="mt-1 text-xl font-semibold text-slate-950">{formatNumber(value)}</p>
              </Link>
            ))}
          </div>
        </section>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Workspaces</h2>
              <p className="text-sm text-slate-500">Core HR modules, grouped as practical operating areas.</p>
            </div>
            <Link href="/hrm/analytics" className="text-sm font-medium text-blue-700 hover:text-blue-900">Analytics</Link>
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {enterpriseModules.map((module) => (
              <Link key={module.href} href={module.href} className="group rounded-lg border border-slate-200 bg-white p-4 transition hover:border-blue-200 hover:bg-blue-50/35">
                <div className="flex items-start gap-3">
                  <span className="rounded-lg bg-slate-100 p-2 text-slate-700 group-hover:bg-white group-hover:text-blue-700">
                    <module.icon size={18} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold text-slate-950">{module.label}</p>
                      <ArrowRight size={15} className="shrink-0 text-slate-400 group-hover:text-blue-700" />
                    </div>
                    <p className="mt-1 text-sm leading-5 text-slate-600">{module.description}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Attention</h2>
              <p className="text-sm text-slate-500">Items that affect data quality or workflow readiness.</p>
            </div>
            <ShieldCheck size={20} className="text-slate-400" />
          </div>
          <div className="space-y-2">
            {data.alerts.map((alert) => (
              <Link key={alert.label} href={alert.href} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-3 transition hover:bg-slate-50">
                <div className="flex min-w-0 items-center gap-3">
                  {alert.severity === "good" ? <CheckCircle2 size={18} className="shrink-0 text-emerald-600" /> : <AlertTriangle size={18} className="shrink-0 text-amber-600" />}
                  <span className="truncate text-sm text-slate-700">{alert.label}</span>
                </div>
                <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${statusTone(alert.severity)}`}>{alert.value}</span>
              </Link>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Workflow Flow</h2>
              <p className="text-sm text-slate-500">Process queues connected to their operational modules.</p>
            </div>
            <GitBranch size={20} className="text-slate-400" />
          </div>
          <div className="space-y-3">
            {data.processes.map((process) => (
              <Link key={process.name} href={process.href} className="block rounded-lg border border-slate-200 p-4 transition hover:border-blue-200 hover:bg-blue-50/35">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-950">{process.name}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {process.steps.map((step) => (
                        <span key={step} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                          {step}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span className="rounded-full bg-slate-950 px-3 py-1 text-sm font-semibold text-white">{process.open_items}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <Link href="/hrm/departments" className="block rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-blue-200 hover:shadow-md">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Department Distribution</h2>
              <p className="text-sm text-slate-500">Headcount concentration by department.</p>
            </div>
            <BarChart3 size={20} className="text-slate-400" />
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.department_distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.32)" />
                <XAxis dataKey="name" tickFormatter={formatLabel} tick={{ fill: "#64748b", fontSize: 12 }} />
                <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                <Tooltip cursor={{ fill: "rgba(37, 99, 235, 0.06)" }} />
                <Bar dataKey="employees" fill="#2563eb" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Link>
      </div>
    </div>
  );
}
