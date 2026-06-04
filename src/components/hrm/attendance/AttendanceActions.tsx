export default function AttendanceActions() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-5">
        <input
          type="date"
          className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400"
        />

        <input
          type="text"
          placeholder="Search employee..."
          className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400"
        />

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Status</option>
          <option>Present</option>
          <option>Late</option>
          <option>Absent</option>
          <option>On Leave</option>
        </select>

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Work Modes</option>
          <option>Office</option>
          <option>Remote</option>
          <option>Hybrid</option>
          <option>Field Work</option>
        </select>

        <button className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800">
          Apply Filters
        </button>
      </div>
    </section>
  );
}