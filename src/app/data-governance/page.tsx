"use client";

import { useEffect, useState } from "react";
import { RefreshCw, ShieldCheck } from "lucide-react";
import Button from "@/components/ui/Button";
import { api } from "@/services/api";

type OwnershipPolicy = {
  domain: string;
  owner: string;
  master_records: string[];
  policy: string;
};

type DuplicateGroup = {
  key: string;
  count: number;
  label: string;
  ids: string[];
};

type DuplicateSection = {
  domain: string;
  resource: string;
  owner: string;
  duplicates: DuplicateGroup[];
};

type GovernanceSummary = {
  policies: OwnershipPolicy[];
  duplicate_sections: DuplicateSection[];
  summary: {
    duplicate_groups: number;
    status: string;
    rule: string;
  };
};

export default function DataGovernancePage() {
  const [data, setData] = useState<GovernanceSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      setData(await api.get<GovernanceSummary>("/api/data-governance/summary"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load governance summary");
    } finally {
      setIsLoading(false);
    }
  }

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    loadData();
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-950">Data Governance</h1>
          <p className="mt-1 max-w-4xl text-sm text-slate-500">
            Central ownership rules and duplicate discovery across HRM, CRM, Finance, Invoices, Projects, ERP, and Support.
          </p>
        </div>
        <Button variant="secondary" onClick={loadData}>
          <RefreshCw size={16} />
          Refresh
        </Button>
      </div>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="rounded-xl border bg-white p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-blue-600" size={24} />
          <div>
            <p className="text-sm font-medium uppercase text-slate-500">System Rule</p>
            <p className="mt-1 text-slate-900">{data?.summary.rule ?? "Loading governance rules..."}</p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Duplicate Groups</p>
            <p className="mt-1 text-2xl font-semibold text-slate-950">{data?.summary.duplicate_groups ?? 0}</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Status</p>
            <p className="mt-1 text-2xl font-semibold capitalize text-slate-950">{data?.summary.status?.replaceAll("_", " ") ?? "Loading"}</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Ownership Policies</p>
            <p className="mt-1 text-2xl font-semibold text-slate-950">{data?.policies.length ?? 0}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {(data?.policies ?? []).map((policy) => (
          <div key={policy.domain} className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">{policy.domain}</h2>
                <p className="mt-1 text-sm font-medium text-blue-700">{policy.owner}</p>
              </div>
            </div>
            <p className="mt-3 text-sm text-slate-600">{policy.policy}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {policy.master_records.map((record) => (
                <span key={record} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                  {record}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="border-b p-4">
          <h2 className="text-lg font-semibold text-slate-950">Duplicate Discovery</h2>
          <p className="mt-1 text-sm text-slate-500">Potential duplicate groups by owning module.</p>
        </div>
        <div className="divide-y">
          {isLoading ? (
            <div className="p-6 text-sm text-slate-500">Loading duplicate discovery...</div>
          ) : (data?.duplicate_sections ?? []).map((section) => (
            <div key={`${section.domain}-${section.resource}`} className="p-4">
              <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="font-semibold text-slate-900">{section.resource}</p>
                  <p className="text-sm text-slate-500">{section.owner}</p>
                </div>
                <span className="text-sm text-slate-600">{section.duplicates.length} duplicate group(s)</span>
              </div>
              {section.duplicates.length > 0 && (
                <div className="mt-3 space-y-2">
                  {section.duplicates.map((duplicate) => (
                    <div key={duplicate.key} className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                      <span className="font-medium">{duplicate.label}</span> appears {duplicate.count} times.
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
