# HRMS Recruitment / ATS Automation REC-001 to REC-030

## Gap Analysis

The existing Recruitment module was a generic CRUD resource over `hrm_recruitment`. It could store candidate/job fields, but it did not enforce a requisition-to-opening-to-application workflow, did not expose a Successful Applicants window, and did not convert accepted candidates into employee records automatically.

Business OS v5.5 adds an ATS automation layer while preserving the existing `hrm_recruitment` table and generic HRM recruitment resource.

## Implemented Checklist

- [x] REC-001 Create Job Requisition
- [x] REC-002 Approve Job Requisition
- [x] REC-003 Create Job Opening
- [x] REC-004 Publish Job Opening
- [x] REC-005 Receive Candidate Application
- [x] REC-006 Parse Candidate CV
- [x] REC-007 Candidate Profile Creation
- [x] REC-008 Application Screening
- [x] REC-009 Candidate Shortlisting
- [x] REC-010 Schedule Interview
- [x] REC-011 Assign Interview Panel
- [x] REC-012 Conduct Interview
- [x] REC-013 Submit Interview Feedback
- [x] REC-014 Score and Rank Candidates
- [x] REC-015 Background / Compliance Check
- [x] REC-016 Generate Offer Letter
- [x] REC-017 Approve Offer Letter
- [x] REC-018 Send Offer to Candidate
- [x] REC-019 Candidate Accepts Offer
- [x] REC-020 Candidate Rejects Offer
- [x] REC-021 Mark Candidate as Successful Applicant
- [x] REC-022 Successful Applicants Window
- [x] REC-023 Convert Successful Applicant to Employee
- [x] REC-024 Trigger Employee Onboarding
- [x] REC-025 Recruitment Pipeline Analytics
- [x] REC-026 Recruitment Document Management
- [x] REC-027 Talent Pool Management
- [x] REC-028 Rehire Candidate Processing
- [x] REC-029 Recruitment Approval Workflow
- [x] REC-030 Recruitment Integration Events

## Backend

New and extended models:

- `HRMRecruitment`
- `HRMJobRequisition`
- `HRMJobOpening`
- `HRMCandidateDocument`
- `HRMInterview`
- `HRMInterviewFeedback`
- `HRMOfferLetter`
- `HRMCandidateEmployeeConversion`
- `HRMRecruitmentAuditLog`

Key endpoints:

- `POST /api/hrm/recruitment/requisitions`
- `POST /api/hrm/recruitment/requisitions/{id}/approve`
- `POST /api/hrm/recruitment/openings`
- `POST /api/hrm/recruitment/openings/{id}/publish`
- `POST /api/hrm/recruitment/applications`
- `POST /api/hrm/recruitment/applications/{id}/screen`
- `POST /api/hrm/recruitment/applications/{id}/shortlist`
- `POST /api/hrm/recruitment/interviews`
- `POST /api/hrm/recruitment/interviews/{id}/feedback`
- `POST /api/hrm/recruitment/offers`
- `POST /api/hrm/recruitment/offers/{id}/approve`
- `POST /api/hrm/recruitment/offers/{id}/send`
- `POST /api/hrm/recruitment/offers/{id}/accept`
- `GET /api/hrm/recruitment/successful-applicants`
- `POST /api/hrm/recruitment/successful-applicants/{id}/convert-to-employee`
- `POST /api/hrm/recruitment/successful-applicants/bulk-convert`
- `GET /api/hrm/recruitment/analytics`

## Conversion Logic

Successful applicant conversion maps candidate and offer data into `HRMEmployee`, generates an immutable employee number through the existing EMP-002 sequence service, creates employment type and probation records where applicable, migrates recruitment documents into employee documents, and triggers:

- Payroll profile creation
- IAM account request
- Onboarding tasks
- Finance cost center mapping
- Asset request
- Leave balances and readiness
- Notifications
- Audit logs
- Integration events

Duplicate prevention checks existing employees by email, phone, National ID, and passport number.

## Frontend

The Recruitment page now uses `RecruitmentAutomationWorkspace`, which adds:

- ATS metrics
- Create and approve requisition action
- Create and publish opening action
- Receive application action
- Pipeline progression action
- Successful Applicants window
- Convert to Employee action
- Existing enterprise recruitment records below the automation panel

## Known Limitations / Next Hardening

- CV parsing is a structured placeholder with confidence metadata; external parser integration can be added later.
- Permission checks currently use the existing admin/manager role gate and should be expanded into the named recruitment permissions when the central RBAC matrix is finalized.
- Offer document generation stores offer metadata; branded PDF generation can be layered on top.
- Rehire detection is handled by duplicate matching today; a richer EMP-008 eligibility workflow can be linked when rehire history policy is finalized.
