const benefits = [
  {
    employee: "Grace Wanjiku",
    type: "Medical Cover",
    benefit: "Executive Medical Plan",
    provider: "AAR Insurance",
    employer: "KES 24,000",
    employeeContribution: "KES 6,000",
    status: "Active",
  },
  {
    employee: "Brian Otieno",
    type: "Pension",
    benefit: "Staff Pension Scheme",
    provider: "Britam",
    employer: "KES 18,000",
    employeeContribution: "KES 18,000",
    status: "Active",
  },
  {
    employee: "Mercy Achieng",
    type: "Allowance",
    benefit: "Transport Allowance",
    provider: "Internal",
    employer: "KES 15,000",
    employeeContribution: "KES 0",
    status: "Active",
  },
  {
    employee: "Daniel Mwangi",
    type: "Insurance",
    benefit: "Group Life Cover",
    provider: "ICEA Lion",
    employer: "KES 8,500",
    employeeContribution: "KES 0",
    status: "Active",
  },
];

export default function BenefitsTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Employee Benefits
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Employee benefits, providers, contributions, and statuses.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Benefit</th>
              <th className="px-4 py-3 font-medium">Provider</th>
              <th className="px-4 py-3 font-medium">Employer</th>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {benefits.map((item) => (
              <tr key={`${item.employee}-${item.benefit}`}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {item.employee}
                </td>
                <td className="px-4 py-3 text-slate-600">{item.type}</td>
                <td className="px-4 py-3 text-slate-600">{item.benefit}</td>
                <td className="px-4 py-3 text-slate-600">{item.provider}</td>
                <td className="px-4 py-3 font-semibold text-slate-900">
                  {item.employer}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {item.employeeContribution}
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {item.status}
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