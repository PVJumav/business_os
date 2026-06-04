const timeline = [
  {
    title: "Client meeting completed",
    detail: "Introductory meeting held with Parker Russell Kenya.",
    time: "09:30 AM",
  },
  {
    title: "Proposal submitted",
    detail: "Imperva and Tenable proposals submitted.",
    time: "Yesterday",
  },
  {
    title: "Demo scheduled",
    detail: "CyberArk PAM demo scheduled for Consolidated Bank.",
    time: "Upcoming",
  },
];

export default function ActivityTimeline() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold">Recent Timeline</h2>

      <div className="space-y-4">
        {timeline.map((item) => (
          <div key={item.title} className="border-l-2 pl-4">
            <p className="font-medium">{item.title}</p>
            <p className="text-sm text-muted-foreground">{item.detail}</p>
            <p className="mt-1 text-xs text-muted-foreground">{item.time}</p>
          </div>
        ))}
      </div>
    </div>
  );
}