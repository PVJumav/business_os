"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, CheckCircle2, FileDown, RefreshCw, Send, Settings } from "lucide-react";
import { api } from "@/services/api";
import HRMEnterpriseModule from "@/components/hrm/HRMEnterpriseModule";

type CellValue = string | number | boolean | null | undefined | Record<string, unknown> | unknown[];
type RecordMap = Record<string, CellValue>;
type CalculationResult = RecordMap & { blocking_errors?: string[] };

const inputClass = "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

function today(offset = 0) {
  const value = new Date();
  value.setDate(value.getDate() + offset);
  return value.toISOString().slice(0, 10);
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function SimpleTable({ rows, columns }: { rows: RecordMap[]; columns: string[] }) {
  if (!rows.length) return <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">No records yet.</p>;
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>{columns.map((column) => <th key={column} className="px-3 py-2">{column.replaceAll("_", " ")}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, index) => (
            <tr key={String(row.id ?? index)}>
              {columns.map((column) => <td key={column} className="px-3 py-2 text-slate-700">{String(row[column] ?? "-")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function LeaveManagementWorkspace() {
  const [employees, setEmployees] = useState<RecordMap[]>([]);
  const [requests, setRequests] = useState<RecordMap[]>([]);
  const [policies, setPolicies] = useState<RecordMap[]>([]);
  const [balances, setBalances] = useState<RecordMap[]>([]);
  const [report, setReport] = useState<RecordMap | null>(null);
  const [calendar, setCalendar] = useState<{ leave?: RecordMap[]; public_holidays?: RecordMap[] }>({});
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [leaveType, setLeaveType] = useState("Annual Leave");
  const [startDate, setStartDate] = useState(today(7));
  const [endDate, setEndDate] = useState(today(9));
  const [startDayType, setStartDayType] = useState("Full Day");
  const [endDayType, setEndDayType] = useState("Full Day");
  const [reason, setReason] = useState("");
  const [calculation, setCalculation] = useState<CalculationResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedPolicy = useMemo(() => policies[0], [policies]);

  async function load() {
    setError(null);
    try {
      const [employeeRows, requestRows, policyRows, reportData, calendarData] = await Promise.all([
        api.get<RecordMap[]>("/api/hrm/employees"),
        api.get<RecordMap[]>("/api/hrm/leave/requests"),
        api.get<RecordMap[]>("/api/hrm/leave/policies"),
        api.get<RecordMap>("/api/hrm/leave/reports"),
        api.get<{ leave?: RecordMap[]; public_holidays?: RecordMap[] }>("/api/hrm/leave/calendar"),
      ]);
      setEmployees(employeeRows);
      setRequests(requestRows);
      setPolicies(policyRows);
      setReport(reportData);
      setCalendar(calendarData);
      const employeeId = selectedEmployee || String(employeeRows[0]?.id ?? "");
      setSelectedEmployee(employeeId);
      if (employeeId) {
        const balanceData = await api.get<{ balances: RecordMap[] }>(`/api/hrm/leave/balances/${employeeId}`);
        setBalances(balanceData.balances ?? []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load leave module");
    }
  }

  async function calculate() {
    if (!selectedEmployee) return;
    setError(null);
    try {
      const result = await api.post<CalculationResult>("/api/hrm/leave/calculate", {
        employee_id: selectedEmployee,
        leave_type: leaveType,
        policy_id: selectedPolicy?.id,
        start_date: startDate,
        end_date: endDate,
        start_day_type: startDayType,
        end_day_type: endDayType,
      });
      setCalculation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Leave calculation failed");
    }
  }

  async function submitRequest() {
    if (!selectedEmployee) return;
    setError(null);
    try {
      const result = await api.post<RecordMap>("/api/hrm/leave/requests", {
        employee_id: selectedEmployee,
        leave_type: leaveType,
        policy_id: selectedPolicy?.id,
        start_date: startDate,
        end_date: endDate,
        start_day_type: startDayType,
        end_day_type: endDayType,
        reason,
        submit: true,
      });
      setMessage(`Leave request submitted: ${result.status}`);
      setReason("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Leave request failed");
    }
  }

  async function approveRequest(id: string) {
    setError(null);
    try {
      await api.post(`/api/hrm/leave/requests/${id}/approve`, { comments: "Approved from leave workspace" });
      setMessage("Leave request approved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    }
  }

  async function exportReport() {
    setError(null);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const response = await fetch("/api/hrm/leave/reports/export", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ report_type: "leave", export_format: "csv" }),
      });
      if (!response.ok) throw new Error("Report export failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "leave-report.csv";
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report export failed");
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void calculate();
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEmployee, leaveType, startDate, endDate, startDayType, endDayType, selectedPolicy?.id]);

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">HRMS v5.5 / LEV-001 to LEV-022</p>
            <h1 className="mt-2 text-2xl font-bold text-slate-950">Leave Management</h1>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
              Apply, calculate, approve, review, adjust balances, track holidays, and report on leave with attendance and payroll impacts.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              <RefreshCw size={16} /> Refresh
            </button>
            <button type="button" onClick={exportReport} className="inline-flex items-center gap-2 rounded-lg bg-slate-950 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800">
              <FileDown size={16} /> Export
            </button>
          </div>
        </div>
      </section>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {message && <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div>}

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Send size={18} className="text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-950">Apply for leave</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">Employee<select value={selectedEmployee} onChange={(event) => setSelectedEmployee(event.target.value)} className={inputClass}>{employees.map((employee) => <option key={String(employee.id)} value={String(employee.id)}>{String(employee.first_name ?? "")} {String(employee.last_name ?? "")}</option>)}</select></label>
            <label className="text-sm font-medium text-slate-700">Leave Type<select value={leaveType} onChange={(event) => setLeaveType(event.target.value)} className={inputClass}>{["Annual Leave", "Sick Leave", "Maternity Leave", "Paternity Leave", "Compassionate Leave", "Study Leave", "Unpaid Leave", "Leave of Absence", "Custom Leave Type"].map((type) => <option key={type}>{type}</option>)}</select></label>
            <label className="text-sm font-medium text-slate-700">Start Date<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className={inputClass} /></label>
            <label className="text-sm font-medium text-slate-700">End Date<input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className={inputClass} /></label>
            <label className="text-sm font-medium text-slate-700">Start Day<select value={startDayType} onChange={(event) => setStartDayType(event.target.value)} className={inputClass}><option>Full Day</option><option>First Half</option><option>Second Half</option></select></label>
            <label className="text-sm font-medium text-slate-700">End Day<select value={endDayType} onChange={(event) => setEndDayType(event.target.value)} className={inputClass}><option>Full Day</option><option>First Half</option><option>Second Half</option></select></label>
            <label className="text-sm font-medium text-slate-700 md:col-span-2">Reason<textarea value={reason} onChange={(event) => setReason(event.target.value)} className={`${inputClass} min-h-20`} /></label>
          </div>
          <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-900">
            Note: Leave requests may affect attendance and payroll depending on policy. Some leave types require supporting documents or HR review.
          </div>
          <button type="button" onClick={submitRequest} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
            <Send size={16} /> Submit Leave Request
          </button>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <CalendarDays size={18} className="text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-950">Live calculation</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="Calendar Days" value={String(calculation?.calendar_days ?? "-")} />
            <Metric label="Working Days" value={String(calculation?.working_days ?? "-")} />
            <Metric label="Leave Days" value={String(calculation?.leave_days ?? "-")} />
            <Metric label="Return Date" value={String(calculation?.return_to_work_date ?? "-")} />
            <Metric label="Balance Before" value={String(calculation?.balance_before ?? "-")} />
            <Metric label="Balance After" value={String(calculation?.balance_after ?? "-")} />
          </div>
          {Array.isArray(calculation?.blocking_errors) && calculation.blocking_errors.length > 0 && (
            <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{calculation.blocking_errors.join(", ")}</div>
          )}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <Metric label="Pending Approvals" value={String(report?.pending_approvals ?? 0)} />
        <Metric label="Approved Requests" value={String(report?.approved_requests ?? 0)} />
        <Metric label="Unpaid Leave Impact" value={String(report?.unpaid_leave_requests ?? 0)} />
        <Metric label="Leave Liability Days" value={String(report?.leave_liability_days ?? 0)} />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-950">Leave requests</h2>
            <span className="text-xs font-medium text-slate-500">manager and HR workflow</span>
          </div>
          <SimpleTable rows={requests} columns={["leave_type", "start_date", "end_date", "leave_days", "status"]} />
          <div className="mt-3 flex flex-wrap gap-2">
            {requests.filter((request) => ["Submitted", "Pending Manager Approval"].includes(String(request.status))).slice(0, 3).map((request) => (
              <button key={String(request.id)} type="button" onClick={() => approveRequest(String(request.id))} className="inline-flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-100">
                <CheckCircle2 size={14} /> Approve {String(request.leave_type)}
              </button>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-lg font-semibold text-slate-950">Balances and calendar</h2>
          <SimpleTable rows={balances} columns={["leave_type", "fiscal_year", "opening_balance", "used_days", "available_days"]} />
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <Metric label="Calendar Leave Events" value={calendar.leave?.length ?? 0} />
            <Metric label="Public Holidays" value={calendar.public_holidays?.length ?? 0} />
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <Settings size={18} className="text-slate-600" />
          <h2 className="text-lg font-semibold text-slate-950">Policy, holidays, carry-forward, encashment and reports</h2>
        </div>
        <HRMEnterpriseModule moduleKey="leave" />
      </section>
    </div>
  );
}
