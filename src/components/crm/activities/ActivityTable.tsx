const activities = [
  {
    activity: "FortiSIEM proposal follow-up",
    account: "Niwa Sacco",
    type: "Follow-up",
    owner: "Paul Juma",
    dueDate: "Today",
    status: "Pending",
  },
  {
    activity: "CyberArk PAM demo",
    account: "Consolidated Bank",
    type: "Demo",
    owner: "Paul Juma",
    dueDate: "21 May",
    status: "Scheduled",
  },
  {
    activity: "SentinelOne XDR discussion",
    account: "Amaco",
    type: "Meeting",
    owner: "Albanus",
    dueDate: "21 May",
    status: "Scheduled",
  },
];

export default function ActivityTable() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-semibold">Activity List</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="pb-3">Activity</th>
              <th className="pb-3">Account</th>
              <th className="pb-3">Type</th>
              <th className="pb-3">Owner</th>
              <th className="pb-3">Due Date</th>
              <th className="pb-3">Status</th>
            </tr>
          </thead>

          <tbody>
            {activities.map((item) => (
              <tr key={item.activity} className="border-b">
                <td className="py-4 font-medium">{item.activity}</td>
                <td>{item.account}</td>
                <td>{item.type}</td>
                <td>{item.owner}</td>
                <td>{item.dueDate}</td>
                <td>
                  <span className="rounded-full bg-muted px-3 py-1 text-xs">
                    {item.status}
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