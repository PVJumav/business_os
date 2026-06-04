const stats = [
  {
    title: "Active Benefits",
    value: "214",
    note: "Assigned to employees",
  },
  {
    title: "Medical Cover",
    value: "139",
    note: "Employees covered",
  },
  {
    title: "Pension Enrolled",
    value: "126",
    note: "Active pension members",
  },
  {
    title: "Monthly Cost",
    value: "KES 2.1M",
    note: "Employer contribution",
  },
];

export default function BenefitsStats() {
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