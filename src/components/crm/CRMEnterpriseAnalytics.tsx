"use client";

import { useEffect, useState } from "react";
import { BarChart3, Building2, Contact, LifeBuoy, Megaphone, Target, Trophy } from "lucide-react";
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

const cards = [
  { label: "Accounts", path: "accounts", icon: Building2, color: "rgba(37, 99, 235, 0.13)" },
  { label: "Contacts", path: "contacts", icon: Contact, color: "rgba(14, 165, 233, 0.13)" },
  { label: "Lead Conversion", path: "leads.conversion_rate", icon: Target, suffix: "%", color: "rgba(16, 185, 129, 0.14)" },
  { label: "Open Pipeline", path: "pipeline.open", icon: BarChart3, color: "rgba(245, 158, 11, 0.15)" },
  { label: "Won Deals", path: "win_loss.won", icon: Trophy, color: "rgba(124, 58, 237, 0.13)" },
  { label: "Open Tickets", path: "tickets.open", icon: LifeBuoy, color: "rgba(239, 68, 68, 0.11)" },
  { label: "Campaigns", path: "campaigns", icon: Megaphone, color: "rgba(20, 184, 166, 0.12)" },
];

function read(data: CRMAnalytics, path: string) {
  return path.split(".").reduce<unknown>((current, part) => {
    if (current && typeof current === "object" && part in current) return (current as Record<string, unknown>)[part];
    return 0;
  }, data) as number;
}

export default function CRMEnterpriseAnalytics() {
  const [data, setData] = useState<CRMAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<CRMAnalytics>("/api/crm/enterprise/analytics")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load CRM analytics"));
  }, []);

  if (error) return <div className="rounded-xl border bg-red-50 p-5 text-sm text-red-700">{error}</div>;
  if (!data) return <div className="rounded-xl border bg-white p-5 text-sm text-slate-500">Loading CRM analytics...</div>;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">CRM Intelligence</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">CRM Analytics</h1>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
          Sales, account, lead conversion, revenue forecast, support, and campaign performance in one view.
        </p>
      </section>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.path} className="rounded-2xl border p-5 shadow-sm" style={{ backgroundColor: card.color }}>
            <div className="rounded-xl bg-white/80 p-2 text-slate-950 shadow-sm w-fit">
              <card.icon size={18} />
            </div>
            <p className="mt-4 text-sm font-medium text-slate-600">{card.label}</p>
            <p className="mt-1 text-3xl font-bold text-slate-950">{read(data, card.path).toLocaleString()}{card.suffix ?? ""}</p>
          </div>
        ))}
      </div>
      <section className="rounded-2xl border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Revenue Forecast</h2>
        <p className="mt-2 text-3xl font-bold text-slate-950">{data.pipeline.forecast.toLocaleString()}</p>
      </section>
    </div>
  );
}
