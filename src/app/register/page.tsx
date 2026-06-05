"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, error, isLoading, isAuthenticated, clearError } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    username: "",
    email: "",
    password: "",
  });

  useEffect(() => {
    if (isAuthenticated) router.replace("/");
  }, [isAuthenticated, router]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    const ok = await register({
      full_name: form.full_name,
      username: form.username || undefined,
      email: form.email,
      password: form.password,
    });
    if (ok) router.replace("/login");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-white p-8 shadow-2xl">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">BusinessOS</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Create account</h1>
          <p className="mt-2 text-sm text-slate-500">
            Register with a username and password. After creating the account, sign in manually.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Full name</span>
            <input
              type="text"
              value={form.full_name}
              onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
              required
              className="mt-1 h-11 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Username</span>
            <input
              type="text"
              value={form.username}
              onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
              minLength={3}
              className="mt-1 h-11 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
            />
          </label>

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
              minLength={6}
              className="mt-1 h-11 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
            />
          </label>

          {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}

          <Button type="submit" className="w-full justify-center" disabled={isLoading}>
            {isLoading ? "Creating account..." : "Create account"}
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-blue-700 hover:text-blue-900">
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
