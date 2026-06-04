const stats = [
  {
    title: "Open Positions",
    value: "6",
    note: "Active vacancies",
  },
  {
    title: "Total Candidates",
    value: "84",
    note: "Across all roles",
  },
  {
    title: "Interviews Scheduled",
    value: "14",
    note: "This week",
  },
  {
    title: "Offers Pending",
    value: "3",
    note: "Awaiting acceptance",
  },
];

export default function RecruitmentStats() {
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