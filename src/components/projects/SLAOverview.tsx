"use client";

const slas = [
  {
    client: "Equity Bank",
    tier: "Platinum",
    tickets: 24,
    health: "Excellent",
  },
  {
    client: "NCBA",
    tier: "Gold",
    tickets: 12,
    health: "Good",
  },
];

export default function SLAOverview() {
  return (
    <div className="bg-white rounded-2xl border p-5">

      <div className="mb-5">

        <h3 className="text-lg font-semibold">
          SLA Management
        </h3>

        <p className="text-sm text-slate-500">
          Monitor SLAs, approvals, health checks and ticketing
        </p>

      </div>

      <div className="space-y-4">

        {slas.map((sla, index) => (
          <div
            key={index}
            className="border rounded-xl p-4 flex items-center justify-between"
          >

            <div>

              <h4 className="font-semibold">
                {sla.client}
              </h4>

              <p className="text-sm text-slate-500">
                {sla.tier} Tier
              </p>

            </div>

            <div className="text-right">

              <p className="text-sm">
                Tickets: {sla.tickets}
              </p>

              <p className="text-sm text-green-600">
                {sla.health}
              </p>

            </div>

          </div>
        ))}

      </div>

    </div>
  );
}