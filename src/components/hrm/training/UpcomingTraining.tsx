const upcoming = [
  {
    title: "Enterprise Sales Masterclass",
    date: "10 May 2026",
  },
  {
    title: "Cybersecurity Awareness",
    date: "14 May 2026",
  },
  {
    title: "Leadership Coaching",
    date: "20 May 2026",
  },
];

export default function UpcomingTraining() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Upcoming Training
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Scheduled learning sessions.
      </p>

      <div className="mt-5 space-y-3">
        {upcoming.map((item) => (
          <div
            key={`${item.title}-${item.date}`}
            className="rounded-xl border border-slate-200 p-4"
          >
            <p className="text-sm font-semibold text-slate-900">
              {item.title}
            </p>
            <p className="mt-1 text-xs text-slate-500">{item.date}</p>
          </div>
        ))}
      </div>
    </section>
  );
}