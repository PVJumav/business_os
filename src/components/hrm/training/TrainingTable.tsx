const trainingRecords = [
  {
    employee: "Daniel Mwangi",
    title: "Fortinet NSE Training",
    provider: "Fortinet",
    type: "Technical",
    start: "05 May 2026",
    end: "16 May 2026",
    cost: "KES 120,000",
    status: "In Progress",
  },
  {
    employee: "Grace Wanjiku",
    title: "HR Compliance Workshop",
    provider: "Internal",
    type: "Compliance",
    start: "02 May 2026",
    end: "03 May 2026",
    cost: "KES 35,000",
    status: "Completed",
  },
  {
    employee: "Mercy Achieng",
    title: "Enterprise Sales Masterclass",
    provider: "LinkedIn Learning",
    type: "Sales",
    start: "10 May 2026",
    end: "20 May 2026",
    cost: "KES 42,000",
    status: "Not Started",
  },
  {
    employee: "Brian Otieno",
    title: "Advanced Financial Reporting",
    provider: "ACCA",
    type: "Finance",
    start: "15 Apr 2026",
    end: "30 Apr 2026",
    cost: "KES 85,000",
    status: "Completed",
  },
];

export default function TrainingTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Training Records
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Employee learning, certification, and development records.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Training</th>
              <th className="px-4 py-3 font-medium">Provider</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Start</th>
              <th className="px-4 py-3 font-medium">End</th>
              <th className="px-4 py-3 font-medium">Cost</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {trainingRecords.map((record) => (
              <tr key={`${record.employee}-${record.title}`}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {record.employee}
                </td>
                <td className="px-4 py-3 text-slate-600">{record.title}</td>
                <td className="px-4 py-3 text-slate-600">{record.provider}</td>
                <td className="px-4 py-3 text-slate-600">{record.type}</td>
                <td className="px-4 py-3 text-slate-600">{record.start}</td>
                <td className="px-4 py-3 text-slate-600">{record.end}</td>
                <td className="px-4 py-3 font-semibold text-slate-900">
                  {record.cost}
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {record.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}