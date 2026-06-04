import { CalendarCheck, Clock, PhoneCall, Users } from "lucide-react";

export default function ActivityStats() {
  const stats = [
    {
      title: "Total Activities",
      value: "386",
      icon: CalendarCheck,
    },
    {
      title: "Meetings",
      value: "74",
      icon: Users,
    },
    {
      title: "Calls",
      value: "128",
      icon: PhoneCall,
    },
    {
      title: "Pending Follow-ups",
      value: "31",
      icon: Clock,
    },
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