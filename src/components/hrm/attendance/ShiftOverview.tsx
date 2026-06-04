const shifts = [
  {
    name: "Morning Shift",
    time: "08:00 AM - 05:00 PM",
    employees: 104,
  },
  {
    name: "Support Shift",
    time: "09:00 AM - 06:00 PM",
    employees: 28,
  },
  {
    name: "Field Shift",
    time: "Flexible",
    employees: 16,
  },
];

export default function ShiftOverview() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Shift Overview
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Active work schedules.
      </p>

      <div className="mt-5 space-y-3">
        {shifts.map((shift) => (
          <div
            key={shift.name}
            className="rounded-xl border border-slate-200 p-4"
          >
            <p className="text-sm font-semibold text-slate-900">
              {shift.name}
            </p>
            <p className="mt-1 text-xs text-slate-500">{shift.time}</p>
            <p className="mt-2 text-xs font-medium text-slate-700">
              {shift.employees} employees assigned
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}