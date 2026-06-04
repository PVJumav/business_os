import { Building2, DollarSign, Users, TrendingUp } from "lucide-react";

export default function AccountStats() {
  const stats = [
    {
      title: "Total Accounts",
      value: "248",
      icon: Building2,
    },
    {
      title: "Enterprise Accounts",
      value: "54",
      icon: Users,
    },
    {
      title: "Revenue Pipeline",
      value: "$1.8M",
      icon: DollarSign,
    },
    {
      title: "Growth Rate",
      value: "+18%",
      icon: TrendingUp,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.title}
          className="rounded-2xl border bg-background p-6 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">
                {stat.title}
              </p>

              <h3 className="mt-2 text-3xl font-bold">
                {stat.value}
              </h3>
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