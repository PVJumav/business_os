const certifications = [
  { name: "Technical Certifications", count: 18 },
  { name: "Compliance Certificates", count: 9 },
  { name: "Leadership Programs", count: 6 },
  { name: "Sales Certifications", count: 4 },
];

export default function CertificationSummary() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Certifications
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Awarded certificates by category.
      </p>

      <div className="mt-5 space-y-4">
        {certifications.map((item) => (
          <div key={item.name} className="flex items-center justify-between">
            <span className="text-sm text-slate-600">{item.name}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-900">
              {item.count}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}