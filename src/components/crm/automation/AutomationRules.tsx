const rules = [
  {
    name: "Qualified Lead to Opportunity",
    trigger: "Lead status changes to Qualified",
    action: "Create opportunity and assign account manager",
    status: "Active",
  },
  {
    name: "Proposal Follow-up",
    trigger: "Proposal sent",
    action: "Create follow-up activity after 3 days",
    status: "Active",
  },
  {
    name: "Inactive Account Reminder",
    trigger: "No activity for 30 days",
    action: "Notify account owner",
    status: "Paused",
  },
];

export default function AutomationRules() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-semibold">Workflow Rules</h2>

      <div className="space-y-4">
        {rules.map((rule) => (
          <div key={rule.name} className="rounded-xl border p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold">{rule.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  When {rule.trigger}
                </p>
                <p className="text-sm text-muted-foreground">
                  Then {rule.action}
                </p>
              </div>

              <span className="rounded-full bg-muted px-3 py-1 text-xs">
                {rule.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}