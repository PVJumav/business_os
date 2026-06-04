"use client";

import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import { useState } from "react";
import { Menu } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(true);

  return (
    <div className="h-screen flex bg-slate-100 overflow-hidden">

      {/* SIDEBAR (responsive) */}
      <div className={`${open ? "block" : "hidden"} md:block`}>
        <Sidebar />
      </div>

      {/* MAIN */}
      <div className="flex-1 flex flex-col">

        {/* TOPBAR */}
        <div className="flex items-center gap-3">
          
          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 ml-3"
            onClick={() => setOpen(!open)}
          >
            <Menu />
          </button>

          <Topbar />
        </div>

        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>

      </div>

    </div>
  );
}