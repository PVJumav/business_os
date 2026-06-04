export default function LeadQuickActions() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">Quick Actions</h2>

      <div className="space-y-3">
        <button className="w-full rounded-xl bg-black px-4 py-3 text-white">
          Add Lead
        </button>

        <button className="w-full rounded-xl border px-4 py-3">
          Import Leads
        </button>

        <button className="w-full rounded-xl border px-4 py-3">
          Convert Lead
        </button>
      </div>
    </div>
  );
}