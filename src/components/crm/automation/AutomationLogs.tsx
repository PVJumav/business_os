const logs = [
  {
    workflow: "Qualified Lead to Opportunity",
    result: "Opportunity created successfully",
    time: "10 minutes ago",
    status: "Success",
  },
  {
    workflow: "Proposal Follow-up",
    result: "Follow-up activity created",
    time: "1 hour ago",
    status: "Success",
  },
  {
    workflow: "Inactive Account Reminder",
    result: "Workflow skipped because rule is paused",
    time: "Yesterday",
    status: "Skipped",
  },
];

export default function AutomationLogs() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-semibold">Automation Logs</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="pb-3">Workflow</th>
              <th className="pb-3">Result</th>
              <th className="pb-3">Time</th>
              <th className="pb-3">Status</th>
            </tr>
          </thead>

          <tbody>
            {logs.map((log) => (
              <tr key={`${log.workflow}-${log.time}`} className="border-b">
                <td className="py-4 font-medium">{log.workflow}</td>
                <td>{log.result}</td>
                <td>{log.time}</td>
                <td>
                  <span className="rounded-full bg-muted px-3 py-1 text-xs">
                    {log.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}