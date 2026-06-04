"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import { useAuth } from "@/hooks/useAuth";
import { canAccessPath } from "@/lib/permissions";
import { SearchProvider } from "@/store/searchStore";

export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading, isAuthenticated } = useAuth();

  const isLoginRoute = pathname === "/login";

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated && !isLoginRoute) {
      router.replace("/login");
      return;
    }
    if (isAuthenticated && !canAccessPath(user?.role, pathname)) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, isLoginRoute, pathname, router, user?.role]);

  if (isLoginRoute) {
    return <>{children}</>;
  }

  if (isLoading || !isAuthenticated || !canAccessPath(user?.role, pathname)) {
    return (
      <div className="app-canvas flex min-h-screen items-center justify-center text-sm text-slate-500">
        <div className="glass-panel rounded-lg px-5 py-4">Loading your workspace...</div>
      </div>
    );
  }

  const isWorkspaceRoute = pathname.startsWith("/crm") || pathname.startsWith("/hrm") || pathname.startsWith("/finance");

  if (isWorkspaceRoute) {
    return <SearchProvider>{children}</SearchProvider>;
  }

  return (
    <SearchProvider>
      <div className="app-canvas flex h-screen">
        <Sidebar />

        <div className="flex flex-1 flex-col overflow-hidden">
          <Topbar />

          <main className="flex-1 overflow-y-auto p-6">
            <div className="mx-auto max-w-[1520px]">
              {children}
            </div>
          </main>
        </div>
      </div>
    </SearchProvider>
  );
}
