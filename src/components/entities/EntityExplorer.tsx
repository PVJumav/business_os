"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Database, RefreshCw, Search } from "lucide-react";
import { api } from "@/services/api";

type EntityHit = {
  type: string;
  id: string;
  title: string;
  subtitle: string;
};

type EntityDetail = {
  type: string;
  record: Record<string, string | number | boolean | null>;
  metrics: Array<{ label: string; value: string | number }>;
  sections: Record<string, Array<Record<string, string | number | boolean | null>>>;
};

const entityTypes = [
  { value: "all", label: "All" },
  { value: "accounts", label: "Accounts" },
  { value: "leads", label: "Leads" },
  { value: "opportunities", label: "Opportunities" },
  { value: "deals", label: "Deals" },
  { value: "projects", label: "Projects" },
  { value: "slas", label: "SLAs" },
  { value: "licences", label: "Licences" },
  { value: "departments", label: "Departments" },
  { value: "staff", label: "Staff" },
  { value: "contacts", label: "Contacts" },
  { value: "finance-invoices", label: "Finance Invoices" },
  { value: "connectors", label: "Connectors" },
  { value: "imports", label: "Imports" },
];

function formatKey(key: string) {
  return key.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatValue(value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return String(value);
}

function recordTitle(detail: EntityDetail) {
  const record = detail.record;
  return (
    record.company_name ||
    record.deal_name ||
    record.project_name ||
    record.solution ||
    record.name ||
    record.licence_name ||
    [record.first_name, record.last_name].filter(Boolean).join(" ") ||
    "Record"
  );
}

export default function EntityExplorer() {
  const searchParams = useSearchParams();
  const [query, setQuery] = useState("");
  const [entityType, setEntityType] = useState(searchParams.get("type") ?? "all");
  const [results, setResults] = useState<EntityHit[]>([]);
  const [detail, setDetail] = useState<EntityDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const type = searchParams.get("type");
    const id = searchParams.get("id");
    if (type && id) {
      loadDetail({ type, id, title: "Selected entity", subtitle: "" });
    }
  }, [searchParams]);

  async function runSearch(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    if (query.trim().length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const rows = await api.get<EntityHit[]>("/api/entities/search", {
        params: { query: query.trim(), entity_type: entityType },
      });
      setResults(rows);
      if (rows[0]) {
        await loadDetail(rows[0]);
      } else {
        setDetail(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(hit: EntityHit) {
    setLoading(true);
    setError(null);
    try {
      const payload = await api.get<EntityDetail>(`/api/entities/${hit.type}/${hit.id}`);
      setDetail(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load record");
    } finally {
      setLoading(false);
    }
  }

  const importantFields = detail
    ? Object.entries(detail.record).filter(
        ([key, value]) =>
          value !== null &&
          value !== "" &&
          !["id", "created_at", "updated_at", "notes"].includes(key)
      )
    : [];

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-950">Entity Explorer</h1>
            <p className="mt-1 text-sm text-slate-500">
              Search any operational record and drill into connected accounts, revenue, projects, SLAs, licences, contacts, and teams.
            </p>
          </div>
          <Link
            href="/integrations"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <Database size={16} />
            Integrations
          </Link>
        </div>

        <form onSubmit={runSearch} className="mt-5 grid gap-3 md:grid-cols-[180px_1fr_auto]">
          <select
            value={entityType}
            onChange={(event) => setEntityType(event.target.value)}
            className="rounded-xl border border-slate-200 px-3 py-3 text-sm outline-none focus:border-slate-500"
          >
            {entityTypes.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search KPA, Safaricom, KRON PAM, Imperva, project name, engineer, department..."
            className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-500"
          />
          <button
            type="submit"
            disabled={loading || query.trim().length < 2}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-medium text-white hover:bg-slate-800 disabled:bg-slate-300"
          >
            {loading ? <RefreshCw size={16} className="animate-spin" /> : <Search size={16} />}
            Search
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <div className="rounded-2xl border border-slate-200 bg-white">
          <div className="border-b border-slate-100 px-4 py-3 text-sm font-semibold text-slate-700">Results</div>
          <div className="max-h-[720px] divide-y divide-slate-100 overflow-y-auto">
            {results.length === 0 && (
              <div className="p-5 text-sm text-slate-500">Search by account, deal, project, SLA, licence, department, or staff name.</div>
            )}
            {results.map((hit) => (
              <button
                key={`${hit.type}-${hit.id}`}
                onClick={() => loadDetail(hit)}
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium text-slate-900">{hit.title}</p>
                  <p className="text-xs capitalize text-slate-500">{hit.type} | {hit.subtitle}</p>
                </div>
                <ArrowRight size={16} className="text-slate-400" />
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          {!detail && <p className="text-sm text-slate-500">Select a result to view connected operational information.</p>}
          {detail && (
            <div className="space-y-5">
              <div>
                <p className="text-sm capitalize text-slate-500">{detail.type}</p>
                <h2 className="text-2xl font-semibold text-slate-950">{formatValue(recordTitle(detail))}</h2>
              </div>

              {detail.metrics.length > 0 && (
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                  {detail.metrics.map((metric) => (
                    <div key={metric.label} className="rounded-xl border border-slate-200 p-3">
                      <p className="text-xs text-slate-500">{metric.label}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-950">{formatValue(metric.value)}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="grid gap-3 md:grid-cols-2">
                {importantFields.slice(0, 12).map(([key, value]) => (
                  <div key={key} className="rounded-xl bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">{formatKey(key)}</p>
                    <p className="mt-1 text-sm font-medium text-slate-900">{formatValue(value)}</p>
                  </div>
                ))}
              </div>

              {Object.entries(detail.sections).map(([name, rows]) => (
                <div key={name} className="rounded-xl border border-slate-200">
                  <div className="border-b border-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">
                    {formatKey(name)} ({rows.length})
                  </div>
                  <div className="max-h-72 divide-y divide-slate-100 overflow-y-auto">
                    {rows.length === 0 && <div className="px-3 py-3 text-sm text-slate-500">No linked records.</div>}
                    {rows.map((row, index) => (
                      <div key={`${name}-${index}`} className="grid gap-2 px-3 py-3 text-sm md:grid-cols-3">
                        {Object.entries(row)
                          .filter(([key, value]) => value !== null && value !== "" && !["id", "created_at", "updated_at"].includes(key))
                          .slice(0, 6)
                          .map(([key, value]) => (
                            <div key={key}>
                              <p className="text-xs text-slate-500">{formatKey(key)}</p>
                              <p className="font-medium text-slate-800">{formatValue(value)}</p>
                            </div>
                          ))}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
