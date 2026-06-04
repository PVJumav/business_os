// src/components/crm/layout/CRMLayout.tsx

"use client";

import CRMSidebar from "./CRMSidebar";
import CRMTopbar from "./CRMTopbar";

export default function CRMLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="app-canvas flex min-h-screen">
      {/* Constant Sidebar */}
      <CRMSidebar />

      {/* Right Side */}
      <div className="flex min-h-screen flex-1 flex-col">
        {/* Constant Topbar */}
        <CRMTopbar />

        {/* Only this area changes when you open CRM pages */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-[1520px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
