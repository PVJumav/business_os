export default function BenefitsActions() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-5">
        <input
          type="text"
          placeholder="Search employee or benefit..."
          className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400"
        />

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Benefit Types</option>
          <option>Medical Cover</option>
          <option>Pension</option>
          <option>Insurance</option>
          <option>Allowance</option>
          <option>Loan</option>
          <option>Staff Welfare</option>
        </select>

        <select className="rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400">
          <option>All Status</option>
          <option>Active</option>
          <option>Inactive</option>
          <option>Expired</option>
          <option>Pending</option>
        </select>

        <button className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">
          Export Benefits
        </button>

        <button className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800">
          Apply Filters
        </button>
      </div>
    </section>
  );
}