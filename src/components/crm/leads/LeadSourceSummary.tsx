export default function LeadSourceSummary() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">Lead Sources</h2>

      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between">
          <span>Website</span>
          <span className="font-semibold">42</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Referrals</span>
          <span className="font-semibold">38</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Events</span>
          <span className="font-semibold">27</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Partners</span>
          <span className="font-semibold">31</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Cold Outreach</span>
          <span className="font-semibold">46</span>
        </div>
      </div>
    </div>
  );
}