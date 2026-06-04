"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Database, FileUp, PlugZap, RefreshCw, ShieldAlert } from "lucide-react";
import ResourcePage from "@/components/data/ResourcePage";
import { api } from "@/services/api";

type ImportResult = {
  business_id?: string;
  file_name?: string;
  source_format?: string;
  target_resource?: string;
  parsed_rows?: number;
  imported_rows?: number;
  error_rows?: number;
  parse_summary?: string;
  status?: string;
};

type IntegrationSummary = {
  connectors: {
    total: number;
    active: number;
    inactive: number;
    by_type: Record<string, number>;
  };
  imports: {
    total: number;
    recent: ImportResult[];
    failed_recent: number;
    formats: Record<string, number>;
    imported_rows: number;
    error_rows: number;
  };
  readiness: Array<{ label: string; status: string }>;
};

const targetOptions = [
  ["pipeline", "Pipeline / Deals"],
  ["accounts", "Accounts"],
  ["licences", "Licences"],
  ["staff", "Staff"],
  ["finance", "Finance"],
];

const acceptedExtensions = [".csv", ".json", ".yaml", ".yml", ".xlsx", ".xls", ".pdf", ".doc", ".docx", ".txt"];

export default function IntegrationsCenter() {
  const [targetResource, setTargetResource] = useState("pipeline");
  const [sourceName, setSourceName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [summary, setSummary] = useState<IntegrationSummary | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectorDraft, setConnectorDraft] = useState({ connector_name: "", connector_type: "database", environment: "production", system_owner: "", status: "active" });

  async function loadSummary() {
    const data = await api.get<IntegrationSummary>("/api/integrations/summary");
    setSummary(data);
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadSummary().catch((err) => setError(err instanceof Error ? err.message : "Could not load integrations summary"));
  }, []);

  const fileValidation = useMemo(() => {
    if (!file) return "Choose a file to import.";
    const lower = file.name.toLowerCase();
    const allowed = acceptedExtensions.some((ext) => lower.endsWith(ext));
    if (!allowed) return `Unsupported file type. Accepted: ${acceptedExtensions.join(", ")}`;
    if (file.size > 20 * 1024 * 1024) return "File is too large for this import screen. Keep uploads under 20MB.";
    return "";
  }, [file]);

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setResult(null);
    setError(null);
  }

  async function uploadFile() {
    if (!file || fileValidation) {
      setError(fileValidation || "Choose a valid file first.");
      return;
    }
    setIsUploading(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    const token = localStorage.getItem("access_token");
    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
    try {
      const response = await fetch(
        `${baseUrl}/api/integrations/imports/upload?target_resource=${encodeURIComponent(targetResource)}&source_name=${encodeURIComponent(sourceName || "Manual upload")}`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          body: form,
        }
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(payload.detail ?? "Upload failed");
      }
      setResult(await response.json());
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function createConnector() {
    if (!connectorDraft.connector_name.trim()) {
      setError("Connector name is required.");
      return;
    }
    setError(null);
    await api.post("/api/enterprise/connectors", connectorDraft);
    setConnectorDraft({ connector_name: "", connector_type: "database", environment: "production", system_owner: "", status: "active" });
    await loadSummary();
  }

  const cards = [
    { label: "Connectors", value: summary?.connectors.total ?? 0, hint: `${summary?.connectors.active ?? 0} active`, icon: PlugZap },
    { label: "Imports", value: summary?.imports.total ?? 0, hint: `${summary?.imports.imported_rows ?? 0} rows imported`, icon: FileUp },
    { label: "Import Errors", value: summary?.imports.error_rows ?? 0, hint: `${summary?.imports.failed_recent ?? 0} recent failed`, icon: ShieldAlert },
    { label: "Formats", value: Object.keys(summary?.imports.formats ?? {}).length, hint: Object.keys(summary?.imports.formats ?? {}).join(", ") || "none", icon: Database },
  ];

  return (
    <div className="space-y-6">
      <section className="soft-panel rounded-lg p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-blue-800">Integration Operations</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Gateways and Data Ingestion</h1>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
              Configure system gateways, upload operational files, validate imports, and keep source-system data flowing into BusinessOS without duplicate manual entry.
            </p>
          </div>
          <button
            type="button"
            onClick={() => loadSummary().catch((err) => setError(err instanceof Error ? err.message : "Refresh failed"))}
            className="focus-ring inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </section>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="interactive-lift soft-panel rounded-lg p-4">
            <div className="flex items-center justify-between">
              <card.icon size={18} className="text-blue-800" />
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{card.hint}</span>
            </div>
            <p className="mt-4 text-xs font-semibold uppercase text-slate-500">{card.label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
        <section className="soft-panel rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Upload Data</h2>
              <p className="text-sm text-slate-600">Use this for pipeline, accounts, staff, licence, finance, and operational imports.</p>
            </div>
            <FileUp size={20} className="text-blue-800" />
          </div>

          <div className="grid gap-3 lg:grid-cols-[180px_1fr]">
            <select value={targetResource} onChange={(event) => setTargetResource(event.target.value)} className="focus-ring h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900">
              {targetOptions.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <input
              value={sourceName}
              onChange={(event) => setSourceName(event.target.value)}
              placeholder="Source name, e.g. Sales pipeline upload, AD export, ERP extract"
              className="focus-ring h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm text-slate-900"
            />
          </div>

          <div className="mt-3 grid gap-3 lg:grid-cols-[1fr_auto]">
            <input
              type="file"
              onChange={chooseFile}
              accept={acceptedExtensions.join(",")}
              className="focus-ring rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-800 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white"
            />
            <button
              type="button"
              onClick={uploadFile}
              disabled={!file || isUploading || Boolean(fileValidation)}
              className="focus-ring rounded-lg bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800 disabled:bg-slate-300 disabled:text-slate-600"
            >
              {isUploading ? "Uploading..." : "Upload and Process"}
            </button>
          </div>
          <p className={`mt-2 text-sm ${fileValidation && file ? "text-amber-700" : "text-slate-500"}`}>
            {fileValidation || `Ready to process ${file?.name}`}
          </p>

          {result && (
            <div className="mt-4 grid gap-3 rounded-lg bg-slate-50 p-4 text-sm md:grid-cols-4">
              {[
                ["Import ID", result.business_id ?? "-"],
                ["Parsed Rows", result.parsed_rows ?? 0],
                ["Imported Rows", result.imported_rows ?? 0],
                ["Status", result.status ?? "-"],
              ].map(([label, value]) => (
                <div key={label}>
                  <p className="text-slate-500">{label}</p>
                  <p className="font-semibold text-slate-900">{value}</p>
                </div>
              ))}
              <p className="text-slate-600 md:col-span-4">{result.parse_summary}</p>
            </div>
          )}
        </section>

        <section className="soft-panel rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Quick Connector</h2>
              <p className="text-sm text-slate-600">Register a gateway before detailed configuration.</p>
            </div>
            <PlugZap size={20} className="text-blue-800" />
          </div>
          <div className="grid gap-3">
            <input value={connectorDraft.connector_name} onChange={(event) => setConnectorDraft((current) => ({ ...current, connector_name: event.target.value }))} placeholder="Connector name" className="focus-ring h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm" />
            <div className="grid gap-3 sm:grid-cols-2">
              <select value={connectorDraft.connector_type} onChange={(event) => setConnectorDraft((current) => ({ ...current, connector_type: event.target.value }))} className="focus-ring h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm">
                <option value="database">Database</option>
                <option value="active_directory">Active Directory</option>
                <option value="erp">ERP</option>
                <option value="ticketing">Ticketing</option>
                <option value="banking">Banking</option>
                <option value="cloud_storage">Cloud Storage</option>
              </select>
              <select value={connectorDraft.environment} onChange={(event) => setConnectorDraft((current) => ({ ...current, environment: event.target.value }))} className="focus-ring h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm">
                <option value="production">Production</option>
                <option value="staging">Staging</option>
                <option value="sandbox">Sandbox</option>
              </select>
            </div>
            <input value={connectorDraft.system_owner} onChange={(event) => setConnectorDraft((current) => ({ ...current, system_owner: event.target.value }))} placeholder="System owner" className="focus-ring h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm" />
            <button type="button" onClick={createConnector} className="focus-ring inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
              <CheckCircle2 size={16} />
              Save Gateway
            </button>
          </div>

          <div className="mt-5 space-y-2">
            <p className="text-sm font-semibold text-slate-900">Readiness</p>
            {summary?.readiness.map((item) => (
              <div key={item.label} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                <span className="text-slate-700">{item.label}</span>
                <span className={`rounded-full px-2 py-1 text-xs font-semibold ${item.status === "healthy" || item.status === "ready" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"}`}>
                  {item.status.replace("_", " ")}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <ResourcePage resourceKey="enterprise.connectors" />
      <ResourcePage resourceKey="enterprise.imports" />
    </div>
  );
}
