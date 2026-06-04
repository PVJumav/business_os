"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Briefcase, Building2, Contact, FileText, LifeBuoy, Megaphone, ShieldCheck, Target } from "lucide-react";
import { api } from "@/services/api";

interface CRMAnalytics {
  accounts: number;
  contacts: number;
  leads: { total: number; converted: number; conversion_rate: number };
  pipeline: { open: number; forecast: number };
  win_loss: { won: number; lost: number };
  tickets: { open: number };
  campaigns: number;
}

const modules = [
  { label: "Accounts & Contacts", href: "/crm/accounts", icon: Building2, description: "Organizations, contacts, ownership, and relationship history." },
  { label: "Lead Management", href: "/crm/leads", icon: Target, description: "Capture, qualify, assign, score, and convert leads." },
  { label: "Pipeline", href: "/crm/opportunities", icon: BarChart3, description: "Opportunities, stages, probability, forecast, and win/loss." },
  { label: "Activities & Tasks", href: "/crm/activities", icon: Contact, description: "Calls, meetings, emails, follow-ups, notes, and reminders." },
  { label: "Products & Quotes", href: "/crm/quotations", icon: FileText, description: "Catalog, price books, quote lines, approval, expiry, and acceptance." },
  { label: "Contracts", href: "/crm/contracts", icon: Briefcase, description: "Customer contracts, values, renewals, documents, and SLA linkage." },
  { label: "Support", href: "/crm/tickets", icon: LifeBuoy, description: "Tickets, priority, escalation, SLA health, and resolution." },
  { label: "Campaigns", href: "/crm/campaigns", icon: Megaphone, description: "Campaigns, responses, lead generation, spend, and ROI." },
  { label: "Approvals & Audit", href: "/crm/approvals", icon: ShieldCheck, description: "Approval rules, pipeline rules, sharing, and audit history." },
];

const colors = ["var(--brand-soft)", "var(--gold-soft)", "rgba(107, 75, 42, 0.12)"];

export default function CRMOperatingDashboard() {
  const [data, setData] = useState<CRMAnalytics | null>(null);

  useEffect(() => {
    api.get<CRMAnalytics>("/api/crm/enterprise/analytics").then(setData).catch(() => setData(null));
  }, []);

  return (
    <div className="space-y-6">
      <section className="module-hero rounded-lg p-6 text-white">
        <p className="text-sm font-medium uppercase text-[var(--gold-soft)]">BusinessOS CRM</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">Enterprise CRM Operating Dashboard</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-white/82">
          A single relationship engine for accounts, leads, opportunities, quotations, contracts, support, campaigns, approvals, and revenue intelligence.
        </p>
      </section>

      {data && (
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          {[
            ["Accounts", data.accounts],
            ["Contacts", data.contacts],
            ["Leads", data.leads.total],
            ["Conversion", `${data.leads.conversion_rate}%`],
            ["Open Pipeline", data.pipeline.open],
            ["Open Tickets", data.tickets.open],
          ].map(([label, value], index) => (
            <Link key={label} href="/crm/analytics" className="interactive-lift rounded-lg border p-4 shadow-sm" style={{ backgroundColor: colors[index % colors.length] }}>
              <p className="text-xs font-medium uppercase text-slate-600">{label}</p>
              <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
            </Link>
          ))}
        </div>
      )}

      <section className="soft-panel rounded-lg p-5">
        <h2 className="text-lg font-semibold text-slate-950">CRM Workspaces</h2>
        <p className="mt-1 text-sm text-slate-500">Lean entry points into the complete CRM operating model.</p>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {modules.map((module, index) => (
            <Link key={module.href} href={module.href} className="interactive-lift rounded-lg border p-4" style={{ backgroundColor: colors[index % colors.length] }}>
              <div className="flex items-center justify-between">
                <span className="rounded-lg bg-white/80 p-2 text-[var(--brand)] shadow-sm"><module.icon size={18} /></span>
                <ArrowRight size={16} className="text-slate-500" />
              </div>
              <p className="mt-4 font-semibold text-slate-950">{module.label}</p>
              <p className="mt-1 text-sm leading-5 text-slate-600">{module.description}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
