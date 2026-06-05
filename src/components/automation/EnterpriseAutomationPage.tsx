"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  FileText,
  GitBranch,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import Button from "@/components/ui/Button";
import { automationViews, type AutomationField, type AutomationViewConfig } from "@/lib/automationConfigs";
import { api } from "@/services/api";

type RecordValue = string | number | boolean | null | undefined | Record<string, unknown> | unknown[];
type DataRecord = Record<string, RecordValue> & { id?: string };

type Dashboard = {
  counts: Record<string, number>;
  workflow_state: Array<{ name: string; count: number }>;
  approvals_by_state: Array<{ name: string; count: number }>;
  sla_by_state: Array<{ name: string; count: number }>;
  risk_by_status: Array<{ name: string; count: number }>;
  kpi_health: Array<{ name: string; count: number }>;
  upcoming_reviews: DataRecord[];
  delayed_workflows: DataRecord[];
};

function emptyForm(config: AutomationViewConfig) {
  return config.fields.reduce<Record<string, RecordValue>>((acc, field) => {
    acc[field.name] = field.type === "number" ? 0 : "";
    return acc;
  }, {});
}

function formatValue(value: RecordValue) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value) || typeof value === "object") return JSON.stringify(value);
  return String(value).replaceAll("_", " ");
}

function normalizeRecord(value: unknown): DataRecord {
  if (value && typeof value === "object" && !Array.isArray(value)) return value as DataRecord;
  return {};
}

function normalizeRecordList(value: unknown): DataRecord[] {
  if (Array.isArray(value)) return value.map(normalizeRecord);
  if (value && typeof value === "object") {
    const objectValue = value as Record<string, unknown>;
    for (const key of ["records", "items", "data", "results", "rows"]) {
      if (Array.isArray(objectValue[key])) return (objectValue[key] as unknown[]).map(normalizeRecord);
    }
    if (objectValue.id) return [normalizeRecord(objectValue)];
  }
  return [];
}

function statusTone(value: RecordValue) {
  const key = String(value ?? "").toLowerCase();
  if (["approved", "active", "completed", "closed", "success", "processed", "effective", "compliant"].includes(key)) {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (["rejected", "failed", "breached", "critical", "non_compliant", "ineffective"].includes(key)) {
    return "border-rose-200 bg-rose-50 text-rose-800";
  }
  if (["escalated", "pending", "under review", "partial", "near_breach", "mitigating"].includes(key)) {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function normalizePayload(form: Record<string, RecordValue>, fields: AutomationField[]) {
  return fields.reduce<Record<string, RecordValue>>((payload, field) => {
    const value = form[field.name];
    if (value === "") return payload;
    if (field.type === "number") payload[field.name] = Number(value ?? 0);
    else if (value === "true") payload[field.name] = true;
    else if (value === "false") payload[field.name] = false;
    else payload[field.name] = value;
    return payload;
  }, {});
}

function MiniBar({ items }: { items: Array<{ name: string; count: number }> }) {
  const max = Math.max(1, ...items.map((item) => item.count));
  return (
    <div className="space-y-3">
      {items.slice(0, 5).map((item) => (
        <div key={item.name}>
          <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
            <span>{formatValue(item.name)}</span>
            <span>{item.count}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-slate-800" style={{ width: `${Math.max(8, (item.count / max) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function EnterpriseAutomationPage({ viewKey }: { viewKey: keyof typeof automationViews }) {
  const config = automationViews[viewKey];
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [form, setForm] = useState<Record<string, RecordValue>>(() => emptyForm(config));
  const [selected, setSelected] = useState<DataRecord | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const [items, stats] = await Promise.all([
        api.get<unknown>(config.endpoint),
        api.get<Dashboard>("/api/automation/dashboard").catch(() => null),
      ]);
      setRecords(normalizeRecordList(items));
      setDashboard(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load enterprise automation records");
    } finally {
      setIsLoading(false);
    }
  }

  /* eslint-disable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */
  useEffect(() => {
    load();
  }, [config.endpoint]);
  /* eslint-enable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return records.filter((record) => {
      const matchesSearch = !term || config.searchFields.some((field) => String(record[field] ?? "").toLowerCase().includes(term));
      const matchesStatus = !status || !config.statusField || String(record[config.statusField] ?? "") === status;
      return matchesSearch && matchesStatus;
    });
  }, [config.searchFields, config.statusField, query, records, status]);

  const statusOptions = useMemo(() => {
    if (!config.statusField) return [];
    return Array.from(new Set(records.map((record) => String(record[config.statusField as string] ?? "")).filter(Boolean))).sort();
  }, [config.statusField, records]);

  const tableFields = config.fields.filter((field) => field.table);
  const dashboardCards = (config.dashboardKeys ?? []).map((key) => ({
    key,
    label: key.replaceAll("_", " "),
    value: dashboard?.counts?.[key] ?? 0,
  }));

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = normalizePayload(form, config.fields);
    const saved = normalizeRecord(await api.post<unknown>(config.endpoint, payload));
    setRecords((current) => [saved, ...current]);
    setForm(emptyForm(config));
    setIsFormOpen(false);
  }

  async function seedData() {
    await api.post("/api/automation/seed", {});
    await load();
  }

  if (!config) return null;

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
              <ShieldCheck size={14} />
              Business OS 5.5
            </div>
            <h1 className="text-2xl font-bold text-slate-950">{config.title}</h1>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">{config.description}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={load}>
              <RefreshCw size={16} />
              Refresh
            </Button>
            <Button type="button" variant="secondary" onClick={seedData}>
              <GitBranch size={16} />
              Seed defaults
            </Button>
            <Button type="button" onClick={() => setIsFormOpen(true)}>
              <Plus size={16} />
              New {config.resource}
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {dashboardCards.map((card) => (
          <button
            key={card.key}
            type="button"
            onClick={() => setQuery(card.label)}
            className="rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{card.label}</span>
              <Activity size={16} className="text-slate-400" />
            </div>
            <p className="mt-3 text-3xl font-bold text-slate-950">{card.value.toLocaleString()}</p>
          </button>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-800">
            <Clock size={16} />
            Workflow health
          </div>
          <MiniBar items={dashboard?.workflow_state ?? []} />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-800">
            <CheckCircle2 size={16} />
            Approval state
          </div>
          <MiniBar items={dashboard?.approvals_by_state ?? []} />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-800">
            <AlertTriangle size={16} />
            Risk and SLA
          </div>
          <MiniBar items={[...(dashboard?.sla_by_state ?? []), ...(dashboard?.risk_by_status ?? [])]} />
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-200 p-4 md:flex-row md:items-center md:justify-between">
          <div className="relative max-w-xl flex-1">
            <Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={`Search ${config.resource.toLowerCase()} records`}
              className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-10 pr-3 text-sm text-slate-900 outline-none transition focus:border-slate-500"
            />
          </div>
          {statusOptions.length > 0 && (
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-500"
            >
              <option value="">All status</option>
              {statusOptions.map((option) => (
                <option key={option} value={option}>{formatValue(option)}</option>
              ))}
            </select>
          )}
        </div>

        {error && <div className="border-b border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
        {isLoading ? (
          <div className="p-8 text-sm text-slate-500">Loading enterprise records...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {tableFields.map((field) => (
                    <th key={field.name} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">{field.label}</th>
                  ))}
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Open</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filtered.map((record) => (
                  <tr key={record.id} className="cursor-pointer transition hover:bg-slate-50" onDoubleClick={() => setSelected(record)}>
                    {tableFields.map((field) => {
                      const value = record[field.name];
                      return (
                        <td key={field.name} className="whitespace-nowrap px-4 py-3 text-slate-700">
                          {field.name === config.statusField || field.name === "state" || field.name.includes("status") ? (
                            <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${statusTone(value)}`}>{formatValue(value)}</span>
                          ) : (
                            formatValue(value)
                          )}
                        </td>
                      );
                    })}
                    <td className="px-4 py-3 text-right">
                      <button type="button" onClick={() => setSelected(record)} className="inline-flex items-center gap-1 text-sm font-semibold text-slate-700 hover:text-slate-950">
                        Details <ArrowRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td className="px-4 py-8 text-center text-sm text-slate-500" colSpan={tableFields.length + 1}>No records found. Seed defaults or create a new record.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4">
          <form onSubmit={submit} className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white p-5 shadow-2xl">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-950">Create {config.resource}</h2>
              <button type="button" onClick={() => setIsFormOpen(false)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
                <X size={18} />
              </button>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {config.fields.map((field) => (
                <label key={field.name} className={field.type === "textarea" ? "md:col-span-2" : ""}>
                  <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{field.label}</span>
                  {field.type === "textarea" ? (
                    <textarea
                      value={String(form[field.name] ?? "")}
                      onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.value }))}
                      className="min-h-24 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-500"
                    />
                  ) : field.type === "select" ? (
                    <select
                      required={field.required}
                      value={String(form[field.name] ?? "")}
                      onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.value }))}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-500"
                    >
                      <option value="">Select</option>
                      {field.options?.map((option) => <option key={option} value={option}>{formatValue(option)}</option>)}
                    </select>
                  ) : (
                    <input
                      required={field.required}
                      type={field.type ?? "text"}
                      value={String(form[field.name] ?? "")}
                      onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.value }))}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-500"
                    />
                  )}
                </label>
              ))}
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={() => setIsFormOpen(false)}>Cancel</Button>
              <Button type="submit">Save {config.resource}</Button>
            </div>
          </form>
        </div>
      )}

      {selected && (
        <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl overflow-y-auto border-l border-slate-200 bg-white p-5 shadow-2xl">
          <div className="mb-5 flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{config.module}</p>
              <h2 className="text-xl font-bold text-slate-950">{formatValue(selected[config.fields[1]?.name] ?? selected[config.fields[0]?.name])}</h2>
            </div>
            <button type="button" onClick={() => setSelected(null)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
              <X size={18} />
            </button>
          </div>
          <div className="space-y-3">
            {config.fields.map((field) => (
              <div key={field.name} className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{field.label}</p>
                <p className="mt-1 text-sm text-slate-800">{formatValue(selected[field.name])}</p>
              </div>
            ))}
          </div>
          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
              <FileText size={16} />
              Audit visibility
            </div>
            <p className="text-sm leading-6 text-slate-600">
              Sensitive create, update, workflow transition, approval, SLA, and access actions are written to the enterprise audit log through the Business OS 5.5 automation service.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
