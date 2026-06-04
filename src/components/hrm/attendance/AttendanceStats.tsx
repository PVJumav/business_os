const stats = [
  {
    title: "Present Today",
    value: "132",
    note: "Employees checked in",
  },
  {
    title: "Late Arrivals",
    value: "9",
    note: "Reported after start time",
  },
  {
    title: "Absent",
    value: "7",
    note: "No attendance recorded",
  },
  {
    title: "Overtime Hours",
    value: "64",
    note: "Total this week",
  },
];

export default function AttendanceStats() {
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