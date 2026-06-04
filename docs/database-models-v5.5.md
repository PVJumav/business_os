# Database Models Version 5.5

The following models were added in `backend/models/automation.py` under the `automation` schema.

## Governance And SOP

- `PolicyCategory`
- `GovernancePolicy`
- `PolicyVersion`
- `PolicyException`
- `PolicyAcknowledgement`
- `SOP`
- `SOPStep`

## Workflow, Approvals, Events, Audit

- `WorkflowTemplate`
- `WorkflowStage`
- `WorkflowInstance`
- `WorkflowTask`
- `ApprovalMatrix`
- `ApprovalRequest`
- `ApprovalAction`
- `EnterpriseEvent`
- `AuditLog`

## SLA, IAM, Compliance, Risk, KPI

- `SLAPolicy`
- `SLAInstance`
- `EscalationRule`
- `UserAccessProfile`
- `AccessReview`
- `ComplianceControl`
- `RiskRegister`
- `KPI`
- `KPIResult`
- `CorrectiveAction`

## Common Fields

Most business records include:

- UUID primary key.
- `status`.
- `created_at`.
- `updated_at`.
- `created_by`.
- `updated_by`.
- `deleted_at`.
- `deleted_by`.

The model design supports soft delete, audit logging, workflow ownership, cross-module references, and future migration into formal Alembic revisions.
