"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  Tooltip,
} from "recharts";

const data = [
  { month: "Jan", revenue: 4000 },
  { month: "Feb", revenue: 6500 },
  { month: "Mar", revenue: 8000 },
  { month: "Apr", revenue: 7200 },
  { month: "May", revenue: 9800 },
  { month: "Jun", revenue: 12000 },
];

export default function RevenueChart() {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">

      <div className="mb-6">

        <h3 className="font-semibold text-lg">
          Revenue Analytics
        </h3>

        <p className="text-sm text-slate-500">
          Financial growth overview
        </p>

      </div>

      <div className="h-80">

        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>

            <XAxis dataKey="month" />

            <Tooltip />

            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#2563eb"
              fill="#93c5fd"
            />

          </AreaChart>
        </ResponsiveContainer>

      </div>

    </div>
  );
}