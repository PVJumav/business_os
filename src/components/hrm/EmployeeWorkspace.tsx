"use client";

import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, CheckCircle2, Download, RefreshCw, Search, ShieldCheck, Trash2, Upload, UserPlus, Users, X } from "lucide-react";
import Button from "@/components/ui/Button";
import { API_BASE_URL } from "@/lib/constants";
import { api } from "@/services/api";
import { useGlobalSearch } from "@/store/searchStore";

type Employee = {
  id: string;
  employee_code?: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  preferred_name?: string;
  national_id?: string;
  tax_pin?: string;
  passport_number?: string;
  nationality?: string;
  place_of_birth?: string;
  religion?: string;
  marital_status?: string;
  biography?: string;
  professional_summary?: string;
  skills?: string;
  languages?: string;
  certifications_summary?: string;
  photo_url?: string;
  profile_completion_percentage?: number;
  email?: string;
  personal_email?: string;
  corporate_email?: string;
  phone?: string;
  alternative_phone?: string;
  gender?: string;
  date_of_birth?: string;
  physical_address?: string;
  postal_address?: string;
  city?: string;
  county?: string;
  country?: string;
  department?: string;
  business_unit?: string;
  job_title?: string;
  job_group?: string;
  salary_grade?: string;
  salary_band?: string;
  cost_center_code?: string;
  functional_manager_id?: string;
  functional_manager_scope?: string;
  role_category?: string;
  supervisor_id?: string;
  employment_type?: string;
  employment_type_status?: string;
  employment_start_date?: string;
  employment_end_date?: string;
  extension_approved_until?: string;
  probation_required?: boolean;
  probation_status?: string;
  probation_start_date?: string;
  probation_end_date?: string;
  probation_duration_months?: number;
  confirmation_status?: string;
  confirmation_date?: string;
  confirmed_by?: string;
  confirmation_notes?: string;
  probation_review_id?: string;
  next_confirmation_review_date?: string;
  employment_status?: string;
  hire_date?: string;
  pay_frequency?: string;
  base_salary?: number;
  branch?: string;
  address?: string;
  contract_signed?: boolean;
  budget_approved?: boolean;
  activation_date?: string;
  activated_by?: string;
};

type Department = {
  id: string;
  name: string;
  status?: string;
};

type Position = {
  id: string;
  position_title?: string;
  department?: string;
  headcount_budget?: number;
  current_headcount?: number;
  status?: string;
};

type EmployeeForm = {
  candidate_id: string;
  first_name: string;
  last_name: string;
  national_id: string;
  tax_pin: string;
  email: string;
  phone: string;
  gender: string;
  date_of_birth: string;
  employment_type: string;
  employment_start_date: string;
  employment_end_date: string;
  institution: string;
  internship_supervisor: string;
  consultancy_agreement_ref: string;
  consultancy_project: string;
  probation_required: boolean;
  probation_start_date: string;
  probation_end_date: string;
  probation_duration_months: string;
  probation_extension_reason: string;
  department: string;
  business_unit: string;
  job_title: string;
  supervisor_id: string;
  hire_date: string;
  pay_frequency: string;
  base_salary: string;
  branch: string;
  contract_signed: boolean;
  budget_approved: boolean;
};

type ImportBatch = {
  id: string;
  batch_number: string;
  file_name?: string;
  import_mode?: string;
  processing_status?: string;
  approval_status?: string;
  total_rows?: number;
  valid_rows?: number;
  created_rows?: number;
  updated_rows?: number;
  rejected_rows?: number;
  parse_summary?: string;
};

type ProfileRecord = Record<string, string | number | boolean | null | undefined>;

type EmployeeProfileBundle = {
  profile_completion_percentage: number;
  personal_information: ProfileRecord;
  contact_information: ProfileRecord;
  dependants: ProfileRecord[];
  emergency_contacts: ProfileRecord[];
  biography: ProfileRecord;
  active_photo?: ProfileRecord | null;
  change_requests: ProfileRecord[];
  audit_history: ProfileRecord[];
};

type EmploymentInfoBundle = {
  current: ProfileRecord;
  pending_changes: ProfileRecord[];
  history: ProfileRecord[];
  salary_band_visible: boolean;
};

type AssignmentBundle = {
  current: ProfileRecord;
  departments: ProfileRecord[];
  branches: ProfileRecord[];
  business_units: ProfileRecord[];
  projects: ProfileRecord[];
  teams: ProfileRecord[];
  documents?: ProfileRecord[];
  history: ProfileRecord[];
  analytics: { project_allocation?: number; missing_documents?: string[] };
};

type DocumentCompliance = {
  score?: number;
  missing_count?: number;
  pending_verification?: number;
  rejected?: number;
  expiring_soon?: number;
  expired?: number;
  missing?: string[];
};

type DependantDraft = {
  full_name: string;
  relationship: string;
  date_of_birth: string;
  gender: string;
  beneficiary_percentage: string;
  medical_cover_eligible: boolean;
};

type EmergencyDraft = {
  full_name: string;
  relationship: string;
  phone_number: string;
  alternative_phone: string;
  email: string;
  address: string;
  is_primary: boolean;
};

const initialEmployeeForm: EmployeeForm = {
  candidate_id: "",
  first_name: "",
  last_name: "",
  national_id: "",
  tax_pin: "",
  email: "",
  phone: "",
  gender: "",
  date_of_birth: "",
  employment_type: "Permanent",
  employment_start_date: "",
  employment_end_date: "",
  institution: "",
  internship_supervisor: "",
  consultancy_agreement_ref: "",
  consultancy_project: "",
  probation_required: false,
  probation_start_date: "",
  probation_end_date: "",
  probation_duration_months: "6",
  probation_extension_reason: "",
  department: "",
  business_unit: "",
  job_title: "",
  supervisor_id: "",
  hire_date: "",
  pay_frequency: "monthly",
  base_salary: "0",
  branch: "",
  contract_signed: false,
  budget_approved: false,
};

const initialDependantDraft: DependantDraft = {
  full_name: "",
  relationship: "Child",
  date_of_birth: "",
  gender: "",
  beneficiary_percentage: "0",
  medical_cover_eligible: false,
};

const initialEmergencyDraft: EmergencyDraft = {
  full_name: "",
  relationship: "",
  phone_number: "",
  alternative_phone: "",
  email: "",
  address: "",
  is_primary: false,
};

const inputClass =
  "focus-ring h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

function fullName(employee: Employee) {
  return `${employee.first_name ?? ""} ${employee.last_name ?? ""}`.trim() || employee.email || "Employee";
}

function format(value?: string | null) {
  return value ? value.replaceAll("_", " ") : "-";
}

function employmentExpiryStatus(employee: Employee) {
  if (employee.employment_type_status) return employee.employment_type_status;
  if (!["Contract", "Casual", "Internship", "Consultant"].includes(employee.employment_type ?? "")) return "active";
  const endDate = employee.extension_approved_until || employee.employment_end_date;
  if (!endDate) return "incomplete";
  const days = Math.ceil((new Date(endDate).getTime() - Date.now()) / 86400000);
  if (days < 0) return "expired";
  if (days <= 90) return "expiring_soon";
  return "active";
}

export default function EmployeeWorkspace() {
  const { query } = useGlobalSearch();
  const searchParams = useSearchParams();
  const selectedEmployeeId = searchParams.get("employee");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(selectedEmployeeId);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSavingEmployee, setIsSavingEmployee] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [employeeForm, setEmployeeForm] = useState<EmployeeForm>(initialEmployeeForm);
  const [importMode, setImportMode] = useState("create");
  const [importAsDraft, setImportAsDraft] = useState(true);
  const [rollbackOnError, setRollbackOnError] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [lastBatch, setLastBatch] = useState<ImportBatch | null>(null);
  const [activationMessage, setActivationMessage] = useState<string | null>(null);
  const [activationError, setActivationError] = useState<string | null>(null);
  const [isActivating, setIsActivating] = useState(false);
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [probationFilter, setProbationFilter] = useState("all");
  const [confirmationFilter, setConfirmationFilter] = useState("all");
  const [employeeDetail, setEmployeeDetail] = useState<Employee | null>(null);
  const [employeeDraft, setEmployeeDraft] = useState<Partial<Employee>>({});
  const [profileBundle, setProfileBundle] = useState<EmployeeProfileBundle | null>(null);
  const [employmentInfo, setEmploymentInfo] = useState<EmploymentInfoBundle | null>(null);
  const [assignmentBundle, setAssignmentBundle] = useState<AssignmentBundle | null>(null);
  const [employmentAction, setEmploymentAction] = useState("job-title/change");
  const [employmentNewValue, setEmploymentNewValue] = useState("");
  const [employmentEffectiveDate, setEmploymentEffectiveDate] = useState(new Date().toISOString().slice(0, 10));
  const [employmentReason, setEmploymentReason] = useState("");
  const [employmentAuthorityScope, setEmploymentAuthorityScope] = useState("");
  const [assignmentAction, setAssignmentAction] = useState("department");
  const [assignmentValue, setAssignmentValue] = useState("");
  const [assignmentReason, setAssignmentReason] = useState("");
  const [assignmentDate, setAssignmentDate] = useState(new Date().toISOString().slice(0, 10));
  const [projectRole, setProjectRole] = useState("");
  const [projectAllocation, setProjectAllocation] = useState("0");
  const [documentType, setDocumentType] = useState("National ID");
  const [documentExpiry, setDocumentExpiry] = useState("");
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [documentCompliance, setDocumentCompliance] = useState<DocumentCompliance | null>(null);
  const [documentVersions, setDocumentVersions] = useState<ProfileRecord[]>([]);
  const [movementHistory, setMovementHistory] = useState<ProfileRecord[]>([]);
  const [statusHistory, setStatusHistory] = useState<ProfileRecord[]>([]);
  const [movementAction, setMovementAction] = useState("change-role");
  const [statusAction, setStatusAction] = useState("suspend");
  const [movementReason, setMovementReason] = useState("");
  const [movementEffectiveDate, setMovementEffectiveDate] = useState(new Date().toISOString().slice(0, 10));
  const [movementNewValue, setMovementNewValue] = useState("");
  const [dependantDraft, setDependantDraft] = useState<DependantDraft>(initialDependantDraft);
  const [emergencyDraft, setEmergencyDraft] = useState<EmergencyDraft>(initialEmergencyDraft);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [employeeModalTab, setEmployeeModalTab] = useState("overview");
  const [confirmationDecision, setConfirmationDecision] = useState<"confirm" | "defer" | "reject">("confirm");
  const [confirmationDate, setConfirmationDate] = useState(new Date().toISOString().slice(0, 10));
  const [confirmationNotes, setConfirmationNotes] = useState("");
  const [nextReviewDate, setNextReviewDate] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingProfileSection, setIsSavingProfileSection] = useState(false);
  const importFileRef = useRef<HTMLInputElement | null>(null);
  const validateFileRef = useRef<HTMLInputElement | null>(null);

  async function loadEmployees() {
    setIsLoading(true);
    setError(null);
    try {
      const rows = await api.get<Employee[]>("/api/hrm/employees?summary=true&limit=500");
      setEmployees(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load employees");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadOrganizationOptions() {
    const [departmentRows, positionRows] = await Promise.all([
      api.get<Department[]>("/api/hrm/departments").catch(() => []),
      api.get<Position[]>("/api/hrm/positions").catch(() => []),
    ]);
    setDepartments(departmentRows);
    setPositions(positionRows);
  }

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    loadEmployees();
    loadOrganizationOptions();
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (selectedEmployeeId) setSelectedId(selectedEmployeeId);
  }, [selectedEmployeeId]);
  /* eslint-enable react-hooks/set-state-in-effect */

  /* eslint-disable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */
  useEffect(() => {
    if (!selectedId) {
      setEmployeeDetail(null);
      setEmployeeDraft({});
      setProfileBundle(null);
      setEmploymentInfo(null);
      setAssignmentBundle(null);
      setDocumentCompliance(null);
      setDocumentVersions([]);
      setMovementHistory([]);
      setStatusHistory([]);
      return;
    }
    Promise.all([
      api.get<Employee>(`/api/hrm/employees/${selectedId}`),
      api.get<EmployeeProfileBundle>(`/api/hrm/employees/${selectedId}/profile`).catch(() => null),
      api.get<EmploymentInfoBundle>(`/api/hrm/employment-info/${selectedId}`).catch(() => null),
      api.get<AssignmentBundle>(`/api/hrm/employees/${selectedId}/assignments`).catch(() => null),
      api.get<ProfileRecord[]>(`/api/hrm/employees/${selectedId}/documents`).catch(() => []),
      api.get<DocumentCompliance>(`/api/hrm/employees/${selectedId}/documents/compliance`).catch(() => null),
      api.get<ProfileRecord[]>(`/api/hrm/employees/${selectedId}/movements`).catch(() => []),
      api.get<ProfileRecord[]>(`/api/hrm/employees/${selectedId}/status-history`).catch(() => []),
    ])
      .then(([employee, profile, employment, assignments, documents, compliance, movements, statuses]) => {
        setEmployeeDetail(employee);
        setEmployeeDraft(employee);
        setProfileBundle(profile);
        setEmploymentInfo(employment);
        setAssignmentBundle(assignments ? { ...assignments, documents } as AssignmentBundle & { documents: ProfileRecord[] } : null);
        setDocumentCompliance(compliance);
        setMovementHistory(movements);
        setStatusHistory(statuses);
      })
      .catch(() => {
        const fallback = employees.find((employee) => employee.id === selectedId) ?? null;
        setEmployeeDetail(fallback);
        setEmployeeDraft(fallback ?? {});
        setProfileBundle(null);
        setEmploymentInfo(null);
        setAssignmentBundle(null);
        setDocumentCompliance(null);
        setDocumentVersions([]);
        setMovementHistory([]);
        setStatusHistory([]);
      });
  }, [selectedId]);
  /* eslint-enable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return employees.filter((employee) => {
      const expiryStatus = employmentExpiryStatus(employee);
      if (typeFilter !== "all" && employee.employment_type !== typeFilter) return false;
      if (statusFilter === "expiring" && expiryStatus !== "expiring_soon") return false;
      if (statusFilter === "expired" && expiryStatus !== "expired") return false;
      if (statusFilter === "active" && employee.employment_status !== "active") return false;
      if (statusFilter === "inactive" && !["inactive", "terminated", "suspended"].includes(employee.employment_status ?? "")) return false;
      if (probationFilter === "on_probation" && !["Pending", "In Progress"].includes(employee.probation_status ?? "")) return false;
      if (probationFilter === "due" && employee.probation_status !== "Due for Review") return false;
      if (probationFilter === "extended" && employee.probation_status !== "Extended") return false;
      if (probationFilter === "failed" && employee.probation_status !== "Failed") return false;
      if (probationFilter === "confirmed" && employee.probation_status !== "Confirmed") return false;
      if (confirmationFilter === "pending" && employee.confirmation_status !== "Pending Confirmation") return false;
      if (confirmationFilter === "confirmed" && employee.confirmation_status !== "Confirmed") return false;
      if (confirmationFilter === "deferred" && employee.confirmation_status !== "Confirmation Deferred") return false;
      if (confirmationFilter === "rejected" && employee.confirmation_status !== "Rejected") return false;
      if (!term) return true;
      return [
        employee.employee_code,
        fullName(employee),
        employee.email,
        employee.department,
        employee.job_title,
        employee.role_category,
        employee.employment_type,
        employee.employment_type_status,
        employee.probation_status,
        employee.confirmation_status,
        employee.employment_status,
      ]
        .join(" ")
        .toLowerCase()
        .includes(term);
    });
  }, [employees, query, typeFilter, statusFilter, probationFilter, confirmationFilter]);

  const selectedEmployee = employeeDetail ?? employees.find((employee) => employee.id === selectedId);
  const activeDepartments = departments.filter((department) => department.status === "active");
  const activeManagers = employees.filter((employee) => ["active", "probation", "on_leave"].includes(employee.employment_status ?? ""));
  const modalDepartment = employeeDraft.department ?? selectedEmployee?.department ?? "";
  const modalPositions = positions.filter(
    (position) =>
      position.status === "active" &&
      (!modalDepartment || position.department?.toLowerCase() === modalDepartment.toLowerCase())
  );
  const selectedManager = employees.find((employee) => employee.id === (employeeDraft.supervisor_id ?? selectedEmployee?.supervisor_id));
  const availablePositions = positions.filter(
    (position) =>
      position.status === "active" &&
      (!employeeForm.department || position.department?.toLowerCase() === employeeForm.department.toLowerCase())
  );
  const selectedPosition = availablePositions.find((position) => position.position_title === employeeForm.job_title);
  const headcountAvailable = selectedPosition
    ? Number(selectedPosition.current_headcount ?? 0) < Number(selectedPosition.headcount_budget ?? 0)
    : false;
  const headcountWillBeReserved = Boolean(selectedPosition && !headcountAvailable && employeeForm.budget_approved);
  const preconditions = [
    { label: "Hired recruitment candidate linked", met: Boolean(employeeForm.candidate_id) },
    { label: "Active department selected", met: activeDepartments.some((department) => department.name === employeeForm.department) },
    { label: "Active position exists", met: Boolean(selectedPosition) },
    { label: headcountWillBeReserved ? "Approved headcount will be reserved on save" : "Approved headcount available", met: headcountAvailable || headcountWillBeReserved },
    { label: "Employment contract signed", met: employeeForm.contract_signed },
    { label: "Recruitment budget approved", met: employeeForm.budget_approved },
  ];
  const probationApplies = ["Permanent", "Contract", "Internship"].includes(employeeForm.employment_type);

  function updateEmployeeForm<K extends keyof EmployeeForm>(key: K, value: EmployeeForm[K]) {
    setEmployeeForm((current) => ({
      ...current,
      [key]: value,
      ...(key === "department" ? { job_title: "" } : {}),
    }));
  }

  function openEmployeeCreation() {
    setEmployeeForm(initialEmployeeForm);
    setCreateError(null);
    setIsCreateOpen(true);
  }

  function openEmployee(employee: Employee) {
    setEmployeeModalTab("overview");
    setSelectedId(employee.id);
  }

  function updateEmployeeDraft<K extends keyof Employee>(key: K, value: Employee[K]) {
    setEmployeeDraft((current) => ({
      ...current,
      [key]: value,
      ...(key === "department" ? { job_title: "" } : {}),
    }));
  }

  async function saveSelectedEmployee() {
    if (!selectedEmployee) return;
    setIsSavingProfile(true);
    setActivationError(null);
    setActivationMessage(null);
    try {
      const payload = {
        first_name: employeeDraft.first_name || selectedEmployee.first_name,
        middle_name: employeeDraft.middle_name || null,
        last_name: employeeDraft.last_name || selectedEmployee.last_name,
        preferred_name: employeeDraft.preferred_name || null,
        email: employeeDraft.email || selectedEmployee.email,
        personal_email: employeeDraft.personal_email || null,
        corporate_email: employeeDraft.corporate_email || null,
        phone: employeeDraft.phone || null,
        alternative_phone: employeeDraft.alternative_phone || null,
        national_id: employeeDraft.national_id || null,
        tax_pin: employeeDraft.tax_pin || null,
        passport_number: employeeDraft.passport_number || null,
        nationality: employeeDraft.nationality || null,
        place_of_birth: employeeDraft.place_of_birth || null,
        religion: employeeDraft.religion || null,
        marital_status: employeeDraft.marital_status || null,
        gender: employeeDraft.gender || null,
        date_of_birth: employeeDraft.date_of_birth || null,
        physical_address: employeeDraft.physical_address || employeeDraft.address || null,
        postal_address: employeeDraft.postal_address || null,
        city: employeeDraft.city || null,
        county: employeeDraft.county || null,
        country: employeeDraft.country || null,
        biography: employeeDraft.biography || null,
        professional_summary: employeeDraft.professional_summary || null,
        skills: employeeDraft.skills || null,
        languages: employeeDraft.languages || null,
        certifications_summary: employeeDraft.certifications_summary || null,
        department: employeeDraft.department || selectedEmployee.department,
        business_unit: employeeDraft.business_unit || null,
        job_title: employeeDraft.job_title || selectedEmployee.job_title,
        job_group: employeeDraft.job_group || null,
        salary_grade: employeeDraft.salary_grade || null,
        salary_band: employeeDraft.salary_band || null,
        cost_center_code: employeeDraft.cost_center_code || null,
        functional_manager_id: employeeDraft.functional_manager_id || null,
        functional_manager_scope: employeeDraft.functional_manager_scope || null,
        role_category: employeeDraft.role_category || null,
        supervisor_id: employeeDraft.supervisor_id || null,
        branch: employeeDraft.branch || null,
        address: employeeDraft.address || null,
        employment_type: employeeDraft.employment_type || selectedEmployee.employment_type,
        employment_status: employeeDraft.employment_status || selectedEmployee.employment_status,
        employment_start_date: employeeDraft.employment_start_date || employeeDraft.hire_date || null,
        employment_end_date: employeeDraft.employment_end_date || null,
        hire_date: employeeDraft.hire_date || employeeDraft.employment_start_date || null,
        pay_frequency: employeeDraft.pay_frequency || "monthly",
        base_salary: Number(employeeDraft.base_salary || 0),
        contract_signed: Boolean(employeeDraft.contract_signed),
        budget_approved: Boolean(employeeDraft.budget_approved),
        probation_required: Boolean(employeeDraft.probation_required),
        probation_start_date: employeeDraft.probation_start_date || null,
        probation_end_date: employeeDraft.probation_end_date || null,
        probation_duration_months: Number(employeeDraft.probation_duration_months || 0) || null,
        confirmation_status: employeeDraft.confirmation_status || selectedEmployee.confirmation_status,
        confirmation_notes: employeeDraft.confirmation_notes || null,
        next_confirmation_review_date: employeeDraft.next_confirmation_review_date || null,
      };
      const updated = await api.put<Employee>(`/api/hrm/employees/${selectedEmployee.id}`, payload);
      setEmployeeDetail(updated);
      setEmployeeDraft(updated);
      setActivationMessage("Employee profile updated.");
      await Promise.all([loadEmployees(), loadOrganizationOptions()]);
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Employee update failed");
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function refreshSelectedProfile() {
    if (!selectedEmployee) return;
    const [employee, profile, employment] = await Promise.all([
      api.get<Employee>(`/api/hrm/employees/${selectedEmployee.id}`),
      api.get<EmployeeProfileBundle>(`/api/hrm/employees/${selectedEmployee.id}/profile`),
      api.get<EmploymentInfoBundle>(`/api/hrm/employment-info/${selectedEmployee.id}`).catch(() => null),
    ]);
    const [assignments, documents, compliance, movements, statuses] = await Promise.all([
      api.get<AssignmentBundle>(`/api/hrm/employees/${selectedEmployee.id}/assignments`).catch(() => null),
      api.get<ProfileRecord[]>(`/api/hrm/employees/${selectedEmployee.id}/documents`).catch(() => []),
      api.get<DocumentCompliance>(`/api/hrm/employees/${selectedEmployee.id}/documents/compliance`).catch(() => null),
      api.get<ProfileRecord[]>(`/api/hrm/employees/${selectedEmployee.id}/movements`).catch(() => []),
      api.get<ProfileRecord[]>(`/api/hrm/employees/${selectedEmployee.id}/status-history`).catch(() => []),
    ]);
    setEmployeeDetail(employee);
    setEmployeeDraft(employee);
    setProfileBundle(profile);
    setEmploymentInfo(employment);
    setAssignmentBundle(assignments ? { ...assignments, documents } : null);
    setDocumentCompliance(compliance);
    setMovementHistory(movements);
    setStatusHistory(statuses);
    await loadEmployees();
  }

  async function submitEmploymentInfoChange() {
    if (!selectedEmployee || !employmentNewValue || !employmentReason) return;
    setActivationError(null);
    const isManagerAction = employmentAction.includes("manager");
    const payload = isManagerAction
      ? {
          manager_id: employmentNewValue,
          effective_date: employmentEffectiveDate,
          reason: employmentReason,
          authority_scope: employmentAuthorityScope || null,
        }
      : {
          new_value: employmentNewValue,
          effective_date: employmentEffectiveDate,
          reason: employmentReason,
        };
    try {
      const result = await api.post<{ status?: string; buc_code?: string }>(`/api/hrm/employment-info/${selectedEmployee.id}/${employmentAction}`, payload);
      setActivationMessage(`${result.buc_code ?? "Employment change"} recorded with status ${result.status ?? "submitted"}.`);
      setEmploymentNewValue("");
      setEmploymentReason("");
      setEmploymentAuthorityScope("");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Employment information change failed");
    }
  }

  async function savePersonalProfile() {
    if (!selectedEmployee) return;
    setIsSavingProfileSection(true);
    setActivationError(null);
    try {
      await api.put(`/api/hrm/employees/${selectedEmployee.id}/profile`, {
        first_name: employeeDraft.first_name,
        middle_name: employeeDraft.middle_name,
        last_name: employeeDraft.last_name,
        preferred_name: employeeDraft.preferred_name,
        gender: employeeDraft.gender,
        date_of_birth: employeeDraft.date_of_birth,
        nationality: employeeDraft.nationality,
        national_id: employeeDraft.national_id,
        passport_number: employeeDraft.passport_number,
        place_of_birth: employeeDraft.place_of_birth,
        religion: employeeDraft.religion,
        marital_status: employeeDraft.marital_status,
        change_reason: "Updated from employee profile",
      });
      setActivationMessage("Personal profile saved.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Personal profile update failed");
    } finally {
      setIsSavingProfileSection(false);
    }
  }

  async function saveContactInformation() {
    if (!selectedEmployee) return;
    setIsSavingProfileSection(true);
    setActivationError(null);
    try {
      await api.put(`/api/hrm/employees/${selectedEmployee.id}/contacts`, {
        personal_email: employeeDraft.personal_email || null,
        corporate_email: employeeDraft.corporate_email || employeeDraft.email || null,
        mobile_number: employeeDraft.phone || null,
        alternative_phone: employeeDraft.alternative_phone || null,
        physical_address: employeeDraft.physical_address || employeeDraft.address || null,
        postal_address: employeeDraft.postal_address || null,
        city: employeeDraft.city || null,
        county: employeeDraft.county || null,
        country: employeeDraft.country || null,
        change_reason: "Updated from employee profile",
      });
      setActivationMessage("Contact information saved.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Contact update failed");
    } finally {
      setIsSavingProfileSection(false);
    }
  }

  async function saveBiography() {
    if (!selectedEmployee) return;
    setIsSavingProfileSection(true);
    setActivationError(null);
    try {
      await api.put(`/api/hrm/employees/${selectedEmployee.id}/biography`, {
        employee_bio: employeeDraft.biography || "",
        professional_summary: employeeDraft.professional_summary || "",
        skills: employeeDraft.skills || "",
        languages: employeeDraft.languages || "",
        certifications_summary: employeeDraft.certifications_summary || "",
      });
      setActivationMessage("Biography saved.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Biography update failed");
    } finally {
      setIsSavingProfileSection(false);
    }
  }

  async function addDependant() {
    if (!selectedEmployee) return;
    setActivationError(null);
    try {
      await api.post(`/api/hrm/employees/${selectedEmployee.id}/dependants`, {
        ...dependantDraft,
        date_of_birth: dependantDraft.date_of_birth || null,
        beneficiary_percentage: Number(dependantDraft.beneficiary_percentage || 0),
      });
      setDependantDraft(initialDependantDraft);
      setActivationMessage("Dependant added.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Dependant add failed");
    }
  }

  async function removeDependant(id: string) {
    if (!selectedEmployee) return;
    await api.delete(`/api/hrm/employees/${selectedEmployee.id}/dependants/${id}`);
    setActivationMessage("Dependant archived.");
    await refreshSelectedProfile();
  }

  async function addEmergencyContact() {
    if (!selectedEmployee) return;
    setActivationError(null);
    try {
      await api.post(`/api/hrm/employees/${selectedEmployee.id}/emergency-contacts`, emergencyDraft);
      setEmergencyDraft(initialEmergencyDraft);
      setActivationMessage("Emergency contact added.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Emergency contact add failed");
    }
  }

  async function uploadPhoto() {
    if (!selectedEmployee || !photoFile) return;
    const formData = new FormData();
    formData.append("file", photoFile);
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_BASE_URL}/api/hrm/employees/${selectedEmployee.id}/photo`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: formData,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: "Photo upload failed" }));
      throw new Error(typeof payload.detail === "string" ? payload.detail : "Photo upload failed");
    }
    setPhotoFile(null);
    setActivationMessage("Employee photo uploaded.");
    await refreshSelectedProfile();
  }

  async function submitAssignmentAction() {
    if (!selectedEmployee || !assignmentValue || !assignmentReason) return;
    const isTransfer = assignmentAction.endsWith("-transfer");
    const method = isTransfer ? api.put : api.post;
    const payload = { value: assignmentValue, effective_date: assignmentDate, reason: assignmentReason };
    try {
      await method(`/api/hrm/employees/${selectedEmployee.id}/${assignmentAction}`, payload);
      setActivationMessage("Organizational assignment saved.");
      setAssignmentValue("");
      setAssignmentReason("");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Assignment action failed");
    }
  }

  async function assignProject() {
    if (!selectedEmployee || !assignmentValue || !projectRole) return;
    try {
      await api.post(`/api/hrm/employees/${selectedEmployee.id}/projects`, {
        project_id: assignmentValue,
        role: projectRole,
        allocation_percentage: Number(projectAllocation || 0),
        start_date: assignmentDate,
        reason: assignmentReason || "Project assignment",
      });
      setActivationMessage("Project assignment saved.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Project assignment failed");
    }
  }

  async function assignTeam() {
    if (!selectedEmployee || !assignmentValue) return;
    try {
      await api.post(`/api/hrm/employees/${selectedEmployee.id}/teams`, {
        team_name: assignmentValue,
        department: selectedEmployee.department || employeeDraft.department || "",
        primary_team: true,
        effective_date: assignmentDate,
        reason: assignmentReason || "Team assignment",
      });
      setActivationMessage("Team assignment saved.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Team assignment failed");
    }
  }

  async function uploadEmployeeDocument() {
    if (!selectedEmployee || !documentFile) return;
    setActivationError(null);
    try {
      const formData = new FormData();
      formData.append("file", documentFile);
      const token = localStorage.getItem("access_token");
      const params = new URLSearchParams({ document_type: documentType });
      if (documentExpiry) params.set("expiry_date", documentExpiry);
      const response = await fetch(`${API_BASE_URL}/api/hrm/employees/${selectedEmployee.id}/documents?${params.toString()}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: formData,
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Document upload failed");
      }
      setDocumentFile(null);
      setActivationMessage("Employee document uploaded.");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Document upload failed");
    }
  }

  async function documentAction(documentId: string, action: "verify" | "reject" | "archive") {
    if (!selectedEmployee) return;
    const body = action === "reject" ? { reason: window.prompt("Rejection reason") || "" } : action === "archive" ? { reason: window.prompt("Archive reason") || "" } : { comments: "Verified from employee profile" };
    if (action === "reject" && !body.reason) return;
    if (action === "archive" && !body.reason) return;
    await api.post(`/api/hrm/employees/${selectedEmployee.id}/documents/${documentId}/${action}`, body);
    setActivationMessage(`Document ${action} completed.`);
    await refreshSelectedProfile();
  }

  async function downloadEmployeeDocument(documentId: string) {
    if (!selectedEmployee) return;
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_BASE_URL}/api/hrm/employees/${selectedEmployee.id}/documents/${documentId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!response.ok) throw new Error("Document download failed");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  async function showDocumentVersions(documentId: string) {
    if (!selectedEmployee) return;
    const rows = await api.get<ProfileRecord[]>(`/api/hrm/employees/${selectedEmployee.id}/documents/${documentId}/versions`);
    setDocumentVersions(rows);
  }

  async function createEmployee(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateError(null);
    setIsSavingEmployee(true);
    try {
      const payload = {
        ...employeeForm,
        candidate_id: employeeForm.candidate_id || null,
        supervisor_id: employeeForm.supervisor_id || null,
        date_of_birth: employeeForm.date_of_birth || null,
        hire_date: employeeForm.hire_date || null,
        employment_start_date: employeeForm.employment_start_date || employeeForm.hire_date || null,
        employment_end_date: employeeForm.employment_end_date || null,
        probation_required: employeeForm.probation_required,
        probation_start_date: employeeForm.probation_start_date || employeeForm.hire_date || null,
        probation_end_date: employeeForm.probation_end_date || null,
        probation_duration_months: Number(employeeForm.probation_duration_months || 0),
        base_salary: Number(employeeForm.base_salary || 0),
        employment_status: "pending_activation",
        internal_only: true,
      };
      const created = await api.post<Employee>("/api/hrm/employees", payload);
      setIsCreateOpen(false);
      setSelectedId(created.id);
      await Promise.all([loadEmployees(), loadOrganizationOptions()]);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Could not create employee");
    } finally {
      setIsSavingEmployee(false);
    }
  }

  function employeeImportUrl(kind: "import" | "validate") {
    const params = new URLSearchParams({
      mode: importMode,
      import_as_draft: String(importAsDraft),
      rollback_on_error: String(rollbackOnError),
    });
    return `${API_BASE_URL}/api/hrm/employees/import${kind === "validate" ? "/validate" : ""}?${params.toString()}`;
  }

  async function uploadEmployeeImport(event: ChangeEvent<HTMLInputElement>, kind: "import" | "validate") {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setIsImporting(true);
    setImportError(null);
    setLastBatch(null);
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("access_token");
    try {
      const response = await fetch(employeeImportUrl(kind), {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: formData,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: "Employee import failed" }));
        const detail =
          typeof payload.detail === "string"
            ? payload.detail
            : payload.detail?.message
              ? `${payload.detail.message}${payload.detail.errors?.length ? `: ${payload.detail.errors.join(", ")}` : ""}`
              : JSON.stringify(payload.detail ?? payload);
        throw new Error(detail);
      }
      const batch = await response.json();
      setLastBatch(batch);
      if (kind === "import") await loadEmployees();
    } catch (err) {
      setImportError(err instanceof TypeError ? "Could not reach the backend. Confirm the API is running on port 8055, then try again." : err instanceof Error ? err.message : "Employee import failed");
    } finally {
      setIsImporting(false);
    }
  }

  async function activateSelectedEmployee() {
    if (!selectedEmployee) return;
    setIsActivating(true);
    setActivationError(null);
    setActivationMessage(null);
    try {
      const result = await api.post<{ readiness_score?: number; current_status?: string }>(
        `/api/hrm/employees/${selectedEmployee.id}/activate`,
        {}
      );
      setActivationMessage(`Employee activated successfully. Readiness ${result.readiness_score ?? 100}%.`);
      await Promise.all([loadEmployees(), loadOrganizationOptions()]);
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Employee activation failed");
    } finally {
      setIsActivating(false);
    }
  }

  async function bulkActivateReadyEmployees() {
    const candidateIds = employees
      .filter((employee) => ["draft", "pending_activation", "onboarding", "employee_number_assigned"].includes(employee.employment_status ?? ""))
      .map((employee) => employee.id);
    if (!candidateIds.length) {
      setActivationError("No draft, onboarding, or pending activation employees were found.");
      return;
    }
    setIsActivating(true);
    setActivationError(null);
    setActivationMessage(null);
    try {
      const result = await api.post<{ activated: number; failed: number }>("/api/hrm/employees/bulk-activate", {
        employee_ids: candidateIds,
        continue_on_error: true,
      });
      setActivationMessage(`Bulk activation complete. Activated ${result.activated}; failed ${result.failed}.`);
      await Promise.all([loadEmployees(), loadOrganizationOptions()]);
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Bulk activation failed");
    } finally {
      setIsActivating(false);
    }
  }

  async function extendSelectedEmployment() {
    if (!selectedEmployee) return;
    const newEndDate = window.prompt("Enter the approved new end date (YYYY-MM-DD)");
    if (!newEndDate) return;
    setActivationError(null);
    setActivationMessage(null);
    try {
      await api.post(`/api/hrm/employees/${selectedEmployee.id}/employment-extension`, {
        new_end_date: newEndDate,
        reason: "Extended from employee profile",
      });
      setActivationMessage("Employment extension approved and recorded.");
      await loadEmployees();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Employment extension failed");
    }
  }

  async function reviewSelectedProbation(action: "extend" | "confirm" | "fail" | "close") {
    if (!selectedEmployee) return;
    const body: Record<string, string> = {};
    if (action === "extend") {
      const newEndDate = window.prompt("Enter the new probation end date (YYYY-MM-DD)");
      const reason = window.prompt("Enter the probation extension reason");
      if (!newEndDate || !reason) return;
      body.new_end_date = newEndDate;
      body.reason = reason;
    }
    if (action === "fail") {
      const reason = window.prompt("Enter the probation failure reason");
      if (!reason) return;
      body.reason = reason;
    }
    try {
      await api.post(`/api/hrm/employees/${selectedEmployee.id}/probation/${action}`, body);
      setActivationMessage(`Probation ${action} action completed.`);
      await loadEmployees();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Probation action failed");
    }
  }

  async function submitConfirmationDecision() {
    if (!selectedEmployee) return;
    setActivationError(null);
    setActivationMessage(null);
    try {
      const body = {
        confirmation_date: confirmationDate,
        confirmation_notes: confirmationNotes,
        reason: confirmationNotes,
        next_review_date: nextReviewDate,
      };
      const endpoint =
        confirmationDecision === "confirm"
          ? `/api/hrm/employees/${selectedEmployee.id}/confirm`
          : confirmationDecision === "defer"
            ? `/api/hrm/employees/${selectedEmployee.id}/confirmation/defer`
            : `/api/hrm/employees/${selectedEmployee.id}/confirmation/reject`;
      const result = await api.post<{ confirmation_status?: string }>(endpoint, body);
      setActivationMessage(`Confirmation decision saved: ${result.confirmation_status ?? confirmationDecision}.`);
      const refreshed = await api.get<Employee>(`/api/hrm/employees/${selectedEmployee.id}`);
      setEmployeeDetail(refreshed);
      setEmployeeDraft(refreshed);
      await loadEmployees();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Confirmation decision failed");
    }
  }

  async function submitMovementAction() {
    if (!selectedEmployee || !movementReason) return;
    setActivationError(null);
    const payload: Record<string, string | number | boolean | null> = {
      effective_date: movementEffectiveDate,
      reason: movementReason,
    };
    if (["promote", "demote", "change-role"].includes(movementAction)) payload.new_role = movementNewValue || null;
    if (["transfer", "internal-transfer"].includes(movementAction)) payload.new_department = movementNewValue || null;
    if (["acting-appointment", "temporary-assignment"].includes(movementAction)) {
      payload.start_date = movementEffectiveDate;
      payload.end_date = movementNewValue || movementEffectiveDate;
      payload.assignment_owner = fullName(selectedEmployee);
    }
    if (movementAction === "secondment") {
      payload.start_date = movementEffectiveDate;
      payload.end_date = movementNewValue || movementEffectiveDate;
      payload.host_unit = movementNewValue || "Host unit";
      payload.cost_allocation_rule = "Review by Finance";
    }
    if (movementAction === "return-from-assignment") payload.return_date = movementEffectiveDate;
    try {
      const result = await api.post<ProfileRecord>(`/api/hrm/employees/${selectedEmployee.id}/${movementAction}`, payload);
      setActivationMessage(`Movement recorded: ${result.movement_code ?? movementAction}.`);
      setMovementReason("");
      setMovementNewValue("");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Movement action failed");
    }
  }

  async function submitStatusAction() {
    if (!selectedEmployee || !movementReason) return;
    setActivationError(null);
    const payload: Record<string, string | number | boolean | null> = {
      effective_date: movementEffectiveDate,
      reason: movementReason,
    };
    if (statusAction === "suspend") {
      payload.suspension_type = movementNewValue || "administrative";
      payload.paid = true;
    }
    if (statusAction === "leave-of-absence") {
      payload.leave_type = movementNewValue || "Long Term Leave";
      payload.expected_return_date = movementEffectiveDate;
    }
    if (statusAction === "return-from-leave-of-absence") payload.return_date = movementEffectiveDate;
    if (statusAction === "terminate") payload.termination_type = movementNewValue || "resignation";
    if (statusAction === "retire") payload.retirement_type = movementNewValue || "normal";
    if (statusAction === "death-in-service") {
      payload.date_of_death = movementEffectiveDate;
      payload.supporting_document_url = movementNewValue || "Restricted HR documentation";
    }
    try {
      const result = await api.post<ProfileRecord>(`/api/hrm/employees/${selectedEmployee.id}/${statusAction}`, payload);
      setActivationMessage(`Status action recorded: ${result.status_code ?? statusAction}.`);
      setMovementReason("");
      setMovementNewValue("");
      await refreshSelectedProfile();
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Status action failed");
    }
  }

  async function deleteSelectedEmployee() {
    if (!selectedEmployee) return;
    const confirmed = window.confirm(`Delete ${fullName(selectedEmployee)} from the employee register?`);
    if (!confirmed) return;
    setActivationError(null);
    setActivationMessage(null);
    try {
      await api.delete(`/api/hrm/employees/${selectedEmployee.id}`);
      setActivationMessage("Employee record deleted.");
      setSelectedId(null);
      await Promise.all([loadEmployees(), loadOrganizationOptions()]);
    } catch (err) {
      setActivationError(err instanceof Error ? err.message : "Employee delete failed");
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
              <Users size={14} />
              HRM source of truth
            </div>
            <h1 className="text-2xl font-bold text-slate-950">Employees</h1>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
              Select an employee to drill into department, line manager, direct reports, sales pipeline, accounts,
              invoices, projects, SLAs, KPIs, benefits, leave, payroll visibility, assets, and collaborative work.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={openEmployeeCreation}>
              <UserPlus size={16} />
              Create Employee
            </Button>
            <Button type="button" variant="secondary" disabled={isActivating} onClick={bulkActivateReadyEmployees}>
              <ShieldCheck size={16} />
              Bulk Activate
            </Button>
            <a
              href={`${API_BASE_URL}/api/hrm/employees/import/template`}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <Download size={16} />
              Template
            </a>
            <Button type="button" variant="secondary" onClick={loadEmployees}>
              <RefreshCw size={16} />
              Refresh employees
            </Button>
          </div>
        </div>
      </section>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
      {activationError && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{activationError}</div>}
      {activationMessage && <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">{activationMessage}</div>}

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid gap-3 md:grid-cols-5">
          <Field label="Employment Type Filter">
            <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} className={inputClass}>
              <option value="all">All types</option>
              {["Permanent", "Contract", "Casual", "Internship", "Consultant"].map((type) => <option key={type}>{type}</option>)}
            </select>
          </Field>
          <Field label="Status Filter">
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className={inputClass}>
              <option value="all">All statuses</option>
              <option value="expiring">Expiring soon</option>
              <option value="expired">Expired</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </Field>
          <Field label="Probation Filter">
            <select value={probationFilter} onChange={(event) => setProbationFilter(event.target.value)} className={inputClass}>
              <option value="all">All probation</option>
              <option value="on_probation">On probation</option>
              <option value="due">Due for review</option>
              <option value="extended">Extended</option>
              <option value="failed">Failed</option>
              <option value="confirmed">Confirmed</option>
            </select>
          </Field>
          <Field label="Confirmation Filter">
            <select value={confirmationFilter} onChange={(event) => setConfirmationFilter(event.target.value)} className={inputClass}>
              <option value="all">All confirmations</option>
              <option value="pending">Pending Confirmation</option>
              <option value="confirmed">Confirmed</option>
              <option value="deferred">Deferred Confirmation</option>
              <option value="rejected">Rejected Confirmation</option>
            </select>
          </Field>
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
            Note: Contract, casual, internship, and consultant employees will be automatically deactivated after the end date unless an approved extension exists.
            Probation reminders are sent before the probation end date, and HR must complete review before confirmation.
            Employee confirmation closes the probation workflow and may affect benefits, leave, and promotion eligibility depending on HR policy.
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
              <Upload size={14} />
              EMP-003 Import Employee Records
            </div>
            <h2 className="text-lg font-semibold text-slate-950">Bulk employee import</h2>
            <p className="mt-1 max-w-3xl text-sm text-slate-600">
              Upload CSV or Excel records, validate required columns, detect duplicates, generate employee numbers, and trigger payroll, IAM, leave, finance, assets, notifications, and audit workflows.
            </p>
          </div>
          <div className="grid gap-2 sm:grid-cols-2 xl:min-w-[560px] xl:grid-cols-4">
            <select value={importMode} onChange={(event) => setImportMode(event.target.value)} className={inputClass}>
              <option value="create">Create new only</option>
              <option value="update">Update existing only</option>
              <option value="upsert">Create and update</option>
              <option value="draft">Import as draft</option>
            </select>
            <label className="flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700">
              <input type="checkbox" checked={rollbackOnError} onChange={(event) => setRollbackOnError(event.target.checked)} />
              Full rollback
            </label>
            <input ref={validateFileRef} type="file" accept=".csv,.xlsx,.xls" onChange={(event) => uploadEmployeeImport(event, "validate")} className="hidden" />
            <input ref={importFileRef} type="file" accept=".csv,.xlsx,.xls" onChange={(event) => uploadEmployeeImport(event, "import")} className="hidden" />
            <Button type="button" variant="secondary" disabled={isImporting} onClick={() => validateFileRef.current?.click()}>
              Validate
            </Button>
            <Button type="button" disabled={isImporting} onClick={() => importFileRef.current?.click()}>
              {isImporting ? "Processing..." : "Upload Data"}
            </Button>
          </div>
        </div>
        <label className="mt-3 flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" checked={importAsDraft} onChange={(event) => setImportAsDraft(event.target.checked)} />
          Import valid rows as draft for HR review before activation
        </label>
        {importError && <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{importError}</div>}
        {lastBatch && (
          <div className="mt-4 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm md:grid-cols-6">
            <Metric label="Batch" value={lastBatch.batch_number} />
            <Metric label="Status" value={lastBatch.processing_status ?? "-"} />
            <Metric label="Rows" value={lastBatch.total_rows ?? 0} />
            <Metric label="Valid" value={lastBatch.valid_rows ?? 0} />
            <Metric label="Created/Updated" value={`${lastBatch.created_rows ?? 0}/${lastBatch.updated_rows ?? 0}`} />
            <Metric label="Rejected" value={lastBatch.rejected_rows ?? 0} />
            {lastBatch.parse_summary && <p className="md:col-span-6 text-slate-600">{lastBatch.parse_summary}</p>}
          </div>
        )}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 p-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Search size={16} />
                {query ? <span>Filtering by {query}</span> : <span>Use the static search bar above.</span>}
              </div>
              <span className="text-sm font-semibold text-slate-700">{filtered.length} employee{filtered.length === 1 ? "" : "s"}</span>
            </div>
          </div>
          <div className="divide-y divide-slate-100">
            {isLoading ? (
              <p className="p-4 text-sm text-slate-500">Loading employees...</p>
            ) : filtered.length ? (
              filtered.map((employee) => (
                <button
                  key={employee.id}
                  type="button"
                  onClick={() => openEmployee(employee)}
                  className={`grid w-full gap-3 p-4 text-left transition hover:bg-slate-50 md:grid-cols-[1.4fr_1fr_1fr_auto] md:items-center ${
                    selectedId === employee.id ? "bg-blue-50/70" : "bg-white"
                  }`}
                >
                  <span className="min-w-0">
                    <span className="block font-semibold text-slate-950">{fullName(employee)}</span>
                    <span className="mt-1 block text-xs text-slate-500">{format(employee.employee_code)} / {format(employee.email)}</span>
                  </span>
                  <span className="text-sm text-slate-700">{format(employee.department)} / {format(employee.job_title)}</span>
                  <span className="flex flex-wrap gap-1">
                    <StatusBadge label={format(employee.employment_status)} tone={employee.employment_status === "active" ? "green" : "slate"} />
                    <StatusBadge label={format(employee.employment_type)} tone="blue" />
                    {employmentExpiryStatus(employee) === "expiring_soon" && <StatusBadge label="Expiring soon" tone="amber" />}
                    {employmentExpiryStatus(employee) === "expired" && <StatusBadge label="Expired" tone="red" />}
                    {employee.probation_status && employee.probation_status !== "Not Applicable" && <StatusBadge label={employee.probation_status} tone={employee.probation_status === "Due for Review" ? "amber" : employee.probation_status === "Failed" ? "red" : "blue"} />}
                    {employee.confirmation_status && employee.confirmation_status !== "Not Applicable" && <StatusBadge label={employee.confirmation_status} tone={employee.confirmation_status === "Confirmed" ? "green" : employee.confirmation_status === "Rejected" ? "red" : employee.confirmation_status === "Confirmation Deferred" ? "amber" : "blue"} />}
                  </span>
                  <span className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700">
                    Open
                    <ArrowRight size={16} className="shrink-0" />
                  </span>
                </button>
              ))
            ) : (
              <p className="p-4 text-sm text-slate-500">No matching employees found.</p>
            )}
          </div>
      </section>

      {selectedEmployee && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
          <section className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-2xl">
            <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Employee profile</div>
                <h2 className="mt-1 text-2xl font-bold text-slate-950">{fullName(selectedEmployee)}</h2>
                <p className="mt-1 text-sm text-slate-600">{format(selectedEmployee.employee_code)} / {format(selectedEmployee.email)}</p>
              </div>
              <button type="button" onClick={() => setSelectedId(null)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900">
                <X size={20} />
              </button>
            </div>

            <div className="flex gap-2 overflow-x-auto border-b border-slate-200 px-5 py-3">
              {["overview", "personal", "contact", "dependants", "emergency", "biography", "assignment", "employment", "probation", "confirmation", "audit", "actions"].map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setEmployeeModalTab(tab)}
                  className={`rounded-lg px-3 py-2 text-sm font-semibold capitalize transition ${
                    employeeModalTab === tab ? "bg-blue-600 text-white shadow-sm" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="p-5">
              {employeeModalTab === "overview" && (
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 md:col-span-3">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                      <div className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-white text-xl font-bold text-slate-500">
                        {(profileBundle?.active_photo?.file_url || selectedEmployee.photo_url) ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={`${API_BASE_URL}${String(profileBundle?.active_photo?.file_url || selectedEmployee.photo_url)}`} alt={fullName(selectedEmployee)} className="h-full w-full object-cover" />
                        ) : (
                          fullName(selectedEmployee).slice(0, 2).toUpperCase()
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-slate-950">Profile completion</p>
                        <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-200">
                          <div className="h-full rounded-full bg-blue-600" style={{ width: `${profileBundle?.profile_completion_percentage ?? selectedEmployee.profile_completion_percentage ?? 0}%` }} />
                        </div>
                        <p className="mt-2 text-sm text-slate-600">{profileBundle?.profile_completion_percentage ?? selectedEmployee.profile_completion_percentage ?? 0}% complete. Keep personal, contact, emergency, biography, and photo records current.</p>
                      </div>
                    </div>
                  </div>
                  <Metric label="Department" value={format(selectedEmployee.department)} />
                  <Metric label="Job title" value={format(selectedEmployee.job_title)} />
                  <Metric label="Line manager" value={selectedManager ? fullName(selectedManager) : "-"} />
                  <Metric label="Employment status" value={format(selectedEmployee.employment_status)} />
                  <Metric label="Employment type" value={format(selectedEmployee.employment_type)} />
                  <Metric label="Probation" value={format(selectedEmployee.probation_status)} />
                  <Metric label="Confirmation" value={format(selectedEmployee.confirmation_status)} />
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 md:col-span-3">
                    <p className="text-sm font-semibold text-slate-950">Employee workspace</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      Use this window for employee-owned profile, employment, probation, confirmation, audit, and lifecycle actions. For module-owned workflows, open the linked HR module below so records stay in their source system.
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-white p-4 md:col-span-3">
                    <div className="mb-3 flex items-center justify-between">
                      <p className="text-sm font-semibold text-slate-950">Connected HR Modules</p>
                      <span className="text-xs font-medium text-slate-500">opens source module</span>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                      <ModuleLink href={`/hrm/organization?employee=${selectedEmployee.id}`} label="Organization" detail="Department, branch, team and reporting structure" />
                      <ModuleLink href={`/hrm/grc?employee=${selectedEmployee.id}`} label="Compliance" detail="Tax, statutory, permit, contract and certification readiness" />
                      <ModuleLink href={`/hrm/documents?employee=${selectedEmployee.id}`} label="Documents" detail={`${documentCompliance?.score ?? 0}% compliant / ${documentCompliance?.missing_count ?? 0} missing`} />
                      <ModuleLink href={`/hrm/recruitment?employee=${selectedEmployee.id}`} label="Recruitment" detail="Candidate, offer, onboarding source trail" />
                      <ModuleLink href={`/hrm/leave?employee=${selectedEmployee.id}`} label="Leave" detail="Balances, requests and approvals" />
                      <ModuleLink href={`/hrm/payroll?employee=${selectedEmployee.id}`} label="Payroll" detail="Payroll readiness, pay profile and benefits" />
                      <ModuleLink href={`/hrm/compensation?employee=${selectedEmployee.id}`} label="Compensation" detail="Salary history, allowances, benefits and insurance" />
                      <ModuleLink href={`/hrm/performance?employee=${selectedEmployee.id}`} label="Performance" detail="KPIs, reviews and goals" />
                      <ModuleLink href={`/hrm/training?employee=${selectedEmployee.id}`} label="Training" detail="Courses, certificates and compliance" />
                      <ModuleLink href={`/hrm/assets?employee=${selectedEmployee.id}`} label="Assets & Exit" detail="Assigned assets, recovery and offboarding clearance" />
                      <ModuleLink href={`/hrm/security?employee=${selectedEmployee.id}`} label="Access & Audit" detail="IAM link, permissions and access events" />
                    </div>
                  </div>
                </div>
              )}

              {employeeModalTab === "personal" && (
                <div className="space-y-4">
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                    Note: Changes to legal name, date of birth, and national identification details may require HR approval.
                  </div>
                  <div className="grid gap-4 md:grid-cols-3">
                    <Field label="First Name"><input value={employeeDraft.first_name ?? ""} onChange={(event) => updateEmployeeDraft("first_name", event.target.value)} className={inputClass} /></Field>
                    <Field label="Middle Name"><input value={employeeDraft.middle_name ?? ""} onChange={(event) => updateEmployeeDraft("middle_name", event.target.value)} className={inputClass} /></Field>
                    <Field label="Last Name"><input value={employeeDraft.last_name ?? ""} onChange={(event) => updateEmployeeDraft("last_name", event.target.value)} className={inputClass} /></Field>
                    <Field label="Preferred Name"><input value={employeeDraft.preferred_name ?? ""} onChange={(event) => updateEmployeeDraft("preferred_name", event.target.value)} className={inputClass} /></Field>
                    <Field label="Gender"><select value={employeeDraft.gender ?? ""} onChange={(event) => updateEmployeeDraft("gender", event.target.value)} className={inputClass}><option value="">Select</option><option>Female</option><option>Male</option><option>Non-binary</option><option>Prefer not to say</option></select></Field>
                    <Field label="Date of Birth"><input type="date" value={(employeeDraft.date_of_birth ?? "").slice(0, 10)} onChange={(event) => updateEmployeeDraft("date_of_birth", event.target.value)} className={inputClass} /></Field>
                    <Field label="Nationality"><input value={employeeDraft.nationality ?? ""} onChange={(event) => updateEmployeeDraft("nationality", event.target.value)} className={inputClass} /></Field>
                    <Field label="National ID"><input value={employeeDraft.national_id ?? ""} onChange={(event) => updateEmployeeDraft("national_id", event.target.value)} className={inputClass} /></Field>
                    <Field label="Passport Number"><input value={employeeDraft.passport_number ?? ""} onChange={(event) => updateEmployeeDraft("passport_number", event.target.value)} className={inputClass} /></Field>
                    <Field label="Place of Birth"><input value={employeeDraft.place_of_birth ?? ""} onChange={(event) => updateEmployeeDraft("place_of_birth", event.target.value)} className={inputClass} /></Field>
                    <Field label="Religion"><input value={employeeDraft.religion ?? ""} onChange={(event) => updateEmployeeDraft("religion", event.target.value)} className={inputClass} /></Field>
                    <Field label="Marital Status"><select value={employeeDraft.marital_status ?? ""} onChange={(event) => updateEmployeeDraft("marital_status", event.target.value)} className={inputClass}><option value="">Select</option><option>Single</option><option>Married</option><option>Divorced</option><option>Separated</option><option>Widowed</option></select></Field>
                  </div>
                  <Button type="button" disabled={isSavingProfileSection} onClick={savePersonalProfile}>Save Personal Profile</Button>
                </div>
              )}

              {employeeModalTab === "contact" && (
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <Field label="Personal Email"><input type="email" value={employeeDraft.personal_email ?? ""} onChange={(event) => updateEmployeeDraft("personal_email", event.target.value)} className={inputClass} /></Field>
                    <Field label="Corporate Email"><input type="email" value={employeeDraft.corporate_email ?? employeeDraft.email ?? ""} onChange={(event) => updateEmployeeDraft("corporate_email", event.target.value)} className={inputClass} /></Field>
                    <Field label="Mobile Number"><input value={employeeDraft.phone ?? ""} onChange={(event) => updateEmployeeDraft("phone", event.target.value)} className={inputClass} /></Field>
                    <Field label="Alternative Phone"><input value={employeeDraft.alternative_phone ?? ""} onChange={(event) => updateEmployeeDraft("alternative_phone", event.target.value)} className={inputClass} /></Field>
                    <Field label="Physical Address"><input value={employeeDraft.physical_address ?? employeeDraft.address ?? ""} onChange={(event) => updateEmployeeDraft("physical_address", event.target.value)} className={inputClass} /></Field>
                    <Field label="Postal Address"><input value={employeeDraft.postal_address ?? ""} onChange={(event) => updateEmployeeDraft("postal_address", event.target.value)} className={inputClass} /></Field>
                    <Field label="City"><input value={employeeDraft.city ?? ""} onChange={(event) => updateEmployeeDraft("city", event.target.value)} className={inputClass} /></Field>
                    <Field label="County"><input value={employeeDraft.county ?? ""} onChange={(event) => updateEmployeeDraft("county", event.target.value)} className={inputClass} /></Field>
                    <Field label="Country"><input value={employeeDraft.country ?? ""} onChange={(event) => updateEmployeeDraft("country", event.target.value)} className={inputClass} /></Field>
                  </div>
                  <Button type="button" disabled={isSavingProfileSection} onClick={saveContactInformation}>Save Contact Information</Button>
                </div>
              )}

              {employeeModalTab === "dependants" && (
                <div className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-6">
                    <input value={dependantDraft.full_name} onChange={(event) => setDependantDraft((current) => ({ ...current, full_name: event.target.value }))} className={inputClass} placeholder="Full name" />
                    <select value={dependantDraft.relationship} onChange={(event) => setDependantDraft((current) => ({ ...current, relationship: event.target.value }))} className={inputClass}><option>Spouse</option><option>Child</option><option>Parent</option><option>Guardian</option><option>Other</option></select>
                    <input type="date" value={dependantDraft.date_of_birth} onChange={(event) => setDependantDraft((current) => ({ ...current, date_of_birth: event.target.value }))} className={inputClass} />
                    <select value={dependantDraft.gender} onChange={(event) => setDependantDraft((current) => ({ ...current, gender: event.target.value }))} className={inputClass}><option value="">Gender</option><option>Female</option><option>Male</option><option>Other</option></select>
                    <input type="number" value={dependantDraft.beneficiary_percentage} onChange={(event) => setDependantDraft((current) => ({ ...current, beneficiary_percentage: event.target.value }))} className={inputClass} placeholder="Benefit %" />
                    <Button type="button" onClick={addDependant}>Add</Button>
                  </div>
                  <SimpleTable rows={profileBundle?.dependants ?? []} columns={["full_name", "relationship", "date_of_birth", "beneficiary_percentage", "medical_cover_eligible"]} onRemove={removeDependant} />
                </div>
              )}

              {employeeModalTab === "emergency" && (
                <div className="space-y-4">
                  <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-900">Note: Emergency contact information should be kept current at all times.</div>
                  <div className="grid gap-3 md:grid-cols-4">
                    <input value={emergencyDraft.full_name} onChange={(event) => setEmergencyDraft((current) => ({ ...current, full_name: event.target.value }))} className={inputClass} placeholder="Full name" />
                    <input value={emergencyDraft.relationship} onChange={(event) => setEmergencyDraft((current) => ({ ...current, relationship: event.target.value }))} className={inputClass} placeholder="Relationship" />
                    <input value={emergencyDraft.phone_number} onChange={(event) => setEmergencyDraft((current) => ({ ...current, phone_number: event.target.value }))} className={inputClass} placeholder="Phone number" />
                    <Button type="button" onClick={addEmergencyContact}>Add Contact</Button>
                    <input value={emergencyDraft.email} onChange={(event) => setEmergencyDraft((current) => ({ ...current, email: event.target.value }))} className={inputClass} placeholder="Email" />
                    <input value={emergencyDraft.alternative_phone} onChange={(event) => setEmergencyDraft((current) => ({ ...current, alternative_phone: event.target.value }))} className={inputClass} placeholder="Alternative phone" />
                    <input value={emergencyDraft.address} onChange={(event) => setEmergencyDraft((current) => ({ ...current, address: event.target.value }))} className={inputClass} placeholder="Address" />
                    <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={emergencyDraft.is_primary} onChange={(event) => setEmergencyDraft((current) => ({ ...current, is_primary: event.target.checked }))} />Primary</label>
                  </div>
                  <SimpleTable rows={profileBundle?.emergency_contacts ?? []} columns={["contact_name", "relationship", "phone", "email", "is_primary"]} />
                </div>
              )}

              {employeeModalTab === "biography" && (
                <div className="space-y-4">
                  <Field label="Employee Bio"><textarea value={employeeDraft.biography ?? ""} onChange={(event) => updateEmployeeDraft("biography", event.target.value)} className="min-h-24 w-full rounded-lg border border-slate-200 p-3 text-sm" /></Field>
                  <Field label="Professional Summary"><textarea value={employeeDraft.professional_summary ?? ""} onChange={(event) => updateEmployeeDraft("professional_summary", event.target.value)} className="min-h-24 w-full rounded-lg border border-slate-200 p-3 text-sm" /></Field>
                  <div className="grid gap-4 md:grid-cols-3">
                    <Field label="Skills"><textarea value={employeeDraft.skills ?? ""} onChange={(event) => updateEmployeeDraft("skills", event.target.value)} className="min-h-20 w-full rounded-lg border border-slate-200 p-3 text-sm" /></Field>
                    <Field label="Languages"><textarea value={employeeDraft.languages ?? ""} onChange={(event) => updateEmployeeDraft("languages", event.target.value)} className="min-h-20 w-full rounded-lg border border-slate-200 p-3 text-sm" /></Field>
                    <Field label="Certifications Summary"><textarea value={employeeDraft.certifications_summary ?? ""} onChange={(event) => updateEmployeeDraft("certifications_summary", event.target.value)} className="min-h-20 w-full rounded-lg border border-slate-200 p-3 text-sm" /></Field>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <input type="file" accept=".jpg,.jpeg,.png,.webp" onChange={(event) => setPhotoFile(event.target.files?.[0] ?? null)} className="text-sm text-slate-700" />
                    <Button type="button" variant="secondary" disabled={!photoFile} onClick={uploadPhoto}>Upload Photo</Button>
                    <Button type="button" disabled={isSavingProfileSection} onClick={saveBiography}>Save Biography</Button>
                  </div>
                </div>
              )}

              {employeeModalTab === "audit" && (
                <div className="space-y-4">
                  <SimpleTable rows={profileBundle?.change_requests ?? []} columns={["section", "approval_status", "requested_by", "created_at"]} />
                  <SimpleTable rows={profileBundle?.audit_history ?? []} columns={["action", "summary", "actor_email", "created_at"]} />
                </div>
              )}

              {employeeModalTab === "assignment" && (
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="First Name">
                    <input value={employeeDraft.first_name ?? ""} onChange={(event) => updateEmployeeDraft("first_name", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Last Name">
                    <input value={employeeDraft.last_name ?? ""} onChange={(event) => updateEmployeeDraft("last_name", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Email">
                    <input type="email" value={employeeDraft.email ?? ""} onChange={(event) => updateEmployeeDraft("email", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Phone">
                    <input value={employeeDraft.phone ?? ""} onChange={(event) => updateEmployeeDraft("phone", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Department">
                    <select value={employeeDraft.department ?? ""} onChange={(event) => updateEmployeeDraft("department", event.target.value)} className={inputClass}>
                      <option value="">Select department</option>
                      {activeDepartments.map((department) => <option key={department.id} value={department.name}>{department.name}</option>)}
                    </select>
                  </Field>
                  <Field label="Position / Job Title">
                    <select value={employeeDraft.job_title ?? ""} onChange={(event) => updateEmployeeDraft("job_title", event.target.value)} className={inputClass}>
                      <option value="">Select position</option>
                      {modalPositions.map((position) => <option key={position.id} value={position.position_title}>{position.position_title}</option>)}
                    </select>
                  </Field>
                  <Field label="Line Manager">
                    <select value={employeeDraft.supervisor_id ?? ""} onChange={(event) => updateEmployeeDraft("supervisor_id", event.target.value)} className={inputClass}>
                      <option value="">Top-level or unassigned</option>
                      {activeManagers.filter((manager) => manager.id !== selectedEmployee.id).map((manager) => (
                        <option key={manager.id} value={manager.id}>{fullName(manager)} / {manager.department}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Branch">
                    <input value={employeeDraft.branch ?? ""} onChange={(event) => updateEmployeeDraft("branch", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Business Unit">
                    <input value={employeeDraft.business_unit ?? ""} onChange={(event) => updateEmployeeDraft("business_unit", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Role Category">
                    <input value={employeeDraft.role_category ?? ""} onChange={(event) => updateEmployeeDraft("role_category", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Job Grade">
                    <input value={employeeDraft.salary_grade ?? ""} onChange={(event) => updateEmployeeDraft("salary_grade", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Salary Band">
                    <input value={employeeDraft.salary_band ?? ""} onChange={(event) => updateEmployeeDraft("salary_band", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Cost Center">
                    <input value={employeeDraft.cost_center_code ?? ""} onChange={(event) => updateEmployeeDraft("cost_center_code", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Functional Manager">
                    <select value={employeeDraft.functional_manager_id ?? ""} onChange={(event) => updateEmployeeDraft("functional_manager_id", event.target.value)} className={inputClass}>
                      <option value="">Unassigned</option>
                      {activeManagers.filter((manager) => manager.id !== selectedEmployee.id).map((manager) => (
                        <option key={manager.id} value={manager.id}>{fullName(manager)} / {manager.department}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="Functional Scope">
                    <input value={employeeDraft.functional_manager_scope ?? ""} onChange={(event) => updateEmployeeDraft("functional_manager_scope", event.target.value)} className={inputClass} placeholder="Technical reviews, timesheets, project QA..." />
                  </Field>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 md:col-span-2">
                    <p className="text-sm font-semibold text-slate-950">Employment information workflows</p>
                    <p className="mt-1 text-xs leading-5 text-slate-600">Use these BUC actions for auditable title, grade, salary band, cost center, reporting manager, and functional manager changes. Sensitive changes route for approval.</p>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <select value={employmentAction} onChange={(event) => setEmploymentAction(event.target.value)} className={inputClass}>
                        <option value="job-title/assign">EMP-019 Assign Job Title</option>
                        <option value="job-title/change">EMP-020 Change Job Title</option>
                        <option value="job-grade/assign">EMP-021 Assign Job Grade</option>
                        <option value="job-grade/change">EMP-022 Change Job Grade</option>
                        <option value="salary-band/assign">EMP-023 Assign Salary Band</option>
                        <option value="salary-band/update">EMP-024 Update Salary Band</option>
                        <option value="cost-center/assign">EMP-025 Assign Cost Center</option>
                        <option value="cost-center/change">EMP-026 Change Cost Center</option>
                        <option value="reporting-manager/assign">EMP-027 Assign Reporting Manager</option>
                        <option value="reporting-manager/change">EMP-028 Change Reporting Manager</option>
                        <option value="functional-manager/assign">EMP-029 Assign Functional Manager</option>
                        <option value="functional-manager/change">EMP-030 Change Functional Manager</option>
                      </select>
                      {employmentAction.includes("manager") ? (
                        <select value={employmentNewValue} onChange={(event) => setEmploymentNewValue(event.target.value)} className={inputClass}>
                          <option value="">Select manager</option>
                          {activeManagers.filter((manager) => manager.id !== selectedEmployee.id).map((manager) => (
                            <option key={manager.id} value={manager.id}>{fullName(manager)} / {manager.department}</option>
                          ))}
                        </select>
                      ) : (
                        <input value={employmentNewValue} onChange={(event) => setEmploymentNewValue(event.target.value)} className={inputClass} placeholder="New value" />
                      )}
                      <input type="date" value={employmentEffectiveDate} onChange={(event) => setEmploymentEffectiveDate(event.target.value)} className={inputClass} />
                      <input value={employmentReason} onChange={(event) => setEmploymentReason(event.target.value)} className={inputClass} placeholder="Reason for change" />
                      {employmentAction.includes("functional-manager") && (
                        <input value={employmentAuthorityScope} onChange={(event) => setEmploymentAuthorityScope(event.target.value)} className={inputClass} placeholder="Authority scope" />
                      )}
                      <Button type="button" onClick={submitEmploymentInfoChange}>Submit BUC Action</Button>
                    </div>
                  </div>
                  <div className="md:col-span-2">
                    <SimpleTable rows={employmentInfo?.pending_changes ?? []} columns={["buc_code", "field_type", "new_value", "effective_date", "approval_status"]} />
                  </div>
                  <div className="md:col-span-2">
                    <SimpleTable rows={employmentInfo?.history ?? []} columns={["buc_code", "field_type", "previous_value", "new_value", "effective_from", "status"]} />
                  </div>
                </div>
              )}

              {employeeModalTab === "organization" && (
                <div className="space-y-4">
                  <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-900">
                    Note: Department, branch, and business unit transfers may affect reporting lines, approvals, payroll allocation, and access permissions.
                  </div>
                  <div className="grid gap-3 md:grid-cols-5">
                    <select value={assignmentAction} onChange={(event) => setAssignmentAction(event.target.value)} className={inputClass}>
                      <option value="department">EMP-031 Assign Department</option>
                      <option value="department-transfer">EMP-032 Transfer Department</option>
                      <option value="branch">EMP-033 Assign Branch</option>
                      <option value="branch-transfer">EMP-034 Transfer Branch</option>
                      <option value="business-unit">EMP-035 Assign Business Unit</option>
                      <option value="business-unit-transfer">EMP-036 Transfer Business Unit</option>
                    </select>
                    <input value={assignmentValue} onChange={(event) => setAssignmentValue(event.target.value)} className={inputClass} placeholder="New value" />
                    <input type="date" value={assignmentDate} onChange={(event) => setAssignmentDate(event.target.value)} className={inputClass} />
                    <input value={assignmentReason} onChange={(event) => setAssignmentReason(event.target.value)} className={inputClass} placeholder="Reason" />
                    <Button type="button" onClick={submitAssignmentAction}>Save</Button>
                  </div>
                  <div className="grid gap-4 md:grid-cols-3">
                    <Metric label="Department" value={String(assignmentBundle?.current?.department ?? selectedEmployee.department ?? "-")} />
                    <Metric label="Branch" value={String(assignmentBundle?.current?.branch ?? selectedEmployee.branch ?? "-")} />
                    <Metric label="Business Unit" value={String(assignmentBundle?.current?.business_unit ?? selectedEmployee.business_unit ?? "-")} />
                    <Metric label="Project Allocation" value={`${assignmentBundle?.analytics?.project_allocation ?? 0}%`} />
                    <Metric label="Missing Docs" value={(assignmentBundle?.analytics?.missing_documents ?? []).join(", ") || "None"} />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                      <p className="mb-3 text-sm font-semibold text-slate-950">EMP-037 Assign Project</p>
                      <div className="grid gap-2">
                        <input value={assignmentValue} onChange={(event) => setAssignmentValue(event.target.value)} className={inputClass} placeholder="Project ID" />
                        <input value={projectRole} onChange={(event) => setProjectRole(event.target.value)} className={inputClass} placeholder="Project role" />
                        <input type="number" value={projectAllocation} onChange={(event) => setProjectAllocation(event.target.value)} className={inputClass} placeholder="Allocation %" />
                        <Button type="button" onClick={assignProject}>Assign Project</Button>
                      </div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                      <p className="mb-3 text-sm font-semibold text-slate-950">EMP-039 Assign Team</p>
                      <div className="grid gap-2">
                        <input value={assignmentValue} onChange={(event) => setAssignmentValue(event.target.value)} className={inputClass} placeholder="Team name" />
                        <input value={assignmentReason} onChange={(event) => setAssignmentReason(event.target.value)} className={inputClass} placeholder="Reason" />
                        <Button type="button" onClick={assignTeam}>Assign Team</Button>
                      </div>
                    </div>
                  </div>
                  <SimpleTable rows={assignmentBundle?.projects ?? []} columns={["project_name", "project_role", "allocation_percentage", "start_date", "status"]} />
                  <SimpleTable rows={assignmentBundle?.teams ?? []} columns={["team_name", "department", "primary_team", "effective_from", "status"]} />
                  <SimpleTable rows={assignmentBundle?.history ?? []} columns={["buc_code", "assignment_type", "previous_value", "new_value", "effective_from", "status"]} />
                </div>
              )}

              {employeeModalTab === "documents" && (
                <div className="space-y-4">
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                    Note: Some employee documents require HR verification before the employee is considered compliant. Expired documents may affect activation, payroll readiness, access eligibility, or compliance status.
                  </div>
                  <div className="grid gap-3 md:grid-cols-5">
                    <select value={documentType} onChange={(event) => setDocumentType(event.target.value)} className={inputClass}>
                      {["National ID", "Passport", "Academic Certificate", "Professional Certification", "Employment Contract", "NDA", "CV", "Medical Document", "Tax Document", "Work Permit"].map((type) => <option key={type}>{type}</option>)}
                    </select>
                    <input type="date" value={documentExpiry} onChange={(event) => setDocumentExpiry(event.target.value)} className={inputClass} />
                    <input type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.webp" onChange={(event) => setDocumentFile(event.target.files?.[0] ?? null)} className="text-sm text-slate-700 md:col-span-2" />
                    <Button type="button" disabled={!documentFile} onClick={uploadEmployeeDocument}>Upload</Button>
                  </div>
                  <div className="grid gap-3 md:grid-cols-6">
                    <Metric label="Compliance" value={`${documentCompliance?.score ?? 0}%`} />
                    <Metric label="Missing" value={documentCompliance?.missing_count ?? 0} />
                    <Metric label="Pending" value={documentCompliance?.pending_verification ?? 0} />
                    <Metric label="Rejected" value={documentCompliance?.rejected ?? 0} />
                    <Metric label="Expiring" value={documentCompliance?.expiring_soon ?? 0} />
                    <Metric label="Expired" value={documentCompliance?.expired ?? 0} />
                  </div>
                  {Boolean(documentCompliance?.missing?.length) && (
                    <div className="rounded-lg border border-red-100 bg-red-50 p-3 text-xs font-semibold text-red-800">
                      Missing mandatory documents: {documentCompliance?.missing?.join(", ")}
                    </div>
                  )}
                  <div className="grid gap-3 md:grid-cols-4">
                    <Metric label="Active" value={(assignmentBundle?.documents ?? []).filter((doc) => doc.status === "active").length} />
                    <Metric label="Pending Verification" value={(assignmentBundle?.documents ?? []).filter((doc) => doc.verification_status === "Pending Verification").length} />
                    <Metric label="Rejected" value={(assignmentBundle?.documents ?? []).filter((doc) => doc.verification_status === "Rejected").length} />
                    <Metric label="Archived" value={(assignmentBundle?.documents ?? []).filter((doc) => doc.status === "archived" || doc.is_archived).length} />
                  </div>
                  <SimpleTable rows={assignmentBundle?.documents ?? []} columns={["display_name", "file_name", "version_number", "runtime_status", "expiry_date", "status"]} actions={(row) => (
                    <div className="flex flex-wrap gap-2">
                      <button type="button" className="text-xs font-semibold text-blue-700" onClick={() => row.id && downloadEmployeeDocument(String(row.id))}>View</button>
                      <button type="button" className="text-xs font-semibold text-slate-700" onClick={() => row.id && showDocumentVersions(String(row.id))}>Versions</button>
                      <button type="button" className="text-xs font-semibold text-emerald-700" onClick={() => row.id && documentAction(String(row.id), "verify")}>Verify</button>
                      <button type="button" className="text-xs font-semibold text-red-700" onClick={() => row.id && documentAction(String(row.id), "reject")}>Reject</button>
                      <button type="button" className="text-xs font-semibold text-slate-700" onClick={() => row.id && documentAction(String(row.id), "archive")}>Archive</button>
                    </div>
                  )} />
                  {documentVersions.length > 0 && (
                    <div className="rounded-lg border border-slate-200 bg-white p-3">
                      <div className="mb-2 flex items-center justify-between">
                        <p className="text-sm font-semibold text-slate-950">Version History</p>
                        <button type="button" className="text-xs font-semibold text-slate-600" onClick={() => setDocumentVersions([])}>Close</button>
                      </div>
                      <SimpleTable rows={documentVersions} columns={["version_number", "file_name", "replacement_reason", "uploaded_by_name", "status", "created_at"]} />
                    </div>
                  )}
                </div>
              )}

              {employeeModalTab === "employment" && (
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="Employment Type">
                    <select value={employeeDraft.employment_type ?? "Permanent"} onChange={(event) => updateEmployeeDraft("employment_type", event.target.value)} className={inputClass}>
                      <option>Permanent</option>
                      <option>Contract</option>
                      <option>Casual</option>
                      <option>Internship</option>
                      <option>Consultant</option>
                    </select>
                  </Field>
                  <Field label="Employment Status">
                    <select value={employeeDraft.employment_status ?? "pending_activation"} onChange={(event) => updateEmployeeDraft("employment_status", event.target.value)} className={inputClass}>
                      <option value="draft">Draft</option>
                      <option value="pending_activation">Pending Activation</option>
                      <option value="active">Active</option>
                      <option value="probation">Probation</option>
                      <option value="on_leave">On Leave</option>
                      <option value="inactive">Inactive</option>
                      <option value="suspended">Suspended</option>
                      <option value="terminated">Terminated</option>
                    </select>
                  </Field>
                  <Field label="Start Date">
                    <input type="date" value={(employeeDraft.employment_start_date ?? employeeDraft.hire_date ?? "").slice(0, 10)} onChange={(event) => updateEmployeeDraft("employment_start_date", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="End Date">
                    <input type="date" value={(employeeDraft.employment_end_date ?? "").slice(0, 10)} onChange={(event) => updateEmployeeDraft("employment_end_date", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Pay Frequency">
                    <select value={employeeDraft.pay_frequency ?? "monthly"} onChange={(event) => updateEmployeeDraft("pay_frequency", event.target.value)} className={inputClass}>
                      <option value="monthly">Monthly</option>
                      <option value="biweekly">Biweekly</option>
                      <option value="weekly">Weekly</option>
                    </select>
                  </Field>
                  <Field label="Base Salary">
                    <input type="number" value={employeeDraft.base_salary ?? 0} onChange={(event) => updateEmployeeDraft("base_salary", Number(event.target.value))} className={inputClass} />
                  </Field>
                  <label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                    <input type="checkbox" checked={Boolean(employeeDraft.contract_signed)} onChange={(event) => updateEmployeeDraft("contract_signed", event.target.checked)} />
                    Contract signed
                  </label>
                  <label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                    <input type="checkbox" checked={Boolean(employeeDraft.budget_approved)} onChange={(event) => updateEmployeeDraft("budget_approved", event.target.checked)} />
                    Budget approved
                  </label>
                </div>
              )}

              {employeeModalTab === "probation" && (
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                    <input type="checkbox" checked={Boolean(employeeDraft.probation_required)} onChange={(event) => updateEmployeeDraft("probation_required", event.target.checked)} />
                    Probation required
                  </label>
                  <Metric label="Current status" value={format(selectedEmployee.probation_status)} />
                  <Field label="Probation Start">
                    <input type="date" value={(employeeDraft.probation_start_date ?? "").slice(0, 10)} onChange={(event) => updateEmployeeDraft("probation_start_date", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Probation End">
                    <input type="date" value={(employeeDraft.probation_end_date ?? "").slice(0, 10)} onChange={(event) => updateEmployeeDraft("probation_end_date", event.target.value)} className={inputClass} />
                  </Field>
                  <Field label="Duration Months">
                    <input type="number" min="1" value={employeeDraft.probation_duration_months ?? 6} onChange={(event) => updateEmployeeDraft("probation_duration_months", Number(event.target.value))} className={inputClass} />
                  </Field>
                  <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-900">
                    Probation decisions are audited. Use the action tab for extend, confirm, fail, or close.
                  </div>
                </div>
              )}

              {employeeModalTab === "confirmation" && (
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <Metric label="Confirmation status" value={format(selectedEmployee.confirmation_status)} />
                    <Metric label="Confirmation date" value={selectedEmployee.confirmation_date ? new Date(selectedEmployee.confirmation_date).toLocaleDateString() : "-"} />
                    <Metric label="Confirmed by" value={format(selectedEmployee.confirmed_by)} />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Field label="Decision">
                      <select value={confirmationDecision} onChange={(event) => setConfirmationDecision(event.target.value as "confirm" | "defer" | "reject")} className={inputClass}>
                        <option value="confirm">Confirm</option>
                        <option value="defer">Defer Confirmation</option>
                        <option value="reject">Reject Confirmation</option>
                      </select>
                    </Field>
                    <Field label={confirmationDecision === "defer" ? "Next Review Date" : "Confirmation Date"}>
                      <input
                        type="date"
                        value={confirmationDecision === "defer" ? nextReviewDate : confirmationDate}
                        onChange={(event) => confirmationDecision === "defer" ? setNextReviewDate(event.target.value) : setConfirmationDate(event.target.value)}
                        className={inputClass}
                      />
                    </Field>
                    <Field label={confirmationDecision === "confirm" ? "Confirmation Notes" : "Reason"}>
                      <textarea
                        value={confirmationNotes}
                        onChange={(event) => setConfirmationNotes(event.target.value)}
                        className="min-h-28 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                        placeholder={confirmationDecision === "confirm" ? "Probation review outcome and confirmation notes" : "Required reason"}
                      />
                    </Field>
                    <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-900">
                      Note: Employee confirmation closes the probation workflow and may affect benefits, leave, and promotion eligibility depending on HR policy.
                    </div>
                  </div>
                  <Button type="button" onClick={submitConfirmationDecision}>
                    Save Confirmation Decision
                  </Button>
                </div>
              )}

              {employeeModalTab === "actions" && (
                <div className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-3">
                    <Metric label="Payroll" value={selectedEmployee.employment_status === "active" ? "Eligible" : "Pending activation"} />
                    <Metric label="IAM" value={selectedEmployee.employment_status === "active" ? "Access ready" : "Provisioning pending"} />
                    <Metric label="Confirmation" value={format(selectedEmployee.confirmation_status)} />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button type="button" disabled={isActivating || selectedEmployee.employment_status === "active"} onClick={activateSelectedEmployee}>
                      <ShieldCheck size={16} />
                      {selectedEmployee.employment_status === "active" ? "Active" : "Activate Employee"}
                    </Button>
                    {["Contract", "Casual", "Internship", "Consultant"].includes(selectedEmployee.employment_type ?? "") && (
                      <Button type="button" variant="secondary" onClick={extendSelectedEmployment}>Extend Contract/Engagement</Button>
                    )}
                    {selectedEmployee.probation_status && selectedEmployee.probation_status !== "Not Applicable" && (
                      <>
                        <Button type="button" variant="secondary" onClick={() => reviewSelectedProbation("extend")}>Extend Probation</Button>
                        <Button type="button" variant="secondary" onClick={() => reviewSelectedProbation("confirm")}>Confirm Employee</Button>
                        <Button type="button" variant="secondary" onClick={() => reviewSelectedProbation("fail")}>Fail Probation</Button>
                        <Button type="button" variant="secondary" onClick={() => reviewSelectedProbation("close")}>Close Probation</Button>
                      </>
                    )}
                    <Button type="button" variant="secondary" onClick={() => setEmployeeModalTab("confirmation")}>
                      EMP-007 Confirmation
                    </Button>
                    <Button type="button" variant="secondary" onClick={deleteSelectedEmployee}>
                      <Trash2 size={16} />
                      Delete Record
                    </Button>
                  </div>
                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                      <p className="text-sm font-semibold text-slate-950">Movement Actions</p>
                      <p className="mt-1 text-xs leading-5 text-slate-600">Promotion, demotion, transfer, role change, acting appointment, secondment, temporary assignment, and return from assignment.</p>
                      <div className="mt-3 grid gap-2">
                        <select value={movementAction} onChange={(event) => setMovementAction(event.target.value)} className={inputClass}>
                          <option value="promote">EMP-055 Promote</option>
                          <option value="demote">EMP-056 Demote</option>
                          <option value="transfer">EMP-057 Transfer</option>
                          <option value="change-role">EMP-058 Change Role</option>
                          <option value="acting-appointment">EMP-059 Acting Appointment</option>
                          <option value="secondment">EMP-060 Secondment</option>
                          <option value="internal-transfer">EMP-061 Internal Transfer</option>
                          <option value="temporary-assignment">EMP-062 Temporary Assignment</option>
                          <option value="return-from-assignment">EMP-063 Return From Assignment</option>
                        </select>
                        <input type="date" value={movementEffectiveDate} onChange={(event) => setMovementEffectiveDate(event.target.value)} className={inputClass} />
                        <input value={movementNewValue} onChange={(event) => setMovementNewValue(event.target.value)} className={inputClass} placeholder="New role, department, host unit, end/return date, or related value" />
                        <textarea value={movementReason} onChange={(event) => setMovementReason(event.target.value)} className="min-h-20 rounded-lg border border-slate-200 p-3 text-sm" placeholder="Reason and approval context" />
                        <Button type="button" onClick={submitMovementAction}>Record Movement</Button>
                      </div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                      <p className="text-sm font-semibold text-slate-950">Status Actions</p>
                      <p className="mt-1 text-xs leading-5 text-slate-600">Suspension, reinstatement, leave of absence, inactivity, termination, retirement, and restricted death-in-service records.</p>
                      <div className="mt-3 grid gap-2">
                        <select value={statusAction} onChange={(event) => setStatusAction(event.target.value)} className={inputClass}>
                          <option value="suspend">EMP-067 Suspend</option>
                          <option value="reinstate">EMP-068 Reinstate</option>
                          <option value="leave-of-absence">EMP-069 Leave of Absence</option>
                          <option value="return-from-leave-of-absence">EMP-070 Return From Leave</option>
                          <option value="mark-inactive">EMP-071 Mark Inactive</option>
                          <option value="terminate">EMP-072 Terminate</option>
                          <option value="retire">EMP-073 Retire</option>
                          <option value="death-in-service">EMP-074 Death in Service</option>
                        </select>
                        <input type="date" value={movementEffectiveDate} onChange={(event) => setMovementEffectiveDate(event.target.value)} className={inputClass} />
                        <input value={movementNewValue} onChange={(event) => setMovementNewValue(event.target.value)} className={inputClass} placeholder="Type, expected return date, document reference, or status detail" />
                        <textarea value={movementReason} onChange={(event) => setMovementReason(event.target.value)} className="min-h-20 rounded-lg border border-slate-200 p-3 text-sm" placeholder="Reason and approval context" />
                        <Button type="button" onClick={submitStatusAction}>Record Status Action</Button>
                      </div>
                    </div>
                  </div>
                  <div className="grid gap-4 lg:grid-cols-2">
                    <div>
                      <p className="mb-2 text-sm font-semibold text-slate-950">Movement History</p>
                      <SimpleTable rows={movementHistory} columns={["movement_code", "movement_type", "effective_date", "approval_status", "workflow_status"]} />
                    </div>
                    <div>
                      <p className="mb-2 text-sm font-semibold text-slate-950">Status History</p>
                      <SimpleTable rows={statusHistory} columns={["status_code", "old_status", "new_status", "effective_date", "approval_status"]} />
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="sticky bottom-0 flex flex-col gap-3 border-t border-slate-200 bg-white/95 p-5 backdrop-blur sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-600">Changes update the HRM source-of-truth record and downstream assignments can branch from this profile.</p>
              <div className="flex gap-2">
                <Button type="button" variant="secondary" onClick={() => setSelectedId(null)}>Close</Button>
                <Button type="button" disabled={isSavingProfile} onClick={saveSelectedEmployee}>{isSavingProfile ? "Saving..." : "Save Changes"}</Button>
              </div>
            </div>
          </section>
        </div>
      )}

      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
          <form onSubmit={createEmployee} className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-2xl">
            <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-200 bg-white/95 p-5 backdrop-blur">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                  <ShieldCheck size={14} />
                  EMP-001 Create Employee Record
                </div>
                <h2 className="mt-3 text-2xl font-bold text-slate-950">Create employee master record</h2>
                <p className="mt-1 max-w-3xl text-sm text-slate-600">
                  Use this after recruitment is complete, the contract is signed, budget is approved, and the role exists in the organization structure.
                </p>
              </div>
              <button type="button" onClick={() => setIsCreateOpen(false)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900">
                <X size={20} />
              </button>
            </div>

            <div className="grid gap-5 p-5 lg:grid-cols-[300px_1fr]">
              <aside className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Creation controls</p>
                {preconditions.map((item) => (
                  <div key={item.label} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 size={16} className={item.met ? "mt-0.5 text-emerald-600" : "mt-0.5 text-slate-300"} />
                    <span className={item.met ? "text-slate-800" : "text-slate-500"}>{item.label}</span>
                  </div>
                ))}
                <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-900">
                  On save, the system generates an employee number, creates payroll profile, IAM request, onboarding tasks, finance mapping, asset request, notifications, and audit logs.
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-600">
                  After creation, check Payroll under Compensation/Salary Structures, IAM under Access Profiles, onboarding under HRM Onboarding, Finance under Cost Centers, Assets under Asset Assignments, Notifications under the main queue, and Audit under HRM audit logs.
                </div>
              </aside>

              <div className="space-y-6">
                {createError && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{createError}</div>}

                <section>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Personal Information</h3>
                  <div className="mt-3 grid gap-4 md:grid-cols-2">
                    <Field label="Candidate ID" required>
                      <input required value={employeeForm.candidate_id} onChange={(event) => updateEmployeeForm("candidate_id", event.target.value)} className={inputClass} placeholder="Paste hired recruitment/candidate ID" />
                    </Field>
                    <Field label="Email" required>
                      <input type="email" required value={employeeForm.email} onChange={(event) => updateEmployeeForm("email", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="First Name" required>
                      <input required value={employeeForm.first_name} onChange={(event) => updateEmployeeForm("first_name", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="Last Name" required>
                      <input required value={employeeForm.last_name} onChange={(event) => updateEmployeeForm("last_name", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="National ID" required>
                      <input required value={employeeForm.national_id} onChange={(event) => updateEmployeeForm("national_id", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="Tax PIN" required>
                      <input required value={employeeForm.tax_pin} onChange={(event) => updateEmployeeForm("tax_pin", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="Phone">
                      <input value={employeeForm.phone} onChange={(event) => updateEmployeeForm("phone", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="Gender">
                      <select value={employeeForm.gender} onChange={(event) => updateEmployeeForm("gender", event.target.value)} className={inputClass}>
                        <option value="">Select gender</option>
                        <option>Female</option>
                        <option>Male</option>
                        <option>Non-binary</option>
                        <option>Prefer not to say</option>
                      </select>
                    </Field>
                    <Field label="Date of Birth">
                      <input type="date" value={employeeForm.date_of_birth} onChange={(event) => updateEmployeeForm("date_of_birth", event.target.value)} className={inputClass} />
                    </Field>
                  </div>
                </section>

                <section>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Employment And Organization Assignment</h3>
                  <div className="mt-3 grid gap-4 md:grid-cols-2">
                    <Field label="Department" required>
                      <select required value={employeeForm.department} onChange={(event) => updateEmployeeForm("department", event.target.value)} className={inputClass}>
                        <option value="">Select active department</option>
                        {activeDepartments.map((department) => <option key={department.id} value={department.name}>{department.name}</option>)}
                      </select>
                    </Field>
                    <Field label="Position / Job Title" required>
                      <select required value={employeeForm.job_title} onChange={(event) => updateEmployeeForm("job_title", event.target.value)} className={inputClass}>
                        <option value="">Select active position</option>
                        {availablePositions.map((position) => (
                          <option key={position.id} value={position.position_title}>
                            {position.position_title} ({position.current_headcount ?? 0}/{position.headcount_budget ?? 0})
                            {Number(position.current_headcount ?? 0) >= Number(position.headcount_budget ?? 0) ? " - full" : ""}
                          </option>
                        ))}
                      </select>
                      {selectedPosition && !headcountAvailable && (
                        <p className="mt-1 text-xs text-amber-700">
                          This position is at its current headcount budget. With budget approval checked, EMP-001 will reserve one additional approved headcount on save.
                        </p>
                      )}
                    </Field>
                    <Field label="Business Unit">
                      <input value={employeeForm.business_unit} onChange={(event) => updateEmployeeForm("business_unit", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="Branch">
                      <input value={employeeForm.branch} onChange={(event) => updateEmployeeForm("branch", event.target.value)} className={inputClass} />
                    </Field>
                    <Field label="Line Manager">
                      <select value={employeeForm.supervisor_id} onChange={(event) => updateEmployeeForm("supervisor_id", event.target.value)} className={inputClass}>
                        <option value="">Top-level or assign manager</option>
                        {activeManagers.map((manager) => <option key={manager.id} value={manager.id}>{fullName(manager)} / {manager.department}</option>)}
                      </select>
                    </Field>
                    <Field label="Employee Type">
                      <select value={employeeForm.employment_type} onChange={(event) => updateEmployeeForm("employment_type", event.target.value)} className={inputClass}>
                        <option>Permanent</option>
                        <option>Contract</option>
                        <option>Casual</option>
                        <option>Internship</option>
                        <option>Consultant</option>
                      </select>
                    </Field>
                    <Field label="Employment Start Date" required>
                      <input type="date" required value={employeeForm.hire_date} onChange={(event) => updateEmployeeForm("hire_date", event.target.value)} className={inputClass} />
                    </Field>
                    {employeeForm.employment_type !== "Permanent" && (
                      <>
                        <Field label={`${employeeForm.employment_type} End Date`} required>
                          <input type="date" required value={employeeForm.employment_end_date} onChange={(event) => updateEmployeeForm("employment_end_date", event.target.value)} className={inputClass} />
                        </Field>
                        {employeeForm.employment_type === "Internship" && (
                          <>
                            <Field label="Institution" required>
                              <input required value={employeeForm.institution} onChange={(event) => updateEmployeeForm("institution", event.target.value)} className={inputClass} />
                            </Field>
                            <Field label="Internship Supervisor" required>
                              <input required value={employeeForm.internship_supervisor} onChange={(event) => updateEmployeeForm("internship_supervisor", event.target.value)} className={inputClass} />
                            </Field>
                          </>
                        )}
                        {employeeForm.employment_type === "Consultant" && (
                          <>
                            <Field label="Agreement Reference" required>
                              <input required value={employeeForm.consultancy_agreement_ref} onChange={(event) => updateEmployeeForm("consultancy_agreement_ref", event.target.value)} className={inputClass} />
                            </Field>
                            <Field label="Consultancy Project" required>
                              <input required value={employeeForm.consultancy_project} onChange={(event) => updateEmployeeForm("consultancy_project", event.target.value)} className={inputClass} />
                            </Field>
                          </>
                        )}
                      </>
                    )}
                    {probationApplies && (
                      <>
                        <Field label="Probation Required">
                          <label className="flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700">
                            <input type="checkbox" checked={employeeForm.probation_required} onChange={(event) => updateEmployeeForm("probation_required", event.target.checked)} />
                            Assign probation
                          </label>
                        </Field>
                        {employeeForm.probation_required && (
                          <>
                            <Field label="Probation Start Date" required>
                              <input type="date" required value={employeeForm.probation_start_date || employeeForm.hire_date} onChange={(event) => updateEmployeeForm("probation_start_date", event.target.value)} className={inputClass} />
                            </Field>
                            <Field label="Probation Duration (months)" required>
                              <input type="number" min="1" required value={employeeForm.probation_duration_months} onChange={(event) => {
                                const months = event.target.value;
                                updateEmployeeForm("probation_duration_months", months);
                                const start = employeeForm.probation_start_date || employeeForm.hire_date;
                                if (start && Number(months) > 0) {
                                  const next = new Date(start);
                                  next.setMonth(next.getMonth() + Number(months));
                                  updateEmployeeForm("probation_end_date", next.toISOString().slice(0, 10));
                                }
                              }} className={inputClass} />
                            </Field>
                            <Field label="Probation End Date" required>
                              <input type="date" required value={employeeForm.probation_end_date} onChange={(event) => updateEmployeeForm("probation_end_date", event.target.value)} className={inputClass} />
                            </Field>
                            <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-900 md:col-span-2">
                              Note: Probation reminders are sent before the probation end date, and HR must complete review before confirmation.
                            </div>
                          </>
                        )}
                      </>
                    )}
                    <Field label="Pay Frequency">
                      <select value={employeeForm.pay_frequency} onChange={(event) => updateEmployeeForm("pay_frequency", event.target.value)} className={inputClass}>
                        <option value="monthly">Monthly</option>
                        <option value="biweekly">Biweekly</option>
                        <option value="weekly">Weekly</option>
                      </select>
                    </Field>
                    <Field label="Base Salary">
                      <input type="number" min="0" value={employeeForm.base_salary} onChange={(event) => updateEmployeeForm("base_salary", event.target.value)} className={inputClass} />
                    </Field>
                  </div>
                </section>

                <section className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Preconditions And Approvals</h3>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    <label className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm font-medium text-slate-800">
                      <input type="checkbox" checked={employeeForm.contract_signed} onChange={(event) => updateEmployeeForm("contract_signed", event.target.checked)} className="h-5 w-5" />
                      Employment contract signed
                    </label>
                    <label className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm font-medium text-slate-800">
                      <input type="checkbox" checked={employeeForm.budget_approved} onChange={(event) => updateEmployeeForm("budget_approved", event.target.checked)} className="h-5 w-5" />
                      Recruitment budget approved
                    </label>
                  </div>
                </section>
              </div>
            </div>

            <div className="sticky bottom-0 flex flex-col gap-3 border-t border-slate-200 bg-white/95 p-5 backdrop-blur md:flex-row md:items-center md:justify-between">
              <p className="text-sm text-slate-600">The saved employee will start as <span className="font-semibold text-slate-950">Pending Activation</span>.</p>
              <div className="flex gap-2">
                <Button type="button" variant="secondary" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={isSavingEmployee}>{isSavingEmployee ? "Creating..." : "Create Employee"}</Button>
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">
        {label}
        {required ? <span className="text-red-600"> *</span> : null}
      </span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs font-medium uppercase text-slate-500">{label}</p>
      <p className="mt-1 font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function ModuleLink({ href, label, detail }: { href: string; label: string; detail: string }) {
  return (
    <a href={href} className="group rounded-lg border border-slate-200 bg-slate-50 p-3 transition hover:border-blue-200 hover:bg-blue-50">
      <span className="flex items-center justify-between gap-2 text-sm font-semibold text-slate-950">
        {label}
        <ArrowRight size={15} className="text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-blue-700" />
      </span>
      <span className="mt-1 block text-xs leading-5 text-slate-600">{detail}</span>
    </a>
  );
}

function SimpleTable({ rows, columns, onRemove, actions }: { rows: ProfileRecord[]; columns: string[]; onRemove?: (id: string) => void; actions?: (row: ProfileRecord) => React.ReactNode }) {
  if (!rows.length) {
    return <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">No records found.</div>;
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((column) => (
              <th key={column} className="px-3 py-2 text-left font-semibold capitalize text-slate-600">{column.replaceAll("_", " ")}</th>
            ))}
            {(onRemove || actions) && <th className="px-3 py-2 text-left font-semibold text-slate-600">Action</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, index) => (
            <tr key={String(row.id ?? index)}>
              {columns.map((column) => (
                <td key={column} className="px-3 py-2 text-slate-700">{String(row[column] ?? "-")}</td>
              ))}
              {(onRemove || actions) && (
                <td className="px-3 py-2">
                  {actions ? actions(row) : (
                    <button type="button" onClick={() => row.id && onRemove?.(String(row.id))} className="text-sm font-semibold text-red-600 hover:text-red-700">
                      Archive
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ label, tone }: { label: string; tone: "green" | "blue" | "amber" | "red" | "slate" }) {
  const tones = {
    green: "border-emerald-200 bg-emerald-50 text-emerald-700",
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    red: "border-red-200 bg-red-50 text-red-700",
    slate: "border-slate-200 bg-white text-slate-600",
  };
  return <span className={`inline-flex rounded-full border px-2 py-1 text-xs capitalize ${tones[tone]}`}>{label}</span>;
}
