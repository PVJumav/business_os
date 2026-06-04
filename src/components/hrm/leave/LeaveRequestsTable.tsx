const leaveRequests = [
  {
    employee: "Mercy Achieng",
    type: "Annual Leave",
    start: "12 May 2026",
    end: "16 May 2026",
    days: "5",
    approver: "Grace Wanjiku",
    status: "Pending",
  },
  {
    employee: "Brian Otieno",
    type: "Sick Leave",
    start: "07 May 2026",
    end: "08 May 2026",
    days: "2",
    approver: "Grace Wanjiku",
    status: "Approved",
  },
  {
    employee: "Daniel Mwangi",
    type: "Paternity Leave",
    start: "20 May 2026",
    end: "24 May 2026",
    days: "5",
    approver: "Grace Wanjiku",
    status: "Pending",
  },
  {
    employee: "Sarah Njeri",
    type: "Unpaid Leave",
    start: "03 May 2026",
    end: "04 May 2026",
    days: "2",
    approver: "Grace Wanjiku",
    status: "Rejected",
  },
];

export default function LeaveRequestsTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Leave Requests
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Review and manage employee leave applications.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Leave Type</th>
              <th className="px-4 py-3 font-medium">Start</th>
              <th className="px-4 py-3 font-medium">End</th>
              <th className="px-4 py-3 font-medium">Days</th>
              <th className="px-4 py-3 font-medium">Approver</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Action</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {leaveRequests.map((request) => (
              <tr key={`${request.employee}-${request.start}`}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {request.employee}
                </td>
                <td className="px-4 py-3 text-slate-600">{request.type}</td>
                <td className="px-4 py-3 text-slate-600">{request.start}</td>
                <td className="px-4 py-3 text-slate-600">{request.end}</td>
                <td className="px-4 py-3 text-slate-600">{request.days}</td>
                <td className="px-4 py-3 text-slate-600">
                  {request.approver}
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {request.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button className="text-sm font-medium text-slate-900 hover:underline">
                    Review
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}