const actions = [
  "Add Employee",
  "Import Employees",
  "Export Directory",
  "Assign Department",
  "Update Employment Status",
  "Upload Employee Document",
];

export default function EmployeeQuickActions() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Employee Actions</h2>
      <p className="mt-1 text-sm text-slate-500">
        Quick employee operations.
      </p>

      <div className="mt-5 grid gap-3">
        {actions.map((action) => (
          <button
            key={action}
            className="rounded-xl border border-slate-200 px-4 py-3 text-left text-sm font-medium text-slate-700 hover:border-slate-400 hover:bg-slate-50"
          >
            {action}
          </button>
        ))}
      </div>
    </section>
  );
}