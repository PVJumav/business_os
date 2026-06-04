"use client";

import Link from "next/link";
import UserRegistrationPanel from "@/components/settings/UserRegistrationPanel";
import { useAuth } from "@/hooks/useAuth";

export default function SettingsPanel() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <div className="space-y-6">

      {/* General Settings */}
      <div className="bg-white rounded-2xl border p-5">

        <h3 className="text-lg font-semibold mb-4">
          System Settings
        </h3>

        <div className="grid grid-cols-2 gap-4">

          <div>
            <label className="text-sm text-slate-500">
              Company Name
            </label>

            <input
              className="w-full border rounded-xl px-4 py-3 mt-2"
              placeholder="ISOLS"
            />
          </div>

          <div>
            <label className="text-sm text-slate-500">
              Timezone
            </label>

            <input
              className="w-full border rounded-xl px-4 py-3 mt-2"
              placeholder="Africa/Nairobi"
            />
          </div>

        </div>

      </div>

      {isAdmin && <UserRegistrationPanel />}

      {isAdmin && (
        <div className="bg-white rounded-2xl border p-5">
          <h3 className="text-lg font-semibold mb-4">Admin Configuration</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <Link href="/settings/policies" className="rounded-xl border bg-slate-50 p-4 hover:bg-white">
              <p className="font-semibold text-slate-900">Organization Policies</p>
              <p className="mt-2 text-sm text-slate-500">Customize workflows, terminology, approvals, tax, compliance, automation, and reporting rules.</p>
            </Link>
            <Link href="/settings/access-rights" className="rounded-xl border bg-slate-50 p-4 hover:bg-white">
              <p className="font-semibold text-slate-900">Access Rights</p>
              <p className="mt-2 text-sm text-slate-500">Control role access by module, resource path, action, approval, export, and data scope.</p>
            </Link>
            <Link href="/settings/sequences" className="rounded-xl border bg-slate-50 p-4 hover:bg-white">
              <p className="font-semibold text-slate-900">ID Sequences</p>
              <p className="mt-2 text-sm text-slate-500">Set prefixes and counters for accounts, leads, deals, licences, projects, SLAs, invoices, and imports.</p>
            </Link>
            <Link href="/integrations" className="rounded-xl border bg-slate-50 p-4 hover:bg-white">
              <p className="font-semibold text-slate-900">Integration Gateways</p>
              <p className="mt-2 text-sm text-slate-500">Configure data gateways into AD, databases, ERP, cloud services, and customer environments.</p>
            </Link>
          </div>
        </div>
      )}

    </div>
  );
}
