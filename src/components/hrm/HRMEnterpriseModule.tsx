"use client";

import { useMemo, useState } from "react";
import ResourceManager from "@/components/data/ResourceManager";
import { hrmEnterpriseConfigs, hrmModuleGroups } from "@/lib/hrmEnterpriseConfigs";
import { resourceConfigs } from "@/lib/resourceConfigs";

type ModuleKey = keyof typeof hrmModuleGroups;

const moduleTitles: Record<ModuleKey, { title: string; description: string }> = {
  organization: {
    title: "Organization & Core HR",
    description: "Employee master data, reporting lines, departments, positions, branches, cost centers, contracts, and emergency contacts.",
  },
  security: {
    title: "Access Control & Audit",
    description: "Roles, permissions, user-to-employee linkage, and sensitive action audit trails.",
  },
  leave: {
    title: "Leave Management",
    description: "Leave requests, balances, leave types, policies, carry-forward controls, and blackout periods.",
  },
  attendance: {
    title: "Attendance & Timesheets",
    description: "Clock-ins, shifts, timesheets, overtime requests, holidays, period approval, and locking.",
  },
  payroll: {
    title: "Payroll",
    description: "Salary structures, compensation, payroll periods, runs, payslips, statutory components, and retroactive adjustments.",
  },
  recruitment: {
    title: "Recruitment / ATS",
    description: "Requisitions, openings, candidates, applications, interviews, feedback, offers, and hiring workflow.",
  },
  performance: {
    title: "Performance Management",
    description: "Reviews, goals, KPIs, review cycles, competencies, ratings, and improvement plans.",
  },
  training: {
    title: "Learning & Training",
    description: "Courses, sessions, employee training, certifications, expiry tracking, and mandatory training policies.",
  },
  assets: {
    title: "Assets & Offboarding",
    description: "Company assets, assignments, clearance checklists, exit interviews, termination records, and offboarding approvals.",
  },
};

function configFor(key: string) {
  return hrmEnterpriseConfigs[key] ?? resourceConfigs[key];
}

export default function HRMEnterpriseModule({ moduleKey }: { moduleKey: ModuleKey }) {
  const configs = useMemo(
    () => hrmModuleGroups[moduleKey].map(configFor).filter(Boolean),
    [moduleKey]
  );
  const [activeKey, setActiveKey] = useState(configs[0]?.key ?? "");
  const activeConfig = configs.find((config) => config.key === activeKey) ?? configs[0];
  const copy = moduleTitles[moduleKey];

  if (!activeConfig) {
    return <div className="soft-panel rounded-lg p-6 text-sm text-slate-500">No HRM module configuration found.</div>;
  }

  return (
    <div className="space-y-5">
      <section className="soft-panel rounded-lg p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--brand)]">Enterprise HRM</p>
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
