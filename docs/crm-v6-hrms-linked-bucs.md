# CRM v6 HRMS-Linked BUC Implementation Notes

## Gap Analysis Summary

- Existing CRM pages, tabs, and resource managers were preserved.
- Existing CRM tables already covered leads, accounts, contacts, opportunities, activities, tasks, quotations, LPOs, contracts, audit logs, and analytics.
- Missing v6 gaps were HRMS employee ownership, staged lead conversion, stricter quotation/LPO/won/handover workflow gates, integration events, and active-employee selectors in the CRM UI.
- Lead creation no longer auto-converts to account/contact/opportunity. Conversion is now explicit so CRM-001 through CRM-004 feed one another in sequence.
- All CRM owner, assignee, presales, approver, and handover employee references are validated against active HRMS employees.

## Implemented BUC Trace

- CRM-001 Create Lead: implemented through existing lead create APIs with HRMS active owner validation, source requirement, duplicate flagging, audit support, and no premature conversion.
- CRM-002 Assign Lead Owner: implemented through `/api/crm/leads/{id}/assign-owner` and enterprise `assign` workflow using active sales employee validation.
- CRM-003 Qualify Lead: implemented through `/api/crm/leads/{id}/qualify` with BANT scoring, qualified/disqualified state, reason support, audit log, notification, and event.
- CRM-004 Convert Lead: implemented through `/api/crm/leads/{id}/convert`; creates/links account, contact, and opportunity while carrying owner employee references forward.
- CRM-005 Create Account: owner must be an active Sales/Presales/Business Development employee; owner display names are derived from HRMS.
- CRM-006 Manage Account Team: `/api/crm/accounts/{id}/team-members` validates active HRMS employees and audits assignment.
- CRM-007 Create Contact and CRM-008 Update Contact: contacts remain account-linked and can be owned by active CRM employees.
- CRM-009 Create Opportunity: opportunity owner, presales, project manager, customer success, and technical owner references are HRMS-backed.
- CRM-010 Assign Presales Engineer: `/api/crm/opportunities/{id}/assign-presales` validates active technical/presales employees and creates follow-up task.
- CRM-011 Update Opportunity Stage: `/api/crm/opportunities/{id}/stage` audits stage changes and gates Proposal/Won/Lost requirements.
- CRM-012 Create Sales Task: task assignee and owner can be HRMS employee references.
- CRM-013 Manage Meetings and Engagements: existing CRM activities/engagements remain available in the preserved UI.
- CRM-014 Create Quotation: quote owner is an active sales employee; amount fields and opportunity linkage remain intact.
- CRM-015 Approve Quotation: `/api/crm/quotations/{id}/approve` records approver, approval date, audit, and event.
- CRM-016 Send Quotation: `/api/crm/quotations/{id}/send` requires approved/not-required approval status and records sent state.
- CRM-017 Revise Quotation: `/api/crm/quotations/{id}/revise` increments version and returns quotation to draft/pending approval path.
- CRM-018 Receive LPO: `/api/crm/opportunities/{id}/upload-lpo` stores LPO reference, validates opportunity, and queues finance/project handover signals.
- CRM-019 Convert Won Opportunity to Project: `/api/crm/opportunities/{id}/handover-to-project` requires won status, LPO/contract, and active project manager.
- CRM-020 Customer Success Handover: `/api/crm/opportunities/{id}/customer-success-handover` validates active customer success and technical owners.
- CRM-021 Opportunity Loss Management: `/api/crm/opportunities/{id}/mark-lost` requires loss reason and audits close-lost.
- CRM-022 Reassign CRM Records on Employee Exit: CRM ownership fields now use employee references, enabling offboarding reassignment checks and audit visibility.
- CRM-023 CRM Access Provisioning: `/api/crm/active-employees` exposes active CRM-eligible employees for UI owner selection.
- CRM-024 Sales Target Assignment and CRM-025 Sales Performance Tracking: existing sales target and analytics surfaces remain available and now align with employee ownership patterns.
- CRM-026 CRM Document Management: quotation/LPO/document URL fields and audit events support customer document workflow handoff.
- CRM-027 Customer Contract Tracking and CRM-028 Renewal Opportunity: existing contracts module remains linked to accounts/opportunities and CRM analytics.
- CRM-029 CRM Analytics Dashboard: `/api/crm/analytics/dashboard` provides leads, opportunities, quotation, task, won/lost, and employee-linked CRM metrics.
- CRM-030 CRM Audit and Compliance: CRM action endpoints emit audit logs and integration/notification events for lifecycle transitions.

## Verification

- Schema repair executed successfully through `backend.core.create_tables.create_tables()`.
- Backend import check passed for CRM routes and services.
- API smoke test passed for lead create -> qualify -> convert -> assign presales -> create quote -> approve -> send -> upload LPO -> mark won -> handover -> analytics.
