const reviews = [
  {
    employee: "Grace Wanjiku",
    reviewer: "Managing Director",
    period: "Q2 2026",
    score: "91%",
    rating: "Excellent",
    recommendation: "Promotion",
    status: "Completed",
  },
  {
    employee: "Brian Otieno",
    reviewer: "Finance Manager",
    period: "Q2 2026",
    score: "84%",
    rating: "Good",
    recommendation: "Training",
    status: "Completed",
  },
  {
    employee: "Mercy Achieng",
    reviewer: "Sales Manager",
    period: "Q2 2026",
    score: "76%",
    rating: "Good",
    recommendation: "Sales coaching",
    status: "Pending",
  },
  {
    employee: "Daniel Mwangi",
    reviewer: "Technical Lead",
    period: "Q2 2026",
    score: "88%",
    rating: "Excellent",
    recommendation: "Certification",
    status: "Completed",
  },
];

export default function PerformanceReviewsTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Performance Reviews
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Employee appraisals, scores, ratings, and recommendations.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Reviewer</th>
              <th className="px-4 py-3 font-medium">Period</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Rating</th>
              <th className="px-4 py-3 font-medium">Recommendation</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {reviews.map((review) => (
              <tr key={`${review.employee}-${review.period}`}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {review.employee}
                </td>
                <td className="px-4 py-3 text-slate-600">{review.reviewer}</td>
                <td className="px-4 py-3 text-slate-600">{review.period}</td>
                <td className="px-4 py-3 font-semibold text-slate-900">
                  {review.score}
                </td>
                <td className="px-4 py-3 text-slate-600">{review.rating}</td>
                <td className="px-4 py-3 text-slate-600">
                  {review.recommendation}
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {review.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}