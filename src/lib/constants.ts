export const APP_NAME = "BusinessOS";

export const NAV_ITEMS = [
  { label: "Dashboard", href: "/" },
  { label: "CRM", href: "/crm" },
  { label: "Leads", href: "/leads" },
  { label: "Deals", href: "/deals" },
  { label: "Projects", href: "/projects" },
  { label: "HRM", href: "/hrm" },
  { label: "Finance", href: "/finance" },
  { label: "Analytics", href: "/analytics" },
  { label: "AI Assistant", href: "/ai" },
  { label: "Settings", href: "/settings" },
] as const;

export const DEAL_STAGES = [
  "Lead Qualification",
  "Proposal Sent",
  "Negotiation",
  "Closed Won",
  "Closed Lost",
] as const;

export const API_BASE_URL = "";
