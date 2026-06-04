const candidates = [
  {
    name: "Kevin Maina",
    email: "kevin.maina@email.com",
    role: "Sales Executive",
    stage: "Interview",
    status: "Active",
    interview: "10 May 2026",
  },
  {
    name: "Ann Wambui",
    email: "ann.wambui@email.com",
    role: "HR Assistant",
    stage: "Screening",
    status: "Active",
    interview: "Pending",
  },
  {
    name: "Peter Otieno",
    email: "peter.otieno@email.com",
    role: "Systems Engineer",
    stage: "Offer",
    status: "Offer Sent",
    interview: "Completed",
  },
  {
    name: "Linda Achieng",
    email: "linda.achieng@email.com",
    role: "Finance Officer",
    stage: "Applied",
    status: "New",
    interview: "Pending",
  },
];

export default function CandidateTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Candidate Records
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Track applicants, job roles, hiring stages, and interview status.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Candidate</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Stage</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Interview</th>
              <th className="px-4 py-3 font-medium">Action</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {candidates.map((candidate) => (
              <tr key={candidate.email}>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{candidate.name}</p>
                  <p className="text-xs text-slate-500">{candidate.email}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{candidate.role}</td>
                <td className="px-4 py-3 text-slate-600">{candidate.stage}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {candidate.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {candidate.interview}
                </td>
                <td className="px-4 py-3">
                  <button className="text-sm font-medium text-slate-900 hover:underline">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}