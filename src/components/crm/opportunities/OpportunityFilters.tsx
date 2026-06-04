export default function OpportunityFilters() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          placeholder="Search opportunities..."
          className="w-full rounded-xl border px-4 py-2 outline-none"
        />

        <div className="flex gap-3">
          <select className="rounded-xl border px-4 py-2">
            <option>All Stages</option>
            <option>Discovery</option>
            <option>Proposal</option>
            <option>Negotiation</option>
            <option>Closed Won</option>
            <option>Closed Lost</option>
          </select>

          <select className="rounded-xl border px-4 py-2">
            <option>All Owners</option>
            <option>Paul Juma</option>
            <option>Albanus</option>
            <option>Vivian</option>
          </select>
        </div>
      </div>
    </div>
  );
}