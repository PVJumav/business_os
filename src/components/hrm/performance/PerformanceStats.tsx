const stats = [
  {
    title: "Reviews Completed",
    value: "86",
    note: "Current cycle",
  },
  {
    title: "Pending Reviews",
    value: "24",
    note: "Awaiting completion",
  },
  {
    title: "Average Score",
    value: "82%",
    note: "Across all departments",
  },
  {
    title: "Promotion Recommendations",
    value: "11",
    note: "Submitted by managers",
  },
];

export default function PerformanceStats() {
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