const deductions = [
  { label: "PAYE", value: "KES 690K" },
  { label: "NSSF", value: "KES 118K" },
  { label: "SHIF / Medical", value: "KES 246K" },
  { label: "Loans", value: "KES 185K" },
  { label: "Other Deductions", value: "KES 91K" },
];

export default function PayrollDeductionsSummary() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Deductions Summary
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Statutory and internal deductions.
      </p>

      <div className="mt-5 space-y-4">
        {deductions.map((item) => (
          <div key={item.label} className="flex items-center justify-between">
            <span className="text-sm text-slate-600">{item.label}</span>
            <span className="text-sm font-semibold text-slate-900">
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}