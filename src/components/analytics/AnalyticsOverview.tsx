"use client";

export default function EnterpriseAnalytics() {
  return (
    <div className="space-y-6">

      {/* Analytics Filters */}
      <div className="bg-white rounded-2xl border p-4 flex items-center gap-4">

        <select className="border rounded-lg px-3 py-2">
          <option>Revenue</option>
          <option>Projects</option>
          <option>HRM</option>
          <option>Finance</option>
        </select>

        <select className="border rounded-lg px-3 py-2">
          <option>Last 30 Days</option>
          <option>Quarter</option>
          <option>Year</option>
        </select>

      </div>

      {/* Drill-down Layout */}
      <div className="grid grid-cols-4 gap-6">

        <div className="col-span-3 bg-white rounded-2xl border h-[500px] p-5">
          Interactive Drill-down Analytics
        </div>

        <div className="bg-slate-950 text-white rounded-2xl p-5">
          AI Business Insights
        </div>

      </div>

      {/* Detailed Reports */}
      <div className="bg-white rounded-2xl border h-[300px] p-5">
        Enterprise Reporting Table
      </div>

    </div>
  );
}