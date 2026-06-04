import type { Metadata } from "next";
import "../styles/globals.css";
import AppShell from "@/components/layout/AppShell";
import { AuthProvider } from "@/store/authStore";

export const metadata: Metadata = {
  title: "BusinessOS",
  description: "Enterprise Business Operating System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full" suppressHydrationWarning>
      <body className="min-h-full antialiased" suppressHydrationWarning>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
