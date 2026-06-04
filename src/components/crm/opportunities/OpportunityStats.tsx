import { BadgeDollarSign, Briefcase, Percent, TrendingUp } from "lucide-react";

export default function OpportunityStats() {
  const stats = [
    { title: "Open Opportunities", value: "46", icon: Briefcase },
    { title: "Pipeline Value", value: "$1.2M", icon: BadgeDollarSign },
    { title: "Win Probability", value: "38%", icon: Percent },
    { title: "Growth", value: "+21%", icon: TrendingUp },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.title} className="rounded-2xl border bg-background p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{stat.title}</p>
              <h3 className="mt-2 text-3xl font-bold">{stat.value}</h3>
            </div>

            <div className="rounded-xl bg-muted p-3">
              <stat.icon className="h-6 w-6" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}