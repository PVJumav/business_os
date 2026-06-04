import HRMSidebar from "./HRMSidebar";
import HRMHeader from "./HRMHeader";

export default function HRMLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="app-canvas flex min-h-screen">
      <HRMSidebar />

      <div className="flex flex-1 flex-col">
        <HRMHeader />

        <main className="flex-1 p-6">
          <div className="mx-auto max-w-[1520px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
