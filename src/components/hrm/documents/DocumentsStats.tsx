const stats = [
  {
    title: "Total Documents",
    value: "426",
    note: "Stored HR files",
  },
  {
    title: "Employee Files",
    value: "318",
    note: "Linked to employees",
  },
  {
    title: "Expiring Soon",
    value: "12",
    note: "Within 60 days",
  },
  {
    title: "Confidential Files",
    value: "74",
    note: "Restricted access",
  },
];

export default function DocumentsStats() {
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