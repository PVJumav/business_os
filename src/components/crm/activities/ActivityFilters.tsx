export default function ActivityFilters() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          placeholder="Search activities..."
          className="w-full rounded-xl border px-4 py-2 outline-none"
        />

        <div className="flex gap-3">
          <select className="rounded-xl border px-4 py-2">
            <option>All Types</option>
            <option>Call</option>
            <option>Meeting</option>
            <option>Email</option>
            <option>Demo</option>
            <option>Follow-up</option>
          </select>

          <select className="rounded-xl border px-4 py-2">
            <option>All Status</option>
            <option>Completed</option>
            <option>Pending</option>
            <option>Overdue</option>
          </select>
        </div>
      </div>
    </div>
  );
}