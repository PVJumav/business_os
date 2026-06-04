const stages = [
  {
    title: "Discovery",
    opportunities: [
      {
        name: "Parker Russell Cybersecurity Review",
        account: "Parker Russell Kenya",
        value: "$25,000",
        owner: "Paul Juma",
      },
      {
        name: "DAM Requirements Assessment",
        account: "Customer Account",
        value: "$18,000",
        owner: "Paul Juma",
      },
    ],
  },
  {
    title: "Proposal",
    opportunities: [
      {
        name: "FortiSIEM Licensing",
        account: "Niwa Sacco",
        value: "$45,000",
        owner: "Paul Juma",
      },
      {
        name: "F5 and Fortinet Proposal",
        account: "Enterprise Client",
        value: "$70,000",
        owner: "Paul Juma",
      },
    ],
  },
  {
    title: "Negotiation",
    opportunities: [
      {
        name: "CyberArk PAM Demo",
        account: "Consolidated Bank",
        value: "$80,000",
        owner: "Paul Juma",
      },
    ],
  },
];

export default function OpportunityKanban() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-semibold">Pipeline Board</h2>

      <div className="grid gap-4 md:grid-cols-3">
        {stages.map((stage) => (
          <div key={stage.title} className="rounded-xl border bg-muted/30 p-4">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold">{stage.title}</h3>
              <span className="rounded-full bg-background px-3 py-1 text-xs">
                {stage.opportunities.length}
              </span>
            </div>

            <div className="space-y-3">
              {stage.opportunities.map((opportunity) => (
                <div key={opportunity.name} className="rounded-xl border bg-background p-4">
                  <h4 className="font-medium">{opportunity.name}</h4>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {opportunity.account}
                  </p>

                  <div className="mt-4 flex items-center justify-between text-sm">
                    <span className="font-semibold">{opportunity.value}</span>
                    <span className="text-muted-foreground">{opportunity.owner}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}