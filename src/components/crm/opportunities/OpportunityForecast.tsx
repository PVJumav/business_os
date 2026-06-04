export default function OpportunityForecast() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">Revenue Forecast</h2>

      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between">
          <span>Discovery</span>
          <span className="font-semibold">$180,000</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Proposal</span>
          <span className="font-semibold">$420,000</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Negotiation</span>
          <span className="font-semibold">$310,000</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Committed</span>
          <span className="font-semibold">$290,000</span>
        </div>
      </div>
    </div>
  );
}