import {
  BarChart3,
  Briefcase,
  Building2,
  CalendarDays,
  Clock,
  Contact,
  CreditCard,
  FileText,
  FolderKanban,
  LayoutDashboard,
  Settings,
  Users,
  Wallet,
  ShieldCheck,
  PackageCheck,
  KeyRound,
} from "lucide-react";

export type UserRole =
  | "admin"
  | "manager"
  | "user"
  | "hr"
  | "hr_admin"
  | "hr_manager"
  | "payroll"
  | "payroll_admin"
  | "finance_admin"
  | "accountant"
  | "cfo"
  | "security_admin";

export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  roles: UserRole[];
}

const allRoles: UserRole[] = ["admin", "manager", "user", "hr", "hr_admin", "hr_manager", "payroll", "payroll_admin", "finance_admin", "accountant", "cfo", "security_admin"];
const adminManager: UserRole[] = ["admin", "manager", "hr", "hr_admin", "hr_manager"];
const hrRoles: UserRole[] = ["admin", "manager", "hr", "hr_admin", "hr_manager"];
const payrollRoles: UserRole[] = ["admin", "payroll", "payroll_admin", "finance_admin", "accountant", "cfo"];
const securityRoles: UserRole[] = ["admin", "security_admin", "hr_admin"];

export const appNavItems: NavItem[] = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/", roles: allRoles },
  { label: "CRM", icon: Users, href: "/crm", roles: allRoles },
  { label: "HRM", icon: Building2, href: "/hrm", roles: allRoles },
  { label: "Finance", icon: CreditCard, href: "/finance", roles: allRoles },
  { label: "IAM", icon: KeyRound, href: "/iam", roles: securityRoles },
  { label: "Projects", icon: FolderKanban, href: "/projects", roles: adminManager },
  { label: "Settings", icon: Settings, href: "/settings", roles: ["admin"] },
];

export const crmNavItems: NavItem[] = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/crm", roles: allRoles },
  { label: "Leads", icon: Users, href: "/crm/leads", roles: allRoles },
  { label: "Accounts", icon: Building2, href: "/crm/accounts", roles: allRoles },
  { label: "Opportunities", icon: Briefcase, href: "/crm/opportunities", roles: allRoles },
  { label: "Activities", icon: Clock, href: "/crm/activities", roles: allRoles },
  { label: "Products & Quotes", icon: FileText, href: "/crm/quotations", roles: adminManager },
  { label: "Contracts", icon: Briefcase, href: "/crm/contracts", roles: adminManager },
  { label: "Support", icon: Contact, href: "/crm/tickets", roles: adminManager },
  { label: "Campaigns", icon: FileText, href: "/crm/campaigns", roles: adminManager },
  { label: "Approvals", icon: Settings, href: "/crm/approvals", roles: adminManager },
  { label: "Tenders", icon: FileText, href: "/crm/tenders", roles: adminManager },
  { label: "Analytics", icon: BarChart3, href: "/crm/analytics", roles: adminManager },
];

export const hrmNavItems: NavItem[] = [
  { label: "Dashboard", href: "/hrm", icon: LayoutDashboard, roles: hrRoles },
  { label: "Employees", href: "/hrm/employees", icon: Users, roles: hrRoles },
  { label: "Organization", href: "/hrm/organization", icon: Building2, roles: hrRoles },
  { label: "Leave", href: "/hrm/leave", icon: CalendarDays, roles: hrRoles },
  { label: "Attendance", href: "/hrm/attendance", icon: Clock, roles: hrRoles },
  { label: "Payroll", href: "/hrm/payroll", icon: Wallet, roles: payrollRoles },
  { label: "Recruitment", href: "/hrm/recruitment", icon: Briefcase, roles: hrRoles },
  { label: "Performance", href: "/hrm/performance", icon: BarChart3, roles: hrRoles },
  { label: "Training", href: "/hrm/training", icon: BarChart3, roles: hrRoles },
  { label: "Assets & Exit", href: "/hrm/assets", icon: PackageCheck, roles: hrRoles },
  { label: "Security", href: "/hrm/security", icon: ShieldCheck, roles: ["admin", "hr_admin"] },
  { label: "Analytics", href: "/hrm/analytics", icon: BarChart3, roles: hrRoles },
  { label: "Documents", href: "/hrm/documents", icon: FileText, roles: hrRoles },
  { label: "GRC", href: "/hrm/grc", icon: FileText, roles: hrRoles },
];

export function normalizeRole(role?: string): UserRole {
  if (
    role === "admin" ||
    role === "manager" ||
    role === "user" ||
    role === "hr" ||
    role === "hr_admin" ||
    role === "hr_manager" ||
    role === "payroll" ||
    role === "payroll_admin" ||
    role === "finance_admin" ||
    role === "accountant" ||
    role === "cfo" ||
    role === "security_admin"
  ) return role;
  return "user";
}

export function canAccessPath(role: string | undefined, pathname: string) {
  if (pathname === "/login") return true;
  const normalized = normalizeRole(role);
  const item = [...appNavItems, ...crmNavItems, ...hrmNavItems]
    .filter((nav) => pathname === nav.href || pathname.startsWith(`${nav.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0];

  return item ? item.roles.includes(normalized) : true;
}

export function filterByRole<T extends { roles: UserRole[] }>(items: T[], role?: string) {
  const normalized = normalizeRole(role);
  return items.filter((item) => item.roles.includes(normalized));
}

export function resourceAccessParts(endpoint: string, key: string) {
  const pieces = endpoint.replace(/^\/api\//, "").split("/").filter(Boolean);
  const module = pieces[0] || key.split(".")[0] || "*";
  const resource = pieces.includes("enterprise") ? pieces[pieces.indexOf("enterprise") + 1] : pieces[1] || key.split(".").pop() || "*";
  return { module, resource };
}

export function hasResourcePermission(
  user: { role?: string; permissions?: string[]; roles?: string[] } | null | undefined,
  endpoint: string,
  key: string,
  action: "read" | "create" | "update" | "delete"
) {
  const role = normalizeRole(user?.role);
  if (role === "admin") return true;
  const { module, resource } = resourceAccessParts(endpoint, key);
  const permissions = new Set(user?.permissions ?? []);
  if (
    permissions.has("*:*:*") ||
    permissions.has(`${module}:${resource}:${action}`) ||
    permissions.has(`${module}:*:${action}`) ||
    permissions.has(`*:${resource}:${action}`) ||
    permissions.has(`${module}:${resource}:*`) ||
    permissions.has(`${module}:*:*`)
  ) {
    return true;
  }
  const operationalUserWrites = role === "user" && action !== "delete" && (
    (module === "crm" && ["leads", "accounts", "contacts", "opportunities", "activities", "tasks"].includes(resource)) ||
    (module === "finance" && ["expense-claims", "purchase-requests"].includes(resource)) ||
    (module === "projects" && ["tasks", "timesheets"].includes(resource)) ||
    (module === "hrm" && ["leave", "leave-requests", "documents"].includes(resource))
  );
  if (operationalUserWrites) return true;
  return ["manager", "hr", "hr_admin", "hr_manager", "payroll", "payroll_admin", "finance_admin", "accountant", "cfo"].includes(role);
}
