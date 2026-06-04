const distribution = [
  { rating: "Excellent", count: 28 },
  { rating: "Good", count: 46 },
  { rating: "Average", count: 18 },
  { rating: "Needs Improvement", count: 6 },
];

export default function PerformanceDistribution() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Rating Distribution
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Performance rating breakdown.
      </p>

      <div className="mt-5 space-y-4">
        {distribution.map((item) => (
          <div key={item.rating}>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">{item.rating}</span>
              <span className="text-sm font-semibold text-slate-900">
                {item.count}
              </span>
            </div>

            <div className="mt-2 h-2 rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-slate-900"
                style={{ width: `${item.count}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}