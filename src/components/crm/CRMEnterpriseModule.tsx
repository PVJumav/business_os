"use client";

import { useMemo, useState } from "react";
import ResourceManager from "@/components/data/ResourceManager";
import { crmEnterpriseConfigs, crmModuleGroups } from "@/lib/crmEnterpriseConfigs";

type ModuleKey = keyof typeof crmModuleGroups;

const moduleTitles: Record<ModuleKey, { title: string; description: string }> = {
  accounts: { title: "Accounts & Contacts", description: "Customer accounts, vendors, partners, ownership, contacts, roles, and communication preferences." },
  leads: { title: "Lead Management", description: "Lead capture, source, scoring, assignment, qualification, and conversion into account/contact/opportunity." },
  pipeline: { title: "Opportunities & Pipeline", description: "Sales pipeline, stage controls, expected value, probability, close dates, win/loss, and revenue forecast." },
  activities: { title: "Activities & Tasks", description: "Calls, meetings, emails, follow-ups, reminders, notes, owners, due dates, and completion status." },
  commercial: { title: "Products, Price Books & Quotes", description: "Products, services, SKUs, price books, quote line items, discounts, taxes, approvals, versioning, and expiry." },
  contracts: { title: "Contracts", description: "Customer contracts, renewal dates, values, documents, SLA linkage, reminders, and contract lifecycle." },
  support: { title: "Tickets & Customer Support", description: "Support tickets, categories, priority, SLA status, escalation, owners, and resolution tracking." },
  campaigns: { title: "Campaigns & Marketing", description: "Campaigns, target accounts, responses, lead generation, ROI, and campaign lifecycle." },
  approvals: { title: "Approvals, Workflows & Audit", description: "Configurable approval rules, pipeline stage rules, record sharing, and audit history." },
};

export default function CRMEnterpriseModule({ moduleKey }: { moduleKey: ModuleKey }) {
  const configs = useMemo(() => crmModuleGroups[moduleKey].map((key) => crmEnterpriseConfigs[key]), [moduleKey]);
  const [activeKey, setActiveKey] = useState(configs[0]?.key ?? "");
  const activeConfig = configs.find((config) => config.key === activeKey) ?? configs[0];
  const copy = moduleTitles[moduleKey];

  return (
    <div className="space-y-5">
      <section className="soft-panel rounded-lg p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--brand)]">Enterprise CRM</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">{copy.title}</h1>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">{copy.description}</p>
        <div className="mt-5 flex flex-wrap gap-2">
          {configs.map((config) => (
            <button
              key={config.key}
              type="button"
              onClick={() => setActiveKey(config.key)}
              className={`rounded-full border px-3 py-2 text-sm transition ${
                activeConfig.key === config.key
                  ? "border-[var(--brand)] bg-[var(--brand)] text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:border-[var(--gold)] hover:text-[var(--brand-strong)]"
              }`}
            >
              {config.title}
            </button>
          ))}
        </div>
      </section>
      <ResourceManager config={activeConfig} />
    </div>
  );
}
