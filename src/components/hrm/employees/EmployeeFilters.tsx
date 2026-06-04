export default function EmployeeFilters() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-4">
        <input
          type="text"
          placeholder="Search employee..."
          className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400"
        />

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Departments</option>
          <option>Human Resources</option>
          <option>Finance</option>
          <option>Sales</option>
          <option>Technical</option>
          <option>Operations</option>
        </select>

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Status</option>
          <option>Active</option>
          <option>On Leave</option>
          <option>Probation</option>
          <option>Suspended</option>
          <option>Exited</option>
        </select>

        <button className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800">
          Apply Filters
        </button>
      </div>
    </section>
  );
}