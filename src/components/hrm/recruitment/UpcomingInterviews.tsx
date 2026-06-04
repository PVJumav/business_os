const interviews = [
  {
    candidate: "Kevin Maina",
    role: "Sales Executive",
    time: "10 May, 10:00 AM",
  },
  {
    candidate: "Peter Otieno",
    role: "Systems Engineer",
    time: "11 May, 2:00 PM",
  },
  {
    candidate: "Mary Njeri",
    role: "Finance Officer",
    time: "13 May, 11:30 AM",
  },
];

export default function UpcomingInterviews() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Upcoming Interviews
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Scheduled candidate interviews.
      </p>

      <div className="mt-5 space-y-3">
        {interviews.map((interview) => (
          <div
            key={`${interview.candidate}-${interview.time}`}
            className="rounded-xl border border-slate-200 p-4"
          >
            <p className="text-sm font-semibold text-slate-900">
              {interview.candidate}
            </p>
            <p className="mt-1 text-xs text-slate-500">{interview.role}</p>
            <p className="mt-2 text-xs font-medium text-slate-700">
              {interview.time}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}