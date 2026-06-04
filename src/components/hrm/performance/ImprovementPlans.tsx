const plans = [
  {
    employee: "Mercy Achieng",
    focus: "Sales conversion improvement",
  },
  {
    employee: "Brian Otieno",
    focus: "Advanced financial reporting",
  },
  {
    employee: "Sarah Njeri",
    focus: "Operations leadership coaching",
  },
];

export default function ImprovementPlans() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Development Plans
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Recommended improvement and training plans.
      </p>

      <div className="mt-5 space-y-3">
        {plans.map((plan) => (
          <div
            key={`${plan.employee}-${plan.focus}`}
            className="rounded-xl border border-slate-200 p-4"
          >
            <p className="text-sm font-semibold text-slate-900">
              {plan.employee}
            </p>
            <p className="mt-1 text-xs text-slate-500">{plan.focus}</p>
          </div>
        ))}
      </div>
    </section>
  );
}