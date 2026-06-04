import { FieldConfig, ResourceConfig } from "@/lib/resourceConfigs";

function cfg(key: string, title: string, description: string, resource: string, fields: FieldConfig[], workflowActions: string[] = []): ResourceConfig {
  return {
    key,
    title,
    description,
    endpoint: `/api/iam/${resource}`,
    analyticsEndpoint: `/api/iam/analytics`,
    searchFields: fields.map((field) => field.name),
    statusField: fields.find((field) => field.name === "status") ? "status" : undefined,
    workflowActions,
    fields,
  };
}

const roleSelect: Partial<FieldConfig> = { type: "select", selectEndpoint: "/api/iam/roles", selectLabel: ["role_code", "role_name"] };
const permissionSelect: Partial<FieldConfig> = { type: "select", selectEndpoint: "/api/iam/permissions", selectLabel: ["permission_code"] };
const userSelect: Partial<FieldConfig> = { type: "select", selectEndpoint: "/api/iam/users", selectLabel: ["email", "full_name"] };

export const iamConfigs: Record<string, ResourceConfig> = {
  "iam.roles": cfg("iam.roles", "Roles", "IAM-001 to IAM-004: create, update, clone, version, inherit, and deactivate system roles.", "roles", [
    { name: "role_code", label: "Role Code", required: true, table: true },
    { name: "role_name", label: "Role Name", required: true, table: true },
    { name: "module_scope", label: "Module Scope", table: true, defaultValue: "enterprise" },
    { name: "description", label: "Description", type: "textarea" },
    { name: "requires_mfa", label: "MFA Required", type: "checkbox", table: true },
    { name: "status", label: "Status", type: "select", options: ["active", "inactive", "deprecated", "deleted"], table: true, defaultValue: "active" },
  ]),
  "iam.permissions": cfg("iam.permissions", "Permissions", "IAM-005 and IAM-008: define module_action permissions and permission groups.", "permissions", [
    { name: "permission_code", label: "Permission Code", required: true, table: true },
    { name: "module", label: "Module", required: true, table: true },
    { name: "resource", label: "Resource", required: true, table: true },
    { name: "action", label: "Action", type: "select", options: ["read", "create", "update", "delete", "approve", "reject", "export", "*"], required: true, table: true },
    { name: "description", label: "Description", type: "textarea" },
    { name: "status", label: "Status", type: "select", options: ["active", "inactive"], table: true, defaultValue: "active" },
  ]),
  "iam.rolePermissions": cfg("iam.rolePermissions", "Role Permissions", "IAM-006 to IAM-007: attach and remove permissions from roles with audit history.", "role-permissions", [
    { name: "role_id", label: "Role", ...roleSelect, required: true, table: true },
    { name: "permission_id", label: "Permission", ...permissionSelect, required: true, table: true },
  ]),
  "iam.userRoles": cfg("iam.userRoles", "Employee/User Roles", "IAM-009 to IAM-011: assign, update, and revoke user roles linked to HRMS access events.", "user-roles", [
    { name: "user_id", label: "User", ...userSelect, required: true, table: true },
    { name: "role_id", label: "Role", ...roleSelect, required: true, table: true },
    { name: "status", label: "Status", type: "select", options: ["active", "revoked", "expired"], table: true, defaultValue: "active" },
  ], ["revoke-role"]),
  "iam.accessPolicies": cfg("iam.accessPolicies", "Access Policies", "IAM-020, IAM-031 to IAM-035: SoD, branch, department, project, customer, and approval limit policies.", "access-policies", [
    { name: "policy_name", label: "Policy", required: true, table: true },
    { name: "module", label: "Module", required: true, table: true },
    { name: "resource", label: "Resource", table: true },
    { name: "rules", label: "Rules JSON", type: "textarea" },
    { name: "status", label: "Status", type: "select", options: ["active", "inactive"], table: true, defaultValue: "active" },
  ]),
  "iam.delegations": cfg("iam.delegations", "Delegated Authority", "IAM-036: delegated approval authority linked to FIN-137 and HRMS reporting structure.", "delegations", [
    { name: "delegator_user_id", label: "Delegator", ...userSelect, required: true, table: true },
    { name: "delegate_user_id", label: "Delegate", ...userSelect, required: true, table: true },
    { name: "module", label: "Module", required: true, table: true },
    { name: "starts_on", label: "Starts On", type: "date", required: true },
    { name: "ends_on", label: "Ends On", type: "date", required: true, table: true },
    { name: "reason", label: "Reason", type: "textarea" },
    { name: "status", label: "Status", type: "select", options: ["active", "expired", "revoked"], table: true, defaultValue: "active" },
  ]),
  "iam.mfa": cfg("iam.mfa", "MFA", "IAM-029: enforce MFA for privileged users and finance approvers.", "mfa", [
    { name: "user_id", label: "User", ...userSelect, required: true, table: true },
    { name: "method", label: "Method", type: "select", options: ["totp", "email", "sms", "hardware_key"], table: true, defaultValue: "totp" },
    { name: "enabled", label: "Enabled", type: "checkbox", table: true },
    { name: "enforced_by_role", label: "Enforced By Role", type: "checkbox", table: true },
  ], ["enable-mfa", "disable-mfa"]),
  "iam.sessions": cfg("iam.sessions", "Sessions", "IAM-030: session timeout, concurrent session review, and device tracking.", "sessions", [
    { name: "user_id", label: "User", ...userSelect, table: true },
    { name: "ip_address", label: "IP", table: true },
    { name: "user_agent", label: "Device", type: "textarea" },
    { name: "expires_at", label: "Expires", type: "datetime-local", table: true },
    { name: "revoked_at", label: "Revoked", type: "datetime-local" },
  ]),
  "iam.auditLogs": cfg("iam.auditLogs", "Audit Logs", "IAM-037 to IAM-038: user activity and incident investigation trail.", "audit-logs", [
    { name: "actor_email", label: "Actor", table: true },
    { name: "module", label: "Module", table: true },
    { name: "action", label: "Action", table: true },
    { name: "entity_type", label: "Entity", table: true },
    { name: "summary", label: "Summary", type: "textarea" },
  ]),
  "iam.departmentAccess": cfg("iam.departmentAccess", "Department Access", "IAM-032: department-based access control.", "department-access", [
    { name: "user_id", label: "User", ...userSelect, required: true, table: true },
    { name: "department", label: "Department", required: true, table: true },
    { name: "access_level", label: "Access", type: "select", options: ["read", "write", "approve", "admin"], table: true, defaultValue: "read" },
    { name: "status", label: "Status", type: "select", options: ["active", "inactive"], table: true, defaultValue: "active" },
  ]),
  "iam.branchAccess": cfg("iam.branchAccess", "Branch Access", "IAM-031: branch-based access control.", "branch-access", [
    { name: "user_id", label: "User", ...userSelect, required: true, table: true },
    { name: "branch", label: "Branch", required: true, table: true },
    { name: "access_level", label: "Access", type: "select", options: ["read", "write", "approve", "admin"], table: true, defaultValue: "read" },
    { name: "status", label: "Status", type: "select", options: ["active", "inactive"], table: true, defaultValue: "active" },
  ]),
};

export const iamGroups = {
  access: ["iam.roles", "iam.permissions", "iam.rolePermissions", "iam.userRoles", "iam.accessPolicies"],
  controls: ["iam.delegations", "iam.departmentAccess", "iam.branchAccess", "iam.mfa"],
  audit: ["iam.sessions", "iam.auditLogs"],
};
