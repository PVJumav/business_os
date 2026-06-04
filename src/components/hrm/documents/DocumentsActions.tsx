export default function DocumentsActions() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-5">
        <input
          type="text"
          placeholder="Search document or employee..."
          className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400"
        />

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Document Types</option>
          <option>Contract</option>
          <option>ID Document</option>
          <option>Certificate</option>
          <option>Policy</option>
          <option>Payslip</option>
          <option>Appraisal</option>
        </select>

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Access Levels</option>
          <option>Public</option>
          <option>Internal</option>
          <option>Confidential</option>
          <option>Restricted</option>
        </select>

        <button className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">
          Export Index
        </button>

        <button className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800">
          Apply Filters
        </button>
      </div>
    </section>
  );
}