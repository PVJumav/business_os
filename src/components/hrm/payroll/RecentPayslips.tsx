const payslips = [
  "Grace Wanjiku - May 2026",
  "Brian Otieno - May 2026",
  "Mercy Achieng - May 2026",
  "Daniel Mwangi - May 2026",
];

export default function RecentPayslips() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Recent Payslips
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Latest generated payslips.
      </p>

      <div className="mt-5 space-y-3">
        {payslips.map((payslip) => (
          <button
            key={payslip}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-left text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {payslip}
          </button>
        ))}
      </div>
    </section>
  );
}