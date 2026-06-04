"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, BadgeCheck, CalendarClock, ClipboardList, FileCheck2, FolderKanban, Handshake, Layers3, LineChart, ReceiptText, ShieldCheck, TicketCheck, TimerReset } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/services/api";

interface ProjectAnalytics {
  projects: number;
  active_projects: number;
  completed_projects: number;
  total_budget: number;
  total_cost: number;
  profitability_proxy: number;
  open_sla_tickets: number;
  breached_sla_tickets: number;
  licenses_expiring: number;
  resource_utilization_percent?: number;
  sla_compliance_percent?: number;
  license_consumption_percent?: number;
  invoice_lifecycle_total?: number;
}

const workspaceLinks = [
  { label: "Projects", href: "/projects/projects", icon: FolderKanban, note: "Implementation and internal delivery" },
  { label: "Tasks", href: "/projects/tasks", icon: ClipboardList, note: "Assignments, due dates and effort" },
  { label: "Milestones", href: "/projects/milestones", icon: BadgeCheck, note: "Acceptance, billing and closure" },
  { label: "Deliverables", href: "/projects/deliverables", icon: FileCheck2, note: "Scope outputs and customer acceptance" },
  { label: "Timesheets", href: "/projects/timesheets", icon: TimerReset, note: "Billable effort and utilization" },
  { label: "Risks", href: "/projects/risks", icon: AlertTriangle, note: "Risk, issue and mitigation control" },
  { label: "SLAs", href: "/projects/slas", icon: ShieldCheck, note: "Service agreements and tiers" },
  { label: "SLA Tickets", href: "/projects/sla-tickets", icon: TicketCheck, note: "Incidents, breaches and escalations" },
  { label: "Licenses", href: "/projects/licenses", icon: CalendarClock, note: "Expiry and renewal tracking" },
  { label: "Invoicing", href: "/projects/invoices", icon: ReceiptText, note: "Lifecycle before Finance AR collections" },
  { label: "Vendors", href: "/projects/vendor-engagements", icon: Handshake, note: "OEM and delivery collaboration" },
  { label: "Marketing", href: "/projects/marketing-initiatives", icon: LineChart, note: "Campaign work and ROI delivery" },
];

function money(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export default function ProjectsOverview() {
  const [data, setData] = useState<ProjectAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<ProjectAnalytics>("/api/projects/analytics")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load projects"));
  }, []);

  const lifecycle = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Active", value: data.active_projects },
      { name: "Completed", value: data.completed_projects },
      { name: "Other", value: Math.max(data.projects - data.active_projects - data.completed_projects, 0) },
    ];
  }, [data]);

  const finance = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Budget", value: data.total_budget },
      { name: "Cost", value: data.total_cost },
      { name: "Profitability", value: data.profitability_proxy },
    ];
  }, [data]);

  if (error) {
    return <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">{error}</div>;
  }

  const metrics = [
    { label: "Projects", value: data?.projects ?? 0, href: "/projects/projects" },
    { label: "Active Delivery", value: data?.active_projects ?? 0, href: "/projects/projects" },
    { label: "Open SLA Tickets", value: data?.open_sla_tickets ?? 0, href: "/projects/sla-tickets" },
    { label: "SLA Breaches", value: data?.breached_sla_tickets ?? 0, href: "/projects/sla-tickets" },
    { label: "Utilization", value: `${Math.round(data?.resource_utilization_percent ?? 0)}%`, href: "/projects/timesheets" },
    { label: "Invoices", value: data?.invoice_lifecycle_total ?? 0, href: "/projects/invoices" },
    { label: "Budget", value: money(data?.total_budget ?? 0), href: "/finance/project-finance" },
    { label: "Cost", value: money(data?.total_cost ?? 0), href: "/finance/project-finance" },
  ];

  return (
    <div className="space-y-6">
      <section className="module-hero rounded-lg p-6 text-white">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-100">Projects operating layer</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">Projects, SLAs, Licenses and Delivery</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-blue-50">
              One delivery workspace for implementation projects, SLA service, tasks, milestones, risks, license renewals, vendors, marketing initiatives, and finance-linked delivery performance.
            </p>
          </div>
          <Link href="/projects/projects" className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-blue-50">
            Open Project Register
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        {metrics.map((metric) => (
          <Link key={metric.label} href={metric.href} className="soft-panel interactive-lift rounded-lg p-4">
            <p className="text-xs font-medium uppercase text-slate-500">{metric.label}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-950">{metric.value}</p>
            <p className="mt-2 text-xs text-blue-700">Drill down</p>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Link href="/projects/projects" className="soft-panel interactive-lift rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Lifecycle Mix</h2>
              <p className="text-sm text-slate-500">Click to open project records.</p>
            </div>
            <Layers3 size={20} className="text-slate-500" />
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={lifecycle} dataKey="value" nameKey="name" outerRadius={94} innerRadius={48}>
                  {lifecycle.map((item, index) => (
                    <Cell key={item.name} fill={["#1957d3", "#0f9f7a", "#94a3b8"][index]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Link>

        <Link href="/finance/project-finance" className="soft-panel interactive-lift rounded-lg p-5">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-950">Budget, Cost and Profitability</h2>
            <p className="text-sm text-slate-500">Finance figures synchronized from project operations.</p>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={finance}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.32)" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => money(Number(value))} />
                <Bar dataKey="value" fill="#1957d3" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Link>
      </div>

      <section className="soft-panel rounded-lg p-5">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-slate-950">Delivery Workspaces</h2>
          <p className="text-sm text-slate-500">Former CRM project and SLA tools now live here as the project delivery source of truth.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {workspaceLinks.map((item) => (
            <Link key={item.href} href={item.href} className="interactive-lift rounded-lg border border-slate-200/80 bg-white/70 p-4">
              <div className="flex items-center justify-between">
                <span className="rounded-lg bg-blue-50 p-2 text-blue-800">
                  <item.icon size={18} />
                </span>
                <ArrowRight size={16} className="text-slate-500" />
              </div>
              <p className="mt-4 font-semibold text-slate-950">{item.label}</p>
              <p className="mt-1 text-sm leading-5 text-slate-600">{item.note}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
