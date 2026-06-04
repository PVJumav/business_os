const leads = [
  {
    name: "Njiwa DT Sacco",
    contact: "Anthony Mwangi",
    source: "Referral",
    owner: "Paul Juma",
    value: "$45,000",
    status: "Qualified",
  },
  {
    name: "Madison Assurance",
    contact: "ICT Manager",
    source: "Account Manager",
    owner: "Albanus",
    value: "$60,000",
    status: "Contacted",
  },
  {
    name: "Consolidated Bank",
    contact: "IT Security Team",
    source: "Existing Account",
    owner: "Paul Juma",
    value: "$80,000",
    status: "Qualified",
  },
];

export default function LeadTable() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-semibold">Lead List</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="pb-3">Lead</th>
              <th className="pb-3">Contact</th>
              <th className="pb-3">Source</th>
              <th className="pb-3">Owner</th>
              <th className="pb-3">Value</th>
              <th className="pb-3">Status</th>
            </tr>
          </thead>

          <tbody>
            {leads.map((lead) => (
              <tr key={lead.name} className="border-b">
                <td className="py-4 font-medium">{lead.name}</td>
                <td>{lead.contact}</td>
                <td>{lead.source}</td>
                <td>{lead.owner}</td>
                <td>{lead.value}</td>
                <td>
                  <span className="rounded-full bg-muted px-3 py-1 text-xs">
                    {lead.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}