const stages = [
  {
    name: "Applied",
    count: 36,
  },
  {
    name: "Screening",
    count: 21,
  },
  {
    name: "Interview",
    count: 14,
  },
  {
    name: "Offer",
    count: 3,
  },
  {
    name: "Hired",
    count: 10,
  },
];

export default function RecruitmentPipeline() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Recruitment Pipeline
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Candidate distribution across hiring stages.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        {stages.map((stage) => (
          <div
            key={stage.name}
            className="rounded-xl border border-slate-200 bg-slate-50 p-4"
          >
            <p className="text-sm font-medium text-slate-600">{stage.name}</p>
            <h3 className="mt-3 text-2xl font-bold text-slate-900">
              {stage.count}
            </h3>
            <p className="mt-1 text-xs text-slate-500">Candidates</p>
          </div>
        ))}
      </div>
    </section>
  );
}