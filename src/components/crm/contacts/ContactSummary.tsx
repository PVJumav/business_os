export default function ContactSummary() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">Contact Summary</h2>

      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between">
          <span>Customers</span>
          <span className="font-semibold">318</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Vendors</span>
          <span className="font-semibold">84</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Distributors</span>
          <span className="font-semibold">42</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Third-Party Integrators</span>
          <span className="font-semibold">56</span>
        </div>

        <div className="flex items-center justify-between">
          <span>Partners</span>
          <span className="font-semibold">142</span>
        </div>
      </div>
    </div>
  );
}