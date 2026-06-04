"use client";

import { useMemo, useState } from "react";
import ResourceManager from "@/components/data/ResourceManager";
import { iamConfigs, iamGroups } from "@/lib/iamConfigs";

type GroupKey = keyof typeof iamGroups;

const groupCopy: Record<GroupKey, { title: string; description: string }> = {
  access: {
    title: "Identity & Access Management",
    description: "Roles, permissions, assignments, access policies, role conflicts, and segregation of duties controls.",
  },
  controls: {
    title: "Authority & Access Controls",
    description: "Delegated authority, branch and department restrictions, MFA, and temporary elevated access controls.",
  },
  audit: {
    title: "Sessions, Audit & Compliance",
    description: "Session tracking, activity audit logs, investigations, access analytics, and compliance reporting evidence.",
  },
};

export default function IAMModule() {
  const [group, setGroup] = useState<GroupKey>("access");
  const configs = useMemo(() => iamGroups[group].map((key) => iamConfigs[key]), [group]);
  const [activeKey, setActiveKey] = useState(configs[0].key);
  const activeConfig = configs.find((config) => config.key === activeKey) ?? configs[0];
  const copy = groupCopy[group];

  function switchGroup(next: GroupKey) {
    setGroup(next);
    setActiveKey(iamGroups[next][0]);
  }

  return (
    <div className="space-y-5">
      <section className="module-hero rounded-lg p-6 text-white">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--gold-soft)]">Business OS Security</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">{copy.title}</h1>
        <p className="mt-2 max-w-4xl text-sm leading-6 text-white/82">{copy.description}</p>
        <div className="mt-5 flex flex-wrap gap-2">
          {(Object.keys(iamGroups) as GroupKey[]).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => switchGroup(key)}
              className={`rounded-full border px-3 py-2 text-sm transition ${
                group === key ? "border-white bg-white text-[var(--brand-strong)]" : "border-white/25 bg-white/10 text-white hover:bg-white/18"
              }`}
            >
              {groupCopy[key].title}
            </button>
          ))}
        </div>
      </section>

      <section className="soft-panel rounded-lg p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--brand)]">IAM BUC workspace</p>
        <div className="mt-4 flex flex-wrap gap-2">
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
