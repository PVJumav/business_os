"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/services/api";

interface FinanceDashboardData {
  last_refreshed_at?: string;
  warning?: string | null;
  widgets: {
    financial_kpis: Record<string, number>;
    cash_position: Record<string, number | boolean>;
    revenue_forecast: Record<string, number>;
    budget_utilization: Record<string, number | boolean>;
    ar_summary: Record<string, number>;
    ap_summary: Record<string, number>;
    tax_exposure: Record<string, number>;
    project_profitability: Array<Record<string, number | string | boolean | null>>;
    approval_queue: Array<Record<string, number | string | null>>;
  };
}

const modules = [
  ["General Ledger", "/finance/chart-accounts", "Chart of accounts, journals, trial balance and period closing"],
  ["Accounts Payable", "/finance/bills", "Vendor bills, approvals, due dates and payments"],
  ["Accounts Receivable", "/finance/invoices", "Customer invoices, collections, aging, credit notes and receipts"],
  ["Expense Management", "/finance/expense-claims", "Staff claims, receipts, reimbursements, travel and petty cash"],
  ["Budgeting", "/finance/budgets", "Department, project and annual budget vs actual control"],
  ["Procurement", "/finance/purchase-requests", "Purchase requests, POs, goods received and supplier quotations"],
  ["Cash & Bank", "/finance/bank-accounts", "Bank accounts, cash, reconciliation, transfers and cheques"],
  ["Tax", "/finance/tax-records", "VAT, WHT, PAYE, corporate tax and compliance tracking"],
  ["Fixed Assets", "/finance/fixed-assets", "Asset register, depreciation, custodians and disposal"],
  ["Project Finance", "/finance/project-finance", "Project budgets, revenue, costs, profitability and overruns"],
  ["Revenue", "/finance/revenue-records", "Product, service, recurring and recognized revenue"],
  ["Approvals", "/finance/approvals", "Invoice, expense, purchase, payment and budget approvals"],
  ["Audit & Documents", "/finance/audit-trails", "Audit trails, compliance evidence and finance documents"],
  ["Integrations", "/finance/integration-events", "CRM, HRM, project, banking, email and inventory links"],
];

function money(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export default function FinanceDashboard() {
  const [data, setData] = useState<FinanceDashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<FinanceDashboardData>("/api/finance/control-center/dashboard").then(setData).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to load finance dashboard");
    });
  }, []);

  const cashTrend = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Revenue", value: Number(data.widgets.financial_kpis.revenue ?? 0) },
      { name: "Expenses", value: Number(data.widgets.financial_kpis.operating_expenses ?? 0) },
      { name: "Cash", value: Number(data.widgets.cash_position.cash_position ?? 0) },
      { name: "Forecast", value: Number(data.widgets.revenue_forecast.expected_revenue ?? 0) },
    ];
  }, [data]);

  const cards = [
    ["Revenue", Number(data?.widgets.financial_kpis.revenue ?? 0), "/finance/invoices"],
    ["Operating Expenses", Number(data?.widgets.financial_kpis.operating_expenses ?? 0), "/finance/expense-claims"],
    ["Net Profit", Number(data?.widgets.financial_kpis.net_profit ?? 0), "/finance/project-finance"],
    ["Cash Position", Number(data?.widgets.cash_position.cash_position ?? 0), "/finance/bank-accounts"],
    ["Revenue Forecast", Number(data?.widgets.revenue_forecast.expected_revenue ?? 0), "/finance/revenue-records"],
    ["Receivables", Number(data?.widgets.ar_summary.accounts_receivable ?? 0), "/finance/invoices"],
    ["Payables", Number(data?.widgets.ap_summary.accounts_payable ?? 0), "/finance/bills"],
    ["Pending Approvals", data?.widgets.approval_queue.length ?? 0, "/finance/approvals"],
  ] as const;

  return (
    <div className="space-y-6">
      <section className="module-hero rounded-lg p-6 text-white">
        <p className="text-sm font-medium uppercase text-[var(--gold-soft)]">Finance Workspace</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">Finance Control Center</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-white/82">
          Manage accounting, revenue, expenses, procurement, cash, payroll integration, tax, assets, approvals, audit, and compliance from one finance layer.
        </p>
        <p className="mt-3 text-xs text-[var(--gold-soft)]">
          Last refreshed: {data?.last_refreshed_at ? new Date(data.last_refreshed_at).toLocaleString() : "Pending"}.
          {error ? " Some dashboard values are restricted or temporarily unavailable." : data?.warning ? ` ${data.warning}` : " Values are based on approved, posted, or validated transactions."}
        </p>
      </section>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Finance modules are available below. Dashboard totals could not be loaded for this session: {error}
        </div>
      )}

      {!data && !error && <div className="glass-panel rounded-lg p-5 text-sm text-slate-500">Loading finance control center...</div>}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map(([label, value, href]) => (
          <Link key={label} href={href} className="soft-panel interactive-lift rounded-lg p-5">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-950">{money(value)}</p>
            <p className="mt-1 text-xs text-slate-500">Drill down</p>
          </Link>
        ))}
      </div>

      {data && <div className="grid gap-6 xl:grid-cols-2">
        <section className="soft-panel rounded-lg p-5">
          <h2 className="text-lg font-semibold text-slate-900">Finance Position</h2>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cashTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => money(Number(value))} />
                <Area dataKey="value" stroke="var(--brand)" fill="var(--gold-soft)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="soft-panel rounded-lg p-5">
          <h2 className="text-lg font-semibold text-slate-900">Budget Utilization</h2>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                {
                  department: "Budget",
                  approved: Number(data.widgets.budget_utilization.approved_budget ?? 0),
                  actual: Number(data.widgets.budget_utilization.actual_spend ?? 0),
                },
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" />
                <YAxis />
                <Tooltip formatter={(value) => money(Number(value))} />
                <Bar dataKey="approved" fill="var(--brand)" />
                <Bar dataKey="actual" fill="var(--gold)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>}

      <section className="soft-panel rounded-lg p-5">
        <h2 className="text-lg font-semibold text-slate-900">Finance Components</h2>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {modules.map(([label, href, description]) => (
            <Link key={href} href={href} className="interactive-lift rounded-lg border border-slate-200/80 bg-white/66 p-4">
              <p className="font-semibold text-slate-900">{label}</p>
              <p className="mt-2 text-sm text-slate-500">{description}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
