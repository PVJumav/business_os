export default function PayrollActions() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-5">
        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>May 2026</option>
          <option>April 2026</option>
          <option>March 2026</option>
        </select>

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Departments</option>
          <option>Human Resources</option>
          <option>Finance</option>
          <option>Sales</option>
          <option>Technical</option>
        </select>

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Status</option>
          <option>Pending</option>
          <option>Approved</option>
          <option>Paid</option>
        </select>

        <button className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">
          Generate Payslips
        </button>

        <button className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800">
          Approve Payroll
        </button>
      </div>
    </section>
  );
}