"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Script from "next/script";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

type GoogleIdentity = {
  accounts?: {
    id?: {
      initialize: (options: {
        client_id: string;
        callback: (response: { credential?: string }) => void | Promise<void>;
      }) => void;
      renderButton: (
        element: HTMLElement | null,
        options: { theme: string; size: string; width: number }
      ) => void;
    };
  };
};

export default function LoginPage() {
  const router = useRouter();
  const { login, loginWithGoogle, error, isLoading, isAuthenticated, clearError } = useAuth();
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

  function initializeGoogle() {
    if (!googleClientId || typeof window === "undefined") return;
    const google = (window as typeof window & { google?: GoogleIdentity }).google;
    if (!google?.accounts?.id) return;
    google.accounts.id.initialize({
      client_id: googleClientId,
      callback: async (response: { credential?: string }) => {
        if (!response.credential) return;
        clearError();
        const ok = await loginWithGoogle(response.credential);
        if (ok) router.replace("/");
      },
    });
    google.accounts.id.renderButton(document.getElementById("google-sign-in"), {
      theme: "outline",
      size: "large",
      width: 384,
    });
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      {googleClientId && (
        <Script src="https://accounts.google.com/gsi/client" async defer onLoad={initializeGoogle} />
      )}
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-white p-8 shadow-2xl">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">BusinessOS</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Sign in</h1>
          <p className="mt-2 text-sm text-slate-500">
            Use your email, username, or Google account.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email or username</span>
            <input
              type="text"
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

        {googleClientId && (
          <div className="mt-4">
            <div id="google-sign-in" className="flex justify-center" />
          </div>
        )}

        <p className="mt-5 text-center text-sm text-slate-600">
          No account yet?{" "}
          <Link href="/register" className="font-semibold text-blue-700 hover:text-blue-900">
            Create one
          </Link>
        </p>

        <div className="mt-6 rounded-xl bg-slate-50 p-4 text-xs text-slate-500">
          The first registered account becomes the system admin. Later accounts start as standard users.
        </div>
      </section>
    </main>
  );
}
