export default function ContactFilters() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          placeholder="Search contacts..."
          className="w-full rounded-xl border px-4 py-2 outline-none"
        />

        <div className="flex gap-3">
          <select className="rounded-xl border px-4 py-2">
            <option>All Contact Types</option>
            <option>Customer</option>
            <option>Vendor</option>
            <option>Distributor</option>
            <option>Third-Party Integrator</option>
            <option>Partner</option>
          </select>

          <select className="rounded-xl border px-4 py-2">
            <option>All Status</option>
            <option>Active</option>
            <option>Inactive</option>
            <option>Pending Follow-up</option>
          </select>
        </div>
      </div>
    </div>
  );
}