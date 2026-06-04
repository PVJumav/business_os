const providers = [
  {
    name: "AAR Insurance",
    type: "Medical Cover",
  },
  {
    name: "Britam",
    type: "Pension",
  },
  {
    name: "ICEA Lion",
    type: "Group Life Cover",
  },
  {
    name: "Internal",
    type: "Allowances & Welfare",
  },
];

export default function BenefitsProviders() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Providers
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Benefit providers and schemes.
      </p>

      <div className="mt-5 space-y-3">
        {providers.map((provider) => (
          <div
            key={`${provider.name}-${provider.type}`}
            className="rounded-xl border border-slate-200 p-4"
          >
            <p className="text-sm font-semibold text-slate-900">
              {provider.name}
            </p>
            <p className="mt-1 text-xs text-slate-500">{provider.type}</p>
          </div>
        ))}
      </div>
    </section>
  );
}