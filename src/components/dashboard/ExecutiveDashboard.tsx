"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  Building2,
  CreditCard,
  FolderKanban,
  ShieldCheck,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/services/api";

interface ExecutiveDashboardData {
  kpis: Record<string, number>;
  finance: Record<string, number>;
  workload: Record<string, number>;
  departments: Array<{ name: string; employees: number; open_work: number; href: string }>;
  pipeline_by_stage: Array<{ name: string; count: number }>;
  revenue_by_status: Array<{ name: string; count: number }>;
  drilldowns: Array<{ label: string; href: string; value: number }>;
}

function formatMoney(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function formatLabel(value: unknown) {
  return String(value ?? "").replaceAll("_", " ");
}

export default function ExecutiveDashboard() {
  const [data, setData] = useState<ExecutiveDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ExecutiveDashboardData>("/api/analytics/executive")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load executive dashboard"))
      .finally(() => setIsLoading(false));
  }, []);

  const revenueChart = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Pipeline", value: data.finance.pipeline_value },
      { name: "Deal Revenue", value: data.finance.deal_revenue },
      { name: "Invoiced", value: data.finance.invoice_amount },
      { name: "Paid", value: data.finance.paid_amount },
      { name: "Outstanding", value: data.finance.outstanding_debt },
    ];
  }, [data]);

  if (isLoading) {
    return <div className="glass-panel rounded-lg p-6 text-sm text-slate-500">Loading executive operating dashboard...</div>;
  }

  if (error || !data) {
    return <div className="rounded-lg border bg-red-50 p-6 text-sm text-red-700">{error ?? "Dashboard unavailable"}</div>;
  }

  const kpiCards = [
    { label: "Active Employees", value: data.kpis.employees, icon: Users, href: "/hrm", note: "People currently active" },
    { label: "Accounts", value: data.kpis.accounts, icon: Building2, href: "/crm/accounts", note: "Customers and prospects" },
    { label: "Open Pipeline", value: data.kpis.opportunities, icon: TrendingUp, href: "/crm/opportunities", note: `Value ${formatMoney(data.finance.pipeline_value)}` },
    { label: "Deal GP", value: formatMoney(data.finance.deal_gp), icon: Wallet, href: "/crm/deals", note: `Target ${data.finance.target_attainment}% achieved` },
    { label: "Outstanding Debt", value: formatMoney(data.finance.outstanding_debt), icon: CreditCard, href: "/crm/invoices", note: "Invoices not yet collected" },
    { label: "Open Workload", value: data.workload.open_projects + data.workload.open_tickets + data.workload.pending_tenders, icon: Activity, href: "/analytics", note: "Projects, tickets and tenders" },
  ];

  return (
    <div className="space-y-6">
      <section
        className="module-hero overflow-visible rounded-lg p-6"
        style={{
          background:
            "linear-gradient(135deg, var(--brand-strong), var(--brand))",
        }}
      >
        <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div className="text-white">
            <p className="text-sm font-medium uppercase text-[var(--gold-soft)]">BusinessOS Version 5.5</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">Executive Operating Dashboard</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-white/82">
              One connected view of sales, revenue, finance, people, departments, delivery, SLAs, tenders, tickets, benefits, payroll, and operational workload.
            </p>
          </div>

          <div className="rounded-lg border border-white/20 bg-white/10 px-4 py-3 text-sm text-white/88 backdrop-blur">
            Use the top search for records. Use page filters inside each module.
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {kpiCards.map((card) => (
          <Link
            key={card.label}
            href={card.href}
            className="soft-panel interactive-lift rounded-lg p-5"
            style={{ backgroundColor: "rgba(255, 255, 255, 0.86)" }}
          >
            <div className="flex items-center justify-between">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[var(--brand)] text-white">
                <card.icon size={20} />
              </div>
              <span className="text-xs font-medium text-slate-500">Drill down</span>
            </div>
            <p className="mt-4 text-sm text-slate-500">{card.label}</p>
            <p className="mt-1 text-3xl font-semibold text-slate-950">{card.value}</p>
            <p className="mt-1 text-xs text-slate-500">{card.note}</p>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <section className="soft-panel rounded-lg p-5">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Revenue and Cash Position</h2>
              <p className="text-sm text-slate-500">Pipeline, closed revenue, invoicing, payments and debt.</p>
            </div>
            <BarChart3 size={20} className="text-slate-500" />
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => formatMoney(Number(value))} />
                <Area type="monotone" dataKey="value" stroke="var(--brand)" fill="var(--gold-soft)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="soft-panel rounded-lg p-5">
          <h2 className="text-lg font-semibold text-slate-900">Automation Control Points</h2>
          <p className="mt-1 text-sm text-slate-500">Use these queues to reduce manual work across the organization.</p>
          <div className="mt-5 space-y-3">
            <Queue label="Pending tenders" value={data.workload.pending_tenders} href="/crm/tenders" />
            <Queue label="Open projects" value={data.workload.open_projects} href="/crm/pmo-projects" />
            <Queue label="Active SLAs" value={data.workload.active_slas} href="/crm/sla-assignments" />
            <Queue label="Open tickets" value={data.workload.open_tickets} href="/crm/customer-tickets" />
            <Queue label="Pending leave approvals" value={data.workload.pending_leave} href="/hrm/leave" />
            <Queue label="Pending payroll" value={data.workload.pending_payroll} href="/hrm/payroll" />
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="soft-panel rounded-lg p-5">
          <h2 className="text-lg font-semibold text-slate-900">Pipeline by Stage</h2>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.pipeline_by_stage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tickFormatter={(value) => String(value).replace("Stage ", "S")} />
                <YAxis />
                <Tooltip labelFormatter={formatLabel} />
                <Bar dataKey="count" fill="var(--brand)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="soft-panel rounded-lg p-5">
          <h2 className="text-lg font-semibold text-slate-900">Department Operating Map</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {data.departments.map((department) => (
              <Link key={department.name} href={department.href} className="interactive-lift rounded-lg border border-slate-200/80 bg-white/66 p-4">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-slate-900">{department.name}</p>
                  <ShieldCheck size={16} className="text-slate-500" />
                </div>
                <p className="mt-2 text-sm text-slate-600">{department.employees} employees</p>
                <p className="mt-1 text-sm text-slate-600">{department.open_work} open work items</p>
              </Link>
            ))}
          </div>
        </section>
      </div>

      <section className="soft-panel rounded-lg p-5">
        <h2 className="text-lg font-semibold text-slate-900">Entity Drilldowns</h2>
        <p className="mt-1 text-sm text-slate-500">Every card leads to the operational records behind the number.</p>
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          {data.drilldowns.map((item) => (
            <Link key={item.label} href={item.href} className="interactive-lift rounded-lg border border-slate-200/80 bg-white/66 p-4">
              <div className="flex items-center gap-2 text-slate-600">
                <FolderKanban size={16} />
                <span className="text-sm">{item.label}</span>
              </div>
              <p className="mt-3 text-2xl font-semibold text-slate-950">{formatMoney(item.value)}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function Queue({ label, value, href }: { label: string; value: number; href: string }) {
  return (
    <Link href={href} className="interactive-lift flex items-center justify-between rounded-lg border border-slate-200/80 bg-white/66 px-4 py-3">
      <span className="text-sm text-slate-700">{label}</span>
      <span className="rounded-full bg-[var(--brand)] px-3 py-1 text-sm font-semibold text-white">{value}</span>
    </Link>
  );
}
