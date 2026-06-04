const attendanceRecords = [
  {
    employee: "Grace Wanjiku",
    department: "Human Resources",
    date: "08 May 2026",
    clockIn: "08:03 AM",
    clockOut: "05:12 PM",
    hours: "9.1",
    mode: "Office",
    status: "Present",
  },
  {
    employee: "Brian Otieno",
    department: "Finance",
    date: "08 May 2026",
    clockIn: "08:42 AM",
    clockOut: "05:06 PM",
    hours: "8.4",
    mode: "Office",
    status: "Late",
  },
  {
    employee: "Mercy Achieng",
    department: "Sales",
    date: "08 May 2026",
    clockIn: "-",
    clockOut: "-",
    hours: "0",
    mode: "-",
    status: "On Leave",
  },
  {
    employee: "Daniel Mwangi",
    department: "Technical",
    date: "08 May 2026",
    clockIn: "07:56 AM",
    clockOut: "06:30 PM",
    hours: "10.5",
    mode: "Remote",
    status: "Present",
  },
];

export default function AttendanceTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Attendance Records
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Daily clock-in, clock-out, and work hour records.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Department</th>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Clock In</th>
              <th className="px-4 py-3 font-medium">Clock Out</th>
              <th className="px-4 py-3 font-medium">Hours</th>
              <th className="px-4 py-3 font-medium">Mode</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {attendanceRecords.map((record) => (
              <tr key={`${record.employee}-${record.date}`}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {record.employee}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {record.department}
                </td>
                <td className="px-4 py-3 text-slate-600">{record.date}</td>
                <td className="px-4 py-3 text-slate-600">{record.clockIn}</td>
                <td className="px-4 py-3 text-slate-600">{record.clockOut}</td>
                <td className="px-4 py-3 font-semibold text-slate-900">
                  {record.hours}
                </td>
                <td className="px-4 py-3 text-slate-600">{record.mode}</td>
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