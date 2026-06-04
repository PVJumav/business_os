"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Briefcase, Building2, CalendarDays, CreditCard, Edit3, FolderKanban, Gift, Save, Search, ShieldCheck, Target, Users, X } from "lucide-react";
import { api } from "@/services/api";

type Primitive = string | number | boolean | null | undefined;
type DataRecord = Record<string, Primitive>;

interface StaffSearchResult {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  department?: string | null;
  job_title?: string | null;
  job_group?: string | null;
  salary_grade?: string | null;
  employment_status?: string | null;
}

interface EmployeeOption {
  id: string;
  employee_code?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  full_name?: string | null;
  email?: string | null;
  department?: string | null;
  job_title?: string | null;
  employment_status?: string | null;
}

interface StaffProfile {
  employee: DataRecord & {
    id: string;
    full_name: string;
    employee_code: string;
    department?: string | null;
    job_title?: string | null;
    role_category?: string | null;
    job_group?: string | null;
    salary_grade?: string | null;
    employment_type?: string | null;
    employment_type_status?: string | null;
    employment_start_date?: string | null;
    employment_end_date?: string | null;
    institution?: string | null;
    internship_supervisor?: string | null;
    consultancy_agreement_ref?: string | null;
    consultancy_project?: string | null;
    extension_approved_until?: string | null;
    probation_required?: boolean | null;
    probation_status?: string | null;
    probation_start_date?: string | null;
    probation_end_date?: string | null;
    probation_duration_months?: number | null;
    employment_status?: string | null;
  };
  line_manager: DataRecord | null;
  direct_reports: DataRecord[];
  crm: {
    accounts: DataRecord[];
    opportunities: DataRecord[];
    deals: DataRecord[];
    targets: DataRecord[];
    projects: DataRecord[];
    slas: DataRecord[];
    tenders: DataRecord[];
    tickets: DataRecord[];
    invoices: DataRecord[];
  };
  hr: {
    attendance: DataRecord[];
    leave: DataRecord[];
    leave_balances: DataRecord[];
    training: DataRecord[];
    benefits: DataRecord[];
    documents: DataRecord[];
    onboarding: DataRecord[];
    lifecycle: DataRecord[];
    policy_acknowledgements: DataRecord[];
    asset_assignments: DataRecord[];
    performance: DataRecord[];
    compensation: DataRecord[];
    salary_structures: DataRecord[];
    iam_access: DataRecord[];
    finance_cost_centers: DataRecord[];
    notifications: DataRecord[];
    audit_logs: DataRecord[];
    employee_relations: DataRecord[];
    payroll: DataRecord[];
    probation_records: DataRecord[];
    probation_reviews: DataRecord[];
    sensitive_visible: boolean;
  };
}

const sections = [
  { key: "accounts", label: "Accounts", icon: Building2, columns: ["company_name", "account_status", "country", "vertical"] },
  { key: "opportunities", label: "Pipeline", icon: Briefcase, columns: ["title", "stage", "gross_profit", "expected_close_date"] },
  { key: "deals", label: "Deals", icon: Briefcase, columns: ["deal_name", "deal_status", "gross_profit", "closed_date"] },
  { key: "targets", label: "Targets", icon: ShieldCheck, columns: ["period_label", "arena", "target_gp", "achieved_gp"] },
  { key: "projects", label: "Projects", icon: FolderKanban, columns: ["project_name", "stage", "status", "target_end_date"] },
  { key: "slas", label: "SLAs", icon: FolderKanban, columns: ["solution", "sla_type", "status", "end_date"] },
  { key: "tenders", label: "Tenders", icon: FolderKanban, columns: ["tender_title", "stage", "response_status", "outcome"] },
  { key: "tickets", label: "Tickets", icon: FolderKanban, columns: ["ticket_number", "issue_title", "severity", "status"] },
  { key: "invoices", label: "Collections", icon: CreditCard, columns: ["invoice_number", "amount", "paid_amount", "status"] },
] as const;

function formatValue(value: Primitive) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return value.toLocaleString();
  return String(value).replaceAll("_", " ");
}

function moneyTotal(rows: DataRecord[], field: string) {
  return rows.reduce((sum, row) => {
    const value = Number(row[field] ?? 0);
    return sum + (Number.isFinite(value) ? value : 0);
  }, 0);
}

export default function Staff360({
  embedded = false,
  queryOverride,
  hideSearch = false,
  selectedIdOverride,
  onProfileChanged,
}: {
  embedded?: boolean;
  queryOverride?: string;
  hideSearch?: boolean;
  selectedIdOverride?: string | null;
  onProfileChanged?: () => void | Promise<void>;
}) {
  const [query, setQuery] = useState("");
  const activeQuery = queryOverride ?? query;
  const [results, setResults] = useState<StaffSearchResult[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(selectedIdOverride ?? null);
  const activeSelectedId = selectedIdOverride ?? selectedId;
  const [profile, setProfile] = useState<StaffProfile | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [managerOptions, setManagerOptions] = useState<EmployeeOption[]>([]);
  const [editForm, setEditForm] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const term = activeQuery.trim();
    if (term.length < 2) {
      setResults([]);
      return;
    }

    const handle = window.setTimeout(async () => {
      setIsSearching(true);
      setError(null);
      try {
        const rows = await api.get<StaffSearchResult[]>("/api/staff/search", { params: { query: term } });
        setResults(rows);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to search staff");
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => window.clearTimeout(handle);
  }, [activeQuery]);
  /* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    api.get<EmployeeOption[]>("/api/hrm/employees").then((rows) => {
      setManagerOptions(
        rows.map((row) => ({
          id: row.id,
          employee_code: row.employee_code,
          full_name: `${String(row.first_name ?? "")} ${String(row.last_name ?? "")}`.trim() || row.email,
          email: row.email,
          department: row.department,
          job_title: row.job_title,
          employment_status: row.employment_status,
        }))
      );
    }).catch(() => setManagerOptions([]));
  }, []);

  useEffect(() => {
    if (!activeSelectedId) return;

    async function loadProfile() {
      setIsLoadingProfile(true);
      setError(null);
      try {
        const data = await api.get<StaffProfile>(`/api/staff/${activeSelectedId}/profile`);
        setProfile(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load staff profile");
      } finally {
        setIsLoadingProfile(false);
      }
    }

    loadProfile();
  }, [activeSelectedId]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!profile) return;
    setEditForm({
      first_name: String(profile.employee.first_name ?? ""),
      last_name: String(profile.employee.last_name ?? ""),
      phone: String(profile.employee.phone ?? ""),
      department: String(profile.employee.department ?? ""),
      job_title: String(profile.employee.job_title ?? ""),
      role_category: String(profile.employee.role_category ?? ""),
      job_group: String(profile.employee.job_group ?? ""),
      salary_grade: String(profile.employee.salary_grade ?? ""),
      employment_type: String(profile.employee.employment_type ?? "Permanent"),
      employment_start_date: String(profile.employee.employment_start_date ?? ""),
      employment_end_date: String(profile.employee.employment_end_date ?? ""),
      institution: String(profile.employee.institution ?? ""),
      internship_supervisor: String(profile.employee.internship_supervisor ?? ""),
      consultancy_agreement_ref: String(profile.employee.consultancy_agreement_ref ?? ""),
      consultancy_project: String(profile.employee.consultancy_project ?? ""),
      probation_required: String(Boolean(profile.employee.probation_required)),
      probation_start_date: String(profile.employee.probation_start_date ?? ""),
      probation_end_date: String(profile.employee.probation_end_date ?? ""),
      probation_duration_months: String(profile.employee.probation_duration_months ?? "6"),
      employment_status: String(profile.employee.employment_status ?? "active"),
      supervisor_id: String(profile.employee.supervisor_id ?? ""),
      branch: String(profile.employee.branch ?? ""),
    });
  }, [profile]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const summary = useMemo(() => {
    if (!profile) return null;
    return {
      accounts: profile.crm.accounts.length,
      openPipeline: profile.crm.opportunities.length,
      projects: profile.crm.projects.length + profile.crm.slas.length,
      leaveDays: moneyTotal(profile.hr.leave_balances, "available_days"),
      assets: profile.hr.asset_assignments.filter((item) => String(item.status ?? "").toLowerCase() === "assigned").length,
      targetGp: moneyTotal(profile.crm.targets, "target_gp"),
      achievedGp: moneyTotal(profile.crm.targets, "achieved_gp"),
    };
  }, [profile]);

  async function refreshProfile() {
    if (!activeSelectedId) return;
    setIsLoadingProfile(true);
    setError(null);
    try {
      const data = await api.get<StaffProfile>(`/api/staff/${activeSelectedId}/profile`);
      setProfile(data);
      await onProfileChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh staff profile");
    } finally {
      setIsLoadingProfile(false);
    }
  }

  async function saveProfile() {
    if (!profile?.employee.id) return;
    setIsSavingProfile(true);
    setError(null);
    try {
      await api.put(`/api/hrm/employees/${profile.employee.id}`, {
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        phone: editForm.phone,
        department: editForm.department,
        job_title: editForm.job_title,
        role_category: editForm.role_category,
        job_group: editForm.job_group,
        salary_grade: editForm.salary_grade,
        employment_type: editForm.employment_type,
        employment_start_date: editForm.employment_start_date || null,
        employment_end_date: editForm.employment_end_date || null,
        institution: editForm.institution,
        internship_supervisor: editForm.internship_supervisor,
        consultancy_agreement_ref: editForm.consultancy_agreement_ref,
        consultancy_project: editForm.consultancy_project,
        probation_required: editForm.probation_required === "true",
        probation_start_date: editForm.probation_start_date || null,
        probation_end_date: editForm.probation_end_date || null,
        probation_duration_months: Number(editForm.probation_duration_months || 0),
        employment_status: editForm.employment_status,
        supervisor_id: editForm.supervisor_id || null,
        branch: editForm.branch,
      });
      setIsEditingProfile(false);
      await refreshProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update employee profile");
    } finally {
      setIsSavingProfile(false);
    }
  }

  return (
    <div className="space-y-6">
      {!embedded && (
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Employees</h1>
          <p className="mt-1 text-sm text-slate-500">
            Search one employee and see their role, reporting line, targets, accounts, projects, SLAs, tenders, tickets, and HR records.
          </p>
        </div>
      )}

      <div className="rounded-xl border bg-white p-4 shadow-sm">
        {!hideSearch && (
          <div className="flex h-12 items-center rounded-xl bg-slate-100 px-4">
            <Search size={18} className="text-slate-500" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Type a staff name, email, code, role, or department..."
              className="w-full bg-transparent px-3 text-sm outline-none"
            />
          </div>
        )}

        {hideSearch && !activeQuery.trim() && (
          <p className="text-sm text-slate-500">Use the search bar above to find an employee and open their full profile.</p>
        )}

        {error && <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {results.map((result) => (
            <button
              key={result.id}
              onClick={() => setSelectedId(result.id)}
              className={`rounded-xl border p-4 text-left transition hover:border-slate-400 ${
                activeSelectedId === result.id ? "border-slate-900 bg-slate-50" : "bg-white"
              }`}
            >
              <p className="font-semibold text-slate-900">{result.full_name}</p>
              <p className="mt-1 text-sm text-slate-500">{result.employee_code} / {result.email}</p>
              <p className="mt-2 text-sm text-slate-700">{formatValue(result.department)} / {formatValue(result.job_title)}</p>
              <p className="mt-1 text-xs text-slate-500">{formatValue(result.job_group)} / {formatValue(result.employment_status)}</p>
            </button>
          ))}
        </div>

        {isSearching && <p className="mt-3 text-sm text-slate-500">Searching staff...</p>}
      </div>

      {isLoadingProfile && <div className="rounded-xl border bg-white p-6 text-sm text-slate-500">Loading staff profile...</div>}

      {profile && summary && (
        <div className="space-y-6">
          <section className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 className="text-2xl font-semibold text-slate-900">{profile.employee.full_name}</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {formatValue(profile.employee.employee_code)} / {formatValue(profile.employee.department)} / {formatValue(profile.employee.job_title)}
                </p>
                <p className="mt-2 text-sm text-slate-700">
                  Role category: {formatValue(profile.employee.role_category)} / Job group: {formatValue(profile.employee.job_group)}
                  {profile.hr.sensitive_visible ? ` / Salary grade: ${formatValue(profile.employee.salary_grade)}` : ""}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                    {formatValue(profile.employee.employment_type)}
                  </span>
                  {profile.employee.employment_type_status === "expiring_soon" && (
                    <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">Contract expiring soon</span>
                  )}
                  {profile.employee.employment_type_status === "expired" && (
                    <span className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">Contract expired</span>
                  )}
                  {profile.employee.employment_end_date && (
                    <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                      Ends {new Date(String(profile.employee.extension_approved_until || profile.employee.employment_end_date)).toLocaleDateString()}
                    </span>
                  )}
                  {profile.employee.probation_status && profile.employee.probation_status !== "Not Applicable" && (
                    <span className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                      Probation: {formatValue(profile.employee.probation_status)}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {!isEditingProfile ? (
                  <button
                    type="button"
                    onClick={() => setIsEditingProfile(true)}
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    <Edit3 size={16} />
                    Edit profile
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={saveProfile}
                      disabled={isSavingProfile}
                      className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
                    >
                      <Save size={16} />
                      {isSavingProfile ? "Saving..." : "Save"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsEditingProfile(false)}
                      className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      <X size={16} />
                      Cancel
                    </button>
                  </>
                )}
                <div className="rounded-xl bg-slate-900 px-4 py-3 text-white">
                  <p className="text-xs uppercase text-slate-300">Status</p>
                  <p className="text-lg font-semibold capitalize">{formatValue(profile.employee.employment_status)}</p>
                </div>
              </div>
            </div>

            {isEditingProfile && (
              <div className="mt-5 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-2 xl:grid-cols-3">
                {[
                  ["first_name", "First name"],
                  ["last_name", "Last name"],
                  ["phone", "Phone"],
                  ["department", "Department"],
                  ["job_title", "Role"],
                  ["role_category", "Role category"],
                  ["job_group", "Job group"],
                  ["salary_grade", "Salary grade"],
                  ["branch", "Branch"],
                ].map(([key, label]) => (
                  <label key={key} className="text-sm">
                    <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
                    <input
                      value={editForm[key] ?? ""}
                      onChange={(event) => setEditForm((current) => ({ ...current, [key]: event.target.value }))}
                      className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500"
                    />
                  </label>
                ))}
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Employment type</span>
                  <select
                    value={editForm.employment_type ?? "Permanent"}
                    onChange={(event) => setEditForm((current) => ({ ...current, employment_type: event.target.value }))}
                    className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500"
                  >
                    {["Permanent", "Contract", "Casual", "Internship", "Consultant"].map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </label>
                {editForm.employment_type !== "Permanent" && (
                  <>
                    <label className="text-sm">
                      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Start date</span>
                      <input type="date" value={editForm.employment_start_date ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, employment_start_date: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                    </label>
                    <label className="text-sm">
                      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">End date</span>
                      <input type="date" value={editForm.employment_end_date ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, employment_end_date: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                    </label>
                  </>
                )}
                {editForm.employment_type === "Internship" && (
                  <>
                    <label className="text-sm">
                      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Institution</span>
                      <input value={editForm.institution ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, institution: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                    </label>
                    <label className="text-sm">
                      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Internship supervisor</span>
                      <input value={editForm.internship_supervisor ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, internship_supervisor: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                    </label>
                  </>
                )}
                {editForm.employment_type === "Consultant" && (
                  <>
                    <label className="text-sm">
                      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Agreement reference</span>
                      <input value={editForm.consultancy_agreement_ref ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, consultancy_agreement_ref: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                    </label>
                    <label className="text-sm">
                      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Consultancy project</span>
                      <input value={editForm.consultancy_project ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, consultancy_project: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                    </label>
                  </>
                )}
                {["Permanent", "Contract", "Internship"].includes(editForm.employment_type ?? "") && (
                  <>
                    <label className="text-sm">
                      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Probation required</span>
                      <select value={editForm.probation_required ?? "false"} onChange={(event) => setEditForm((current) => ({ ...current, probation_required: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500">
                        <option value="false">No</option>
                        <option value="true">Yes</option>
                      </select>
                    </label>
                    {editForm.probation_required === "true" && (
                      <>
                        <label className="text-sm">
                          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Probation start</span>
                          <input type="date" value={editForm.probation_start_date ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, probation_start_date: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                        </label>
                        <label className="text-sm">
                          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Probation duration</span>
                          <input type="number" min="1" value={editForm.probation_duration_months ?? "6"} onChange={(event) => setEditForm((current) => ({ ...current, probation_duration_months: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                        </label>
                        <label className="text-sm">
                          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Probation end</span>
                          <input type="date" value={editForm.probation_end_date ?? ""} onChange={(event) => setEditForm((current) => ({ ...current, probation_end_date: event.target.value }))} className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500" />
                        </label>
                      </>
                    )}
                  </>
                )}
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Employment status</span>
                  <select
                    value={editForm.employment_status ?? "active"}
                    onChange={(event) => setEditForm((current) => ({ ...current, employment_status: event.target.value }))}
                    className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500"
                  >
                    {["active", "on_leave", "probation", "inactive", "suspended", "terminated"].map((status) => (
                      <option key={status} value={status}>{formatValue(status)}</option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Line manager</span>
                  <select
                    value={editForm.supervisor_id ?? ""}
                    onChange={(event) => setEditForm((current) => ({ ...current, supervisor_id: event.target.value }))}
                    className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 outline-none focus:border-slate-500"
                  >
                    <option value="">No manager / top-level</option>
                    {managerOptions
                      .filter((employee) => employee.id !== profile.employee.id)
                      .map((employee) => (
                        <option key={employee.id} value={employee.id}>
                          {employee.full_name} / {formatValue(employee.department)}
                        </option>
                      ))}
                  </select>
                </label>
              </div>
            )}

            <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-7">
              <Metric label="Accounts" value={summary.accounts} />
              <Metric label="Pipeline" value={summary.openPipeline} />
              <Metric label="Projects & SLAs" value={summary.projects} />
              <Metric label="Leave Days" value={summary.leaveDays.toLocaleString()} />
              <Metric label="Assets" value={summary.assets} />
              <Metric label="Target GP" value={summary.targetGp.toLocaleString()} />
              <Metric label="Achieved GP" value={summary.achievedGp.toLocaleString()} />
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <InfoBlock title="Line Manager" rows={profile.line_manager ? [profile.line_manager] : []} columns={["full_name", "department", "job_title"]} />
              <InfoBlock title="Direct Reports" rows={profile.direct_reports} columns={["full_name", "department", "job_title"]} />
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              <QuickAction href={`/hrm/leave?employee=${profile.employee.id}`} icon={CalendarDays} label="Assign leave" />
              <QuickAction href={`/hrm/performance?employee=${profile.employee.id}`} icon={Target} label="Update KPIs" />
              <QuickAction href={`/hrm/benefits?employee=${profile.employee.id}`} icon={Gift} label="Benefits" />
              <QuickAction href={`/hrm/payroll?employee=${profile.employee.id}`} icon={CreditCard} label="Payroll" />
              <QuickAction href={`/projects?employee=${profile.employee.id}`} icon={FolderKanban} label="Collaborative work" />
            </div>
          </section>

          <div className="grid gap-4 xl:grid-cols-2">
            {sections.map((section) => (
              <RecordSection
                key={section.key}
                title={section.label}
                icon={section.icon}
                rows={profile.crm[section.key]}
                columns={[...section.columns]}
              />
            ))}
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <RecordSection title="Lifecycle" icon={ShieldCheck} rows={profile.hr.lifecycle} columns={["event_type", "effective_date", "to_value", "status"]} />
            <RecordSection title="Probation Timeline" icon={ShieldCheck} rows={[...profile.hr.probation_records, ...profile.hr.probation_reviews]} columns={["status", "start_date", "end_date", "outcome", "review_date"]} />
            <RecordSection title="Onboarding" icon={Users} rows={profile.hr.onboarding} columns={["task_name", "task_category", "due_date", "status"]} />
            <RecordSection title="Attendance" icon={Users} rows={profile.hr.attendance} columns={["attendance_date", "clock_in", "clock_out", "status", "work_mode"]} />
            <RecordSection title="Leave" icon={Users} rows={profile.hr.leave} columns={["leave_type", "start_date", "end_date", "status"]} />
            <RecordSection title="Leave Balances" icon={Users} rows={profile.hr.leave_balances} columns={["leave_type", "fiscal_year", "available_days", "status"]} />
            <RecordSection title="Training" icon={Users} rows={profile.hr.training} columns={["training_title", "training_type", "completion_status", "certification_awarded"]} />
            <RecordSection title="Benefits" icon={CreditCard} rows={profile.hr.benefits} columns={["benefit_type", "benefit_name", "provider", "status"]} />
            <RecordSection title="Documents" icon={ShieldCheck} rows={profile.hr.documents} columns={["document_title", "document_type", "expiry_date", "status"]} />
            <RecordSection title="Policy Acknowledgements" icon={ShieldCheck} rows={profile.hr.policy_acknowledgements} columns={["policy_name", "policy_version", "due_date", "status"]} />
            <RecordSection title="Assets" icon={Briefcase} rows={profile.hr.asset_assignments} columns={["asset_name", "asset_tag", "assigned_date", "status"]} />
            <RecordSection title="Performance" icon={Users} rows={profile.hr.performance} columns={["review_period", "rating", "performance_score", "status"]} />
            <RecordSection
              title={profile.hr.sensitive_visible ? "Compensation" : "Compensation Restricted"}
              icon={CreditCard}
              rows={profile.hr.compensation}
              columns={["effective_date", "compensation_type", "base_salary", "approval_status"]}
              emptyText={profile.hr.sensitive_visible ? "No compensation records found." : "Compensation is visible to Admin or HR only."}
            />
            <RecordSection
              title={profile.hr.sensitive_visible ? "Payroll Profile" : "Payroll Profile Restricted"}
              icon={CreditCard}
              rows={profile.hr.salary_structures}
              columns={["structure_name", "base_salary", "pay_frequency", "status"]}
              emptyText={profile.hr.sensitive_visible ? "No payroll profile found." : "Payroll profile is visible to Admin or HR only."}
            />
            <RecordSection
              title={profile.hr.sensitive_visible ? "IAM Provisioning" : "IAM Restricted"}
              icon={ShieldCheck}
              rows={profile.hr.iam_access}
              columns={["user_email", "role_name", "access_level", "provisioning_status"]}
              emptyText={profile.hr.sensitive_visible ? "No IAM request found." : "IAM provisioning is visible to Admin or HR only."}
            />
            <RecordSection
              title={profile.hr.sensitive_visible ? "Finance Mapping" : "Finance Mapping Restricted"}
              icon={CreditCard}
              rows={profile.hr.finance_cost_centers}
              columns={["cost_center_code", "cost_center_name", "department", "status"]}
              emptyText={profile.hr.sensitive_visible ? "No finance cost center mapping found." : "Finance mapping is visible to Admin or HR only."}
            />
            <RecordSection title="Notifications" icon={ShieldCheck} rows={profile.hr.notifications} columns={["recipient_name", "subject", "status", "created_at"]} />
            <RecordSection
              title={profile.hr.sensitive_visible ? "Audit Trail" : "Audit Restricted"}
              icon={ShieldCheck}
              rows={profile.hr.audit_logs}
              columns={["action", "sensitivity", "summary", "created_at"]}
              emptyText={profile.hr.sensitive_visible ? "No audit events found." : "Audit events are visible to Admin or HR only."}
            />
            <RecordSection
              title={profile.hr.sensitive_visible ? "Employee Relations" : "Employee Relations Restricted"}
              icon={ShieldCheck}
              rows={profile.hr.employee_relations}
              columns={["case_type", "case_title", "severity", "status"]}
              emptyText={profile.hr.sensitive_visible ? "No employee relations cases found." : "Employee relations cases are visible to Admin or HR only."}
            />
            <RecordSection
              title={profile.hr.sensitive_visible ? "Payroll" : "Payroll Restricted"}
              icon={CreditCard}
              rows={profile.hr.payroll}
              columns={["payroll_month", "basic_salary", "gross_pay", "net_pay", "payment_status"]}
              emptyText={profile.hr.sensitive_visible ? "No payroll records found." : "Payroll and salary records are visible to Admin or HR only."}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function QuickAction({
  href,
  icon: Icon,
  label,
}: {
  href: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
}) {
  return (
    <Link href={href} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
      <Icon size={16} />
      {label}
    </Link>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border bg-slate-50 p-4">
      <p className="text-xs font-medium uppercase text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function InfoBlock({ title, rows, columns }: { title: string; rows: DataRecord[]; columns: string[] }) {
  return (
    <div className="rounded-xl border bg-slate-50 p-4">
      <p className="mb-3 font-semibold text-slate-900">{title}</p>
      {rows.length ? (
        <div className="space-y-2">
          {rows.map((row, index) => (
            <div key={String(row.id ?? index)} className="rounded-lg bg-white p-3 text-sm text-slate-700">
              {columns.map((column) => (
                <span key={column} className="mr-3">{formatValue(row[column])}</span>
              ))}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-500">No records found.</p>
      )}
    </div>
  );
}

function RecordSection({
  title,
  icon: Icon,
  rows,
  columns,
  emptyText = "No records found.",
}: {
  title: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  rows: DataRecord[];
  columns: string[];
  emptyText?: string;
}) {
  return (
    <section className="rounded-xl border bg-white shadow-sm">
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <Icon size={18} className="text-slate-600" />
          <h3 className="font-semibold text-slate-900">{title}</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">{rows.length}</span>
      </div>
      {rows.length ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                {columns.map((column) => (
                  <th key={column} className="px-4 py-3 font-medium">{column.replaceAll("_", " ")}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.slice(0, 8).map((row, index) => (
                <tr key={String(row.id ?? index)}>
                  {columns.map((column) => (
                    <td key={column} className="px-4 py-3 text-slate-700">{formatValue(row[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="p-4 text-sm text-slate-500">{emptyText}</p>
      )}
    </section>
  );
}
