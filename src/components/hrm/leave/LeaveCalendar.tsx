const upcomingLeave = [
  {
    employee: "Mercy Achieng",
    date: "12 May - 16 May",
  },
  {
    employee: "Daniel Mwangi",
    date: "20 May - 24 May",
  },
  {
    employee: "Brian Otieno",
    date: "27 May - 28 May",
  },
];

export default function LeaveCalendar() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Leave Calendar
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Upcoming employee absence.
      </p>

      <div className="mt-5 space-y-3">
        {upcomingLeave.map((leave) => (
          <div
            key={`${leave.employee}-${leave.date}`}
            className="rounded-xl border border-slate-200 p-4"
          >
            <p className="text-sm font-medium text-slate-900">
              {leave.employee}
            </p>
            <p className="mt-1 text-xs text-slate-500">{leave.date}</p>
          </div>
        ))}
      </div>
    </section>
  );
}