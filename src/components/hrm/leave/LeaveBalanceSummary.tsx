const balances = [
  { type: "Annual Leave", used: 84, remaining: 276 },
  { type: "Sick Leave", used: 22, remaining: 118 },
  { type: "Maternity/Paternity", used: 15, remaining: 85 },
  { type: "Unpaid Leave", used: 11, remaining: 0 },
];

export default function LeaveBalanceSummary() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Leave Balances
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Used and remaining leave days.
      </p>

      <div className="mt-5 space-y-4">
        {balances.map((item) => (
          <div key={item.type} className="rounded-xl bg-slate-50 p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-700">{item.type}</p>
              <p className="text-xs text-slate-500">
                {item.remaining} remaining
              </p>
            </div>

            <div className="mt-3 h-2 rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-slate-900"
                style={{
                  width: `${Math.min(
                    100,
                    (item.used / (item.used + item.remaining || 1)) * 100
                  )}%`,
                }}
              />
            </div>

            <p className="mt-2 text-xs text-slate-500">
              {item.used} days used
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}