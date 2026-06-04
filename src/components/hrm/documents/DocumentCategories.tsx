const categories = [
  { name: "Contracts", count: 148 },
  { name: "ID Documents", count: 126 },
  { name: "Certificates", count: 64 },
  { name: "Payslips", count: 52 },
  { name: "Policies", count: 18 },
  { name: "Appraisals", count: 18 },
];

export default function DocumentCategories() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Document Categories
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Files grouped by document type.
      </p>

      <div className="mt-5 space-y-4">
        {categories.map((category) => (
          <div
            key={category.name}
            className="flex items-center justify-between"
          >
            <span className="text-sm text-slate-600">{category.name}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-900">
              {category.count}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}