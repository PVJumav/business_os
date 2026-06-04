export default function AccountFilters() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          placeholder="Search accounts..."
          className="w-full rounded-xl border px-4 py-2 outline-none"
        />

        <div className="flex gap-3">
          <select className="rounded-xl border px-4 py-2">
            <option>All Industries</option>
            <option>Banking</option>
            <option>Insurance</option>
            <option>Government</option>
            <option>Healthcare</option>
          </select>

          <select className="rounded-xl border px-4 py-2">
            <option>All Status</option>
            <option>Active</option>
            <option>Prospect</option>
            <option>Inactive</option>
          </select>
        </div>
      </div>
    </div>
  );
}