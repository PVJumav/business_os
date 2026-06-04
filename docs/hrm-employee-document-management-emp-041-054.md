# HRMS Employee Document Management, EMP-041 to EMP-054

Business OS v5.5 implements employee documents as an employee-scoped, auditable document vault. The subsystem covers National ID, Passport, Academic Certificates, Professional Certifications, Employment Contract, NDA, CV, Medical Documents, Tax Documents, and Work Permit records.

## Implemented Capabilities

- Secure HR upload endpoint with document type classification, file extension validation, MIME validation, size limits, empty-file rejection, executable upload blocking, SHA-256 duplicate detection, and a virus scanning integration hook placeholder.
- Versioning: replacing an existing current document supersedes the old current version and creates a new current document/version row.
- Verification workflow: authorized HR users can verify pending documents.
- Rejection workflow: authorized HR users can reject documents with a required reason and notification event.
- Archive workflow: authorized HR users can archive documents with a required reason. Archived documents remain searchable and are excluded from active compliance calculations.
- Controlled download endpoint that logs document access and audit events instead of exposing storage paths as the primary access route.
- Expiry tracking at 90, 60, 30, and 7 days for expirable documents.
- Compliance summary, missing mandatory documents, global expiring documents, document detail, document download, and document version history endpoints.
- Confidentiality controls for HR/payroll/medical documents, with stricter access for medical documents.

## API Endpoints

- `POST /api/hrm/employees/{employee_id}/documents`
- `GET /api/hrm/employees/{employee_id}/documents`
- `GET /api/hrm/employees/{employee_id}/documents/{document_id}`
- `GET /api/hrm/employees/{employee_id}/documents/{document_id}/download`
- `PUT /api/hrm/employees/{employee_id}/documents/{document_id}`
- `POST /api/hrm/employees/{employee_id}/documents/{document_id}/replace`
- `POST /api/hrm/employees/{employee_id}/documents/{document_id}/verify`
- `POST /api/hrm/employees/{employee_id}/documents/{document_id}/reject`
- `POST /api/hrm/employees/{employee_id}/documents/{document_id}/archive`
- `GET /api/hrm/employees/{employee_id}/documents/{document_id}/versions`
- `GET /api/hrm/employees/documents/expiring`
- `GET /api/hrm/employees/documents/types`
- `GET /api/hrm/employees/{employee_id}/documents/expiring`
- `GET /api/hrm/employees/{employee_id}/documents/missing`
- `GET /api/hrm/employees/{employee_id}/documents/compliance`

## BUC Traceability

- EMP-041 National ID: mandatory, HR verification, one current version.
- EMP-042 Passport: expiry-capable, issue/expiry metadata, reminders.
- EMP-043 Academic Certificate: multiple supported through versioned document records.
- EMP-044 Professional Certification: expiry-capable and verification-capable.
- EMP-045 Employment Contract: mandatory, confidential, verification-capable.
- EMP-046 NDA: confidential and verification-capable.
- EMP-047 CV: versioned and manager-visible where policy permits.
- EMP-048 Medical Document: confidential with restricted access and access logging.
- EMP-049 Tax Document: mandatory, confidential, payroll-readiness input.
- EMP-050 Work Permit: expiry-required, verification-capable, compliance attention on expiry.
- EMP-051 Replace Document: preserves old versions and resets verification through a new current version.
- EMP-052 Verify Document: records verifier, date, review, and audit trail.
- EMP-053 Reject Document: requires reason, keeps record, creates notification and audit trail.
- EMP-054 Archive Document: soft archive with reason and audit trail.

## Frontend

The employee profile modal now includes a Documents tab with upload, compliance summary, missing-document alert, active/pending/rejected/archived counters, controlled view/download action, verification/rejection/archive actions, and a version history drawer.

## Pending Integration Hooks

- Antivirus scanning is represented by validation and storage hooks; a production scanner service can be attached before persistence.
- OCR extraction is queued as metadata text and should later be connected to an OCR worker.
- Reminder delivery is represented by expiry tracking rows and notification events; the scheduler should execute `check_employee_document_expiry_daily` when the deployment scheduler is configured.
