"use client";

import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, Download, FileText, Filter, Plus, RefreshCw, Search, Trash2, Upload, X } from "lucide-react";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { API_BASE_URL } from "@/lib/constants";
import { api } from "@/services/api";
import { FieldConfig, ResourceConfig } from "@/lib/resourceConfigs";
import { hasResourcePermission } from "@/lib/permissions";

type RecordValue = string | number | boolean | null | undefined;
type DataRecord = Record<string, RecordValue> & { id?: string };
type WorkflowDialog = { action: string; title: string } | null;

interface ResourceAnalytics {
  total?: number;
  total_value?: number;
  by_status?: Array<{ name: string; count: number }>;
}

interface OptionRecord {
  id: string;
  [key: string]: RecordValue;
}

interface ResourceManagerProps {
  config: ResourceConfig;
}

function emptyForm(config: ResourceConfig) {
  return config.fields.reduce<Record<string, RecordValue>>((acc, field) => {
    acc[field.name] = field.defaultValue ?? (field.type === "checkbox" ? false : "");
    return acc;
  }, {});
}

function formatLabel(value: RecordValue) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value).replaceAll("_", " ").replaceAll("-", " ");
}

function numberValue(value: RecordValue) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function titleFromFileName(fileName: string) {
  return fileName.replace(/\.[^.]+$/, "").replaceAll("_", " ").replaceAll("-", " ");
}

function inferDocumentType(fileName: string, content: string) {
  const haystack = `${fileName} ${content}`.toLowerCase();
  if (haystack.includes("invoice")) return "Invoice";
  if (haystack.includes("receipt")) return "Receipt";
  if (haystack.includes("contract") || haystack.includes("agreement")) return "Contract";
  if (haystack.includes("quotation") || haystack.includes("quote")) return "Quotation";
  if (haystack.includes("purchase order") || haystack.includes("lpo")) return "LPO";
  if (haystack.includes("tax") || haystack.includes("vat") || haystack.includes("paye")) return "Tax Document";
  if (haystack.includes("payment") || haystack.includes("confirmation")) return "Payment Confirmation";
  const extension = fileName.split(".").pop()?.toUpperCase();
  return extension ? `${extension} Document` : "Document";
}

function inferRelatedRecordType(content: string) {
  const haystack = content.toLowerCase();
  if (haystack.includes("invoice")) return "Invoice";
  if (haystack.includes("receipt")) return "Receipt";
  if (haystack.includes("purchase order") || haystack.includes("lpo")) return "Purchase Order";
  if (haystack.includes("contract") || haystack.includes("agreement")) return "Contract";
  if (haystack.includes("tax") || haystack.includes("vat") || haystack.includes("paye")) return "Tax";
  return "";
}

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? "").split(",")[1] ?? "");
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function isDocumentResource(config: ResourceConfig) {
  return config.key === "finance.documents" || config.key === "hrm.documents";
}

function isPreviewableFile(url: string) {
  return /\.(pdf|png|jpe?g|gif|webp|svg|txt|csv|json|xml|html|md)$/i.test(url);
}

function backendUrl(path: string) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/uploads") || path.startsWith("/api")) return `${API_BASE_URL}${path}`;
  return path;
}

export default function ResourceManager({ config }: ResourceManagerProps) {
  const { user } = useAuth();
  const canWrite = hasResourcePermission(user, config.endpoint, config.key, "create") || hasResourcePermission(user, config.endpoint, config.key, "update");
  const canDelete = hasResourcePermission(user, config.endpoint, config.key, "delete") && (config.key !== "hrm.employees" || user?.role === "admin");
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [analytics, setAnalytics] = useState<ResourceAnalytics | null>(null);
  const [options, setOptions] = useState<Record<string, OptionRecord[]>>({});
  const [form, setForm] = useState<Record<string, RecordValue>>(() => emptyForm(config));
  const [editing, setEditing] = useState<DataRecord | null>(null);
  const [selected, setSelected] = useState<DataRecord | null>(null);
  const [isSelectedEditing, setIsSelectedEditing] = useState(false);
  const [selectedForm, setSelectedForm] = useState<Record<string, RecordValue>>(() => emptyForm(config));
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [localFilter, setLocalFilter] = useState("");
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [workflowDialog, setWorkflowDialog] = useState<WorkflowDialog>(null);
  const [workflowForm, setWorkflowForm] = useState<Record<string, RecordValue>>({});
  const bulkUploadRef = useRef<HTMLInputElement | null>(null);

  const tableFields = config.fields.filter((field) => field.table);
  const statusField = config.statusField;

  function isReadOnlyField(field: FieldConfig) {
    return config.key === "hrm.employees" && field.name === "employee_code";
  }

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const [items, stats] = await Promise.all([
        api.get<DataRecord[]>(config.endpoint),
        api.get<ResourceAnalytics>(config.analyticsEndpoint).catch(() => null),
      ]);
      setRecords(items);
      setSelectedIds(new Set());
      setAnalytics(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load records");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadOptions() {
    const selectFields = config.fields.filter((field) => field.selectEndpoint);
    const optionEntries = await Promise.all(
      selectFields.map(async (field) => {
        const rows = await api.get<OptionRecord[]>(field.selectEndpoint as string).catch(() => []);
        return [field.name, rows] as const;
      })
    );
    setOptions(Object.fromEntries(optionEntries));
  }

  /* eslint-disable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */
  useEffect(() => {
    loadData();
    loadOptions();
  }, [config.key]);
  /* eslint-enable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */

  const filteredRecords = useMemo(() => {
    const term = localFilter.trim().toLowerCase();
    return records.filter((record) => {
      const matchesSearch =
        !term ||
        config.searchFields.some((field) =>
          String(record[field] ?? "").toLowerCase().includes(term)
        );
      const matchesStatus =
        !statusFilter || !statusField || String(record[statusField] ?? "") === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [records, localFilter, statusFilter, config.searchFields, statusField]);

  const localAnalytics = useMemo(() => {
    const byStatus = new Map<string, number>();
    if (statusField) {
      records.forEach((record) => {
        const key = String(record[statusField] ?? "Unspecified");
        byStatus.set(key, (byStatus.get(key) ?? 0) + 1);
      });
    }
    const fallback = {
      total: records.length,
      total_value: config.valueField
        ? records.reduce((sum, record) => sum + numberValue(record[config.valueField as string]), 0)
        : 0,
      by_status: Array.from(byStatus.entries()).map(([name, count]) => ({ name, count })),
    };
    if (analytics) {
      return {
        total: numberValue(analytics.total ?? fallback.total),
        total_value: numberValue(analytics.total_value ?? fallback.total_value),
        by_status: Array.isArray(analytics.by_status) ? analytics.by_status : fallback.by_status,
      };
    }
    return {
      total: fallback.total,
      total_value: fallback.total_value,
      by_status: fallback.by_status,
    };
  }, [analytics, records, statusField, config.valueField]);

  const visibleSelectableIds = useMemo(
    () => filteredRecords.map((record) => record.id).filter((id): id is string => Boolean(id)),
    [filteredRecords]
  );

  const allVisibleSelected = visibleSelectableIds.length > 0 && visibleSelectableIds.every((id) => selectedIds.has(id));

  function optionLabel(field: FieldConfig, value: RecordValue) {
    const rows = options[field.name] ?? [];
    const match = rows.find((row) => row.id === value);
    if (!match) return formatLabel(value);
    const labels = field.selectLabel ?? ["name"];
    return labels.map((label) => match[label]).filter(Boolean).join(" ");
  }

  function displayValue(field: FieldConfig, record: DataRecord) {
    const value = record[field.name];
    if (field.selectEndpoint) return optionLabel(field, value);
    if (field.type === "number" && value !== null && value !== undefined && value !== "") {
      return Number(value).toLocaleString();
    }
    return formatLabel(value);
  }

  function fileUrl(record: DataRecord) {
    const rawUrl = String(record.file_url ?? "");
    if (rawUrl) return backendUrl(rawUrl);
    if (config.key === "finance.documents" && record.id) {
      return backendUrl(`/api/finance/documents/file/${record.id}`);
    }
    return "";
  }

  function documentLabel(record: DataRecord) {
    return String(record.document_title ?? record.file_name ?? "Document");
  }

  function openCreate() {
    setEditing(null);
    setForm(() => {
      const next = emptyForm(config);
      config.fields.forEach((field) => {
        if (field.autoCurrentUser) next[field.name] = user?.full_name ?? "";
      });
      return next;
    });
    setIsFormOpen(true);
  }

  function openSelected(record: DataRecord) {
    setSelected(record);
    setIsSelectedEditing(false);
    setSelectedForm(
      config.fields.reduce<Record<string, RecordValue>>((acc, field) => {
        acc[field.name] = record[field.name] ?? field.defaultValue ?? (field.type === "checkbox" ? false : "");
        return acc;
      }, {})
    );
  }

  function closeSelected() {
    setSelected(null);
    setIsSelectedEditing(false);
    setSelectedForm(emptyForm(config));
    setWorkflowDialog(null);
    setWorkflowForm({});
  }

  function startSelectedEdit() {
    if (!selected) return;
    setSelectedForm(
      config.fields.reduce<Record<string, RecordValue>>((acc, field) => {
        acc[field.name] = selected[field.name] ?? field.defaultValue ?? (field.type === "checkbox" ? false : "");
        return acc;
      }, {})
    );
    setIsSelectedEditing(true);
  }

  async function handleFileSelection(field: FieldConfig, file: File | null) {
    if (!file) return;
    setError(null);
    try {
      const readableText = await file.text().catch(() => "");
      let uploaded: { file_name?: string; file_url?: string } = { file_name: file.name };
      if (field.uploadEndpoint) {
        uploaded = await api.post<{ file_name: string; file_url: string }>(field.uploadEndpoint, {
          file_name: file.name,
          mime_type: file.type,
          content_base64: await fileToBase64(file),
        });
      }

      setForm((current) => ({
        ...current,
        [field.name]: file.name,
        file_name: uploaded.file_name ?? file.name,
        file_url: uploaded.file_url ?? current.file_url ?? "",
        document_title: current.document_title || titleFromFileName(file.name),
        document_type: current.document_type || inferDocumentType(file.name, readableText),
        related_record_type: current.related_record_type || inferRelatedRecordType(readableText),
        uploaded_by: current.uploaded_by || user?.full_name || "",
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not upload or parse document");
    }
  }

  async function handleSelectedFileSelection(field: FieldConfig, file: File | null) {
    if (!file) return;
    setError(null);
    try {
      const readableText = await file.text().catch(() => "");
      let uploaded: { file_name?: string; file_url?: string } = { file_name: file.name };
      if (field.uploadEndpoint) {
        uploaded = await api.post<{ file_name: string; file_url: string }>(field.uploadEndpoint, {
          file_name: file.name,
          mime_type: file.type,
          content_base64: await fileToBase64(file),
        });
      }

      setSelectedForm((current) => ({
        ...current,
        [field.name]: file.name,
        file_name: uploaded.file_name ?? file.name,
        file_url: uploaded.file_url ?? current.file_url ?? "",
        document_title: current.document_title || titleFromFileName(file.name),
        document_type: current.document_type || inferDocumentType(file.name, readableText),
        related_record_type: current.related_record_type || inferRelatedRecordType(readableText),
        uploaded_by: current.uploaded_by || user?.full_name || "",
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not upload or parse document");
    }
  }

  function cleanPayloadFrom(source: Record<string, RecordValue>) {
    return Object.fromEntries(
      Object.entries(source)
        .map(([key, value]) => {
          const field = config.fields.find((item) => item.name === key);
          if (field?.clientOnly) return [key, null];
          if (value === "") return [key, null];
          if (field?.autoCurrentUser && !value) return [key, user?.full_name ?? ""];
          if (field?.type === "number") return [key, Number(value)];
          return [key, value];
        })
        .filter(([, value]) => value !== null)
    );
  }

  function cleanPayload() {
    return cleanPayloadFrom(form);
  }

  async function saveRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      if (editing?.id) {
        await api.put(`${config.endpoint}/${editing.id}`, cleanPayload());
      } else {
        await api.post(config.endpoint, cleanPayload());
      }
      setIsFormOpen(false);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save record");
    } finally {
      setIsSaving(false);
    }
  }

  async function saveSelectedRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected?.id) return;
    setIsSaving(true);
    setError(null);
    try {
      const updated = await api.put<DataRecord>(`${config.endpoint}/${selected.id}`, cleanPayloadFrom(selectedForm));
      setSelected(updated);
      setIsSelectedEditing(false);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save record");
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteRecord(record: DataRecord) {
    if (!record.id) return;
    const label = tableFields.map((field) => displayValue(field, record)).find((value) => value !== "-");
    if (!window.confirm(`Delete ${label ?? "this record"}?`)) return;
    setError(null);
    try {
      await api.delete(`${config.endpoint}/${record.id}`);
      if (selected?.id === record.id) closeSelected();
      await loadData();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete record";
      setError(config.key === "hrm.employees" && message.includes("admin") ? "Deleting employee master data is restricted to admins. Managers can update status, transfer, suspend, or offboard employees instead." : message);
    }
  }

  function actionEndpoint(action: string) {
    if (config.key === "crm.opportunities") {
      if (action === "move-stage") return "stage";
      if (action === "close-won") return "mark-won";
      if (action === "close-lost") return "mark-lost";
    }
    return action;
  }

  function openWorkflowAction(action: string) {
    if (!selected?.id) return;
    if ((config.key === "crm.opportunities" || config.key === "crm.enterprise.opportunities") && ["move-stage", "mark-won", "mark-lost", "close-won", "close-lost"].includes(action)) {
      const currentStage = String(selected.stage ?? "");
      setWorkflowForm({
        stage: currentStage || "Stage 1.a Discovery",
        lpo_document_url: selected.lpo_document_url ?? "",
        loss_reason: selected.win_loss_reason ?? "",
        comments: "",
      });
      setWorkflowDialog({
        action,
        title:
          action === "move-stage"
            ? "Move Opportunity Stage"
            : action === "mark-won" || action === "close-won"
              ? "Close Deal as Won"
              : "Close Deal as Lost",
      });
      return;
    }
    void runWorkflowAction(action);
  }

  async function runWorkflowAction(action: string, payload: Record<string, RecordValue> = {}) {
    if (!selected?.id) return;
    const reason = action === "unlock" ? window.prompt("Reason for unlocking this record?") : null;
    if (action === "unlock" && !reason) return;
    setIsSaving(true);
    setError(null);
    try {
      const updated = await api.post<DataRecord & { recruitment?: DataRecord }>(`${config.endpoint}/${selected.id}/${actionEndpoint(action)}`, {
        ...payload,
        reason,
        comments: payload.comments ?? reason,
        adjustment_reason: payload.adjustment_reason ?? reason,
      });
      setSelected(updated.recruitment ?? updated);
      setWorkflowDialog(null);
      setWorkflowForm({});
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} record`);
    } finally {
      setIsSaving(false);
    }
  }

  function submitWorkflowAction(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!workflowDialog) return;
    const action = workflowDialog.action;
    const payload: Record<string, RecordValue> = {};
    if (action === "move-stage") {
      payload.stage = workflowForm.stage;
      if (String(workflowForm.stage ?? "").includes("Closed as Won")) payload.lpo_document_url = workflowForm.lpo_document_url;
      if (String(workflowForm.stage ?? "").includes("Closed as Lost")) {
        payload.loss_reason = workflowForm.loss_reason;
        payload.reason = workflowForm.loss_reason;
      }
    } else if (action === "mark-won" || action === "close-won") {
      payload.lpo_document_url = workflowForm.lpo_document_url;
      payload.comments = workflowForm.comments;
    } else if (action === "mark-lost" || action === "close-lost") {
      payload.loss_reason = workflowForm.loss_reason;
      payload.reason = workflowForm.loss_reason;
      payload.comments = workflowForm.comments;
    }
    void runWorkflowAction(action, payload);
  }

  function toggleRecordSelection(recordId?: string) {
    if (!recordId) return;
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(recordId)) next.delete(recordId);
      else next.add(recordId);
      return next;
    });
  }

  function toggleAllVisible() {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (allVisibleSelected) {
        visibleSelectableIds.forEach((id) => next.delete(id));
      } else {
        visibleSelectableIds.forEach((id) => next.add(id));
      }
      return next;
    });
  }

  async function deleteSelectedRecords() {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;
    if (!window.confirm(`Delete ${ids.length} selected record${ids.length === 1 ? "" : "s"}?`)) return;
    setError(null);
    try {
      try {
        await api.post("/api/integrations/bulk-delete", { endpoint: config.endpoint, ids });
      } catch {
        await Promise.all(ids.map((id) => api.delete(`${config.endpoint}/${id}`)));
      }
      if (selected?.id && selectedIds.has(selected.id)) closeSelected();
      setSelectedIds(new Set());
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete selected records");
    }
  }

  async function uploadBulkData(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setIsImporting(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    const token = localStorage.getItem("access_token");
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/integrations/imports/bulk-upload?endpoint=${encodeURIComponent(config.endpoint)}&resource_title=${encodeURIComponent(config.title)}`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          body: form,
        }
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(typeof payload.detail === "string" ? payload.detail : "Upload failed");
      }
      const result = await response.json();
      if (!result.imported_rows) {
        throw new Error(result.parse_summary || "The file was read, but no rows matched this section's fields.");
      }
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="module-hero overflow-hidden rounded-lg p-6 text-white">
        <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-100">Operational workspace</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">{config.title}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-blue-50">{config.description}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={loadData} className="border-white/20 bg-white/12 text-white hover:bg-white/20">
            <RefreshCw size={16} />
            Refresh
          </Button>
          {canWrite && (
            <>
              <input
                ref={bulkUploadRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={uploadBulkData}
                className="hidden"
              />
              <Button variant="secondary" onClick={() => bulkUploadRef.current?.click()} disabled={isImporting} className="border-white/20 bg-white/12 text-white hover:bg-white/20">
                <Upload size={16} />
                {isImporting ? "Uploading..." : "Upload Data"}
              </Button>
              <Button onClick={openCreate} className="bg-white text-slate-950 hover:bg-blue-50">
                <Plus size={16} />
                Add {config.title.replace(/s$/, "")}
              </Button>
            </>
          )}
        </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        <button
          onClick={() => setStatusFilter(null)}
          className={`soft-panel interactive-lift rounded-lg p-4 text-left ${!statusFilter ? "ring-2 ring-[var(--gold)]" : ""}`}
        >
          <p className="text-sm text-slate-500">Total Records</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{localAnalytics.total}</p>
          <p className="mt-1 text-xs text-slate-500">Click to view all records</p>
        </button>

        {config.valueField ? (
          <div className="soft-panel rounded-lg p-4">
            <p className="text-sm text-slate-500">Total Value</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {localAnalytics.total_value.toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-slate-500">Calculated from {config.valueField}</p>
          </div>
        ) : (
          <div className="soft-panel rounded-lg p-4">
            <p className="text-sm text-slate-500">Visible Records</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{filteredRecords.length}</p>
            <p className="mt-1 text-xs text-slate-500">After page filters</p>
          </div>
        )}

        <div className="soft-panel rounded-lg p-4">
          <p className="text-sm text-slate-500">{statusField ? "Status Breakdown" : "Record Health"}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {localAnalytics.by_status.length ? (
              localAnalytics.by_status.map((item) => (
                <button
                  key={item.name}
                  onClick={() => setStatusFilter(statusFilter === item.name ? null : item.name)}
                  className={`status-pill px-3 py-1 text-xs transition ${statusFilter === item.name ? "bg-[var(--brand)] text-white" : "text-slate-700 hover:bg-[var(--brand-soft)]"}`}
                >
                  {formatLabel(item.name)}: {item.count}
                </button>
              ))
            ) : (
              <span className="text-sm text-slate-500">Ready for new data</span>
            )}
          </div>
        </div>
      </div>

      <div className="glass-panel overflow-hidden rounded-lg">
        <div className="flex flex-col gap-3 border-b border-slate-200/80 p-4 md:flex-row md:items-center md:justify-between">
          <div className="flex w-full flex-col gap-3 md:flex-row md:items-center">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
              <Filter size={16} />
              <span>Page filters</span>
            </div>
            <div className="focus-ring flex h-10 w-full max-w-lg items-center rounded-lg border border-slate-200 bg-white/82 px-3 shadow-sm">
              <Search size={16} className="text-slate-400" />
              <input
                type="text"
                value={localFilter}
                onChange={(event) => setLocalFilter(event.target.value)}
                placeholder={`Filter ${config.title.toLowerCase()} on this page...`}
                className="w-full bg-transparent px-2 text-sm text-slate-800 outline-none placeholder:text-slate-400"
              />
            </div>
          </div>
          {(statusFilter || localFilter) && (
            <Button
              variant="ghost"
              onClick={() => {
                setStatusFilter(null);
                setLocalFilter("");
              }}
            >
              <X size={16} />
              Clear filters
            </Button>
          )}
        </div>

        {error && <div className="border-b border-red-200 bg-red-50/90 p-4 text-sm text-red-700">{error}</div>}

        {selectedIds.size > 0 && (
          <div className="flex flex-col gap-3 border-b border-slate-200/80 bg-blue-50/70 p-4 text-sm md:flex-row md:items-center md:justify-between">
            <span className="font-medium text-slate-700">
              {selectedIds.size} selected
            </span>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setSelectedIds(new Set())}>
                Clear selection
              </Button>
              {canDelete && (
                <Button variant="danger" onClick={deleteSelectedRecords}>
                  <Trash2 size={16} />
                  Delete selected
                </Button>
              )}
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50/90 text-left text-slate-500">
              <tr>
                <th className="w-12 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={allVisibleSelected}
                    onChange={toggleAllVisible}
                    aria-label="Select all visible records"
                    className="h-4 w-4"
                  />
                </th>
                {tableFields.map((field) => (
                  <th key={field.name} className="px-4 py-3 text-xs font-semibold uppercase tracking-wide">{field.label}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/75">
              {isLoading ? (
                <tr>
                  <td className="px-4 py-8 text-center text-slate-500" colSpan={tableFields.length + 1}>
                    Loading records...
                  </td>
                </tr>
              ) : filteredRecords.length ? (
                filteredRecords.map((record) => (
                  <tr
                    key={record.id}
                    onDoubleClick={() => openSelected(record)}
                    className="cursor-default transition hover:bg-blue-50/45"
                    title="Double-click to view this record"
                  >
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={Boolean(record.id && selectedIds.has(record.id))}
                        onChange={() => toggleRecordSelection(record.id)}
                        onDoubleClick={(event) => event.stopPropagation()}
                        aria-label="Select record"
                        className="h-4 w-4"
                      />
                    </td>
                    {tableFields.map((field, fieldIndex) => (
                      <td key={field.name} className="px-4 py-3 text-slate-700">
                        {isDocumentResource(config) && (field.name === "document_title" || field.name === "file_name") && fileUrl(record) ? (
                          <a
                            href={fileUrl(record)}
                            target="_blank"
                            rel="noreferrer"
                            onDoubleClick={(event) => event.stopPropagation()}
                            className="inline-flex items-center gap-2 text-left font-medium text-blue-700 hover:text-blue-900"
                          >
                            <FileText size={15} />
                            {displayValue(field, record)}
                          </a>
                        ) : fieldIndex === 0 ? (
                          <button
                            type="button"
                            onClick={() => openSelected(record)}
                            onDoubleClick={(event) => {
                              event.stopPropagation();
                              openSelected(record);
                            }}
                            className="text-left font-medium text-blue-700 hover:text-blue-900"
                          >
                            {displayValue(field, record)}
                          </button>
                        ) : (
                          displayValue(field, record)
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-4 py-8 text-center text-slate-500" colSpan={tableFields.length + 1}>
                    No records found. Add the first one to start using this module.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
          <form onSubmit={saveRecord} className="glass-panel max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg p-6">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-xl font-semibold">{editing ? "Edit" : "Add"} {config.title.replace(/s$/, "")}</h2>
              <button type="button" onClick={() => setIsFormOpen(false)} className="focus-ring rounded-lg p-2 hover:bg-slate-100">
                <X size={18} />
              </button>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {config.fields.map((field) => (
                <label key={field.name} className={field.type === "textarea" ? "md:col-span-2" : ""}>
                  <span className="text-sm font-medium text-slate-700">{field.label}</span>
                  {field.type === "textarea" ? (
                    <textarea
                      value={String(form[field.name] ?? "")}
                      onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.value }))}
                      required={field.required}
                      className="focus-ring mt-1 min-h-24 w-full rounded-lg border border-slate-200 bg-white/80 px-3 py-2 text-sm focus:border-blue-500"
                    />
                  ) : field.type === "select" ? (
                    <select
                      value={String(form[field.name] ?? "")}
                      onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.value }))}
                      required={field.required}
                      disabled={isReadOnlyField(field)}
                      className="focus-ring mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white/80 px-3 text-sm focus:border-blue-500"
                    >
                      <option value="">Select {field.label}</option>
                      {field.selectEndpoint
                        ? (options[field.name] ?? []).map((item) => (
                            <option key={item.id} value={item.id}>
                              {optionLabel(field, item.id)}
                            </option>
                          ))
                        : (field.options ?? []).map((option) => (
                            <option key={option} value={option}>{formatLabel(option)}</option>
                          ))}
                    </select>
                  ) : field.type === "checkbox" ? (
                    <input
                      type="checkbox"
                      checked={Boolean(form[field.name])}
                      onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.checked }))}
                      className="mt-3 h-5 w-5"
                    />
                  ) : field.type === "file" ? (
                    <div className="mt-1 rounded-lg border border-dashed border-slate-300 bg-slate-50/80 p-4">
                      <input
                        type="file"
                        onChange={(event) => handleFileSelection(field, event.target.files?.[0] ?? null)}
                        className="w-full text-sm text-slate-700"
                      />
                      <p className="mt-2 text-xs text-slate-500">
                        Upload from this computer. For Drive, OneDrive, SharePoint, or cloud storage, paste the share link in the URL field.
                      </p>
                    </div>
                  ) : (
                    <input
                      type={field.type ?? "text"}
                      value={String(form[field.name] ?? "")}
                      onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.value }))}
                      required={field.required}
                      disabled={isReadOnlyField(field)}
                      placeholder={isReadOnlyField(field) ? "Generated by EMP-002" : undefined}
                      className="focus-ring mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white/80 px-3 text-sm focus:border-blue-500"
                    />
                  )}
                </label>
              ))}
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setIsFormOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={isSaving}>{isSaving ? "Saving..." : "Save Record"}</Button>
            </div>
          </form>
        </div>
      )}

      {selected && (
        <div className="fixed inset-y-0 right-0 z-40 w-full max-w-2xl overflow-y-auto border-l border-slate-200 bg-white/92 p-6 shadow-2xl backdrop-blur-xl">
          <div className="mb-5 flex flex-col gap-3 border-b border-slate-200/80 pb-4 md:flex-row md:items-center md:justify-between">
            <div>
              <button
                onClick={closeSelected}
                className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-950"
              >
                <ArrowLeft size={16} />
                Back
              </button>
              <h2 className="text-xl font-semibold">{isSelectedEditing ? "Edit Record" : "Record Details"}</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {!isSelectedEditing && canWrite && (
                <Button variant="secondary" onClick={startSelectedEdit}>
                  Edit Record
                </Button>
              )}
              {!isSelectedEditing && canWrite && config.workflowActions?.map((action) => (
                <Button key={action} variant="secondary" onClick={() => openWorkflowAction(action)} disabled={isSaving}>
                  {formatLabel(action)}
                </Button>
              ))}
              {canDelete && (
                <Button variant="danger" onClick={() => deleteRecord(selected)}>
                  <Trash2 size={16} />
                  Delete Record
                </Button>
              )}
              <button onClick={closeSelected} className="rounded-lg p-2 hover:bg-slate-100">
                <X size={18} />
              </button>
            </div>
          </div>

          {!isSelectedEditing ? (
            <div className="space-y-3">
              {isDocumentResource(config) && fileUrl(selected) && (
                <div className="rounded-xl border bg-white p-3">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-medium uppercase text-slate-500">Preview</p>
                      <p className="mt-1 text-sm font-semibold text-slate-900">{documentLabel(selected)}</p>
                    </div>
                    <a
                      href={fileUrl(selected)}
                      target="_blank"
                      rel="noreferrer"
                      download={String(selected.file_name ?? documentLabel(selected))}
                    className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800"
                    >
                      <Download size={16} />
                      Download
                    </a>
                  </div>
                  {isPreviewableFile(fileUrl(selected)) ? (
                    <iframe
                      src={fileUrl(selected)}
                      title={documentLabel(selected)}
                      className="h-96 w-full rounded-lg border bg-slate-50"
                    />
                  ) : (
                    <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
                      This file type may not preview in the browser. Use Download/Open to view it.
                    </div>
                  )}
                </div>
              )}
              <div className="grid gap-3 md:grid-cols-2">
                {config.fields.map((field) => (
                <div key={field.name} className="rounded-lg border border-slate-200/80 bg-slate-50/80 p-3">
                    <p className="text-xs font-medium uppercase text-slate-500">{field.label}</p>
                    <p className="mt-1 text-sm text-slate-900">{displayValue(field, selected)}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <form onSubmit={saveSelectedRecord} className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                {config.fields.map((field) => (
                  <label key={field.name} className={field.type === "textarea" ? "md:col-span-2" : ""}>
                    <span className="text-sm font-medium text-slate-700">{field.label}</span>
                    {field.type === "textarea" ? (
                      <textarea
                        value={String(selectedForm[field.name] ?? "")}
                        onChange={(event) => setSelectedForm((current) => ({ ...current, [field.name]: event.target.value }))}
                        required={field.required}
                        className="focus-ring mt-1 min-h-24 w-full rounded-lg border border-slate-200 bg-white/80 px-3 py-2 text-sm focus:border-blue-500"
                      />
                    ) : field.type === "select" ? (
                      <select
                        value={String(selectedForm[field.name] ?? "")}
                        onChange={(event) => setSelectedForm((current) => ({ ...current, [field.name]: event.target.value }))}
                        required={field.required}
                        disabled={isReadOnlyField(field)}
                        className="focus-ring mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white/80 px-3 text-sm focus:border-blue-500"
                      >
                        <option value="">Select {field.label}</option>
                        {field.selectEndpoint
                          ? (options[field.name] ?? []).map((item) => (
                              <option key={item.id} value={item.id}>
                                {optionLabel(field, item.id)}
                              </option>
                            ))
                          : (field.options ?? []).map((option) => (
                              <option key={option} value={option}>{formatLabel(option)}</option>
                            ))}
                      </select>
                    ) : field.type === "checkbox" ? (
                      <input
                        type="checkbox"
                        checked={Boolean(selectedForm[field.name])}
                        onChange={(event) => setSelectedForm((current) => ({ ...current, [field.name]: event.target.checked }))}
                        className="mt-3 h-5 w-5"
                      />
                    ) : field.type === "file" ? (
                      <div className="mt-1 rounded-lg border border-dashed border-slate-300 bg-slate-50/80 p-4">
                        <input
                          type="file"
                          onChange={(event) => handleSelectedFileSelection(field, event.target.files?.[0] ?? null)}
                          className="w-full text-sm text-slate-700"
                        />
                      </div>
                    ) : (
                      <input
                        type={field.type ?? "text"}
                        value={String(selectedForm[field.name] ?? "")}
                        onChange={(event) => setSelectedForm((current) => ({ ...current, [field.name]: event.target.value }))}
                        required={field.required}
                        disabled={isReadOnlyField(field)}
                        placeholder={isReadOnlyField(field) ? "Generated by EMP-002" : undefined}
                        className="focus-ring mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white/80 px-3 text-sm focus:border-blue-500"
                      />
                    )}
                  </label>
                ))}
              </div>
              <div className="flex justify-end gap-3 border-t pt-4">
                <Button type="button" variant="secondary" onClick={() => setIsSelectedEditing(false)}>
                  Cancel Edit
                </Button>
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? "Saving..." : "Save Record"}
                </Button>
              </div>
            </form>
          )}
        </div>
      )}

      {selected && workflowDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
          <form onSubmit={submitWorkflowAction} className="glass-panel w-full max-w-lg rounded-lg p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">{workflowDialog.title}</h2>
                <p className="mt-1 text-sm text-slate-500">{String(selected.title ?? selected.business_id ?? "Selected opportunity")}</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setWorkflowDialog(null);
                  setWorkflowForm({});
                }}
                className="focus-ring rounded-lg p-2 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              {workflowDialog.action === "move-stage" && (
                <label>
                  <span className="text-sm font-medium text-slate-700">Pipeline Stage</span>
                  <select
                    value={String(workflowForm.stage ?? "")}
                    onChange={(event) => setWorkflowForm((current) => ({ ...current, stage: event.target.value }))}
                    required
                    className="focus-ring mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white/80 px-3 text-sm focus:border-blue-500"
                  >
                    <option value="">Select stage</option>
                    {(config.fields.find((field) => field.name === "stage")?.options ?? []).map((stage) => (
                      <option key={stage} value={stage}>{stage}</option>
                    ))}
                  </select>
                </label>
              )}

              {(workflowDialog.action === "mark-won" ||
                workflowDialog.action === "close-won" ||
                String(workflowForm.stage ?? "").includes("Closed as Won")) && (
                <label>
                  <span className="text-sm font-medium text-slate-700">LPO / Contract Document URL</span>
                  <input
                    type="text"
                    value={String(workflowForm.lpo_document_url ?? "")}
                    onChange={(event) => setWorkflowForm((current) => ({ ...current, lpo_document_url: event.target.value }))}
                    required
                    placeholder="Paste uploaded LPO, PO, or contract document link"
                    className="focus-ring mt-1 h-10 w-full rounded-lg border border-slate-200 bg-white/80 px-3 text-sm focus:border-blue-500"
                  />
                  <p className="mt-2 text-xs text-slate-500">Won deals require LPO or contract confirmation before project and finance workflows begin.</p>
                </label>
              )}

              {(workflowDialog.action === "mark-lost" ||
                workflowDialog.action === "close-lost" ||
                String(workflowForm.stage ?? "").includes("Closed as Lost")) && (
                <label>
                  <span className="text-sm font-medium text-slate-700">Loss Reason</span>
                  <textarea
                    value={String(workflowForm.loss_reason ?? "")}
                    onChange={(event) => setWorkflowForm((current) => ({ ...current, loss_reason: event.target.value }))}
                    required
                    className="focus-ring mt-1 min-h-24 w-full rounded-lg border border-slate-200 bg-white/80 px-3 py-2 text-sm focus:border-blue-500"
                  />
                </label>
              )}

              {(workflowDialog.action === "mark-won" || workflowDialog.action === "mark-lost" || workflowDialog.action === "close-won" || workflowDialog.action === "close-lost") && (
                <label>
                  <span className="text-sm font-medium text-slate-700">Comments</span>
                  <textarea
                    value={String(workflowForm.comments ?? "")}
                    onChange={(event) => setWorkflowForm((current) => ({ ...current, comments: event.target.value }))}
                    className="focus-ring mt-1 min-h-20 w-full rounded-lg border border-slate-200 bg-white/80 px-3 py-2 text-sm focus:border-blue-500"
                  />
                </label>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setWorkflowDialog(null);
                  setWorkflowForm({});
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSaving}>{isSaving ? "Saving..." : "Confirm"}</Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
