const stats = [
  {
    title: "Active Trainings",
    value: "18",
    note: "Currently ongoing",
  },
  {
    title: "Completed Trainings",
    value: "64",
    note: "This year",
  },
  {
    title: "Certifications Awarded",
    value: "37",
    note: "Verified certificates",
  },
  {
    title: "Training Cost",
    value: "KES 1.2M",
    note: "Year to date",
  },
];

export default function TrainingStats() {
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