# HRMS Sections 4 and 5: Organizational Assignments and Employee Documents

Business OS v5.5 implements employee-owned BUCs EMP-031 through EMP-054 inside the HRM employee drill-down workflow.

## Section 4: Organizational Assignments

Common controls:
- Employee must exist and remain the source-of-truth HRM record.
- Department and branch values are validated against active HRM masters.
- All assignment changes write `hrm_employee_assignment_history`.
- Current employee fields are synchronized for reporting, workflow routing, approvals, payroll, IAM, finance, projects and analytics.
- Cross-module integration is represented through `EnterpriseEvent` records.
- Future-dated assignment records are supported through effective dates.

Implemented APIs:
- `POST /api/hrm/employees/{id}/department` for EMP-031.
- `PUT /api/hrm/employees/{id}/department-transfer` for EMP-032.
- `POST /api/hrm/employees/{id}/branch` for EMP-033.
- `PUT /api/hrm/employees/{id}/branch-transfer` for EMP-034.
- `POST /api/hrm/employees/{id}/business-unit` for EMP-035.
- `PUT /api/hrm/employees/{id}/business-unit-transfer` for EMP-036.
- `POST /api/hrm/employees/{id}/projects` for EMP-037.
- `DELETE /api/hrm/employees/{id}/projects/{project_id}` for EMP-038.
- `POST /api/hrm/employees/{id}/teams` for EMP-039.
- `DELETE /api/hrm/employees/{id}/teams/{team_id}` for EMP-040.
- `GET /api/hrm/employees/{id}/assignments` for current assignments, history, utilization and compliance.

Key rules:
- One active department, branch, and business unit assignment is maintained.
- Project allocations cannot exceed 100 percent.
- Primary team removal requires a replacement active team.
- History is retained; no assignment history is hard deleted.

## Section 5: Employee Document Management

Common controls:
- Employee documents are employee-scoped.
- Supported upload formats: PDF, JPG, JPEG, PNG, DOCX, XLSX.
- Uploads enforce size limits, duplicate detection by file hash, versioning, verification state and archive state.
- Replacements create a new version and retain the previous version.
- Expiry tracking is created for expirable documents at 90, 60, 30 and 7 day stages.
- Verification, rejection, and archive actions create review/archive/rejection records and audit logs.

Implemented APIs:
- `POST /api/hrm/employees/{id}/documents` for EMP-041 to EMP-051.
- `GET /api/hrm/employees/{id}/documents`.
- `PUT /api/hrm/employees/{id}/documents/{document_id}`.
- `POST /api/hrm/employees/{id}/documents/{document_id}/verify` for EMP-052.
- `POST /api/hrm/employees/{id}/documents/{document_id}/reject` for EMP-053.
- `POST /api/hrm/employees/{id}/documents/{document_id}/archive` for EMP-054.
- `GET /api/hrm/employees/{id}/documents/expiring`.

Document BUC mapping:
- EMP-041 National ID.
- EMP-042 Passport.
- EMP-043 Academic Certificate.
- EMP-044 Professional Certification.
- EMP-045 Employment Contract.
- EMP-046 NDA.
- EMP-047 CV.
- EMP-048 Medical Document.
- EMP-049 Tax Document.
- EMP-050 Work Permit.
- EMP-051 Replace Existing Document.
- EMP-052 Verify Document.
- EMP-053 Reject Document.
- EMP-054 Archive Document.

## Frontend

The employee profile modal now includes:
- Organizational Assignments tab.
- Documents tab.
- Assignment widgets for department, branch, business unit, project allocation and team membership.
- Document widgets for active, pending verification, rejected and archived documents.
- Inline actions for verify, reject and archive.

## Acceptance Criteria Covered

- Models and table updater added.
- Employee-scoped APIs added.
- Assignment and document history retained.
- Audit logs and notifications/events created.
- Frontend tabs added to the existing employee drill-down experience.
- Smoke checks validate API registration and document/assignment reads.

Recommended next hardening:
- Add formal pytest fixtures for upload/version/verify/reject/archive.
- Add scheduler to process future-dated transfer activation and expiry reminders.
- Add OCR/virus scanner adapters behind the existing upload workflow.
