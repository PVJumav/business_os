"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart3, CheckCircle2, Download, Eye, FileText, RefreshCw } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { API_BASE_URL } from "@/lib/constants";
import { api } from "@/services/api";

interface ReportSections {
  title: string;
  sections: Array<{ heading: string; items: string[] }>;
}

interface ReportsSummary {
  available_reports: number;
  executive: Record<string, number>;
  finance: Record<string, number>;
  operations: Record<string, number | string>;
}

const reportTypes = [
  ["ceo", "CEO Executive Report"],
  ["finance", "Finance Report"],
  ["sales", "Sales Report"],
  ["hr", "HR Report"],
  ["sla", "SLA Report"],
  ["projects", "Project Report"],
];

const visualColors = ["rgba(37, 99, 235, 0.78)", "rgba(15, 118, 110, 0.78)", "rgba(217, 119, 6, 0.78)", "rgba(79, 70, 229, 0.72)"];

export default function ReportCustomizer() {
  const [type, setType] = useState("ceo");
  const [data, setData] = useState<ReportSections | null>(null);
  const [summary, setSummary] = useState<ReportsSummary | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(reportType = type) {
    setLoading(true);
    setError(null);
    try {
      const [sections, reportSummary] = await Promise.all([
        api.get<ReportSections>(`/api/reports/${reportType}/sections`),
        api.get<ReportsSummary>("/api/reports/summary"),
      ]);
      setData(sections);
      setSummary(reportSummary);
      setSelected(sections.sections.map((section) => section.heading));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load reports");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load(type);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type]);

  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (selected.length) params.set("include", selected.join(","));
    return params.toString();
  }, [selected]);

  const previewUrl = `${API_BASE_URL}/api/reports/${type}/preview${query ? `?${query}` : ""}`;
  const downloadUrl = `${API_BASE_URL}/api/reports/${type}.pdf${query ? `?${query}` : ""}`;
  const financeVisual = summary
    ? [
        { name: "Revenue", value: Math.max(Number(summary.finance.revenue || 0), 0) },
        { name: "Expenses", value: Math.max(Number(summary.finance.expenses || 0), 0) },
        { name: "Outstanding", value: Math.max(Number(summary.finance.outstanding_invoices || 0), 0) },
      ]
    : [];
  const operationsVisual = summary
    ? [
        { name: "Employees", value: Number(summary.executive.active_employees || 0) },
        { name: "Projects", value: Number(summary.executive.active_projects || 0) },
        { name: "Tickets", value: Number(summary.executive.open_tickets || 0) },
      ]
    : [];

  function toggle(heading: string) {
    setSelected((current) => (current.includes(heading) ? current.filter((item) => item !== heading) : [...current, heading]));
  }

  return (
    <div className="space-y-6">
      <section className="soft-panel rounded-lg p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-blue-800">BusinessOS Reports</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Executive Report Builder</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Build live CEO, HR, finance, sales, SLA, and project reports from the operating database. Preview first, choose sections, then download a PDF.
            </p>
          </div>
          <button
            type="button"
            onClick={() => load()}
            className="focus-ring inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </section>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {summary &&
          [
            ["Reports", summary.available_reports],
            ["Accounts", summary.executive.accounts],
            ["Employees", summary.executive.active_employees],
            ["Profit/Loss", Number(summary.finance.profit_loss || 0).toLocaleString()],
          ].map(([label, value]) => (
            <div key={label} className="interactive-lift soft-panel rounded-lg p-4">
              <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
            </div>
          ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
        <aside className="soft-panel rounded-lg p-5">
          <label className="text-sm font-semibold text-slate-800">
            Report type
            <select
              value={type}
              onChange={(event) => setType(event.target.value)}
              className="focus-ring mt-2 h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900"
            >
              {reportTypes.map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <div className="mt-5 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-900">Included sections</p>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{selected.length}</span>
            </div>
            {loading && <p className="text-sm text-slate-500">Loading sections...</p>}
            {data?.sections.map((section) => (
              <label key={section.heading} className="interactive-lift flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm">
                <input type="checkbox" checked={selected.includes(section.heading)} onChange={() => toggle(section.heading)} className="mt-1" />
                <span>
                  <span className="block font-semibold text-slate-900">{section.heading}</span>
                  <span className="text-xs text-slate-500">{section.items.length} live datapoints</span>
                </span>
              </label>
            ))}
          </div>

          <div className="mt-5 grid gap-2 sm:grid-cols-2">
            <a href={previewUrl} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50">
              <Eye size={16} />
              Preview
            </a>
            <a href={downloadUrl} className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-700 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-800">
              <Download size={16} />
              PDF
            </a>
          </div>

          <div className="mt-5 rounded-lg bg-slate-50 p-4 text-sm text-slate-700">
            <div className="flex items-center gap-2 font-semibold text-slate-900">
              <CheckCircle2 size={16} />
              Report controls
            </div>
            <p className="mt-2 leading-6">The preview and PDF use the same selected sections, so what you inspect is what you download.</p>
          </div>
        </aside>

        <div className="space-y-6">
          <section className="report-visual grid gap-4 lg:grid-cols-2">
            <div className="soft-panel rounded-lg p-5">
              <div className="mb-4 flex items-center gap-2">
                <BarChart3 size={18} className="text-blue-800" />
                <h2 className="font-semibold text-slate-950">Finance Visual</h2>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={financeVisual}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {financeVisual.map((_, index) => (
                        <Cell key={index} fill={visualColors[index % visualColors.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="soft-panel rounded-lg p-5">
              <div className="mb-4 flex items-center gap-2">
                <FileText size={18} className="text-blue-800" />
                <h2 className="font-semibold text-slate-950">Operations Visual</h2>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={operationsVisual} dataKey="value" nameKey="name" outerRadius={88} label>
                      {operationsVisual.map((_, index) => (
                        <Cell key={index} fill={visualColors[index % visualColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-sm font-semibold text-slate-900">{data?.title ?? "Report preview"}</p>
              <span className="text-xs font-medium text-slate-500">Live preview</span>
            </div>
            <iframe src={previewUrl} title="Report preview" className="h-[720px] w-full bg-white" />
          </section>
        </div>
      </div>
    </div>
  );
}
