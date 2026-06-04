const summary = [
  { label: "Office", value: "96" },
  { label: "Remote", value: "24" },
  { label: "Hybrid", value: "12" },
  { label: "Field Work", value: "8" },
];

export default function AttendanceSummary() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Work Mode Summary
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Attendance by work arrangement.
      </p>

      <div className="mt-5 space-y-4">
        {summary.map((item) => (
          <div key={item.label} className="flex items-center justify-between">
            <span className="text-sm text-slate-600">{item.label}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-900">
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}