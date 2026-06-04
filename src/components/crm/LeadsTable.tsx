"use client";

const leads = [
  { id: 1, name: "Acme Corp", contact: "Jane Doe", status: "New", value: "$12,000", date: "2026-05-01" },
  { id: 2, name: "TechFlow Ltd", contact: "Mark Evans", status: "Contacted", value: "$8,400", date: "2026-04-28" },
  { id: 3, name: "Vertex AI", contact: "Sara Omondi", status: "Qualified", value: "$31,000", date: "2026-04-22" },
  { id: 4, name: "BlueWave Inc", contact: "Tom Carter", status: "Proposal", value: "$19,500", date: "2026-04-18" },
];

const statusColors: Record<string, string> = {
  New: "bg-slate-100 text-slate-600",
  Contacted: "bg-blue-100 text-blue-700",
  Qualified: "bg-green-100 text-green-700",
  Proposal: "bg-purple-100 text-purple-700",
};

export default function LeadsTable() {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">

      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-semibold">Leads</h3>
        <button className="text-sm text-blue-600 hover:underline">View All</button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="border-b border-slate-200">
              {["Company", "Contact", "Status", "Value", "Date"].map((h) => (
                <th key={h} className="px-4 py-3 font-semibold text-slate-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                <td className="px-4 py-3 font-medium">{lead.name}</td>
                <td className="px-4 py-3 text-slate-600">{lead.contact}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColors[lead.status] ?? "bg-slate-100 text-slate-600"}`}>
                    {lead.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-blue-600 font-semibold">{lead.value}</td>
                <td className="px-4 py-3 text-slate-500">{lead.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}
