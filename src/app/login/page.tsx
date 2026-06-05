"use client";

import { useEffect, useState } from "react";
import Script from "next/script";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
const githubClientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;

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
  const { login, loginWithGoogle, loginWithGithub, register, error, isLoading, isAuthenticated, clearError } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    username: "",
  });

  useEffect(() => {
    if (isAuthenticated) router.replace("/");
  }, [isAuthenticated, router]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("github_code") || params.get("code");
    const state = params.get("state");
    const expectedState = sessionStorage.getItem("businessos_github_oauth_state");
    if (!code || !state || state !== expectedState) return;

    sessionStorage.removeItem("businessos_github_oauth_state");
    window.history.replaceState({}, document.title, window.location.pathname);
    clearError();
    loginWithGithub(code, `${window.location.origin}/login`).then((ok) => {
      if (ok) router.replace("/");
    });
  }, [clearError, loginWithGithub, router]);

  async function submitLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    setNotice(null);
    const ok = await login({ email: form.email, password: form.password });
    if (ok) router.replace("/");
  }

  async function submitRegister(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearError();
    setNotice(null);
    const ok = await register({
      full_name: form.full_name,
      username: form.username || undefined,
      email: form.email,
      password: form.password,
    });
    if (ok) {
      setMode("login");
      setNotice("Account created. Sign in with your username or email to continue.");
      setForm((current) => ({ ...current, password: "" }));
    }
  }

  function switchMode(nextMode: "login" | "register") {
    clearError();
    setNotice(null);
    setMode(nextMode);
  }

  function startGithubLogin() {
    if (!githubClientId || typeof window === "undefined") return;
    clearError();
    setNotice(null);
    const state = crypto.randomUUID();
    sessionStorage.setItem("businessos_github_oauth_state", state);
    const params = new URLSearchParams({
      client_id: githubClientId,
      redirect_uri: `${window.location.origin}/login`,
      scope: "read:user user:email",
      state,
    });
    window.location.href = `https://github.com/login/oauth/authorize?${params.toString()}`;
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
          <h1 className="mt-2 text-3xl font-bold text-slate-950">
            {mode === "login" ? "Sign in" : "Create account"}
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            {mode === "login"
              ? "Use your email, username, or Google account."
              : "Register with a username and password. The first account becomes admin."}
          </p>
        </div>

        <form onSubmit={mode === "login" ? submitLogin : submitRegister} className="space-y-4">
          {mode === "register" && (
            <>
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
            </>
          )}

          <label className="block">
            <span className="text-sm font-medium text-slate-700">
              {mode === "login" ? "Email or username" : "Email"}
            </span>
            <input
              type={mode === "login" ? "text" : "email"}
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

          {notice && <p className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
          {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}

          <Button type="submit" className="w-full justify-center" disabled={isLoading}>
            {isLoading ? (mode === "login" ? "Signing in..." : "Creating account...") : mode === "login" ? "Sign in" : "Create account"}
          </Button>
        </form>

        {mode === "login" && googleClientId && (
          <div className="mt-4">
            <div id="google-sign-in" className="flex justify-center" />
          </div>
        )}

        {mode === "login" && githubClientId && (
          <Button
            type="button"
            variant="secondary"
            className="mt-3 w-full justify-center"
            disabled={isLoading}
            onClick={startGithubLogin}
          >
            Sign in with GitHub
          </Button>
        )}

        <p className="mt-5 text-center text-sm text-slate-600">
          {mode === "login" ? "No account yet?" : "Already have an account?"}{" "}
          <button
            type="button"
            onClick={() => switchMode(mode === "login" ? "register" : "login")}
            className="font-semibold text-blue-700 hover:text-blue-900"
          >
            {mode === "login" ? "Create one" : "Sign in"}
          </button>
        </p>

        <div className="mt-6 rounded-xl bg-slate-50 p-4 text-xs text-slate-500">
          {mode === "login"
            ? "The first registered account becomes the system admin. Later accounts start as standard users."
            : "After creation, sign in manually so the session starts from the approved login flow."}
        </div>
      </section>
    </main>
  );
}
