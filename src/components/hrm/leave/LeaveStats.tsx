const stats = [
  {
    title: "Pending Requests",
    value: "17",
    note: "Awaiting approval",
  },
  {
    title: "Approved Leave",
    value: "42",
    note: "This month",
  },
  {
    title: "Employees Away",
    value: "9",
    note: "Currently on leave",
  },
  {
    title: "Rejected Requests",
    value: "3",
    note: "This month",
  },
];

export default function LeaveStats() {
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