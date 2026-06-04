# HRMS Employee Remaining Capabilities, EMP-075 to EMP-124

Business OS v5.5 implements the remaining employee module capabilities as gap-completion endpoints, models, audit events, notifications, and integration-ready enterprise events. Existing document, payroll, benefits, IAM, reporting, movement, and offboarding modules are reused instead of duplicating whole modules inside the employee page.

## Gap Analysis

- Existing: employee master records, documents, document compliance, profile management, employment info, probation, confirmation, movement/status workflows, compensation records, benefits, clearance checklists, audit logs, notification events, analytics, reports, and IAM access profile foundations.
- Added: centralized employee compliance validation, statutory identifiers, passport/visa/work-permit/contract/certification tracking, access request/role/account lifecycle endpoints, salary history, allowance/benefit/insurance action endpoints, self-service endpoints, employee analytics/report exports, and end-to-end offboarding case workflow endpoints.
- Preserved: employee modal stays lean. Module-owned work remains linked through HRM side-nav modules such as Documents, Organization, Payroll, Compensation, Assets, GRC, Security, Reports, and Analytics.

## Implementation Checklist

- [x] EMP-075 Capture Tax PIN: `POST /api/hrm/employees/{id}/compliance/tax-pin`
- [x] EMP-076 Capture NSSF Number: `POST /api/hrm/employees/{id}/compliance/nssf`
- [x] EMP-077 Capture SHA/NHIF Number: `POST /api/hrm/employees/{id}/compliance/health-insurance`
- [x] EMP-078 Capture Passport Information: `POST /api/hrm/employees/{id}/compliance/passport`
- [x] EMP-079 Capture Visa Information: `POST /api/hrm/employees/{id}/compliance/visa`
- [x] EMP-080 Track Work Permit Expiry: `POST /api/hrm/employees/{id}/compliance/work-permit`
- [x] EMP-081 Track Contract Expiry: `POST /api/hrm/employees/{id}/compliance/contract`
- [x] EMP-082 Track Certification Expiry: `POST /api/hrm/employees/{id}/compliance/certifications`
- [x] EMP-083 Compliance Validation: `GET /api/hrm/employees/{id}/compliance`, `POST /api/hrm/employees/{id}/compliance/validate`, `GET /api/hrm/compliance/non-compliant`, `GET /api/hrm/compliance/expiring`
- [x] EMP-084 Create User Account Request: `POST /api/hrm/employees/{id}/access/account-request`
- [x] EMP-085 Assign System Role: `POST /api/hrm/employees/{id}/access/roles`
- [x] EMP-086 Update System Role: `PUT /api/hrm/employees/{id}/access/roles/{role_id}`
- [x] EMP-087 Request Additional Access: `POST /api/hrm/employees/{id}/access/request`
- [x] EMP-088 Revoke Access: `POST /api/hrm/employees/{id}/access/revoke`
- [x] EMP-089 Lock Employee Account: `POST /api/hrm/employees/{id}/access/lock`
- [x] EMP-090 Unlock Employee Account: `POST /api/hrm/employees/{id}/access/unlock`
- [x] EMP-091 Reset Employee Access: `POST /api/hrm/employees/{id}/access/reset`
- [x] EMP-092 Capture Salary Information: `POST /api/hrm/employees/{id}/compensation/salary`
- [x] EMP-093 Update Salary: `PUT /api/hrm/employees/{id}/compensation/salary`
- [x] EMP-094 Record Salary Increment: `POST /api/hrm/employees/{id}/compensation/increment`
- [x] EMP-095 Record Salary Reduction: `POST /api/hrm/employees/{id}/compensation/reduction`
- [x] EMP-096 Assign Allowances: `POST /api/hrm/employees/{id}/allowances`
- [x] EMP-097 Remove Allowances: `DELETE /api/hrm/employees/{id}/allowances/{allowance_id}`
- [x] EMP-098 Assign Benefits: `POST /api/hrm/employees/{id}/benefits`
- [x] EMP-099 Remove Benefits: `DELETE /api/hrm/employees/{id}/benefits/{benefit_id}`
- [x] EMP-100 Assign Insurance Plans: `POST /api/hrm/employees/{id}/insurance-plans`
- [x] EMP-101 View Profile: `GET /api/hrm/self-service/profile`
- [x] EMP-102 Update Personal Information: `PUT /api/hrm/self-service/profile`
- [x] EMP-103 Upload Documents: `POST /api/hrm/self-service/documents` plus existing employee document upload endpoint
- [x] EMP-104 Download Documents: existing controlled employee document download endpoint plus self-service document listing
- [x] EMP-105 View Reporting Structure: `GET /api/hrm/self-service/reporting-structure`
- [x] EMP-106 View Employment History: `GET /api/hrm/self-service/employment-history`
- [x] EMP-107 View Compensation History: `GET /api/hrm/self-service/compensation-history`
- [x] EMP-108 Submit Profile Change Request: `POST /api/hrm/self-service/profile-change-requests`
- [x] EMP-109 View Employee Dashboard: `GET /api/hrm/analytics/employees/dashboard`
- [x] EMP-110 Generate Employee Report: `GET /api/hrm/reports/employees`
- [x] EMP-111 Export Employee Data: `POST /api/hrm/reports/employees/export`
- [x] EMP-112 View Headcount Analysis: `GET /api/hrm/analytics/headcount`
- [x] EMP-113 View Workforce Demographics: `GET /api/hrm/analytics/demographics`
- [x] EMP-114 View Employee Movement Reports: `GET /api/hrm/reports/movements`
- [x] EMP-115 View Compliance Reports: `GET /api/hrm/reports/compliance`
- [x] EMP-116 View Organization Reports: `GET /api/hrm/reports/organization`
- [x] EMP-117 Initiate Separation: `POST /api/hrm/employees/{id}/offboarding/separation`
- [x] EMP-118 Initiate Clearance Workflow: `POST /api/hrm/employees/{id}/offboarding/clearance`
- [x] EMP-119 Recover Assets: `POST /api/hrm/employees/{id}/offboarding/assets/recover`
- [x] EMP-120 Revoke Access: `POST /api/hrm/employees/{id}/offboarding/access/revoke`
- [x] EMP-121 Generate Exit Documentation: `POST /api/hrm/employees/{id}/offboarding/documents/generate`
- [x] EMP-122 Archive Employee Record: `POST /api/hrm/employees/{id}/offboarding/archive`
- [x] EMP-123 Process Final Settlement: `POST /api/hrm/employees/{id}/offboarding/final-settlement`
- [x] EMP-124 Complete Offboarding: `POST /api/hrm/employees/{id}/offboarding/complete`, `GET /api/hrm/employees/{id}/offboarding/status`

## Database Models Added

- `HRMEmployeeComplianceRecord`
- `HRMEmployeeStatutoryIdentifier`
- `HRMEmployeePassportRecord`
- `HRMEmployeeVisaRecord`
- `HRMEmployeeWorkPermit`
- `HRMEmployeeContractTracking`
- `HRMEmployeeCertificationTracking`
- `HRMEmployeeAccessRequest`
- `HRMEmployeeSystemRole`
- `HRMEmployeeAccessLog`
- `HRMEmployeeAccountStatus`
- `HRMEmployeeSalaryHistory`
- `HRMEmployeeAllowance`
- `HRMEmployeeBenefitAssignment`
- `HRMEmployeeInsurancePlan`
- `HRMEmployeeReportExport`
- `HRMEmployeeOffboardingCase`
- `HRMEmployeeAssetRecovery`
- `HRMEmployeeExitDocument`
- `HRMEmployeeFinalSettlement`

## Integration Behavior

Each sensitive action writes an HRM audit log and queues enterprise events for Payroll, IAM, Finance, Assets, Compliance, Reporting, or Enterprise workflow orchestration. These events are integration-ready placeholders for production connectors.

## Validation

Representative smoke tests passed for compliance capture/validation, account request, role assignment, account lock/unlock, salary capture, allowance assignment, benefit assignment, dashboard/reporting, separation initiation, clearance, access revocation, and offboarding status.

## Pending Hardening

- Replace admin/manager role checks with final granular IAM claim enforcement once production permission claims are finalized.
- Add full binary self-service document upload screen that reuses the secure document upload endpoint.
- Add scheduled daily compliance-expiry runner to send reminders from the tracking tables; expiry statuses are already queryable and validation-ready.
