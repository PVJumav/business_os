export default function PerformanceActions() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-5">
        <input
          type="text"
          placeholder="Search employee..."
          className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400"
        />

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Periods</option>
          <option>Q1 2026</option>
          <option>Q2 2026</option>
          <option>Q3 2026</option>
          <option>Q4 2026</option>
        </select>

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Ratings</option>
          <option>Excellent</option>
          <option>Good</option>
          <option>Average</option>
          <option>Needs Improvement</option>
        </select>

        <button className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">
          Export Reviews
        </button>

        <button className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800">
          Apply Filters
        </button>
      </div>
    </section>
  );
}