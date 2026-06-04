export default function AccountSummary() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">
        Account Summary
      </h2>

      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between">
          <span>Total Active</span>
          <span className="font-semibold">192</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Enterprise Clients</span>
          <span className="font-semibold">54</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Pending Renewals</span>
          <span className="font-semibold">16</span>
        </div>

        <div className="flex items-center justify-between">
          <span>High Value Accounts</span>
          <span className="font-semibold">28</span>
        </div>
      </div>
    </div>
  );
}