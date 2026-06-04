const triggers = [
  "Lead created",
  "Lead status changed",
  "Opportunity stage changed",
  "Proposal sent",
  "Account inactive",
  "Task overdue",
];

export default function AutomationTriggers() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">Available Triggers</h2>

      <div className="space-y-3">
        {triggers.map((trigger) => (
          <div key={trigger} className="rounded-xl border px-4 py-3 text-sm">
            {trigger}
          </div>
        ))}
      </div>
    </div>
  );
}