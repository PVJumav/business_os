import React from "react";
import HRMSidebar from "@/components/hrm/layout/HRMSidebar";
import GlobalSearchBox from "@/components/layout/GlobalSearchBox";
import ThemeSwitcher from "@/components/layout/ThemeSwitcher";

export default function HRMLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="app-canvas grid min-h-screen lg:grid-cols-[260px_1fr]">
      <HRMSidebar />

      <div className="flex min-h-screen flex-col">
        <header className="app-topbar sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b px-6 shadow-sm backdrop-blur-xl">
          <GlobalSearchBox className="w-full max-w-2xl" />
          <ThemeSwitcher />
        </header>
        <main className="p-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
