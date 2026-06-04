const deals = [
  {
    stage: "Lead Qualification",
    value: "$18,000",
    count: 12,
    color: "bg-yellow-100 text-yellow-700",
  },
  {
    stage: "Proposal Sent",
    value: "$42,500",
    count: 8,
    color: "bg-blue-100 text-blue-700",
  },
  {
    stage: "Negotiation",
    value: "$67,200",
    count: 5,
    color: "bg-purple-100 text-purple-700",
  },
  {
    stage: "Closed Won",
    value: "$128,420",
    count: 24,
    color: "bg-green-100 text-green-700",
  },
];

export default function DealsPipeline() {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">

      <div className="flex items-center justify-between mb-5">

        <h3 className="text-lg font-semibold">
          CRM Pipeline
        </h3>

        <button className="text-sm text-blue-600 hover:underline">
          View All
        </button>

      </div>

      <div className="grid grid-cols-4 gap-4">

        {deals.map((deal, index) => (
          <div
            key={index}
            className="border border-slate-200 rounded-xl p-4"
          >

            <span className={`inline-block text-xs font-medium px-2 py-1 rounded-full mb-3 ${deal.color}`}>
              {deal.count} deals
            </span>

            <p className="font-medium text-sm">
              {deal.stage}
            </p>

            <p className="text-xl font-bold mt-1 text-blue-600">
              {deal.value}
            </p>

          </div>
        ))}

      </div>

    </div>
  );
}
