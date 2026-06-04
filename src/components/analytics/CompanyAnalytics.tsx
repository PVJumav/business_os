"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download, X } from "lucide-react";
import { api } from "@/services/api";
import { API_BASE_URL } from "@/lib/constants";

interface DepartmentData {
  name: string;
  employees: number;
  open_work: number;
  activities: number;
  activity_spend: number;
  certifications: number;
  training_spend: number;
  budget: number;
  actual_spend: number;
  performance: string[];
}

interface ExecutiveData {
  kpis: Record<string, number>;
  finance: Record<string, number>;
  workload: Record<string, number>;
  departments: DepartmentData[];
  pipeline_by_stage: Array<{ name: string; count: number }>;
  revenue_by_status: Array<{ name: string; count: number }>;
}

const scopes = ["company", "finance", "hr", "sales", "sla", "projects"];

function money(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export default function CompanyAnalytics() {
  const [data, setData] = useState<ExecutiveData | null>(null);
  const [scope, setScope] = useState("company");
  const [department, setDepartment] = useState<DepartmentData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<ExecutiveData>("/api/analytics/executive").then(setData).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    });
  }, []);

  const scoped = useMemo(() => {
    if (!data) return { metrics: [], charts: [] };
    const maps = {
      company: {
        metrics: [
          ["Employees", data.kpis.employees],
          ["Accounts", data.kpis.accounts],
          ["Opportunities", data.kpis.opportunities],
          ["Open Work", data.workload.open_projects + data.workload.open_tickets + data.workload.pending_tenders],
        ],
        charts: [
          { title: "Finance Performance", data: financeBars(data) },
          { title: "Pipeline by Stage", data: data.pipeline_by_stage.map((item) => ({ name: item.name, value: item.count })) },
        ],
      },
      finance: {
        metrics: [
          ["Revenue", data.finance.recognized_revenue ?? data.finance.deal_revenue],
          ["Invoices", data.finance.invoice_amount],
          ["Paid", data.finance.paid_amount],
          ["Debt", data.finance.outstanding_debt],
        ],
        charts: [
          { title: "Finance Performance", data: financeBars(data) },
          { title: "Revenue Status", data: data.revenue_by_status.map((item) => ({ name: item.name, value: item.count })) },
        ],
      },
      hr: {
        metrics: [
          ["Employees", data.kpis.employees],
          ["Departments", data.kpis.departments],
          ["Pending Leave", data.kpis.leave_pending],
          ["Payroll Records", data.kpis.payroll_records],
        ],
        charts: [
          { title: "Department Headcount", data: data.departments.map((item) => ({ name: item.name, value: item.employees })) },
          { title: "HR Spend by Department", data: data.departments.map((item) => ({ name: item.name, value: item.activity_spend + item.training_spend })) },
        ],
      },
      sales: {
        metrics: [
          ["Leads", data.kpis.leads],
          ["Opportunities", data.kpis.opportunities],
          ["Open Deals", data.kpis.open_deals],
          ["Closed Won", data.kpis.closed_won],
        ],
        charts: [
          { title: "Pipeline by Stage", data: data.pipeline_by_stage.map((item) => ({ name: item.name, value: item.count })) },
          { title: "Sales Value", data: [
            { name: "Pipeline", value: data.finance.pipeline_value },
            { name: "Deal Revenue", value: data.finance.deal_revenue },
            { name: "GP", value: data.finance.deal_gp },
            { name: "Target GP", value: data.finance.target_gp },
          ] },
        ],
      },
      sla: {
        metrics: [
          ["Active SLAs", data.kpis.active_slas],
          ["Open Tickets", data.kpis.tickets_open],
          ["Open Projects", data.workload.open_projects],
          ["Automation Rules", data.workload.automation_rules],
        ],
        charts: [
          { title: "SLA Workload", data: [
            { name: "Active SLAs", value: data.workload.active_slas },
            { name: "Open Tickets", value: data.workload.open_tickets },
            { name: "Open Projects", value: data.workload.open_projects },
          ] },
        ],
      },
      projects: {
        metrics: [
          ["Projects", data.kpis.projects],
          ["Open Projects", data.workload.open_projects],
          ["Active SLAs", data.workload.active_slas],
          ["Open Tickets", data.workload.open_tickets],
        ],
        charts: [
          { title: "Project Delivery Load", data: [
            { name: "Projects", value: data.kpis.projects },
            { name: "SLAs", value: data.workload.active_slas },
            { name: "Tickets", value: data.workload.open_tickets },
          ] },
        ],
      },
    };
    return maps[scope as keyof typeof maps];
  }, [data, scope]);

  if (error) return <div className="rounded-xl border bg-red-50 p-5 text-sm text-red-700">{error}</div>;
  if (!data) return <div className="rounded-xl border bg-white p-5 text-sm text-slate-500">Loading analytics...</div>;

  return (
    <div className="space-y-6">
      <section className="rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-medium uppercase text-slate-500">BusinessOS Analytics</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Company Analytics</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Filter by company area and drill into departments for performance, expenditure, certifications, activities, and work items.
            </p>
          </div>
          <Link href="/reports" className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800">
            <Download size={16} />
            Report Center
          </Link>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {scopes.map((item) => (
            <button
              key={item}
              onClick={() => setScope(item)}
              className={`rounded-full px-4 py-2 text-sm capitalize ${scope === item ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-4">
        {scoped.metrics.map(([label, value]) => (
          <Metric key={String(label)} label={String(label)} value={Number(value ?? 0)} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        {scoped.charts.map((chart) => (
          <Chart key={chart.title} title={chart.title} data={chart.data} />
        ))}
      </div>

      <section className="rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Department Analytics</h2>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {data.departments.map((item) => (
            <button key={item.name} onClick={() => setDepartment(item)} className="rounded-xl border bg-slate-50 p-4 text-left hover:bg-white">
              <p className="font-semibold text-slate-900">{item.name}</p>
              <p className="mt-2 text-sm text-slate-600">{item.employees} employees</p>
              <p className="mt-1 text-sm text-slate-600">{item.open_work} open work items</p>
              <p className="mt-1 text-sm text-slate-600">Spend: {money(item.actual_spend + item.activity_spend + item.training_spend)}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Quick Report Downloads</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          {["ceo", "finance", "sales", "hr", "sla", "projects"].map((report) => (
            <a key={report} href={`${API_BASE_URL}/api/reports/${report}.pdf`} className="rounded-lg border px-4 py-2 text-sm capitalize hover:bg-slate-50">
              Download {report} report
            </a>
          ))}
        </div>
      </section>

      {department && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40">
          <aside className="h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-slate-950">{department.name} Drilldown</h2>
              <button onClick={() => setDepartment(null)} className="rounded-lg p-2 hover:bg-slate-100"><X size={18} /></button>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <Metric label="Employees" value={department.employees} />
              <Metric label="Open Work" value={department.open_work} />
              <Metric label="Activities" value={department.activities} />
              <Metric label="Certifications" value={department.certifications} />
              <Metric label="Budget" value={department.budget} />
              <Metric label="Actual Spend" value={department.actual_spend + department.activity_spend + department.training_spend} />
            </div>
            <div className="mt-5 rounded-xl border bg-slate-50 p-4">
              <h3 className="font-semibold text-slate-900">Performance Notes</h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-700">
                {department.performance.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

function financeBars(data: ExecutiveData) {
  return [
    { name: "Pipeline", value: data.finance.pipeline_value ?? 0 },
    { name: "Revenue", value: data.finance.recognized_revenue ?? data.finance.deal_revenue ?? 0 },
    { name: "Invoices", value: data.finance.invoice_amount ?? 0 },
    { name: "Paid", value: data.finance.paid_amount ?? 0 },
    { name: "Debt", value: data.finance.outstanding_debt ?? 0 },
    { name: "People Cost", value: data.finance.people_cost ?? 0 },
  ];
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-950">{money(value)}</p>
    </div>
  );
}

function Chart({ title, data }: { title: string; data: Array<{ name: string; value: number }> }) {
  return (
    <section className="rounded-xl border bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <div className="mt-5 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tickFormatter={(value) => String(value).slice(0, 12)} />
            <YAxis />
            <Tooltip formatter={(value) => Number(value).toLocaleString()} />
            <Bar dataKey="value" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
