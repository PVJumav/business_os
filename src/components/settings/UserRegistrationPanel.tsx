"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import { authService } from "@/services/auth.service";

export default function UserRegistrationPanel() {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "user",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setMessage(null);
    setError(null);

    try {
      const user = await authService.register(form);
      setMessage(`Created user ${user.full_name} (${user.email})`);
      setForm({ full_name: "", email: "", password: "", role: "user" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register user");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold">Register User</h3>
      <p className="mt-1 text-sm text-slate-500">
        Create login accounts for users who need access to BusinessOS.
      </p>

      <form onSubmit={submit} className="mt-5 grid gap-4 md:grid-cols-2">
        <label>
          <span className="text-sm font-medium text-slate-700">Full Name</span>
          <input
            value={form.full_name}
            onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
            required
            className="mt-1 h-10 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
          />
        </label>

        <label>
          <span className="text-sm font-medium text-slate-700">Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            required
            className="mt-1 h-10 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
          />
        </label>

        <label>
          <span className="text-sm font-medium text-slate-700">Password</span>
          <input
            type="password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            required
            minLength={6}
            className="mt-1 h-10 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
          />
        </label>

        <label>
          <span className="text-sm font-medium text-slate-700">Role</span>
          <select
            value={form.role}
            onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}
            className="mt-1 h-10 w-full rounded-xl border px-3 text-sm outline-none focus:border-blue-500"
          >
            <option value="admin">Admin</option>
            <option value="manager">Manager</option>
            <option value="user">User</option>
          </select>
        </label>

        <div className="md:col-span-2">
          <Button type="submit" disabled={isSaving}>
            {isSaving ? "Creating..." : "Create User"}
          </Button>
        </div>
      </form>

      {message && <p className="mt-4 rounded-xl bg-green-50 p-3 text-sm text-green-700">{message}</p>}
      {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    </section>
  );
}
