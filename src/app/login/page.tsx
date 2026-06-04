"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const router = useRouter();
  const { login, error, isLoading, isAuthenticated, clearError } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });

  useEffect(() => {
    if (isAuthenticated) router.replace("/");
  }, [isAuthenticated, router]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    const ok = await login(form);
    if (ok) router.replace("/");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-white p-8 shadow-2xl">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">BusinessOS</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Sign in</h1>
          <p className="mt-2 text-sm text-slate-500">
            Use the account created for you in Settings.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              required
              className="mt-1 h-11 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              required
              className="mt-1 h-11 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
            />
          </label>

          {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}

          <Button type="submit" className="w-full justify-center" disabled={isLoading}>
            {isLoading ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <div className="mt-6 rounded-xl bg-slate-50 p-4 text-xs text-slate-500">
          Roles: admin sees all modules, manager sees operational modules, user sees core CRM and dashboard views.
        </div>
      </section>
    </main>
  );
}
