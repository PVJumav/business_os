const actions = [
  "Create opportunity",
  "Assign owner",
  "Send notification",
  "Create follow-up task",
  "Update status",
  "Generate reminder",
];

export default function AutomationActions() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">Available Actions</h2>

      <div className="space-y-3">
        {actions.map((action) => (
          <div key={action} className="rounded-xl border px-4 py-3 text-sm">
            {action}
          </div>
        ))}
      </div>
    </div>
  );
}