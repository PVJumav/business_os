export default function LeadFilters() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          placeholder="Search leads..."
          className="w-full rounded-xl border px-4 py-2 outline-none"
        />

        <div className="flex gap-3">
          <select className="rounded-xl border px-4 py-2">
            <option>All Sources</option>
            <option>Website</option>
            <option>Referral</option>
            <option>Cold Outreach</option>
            <option>Event</option>
            <option>Partner</option>
          </select>

          <select className="rounded-xl border px-4 py-2">
            <option>All Status</option>
            <option>New</option>
            <option>Contacted</option>
            <option>Qualified</option>
            <option>Lost</option>
          </select>
        </div>
      </div>
    </div>
  );
}