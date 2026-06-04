const departments = [
  { name: "Technical", count: 46 },
  { name: "Sales", count: 32 },
  { name: "Operations", count: 28 },
  { name: "Finance", count: 18 },
  { name: "Human Resources", count: 12 },
  { name: "Management", count: 12 },
];

export default function DepartmentSummary() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Department Summary
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Employee distribution.
      </p>

      <div className="mt-5 space-y-4">
        {departments.map((department) => (
          <div
            key={department.name}
            className="flex items-center justify-between"
          >
            <span className="text-sm text-slate-600">{department.name}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-900">
              {department.count}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}