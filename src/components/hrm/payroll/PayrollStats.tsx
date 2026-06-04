const stats = [
  {
    title: "Gross Payroll",
    value: "KES 9.8M",
    note: "Current payroll cycle",
  },
  {
    title: "Net Payroll",
    value: "KES 8.4M",
    note: "After deductions",
  },
  {
    title: "Employees Paid",
    value: "139",
    note: "Ready for disbursement",
  },
  {
    title: "Pending Approval",
    value: "9",
    note: "Payroll records pending",
  },
];

export default function PayrollStats() {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.title}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <p className="text-sm font-medium text-slate-500">{stat.title}</p>
          <h3 className="mt-3 text-2xl font-bold text-slate-900">
            {stat.value}
          </h3>
          <p className="mt-2 text-xs text-slate-500">{stat.note}</p>
        </div>
      ))}
    </section>
  );
}