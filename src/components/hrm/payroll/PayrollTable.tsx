const payrollRecords = [
  {
    employee: "Grace Wanjiku",
    department: "Human Resources",
    basic: "KES 280,000",
    allowances: "KES 45,000",
    deductions: "KES 68,000",
    net: "KES 257,000",
    status: "Approved",
  },
  {
    employee: "Brian Otieno",
    department: "Finance",
    basic: "KES 220,000",
    allowances: "KES 35,000",
    deductions: "KES 52,000",
    net: "KES 203,000",
    status: "Pending",
  },
  {
    employee: "Mercy Achieng",
    department: "Sales",
    basic: "KES 180,000",
    allowances: "KES 60,000",
    deductions: "KES 41,000",
    net: "KES 199,000",
    status: "Approved",
  },
  {
    employee: "Daniel Mwangi",
    department: "Technical",
    basic: "KES 300,000",
    allowances: "KES 80,000",
    deductions: "KES 74,000",
    net: "KES 306,000",
    status: "Paid",
  },
];

export default function PayrollTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Payroll Records
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Monthly salary processing and payment records.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Department</th>
              <th className="px-4 py-3 font-medium">Basic</th>
              <th className="px-4 py-3 font-medium">Allowances</th>
              <th className="px-4 py-3 font-medium">Deductions</th>
              <th className="px-4 py-3 font-medium">Net Pay</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {payrollRecords.map((record) => (
              <tr key={record.employee}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {record.employee}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {record.department}
                </td>
                <td className="px-4 py-3 text-slate-600">{record.basic}</td>
                <td className="px-4 py-3 text-slate-600">
                  {record.allowances}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {record.deductions}
                </td>
                <td className="px-4 py-3 font-semibold text-slate-900">
                  {record.net}
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