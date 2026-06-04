# Business OS Version 5.5 Framework

Business OS 5.5 adds an enterprise automation foundation on top of CRM, HRM, Projects, Finance, and IAM.

## Core Platform Capabilities

- Governance policy register and policy exceptions.
- SOP register with department ownership and steps.
- Workflow templates and workflow instances.
- Approval matrix and approval requests.
- Enterprise event bus records for cross-module triggers.
- Immutable-style audit log records.
- SLA policy, SLA instance, and escalation structures.
- IAM access profiles and access reviews.
- Compliance controls, risk register, KPIs, KPI results, and corrective actions.

## Source Of Truth

- HRM owns employees, departments, employment lifecycle, attendance, leave, payroll calculations, skills, and manager hierarchy.
- CRM owns accounts, contacts, leads, opportunities, quotations, LPOs, contracts, and customer-facing commercial history.
- Projects owns implementation execution, project teams, milestones, tasks, SLAs, license delivery, project risks, and signoff.
- Finance owns invoices, payments, expenses, budgets, journals, financial periods, purchase orders, and revenue reporting.
- IAM owns users, roles, permissions, access profiles, sessions, API keys, and access reviews.
- Automation owns policies, SOPs, workflow orchestration, approvals, enterprise events, audit logs, SLA timers, compliance, risk, KPIs, and corrective actions.

## Enforced Rules Added In The Service Layer

- Duplicate governance policies and SOPs are blocked by code.
- Workflow status transitions must use recognized states.
- Workflows cannot close while pending workflow tasks exist.
- Approval actions block self-approval where submitter and approver match.
- SLA instances are calculated from SLA policy response and resolution timers.
- Sensitive create/update/delete/workflow/approval operations write audit events.
