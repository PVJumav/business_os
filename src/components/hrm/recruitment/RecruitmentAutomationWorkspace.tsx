"use client";

import { useEffect, useMemo, useState } from "react";
import { Briefcase, CheckCircle2, RefreshCw, Send, UserPlus, Users } from "lucide-react";
import { api } from "@/services/api";
import HRMEnterpriseModule from "@/components/hrm/HRMEnterpriseModule";

type CellValue = string | number | boolean | null | undefined | Record<string, unknown> | unknown[];
type Row = Record<string, CellValue>;

const inputClass = "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

function today(offset = 0) {
  const value = new Date();
  value.setDate(value.getDate() + offset);
  return value.toISOString().slice(0, 10);
}

function asText(value: CellValue) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function StatusBadge({ value }: { value: CellValue }) {
  const text = asText(value);
  const tone = text.includes("ready") || text.includes("approved") || text.includes("converted") ? "border-emerald-200 bg-emerald-50 text-emerald-700" : text.includes("pending") ? "border-amber-200 bg-amber-50 text-amber-700" : "border-slate-200 bg-slate-50 text-slate-600";
  return <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${tone}`}>{text.replaceAll("_", " ")}</span>;
}

export default function RecruitmentAutomationWorkspace() {
  const [analytics, setAnalytics] = useState<Row | null>(null);
  const [successfulApplicants, setSuccessfulApplicants] = useState<Row[]>([]);
  const [requisitions, setRequisitions] = useState<Row[]>([]);
  const [openings, setOpenings] = useState<Row[]>([]);
  const [applications, setApplications] = useState<Row[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [requisition, setRequisition] = useState({
    job_title: "",
    department: "",
    vacancies: 1,
    employment_type: "Permanent",
    salary_band: "",
    reason_for_hire: "",
    required_start_date: today(30),
  });
  const [candidate, setCandidate] = useState({
    opening_id: "",
    candidate_name: "",
    candidate_email: "",
    candidate_phone: "",
    expected_salary: "",
    availability_date: today(30),
  });

  const approvedRequisitions = useMemo(() => requisitions.filter((item) => item.approval_status === "approved"), [requisitions]);
  const publishedOpenings = useMemo(() => openings.filter((item) => item.status === "published"), [openings]);

  async function load() {
    setError(null);
    try {
      const [analyticsData, applicantsData, requisitionRows, openingRows, applicationRows] = await Promise.all([
        api.get<Row>("/api/hrm/recruitment/analytics"),
        api.get<Row[]>("/api/hrm/recruitment/successful-applicants"),
        api.get<Row[]>("/api/hrm/recruitment/requisitions"),
        api.get<Row[]>("/api/hrm/recruitment/openings"),
        api.get<Row[]>("/api/hrm/recruitment/applications"),
      ]);
      setAnalytics(analyticsData);
      setSuccessfulApplicants(applicantsData);
      setRequisitions(requisitionRows);
      setOpenings(openingRows);
      setApplications(applicationRows);
      if (!candidate.opening_id && openingRows[0]?.id) {
        setCandidate((current) => ({ ...current, opening_id: String(openingRows[0].id) }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load recruitment automation");
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createRequisition() {
    setError(null);
    try {
      const row = await api.post<Row>("/api/hrm/recruitment/requisitions", {
        ...requisition,
        vacancies: Number(requisition.vacancies || 1),
        required_skills: [],
        required_certifications: [],
      });
      await api.post(`/api/hrm/recruitment/requisitions/${String(row.id)}/approve`, { comments: "Approved from ATS automation workspace" });
      setMessage("Job requisition created and approved.");
      setRequisition({ job_title: "", department: "", vacancies: 1, employment_type: "Permanent", salary_band: "", reason_for_hire: "", required_start_date: today(30) });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create requisition");
    }
  }

  async function createOpening() {
    setError(null);
    const requisitionId = approvedRequisitions[0]?.id;
    if (!requisitionId) {
      setError("Create and approve a requisition first.");
      return;
    }
    try {
      const row = await api.post<Row>("/api/hrm/recruitment/openings", {
        requisition_id: requisitionId,
        description: "Created from ATS automation workspace.",
        closing_date: today(21),
        publishing_channels: ["Internal portal"],
      });
      await api.post(`/api/hrm/recruitment/openings/${String(row.id)}/publish`, { comments: "Published from ATS automation workspace" });
      setMessage("Job opening created and published.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not publish opening");
    }
  }

  async function createApplication() {
    setError(null);
    if (!candidate.opening_id) {
      setError("Select a published opening first.");
      return;
    }
    try {
      await api.post<Row>("/api/hrm/recruitment/applications", {
        ...candidate,
        expected_salary: candidate.expected_salary ? Number(candidate.expected_salary) : undefined,
      });
      setMessage("Candidate application received.");
      setCandidate({ opening_id: candidate.opening_id, candidate_name: "", candidate_email: "", candidate_phone: "", expected_salary: "", availability_date: today(30) });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create application");
    }
  }

  async function progressToSuccessfulApplicant(application: Row) {
    setError(null);
    try {
      await api.post(`/api/hrm/recruitment/applications/${String(application.id)}/screen`, { screening_score: 80, assessment_score: 75 });
      await api.post(`/api/hrm/recruitment/applications/${String(application.id)}/shortlist`, { comments: "Shortlisted from ATS automation workspace" });
      const offer = await api.post<Row>("/api/hrm/recruitment/offers", {
        recruitment_id: application.id,
        start_date: application.target_start_date ?? today(30),
        salary_band: application.salary_band,
        base_salary: application.expected_salary,
        probation_months: 6,
        offer_expiry_date: today(14),
      });
      await api.post(`/api/hrm/recruitment/offers/${String(offer.id)}/approve`, { comments: "Approved from ATS automation workspace" });
      await api.post(`/api/hrm/recruitment/offers/${String(offer.id)}/send`, { comments: "Sent from ATS automation workspace" });
      await api.put(`/api/hrm/recruitment/${String(application.id)}`, {
        headcount_approved: true,
        budget_approved: true,
        contract_signed: true,
        employment_contract_reference: `CONTRACT-${String(application.id).slice(0, 8)}`,
        background_check_status: "passed",
        approval_status: "approved",
        employment_type: application.employment_type ?? "Permanent",
        target_start_date: application.target_start_date ?? today(30),
      });
      await api.post(`/api/hrm/recruitment/offers/${String(offer.id)}/accept`, {});
      setMessage("Candidate moved to Successful Applicants.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not progress candidate");
    }
  }

  async function convertApplicant(applicant: Row) {
    setError(null);
    try {
      const result = await api.post<Row>(`/api/hrm/recruitment/successful-applicants/${String(applicant.id)}/convert-to-employee`, {
        confirm_missing_data: true,
        employee_overrides: {},
      });
      const employee = result.employee as Row | undefined;
      setMessage(`Converted to employee ${asText(employee?.employee_code)}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not convert applicant");
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">HRMS v5.5 / REC-001 to REC-030</p>
            <h1 className="mt-2 text-2xl font-bold text-slate-950">Recruitment / ATS Automation</h1>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
              Automate hiring from requisition to successful applicant conversion, then create employee records and downstream onboarding workflows.
            </p>
          </div>
          <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </section>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {message && <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div>}

      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Applications" value={asText(analytics?.applications_received ?? 0)} />
        <Metric label="Offers Accepted" value={asText(analytics?.offers_accepted ?? 0)} />
        <Metric label="Successful Applicants" value={asText(analytics?.successful_applicants ?? 0)} />
        <Metric label="Converted Employees" value={asText(analytics?.candidates_converted_to_employees ?? 0)} />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Briefcase size={18} className="text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-950">Create requisition</h2>
          </div>
          <div className="space-y-3">
            <input value={requisition.job_title} onChange={(event) => setRequisition((current) => ({ ...current, job_title: event.target.value }))} className={inputClass} placeholder="Job title" />
            <input value={requisition.department} onChange={(event) => setRequisition((current) => ({ ...current, department: event.target.value }))} className={inputClass} placeholder="Department" />
            <select value={requisition.employment_type} onChange={(event) => setRequisition((current) => ({ ...current, employment_type: event.target.value }))} className={inputClass}>
              {["Permanent", "Contract", "Casual", "Internship", "Consultant"].map((type) => <option key={type}>{type}</option>)}
            </select>
            <input value={requisition.salary_band} onChange={(event) => setRequisition((current) => ({ ...current, salary_band: event.target.value }))} className={inputClass} placeholder="Salary band" />
            <button type="button" onClick={createRequisition} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700">
              <CheckCircle2 size={16} /> Create and Approve
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Send size={18} className="text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-950">Publish opening</h2>
          </div>
          <p className="mb-4 text-sm text-slate-600">Uses the latest approved requisition and publishes it to the internal portal.</p>
          <Metric label="Approved Requisitions" value={approvedRequisitions.length} />
          <button type="button" onClick={createOpening} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-950 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800">
            <Send size={16} /> Create Opening
          </button>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Users size={18} className="text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-950">Receive application</h2>
          </div>
          <div className="space-y-3">
            <select value={candidate.opening_id} onChange={(event) => setCandidate((current) => ({ ...current, opening_id: event.target.value }))} className={inputClass}>
              <option value="">Select opening</option>
              {publishedOpenings.map((opening) => <option key={String(opening.id)} value={String(opening.id)}>{asText(opening.job_title)} / {asText(opening.department)}</option>)}
            </select>
            <input value={candidate.candidate_name} onChange={(event) => setCandidate((current) => ({ ...current, candidate_name: event.target.value }))} className={inputClass} placeholder="Candidate name" />
            <input value={candidate.candidate_email} onChange={(event) => setCandidate((current) => ({ ...current, candidate_email: event.target.value }))} className={inputClass} placeholder="Candidate email" />
            <input value={candidate.candidate_phone} onChange={(event) => setCandidate((current) => ({ ...current, candidate_phone: event.target.value }))} className={inputClass} placeholder="Phone" />
            <button type="button" onClick={createApplication} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700">
              <UserPlus size={16} /> Add Application
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Successful Applicants</h2>
            <p className="text-sm text-slate-600">Note: Successful applicants can be converted into employee records without manually recreating their profiles.</p>
          </div>
          <StatusBadge value={`${successfulApplicants.length} pending conversion`} />
        </div>
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                {["Candidate", "Job Title", "Department", "Offer", "Compliance", "Documents", "Conversion", "Actions"].map((column) => <th key={column} className="px-3 py-2">{column}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {successfulApplicants.map((applicant) => (
                <tr key={String(applicant.id)}>
                  <td className="px-3 py-2 font-medium text-slate-900">{asText(applicant.candidate_name)}<div className="text-xs text-slate-500">{asText(applicant.candidate_email)}</div></td>
                  <td className="px-3 py-2 text-slate-700">{asText(applicant.job_title)}</td>
                  <td className="px-3 py-2 text-slate-700">{asText(applicant.department)}</td>
                  <td className="px-3 py-2"><StatusBadge value={applicant.offer_status} /></td>
                  <td className="px-3 py-2"><StatusBadge value={applicant.compliance_readiness} /></td>
                  <td className="px-3 py-2"><StatusBadge value={applicant.document_readiness} /></td>
                  <td className="px-3 py-2"><StatusBadge value={applicant.conversion_status} /></td>
                  <td className="px-3 py-2">
                    <button type="button" onClick={() => convertApplicant(applicant)} className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-100">
                      <UserPlus size={14} /> Convert
                    </button>
                  </td>
                </tr>
              ))}
              {!successfulApplicants.length && (
                <tr><td colSpan={8} className="px-3 py-5 text-center text-slate-500">No successful applicants waiting for conversion.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-950">Pipeline actions</h2>
          <span className="text-xs font-medium text-slate-500">screen, shortlist, offer, accept</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {applications.filter((item) => item.conversion_status !== "converted").slice(0, 6).map((application) => (
            <button key={String(application.id)} type="button" onClick={() => progressToSuccessfulApplicant(application)} className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100">
              <CheckCircle2 size={14} /> Progress {asText(application.candidate_name)}
            </button>
          ))}
        </div>
      </section>

      <HRMEnterpriseModule moduleKey="recruitment" />
    </div>
  );
}
