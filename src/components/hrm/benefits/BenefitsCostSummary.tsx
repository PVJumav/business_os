const costs = [
  { label: "Medical Cover", value: "KES 980K" },
  { label: "Pension", value: "KES 720K" },
  { label: "Insurance", value: "KES 210K" },
  { label: "Allowances", value: "KES 155K" },
  { label: "Staff Welfare", value: "KES 65K" },
];

export default function BenefitsCostSummary() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Cost Summary
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Monthly employer benefit costs.
      </p>

      <div className="mt-5 space-y-4">
        {costs.map((item) => (
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