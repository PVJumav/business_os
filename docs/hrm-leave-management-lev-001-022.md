# HRMS Leave Management, LEV-001 to LEV-022

Business OS v5.5 now extends the existing HRM leave module from basic CRUD into an enterprise leave workflow with calculation, balance, approval, policy, holiday, calendar, payroll/attendance impact, audit, notification, and integration-event support.

## Gap Analysis

- Existing: `HRMLeave`, leave balances, leave types, leave policies, holidays, basic CRUD API, generic HRM leave frontend module.
- Added: reusable leave calculation service, request workflow endpoints, manager/HR approval history, request day records, balance transactions, adjustments, carry-forward, encashment, recall, cancellation, extension, calendar events, public holiday CRUD, reports/export, and a live leave application workspace.
- Reused: employee lifecycle and leave-of-absence status integration, existing notification events, enterprise integration events, HRM audit pattern, HRM employees, documents, attendance/payroll status fields, and existing ResourceManager leave admin screens.

## Implementation Checklist

- [x] LEV-001 Apply for Annual Leave
- [x] LEV-002 Apply for Sick Leave
- [x] LEV-003 Apply for Maternity Leave
- [x] LEV-004 Apply for Paternity Leave
- [x] LEV-005 Apply for Compassionate Leave
- [x] LEV-006 Apply for Study Leave
- [x] LEV-007 Apply for Unpaid Leave
- [x] LEV-008 Apply for Leave of Absence
- [x] LEV-009 Cancel Leave Request
- [x] LEV-010 Manager Approves Leave
- [x] LEV-011 HR Reviews Leave
- [x] LEV-012 Reject Leave Request
- [x] LEV-013 Recall Employee From Leave
- [x] LEV-014 Extend Approved Leave
- [x] LEV-015 View Leave Balance
- [x] LEV-016 Adjust Leave Balance
- [x] LEV-017 Carry Forward Leave
- [x] LEV-018 Leave Encashment
- [x] LEV-019 Leave Calendar Management
- [x] LEV-020 Generate Leave Reports
- [x] LEV-021 Public Holiday Configuration
- [x] LEV-022 Leave Policy Assignment

## Core APIs

- `POST /api/hrm/leave/calculate`
- `POST /api/hrm/leave/requests`
- `GET /api/hrm/leave/requests`
- `GET /api/hrm/leave/requests/{id}`
- `POST /api/hrm/leave/requests/{id}/submit`
- `POST /api/hrm/leave/requests/{id}/approve`
- `POST /api/hrm/leave/requests/{id}/hr-review`
- `POST /api/hrm/leave/requests/{id}/reject`
- `POST /api/hrm/leave/requests/{id}/cancel`
- `POST /api/hrm/leave/requests/{id}/recall`
- `POST /api/hrm/leave/requests/{id}/extend`
- `GET /api/hrm/leave/balances/{employee_id}`
- `POST /api/hrm/leave/balances/{employee_id}/adjust`
- `POST /api/hrm/leave/carry-forward/run`
- `POST /api/hrm/leave/encashments`
- `GET /api/hrm/leave/calendar`
- `GET /api/hrm/leave/reports`
- `POST /api/hrm/leave/reports/export`
- `GET /api/hrm/leave/policies`
- `POST /api/hrm/leave/policies`
- `PUT /api/hrm/leave/policies/{id}`
- `POST /api/hrm/leave/policies/{id}/assign`
- `GET /api/hrm/leave/public-holidays`
- `POST /api/hrm/leave/public-holidays`
- `PUT /api/hrm/leave/public-holidays/{id}`
- `DELETE /api/hrm/leave/public-holidays/{id}`

## Calculation Coverage

- Calendar days
- Working days
- Weekend exclusion
- Public holiday exclusion
- Half-day calculation
- Return-to-work date
- Balance before and after
- Payroll paid/unpaid impact
- Attendance exclusion impact
- Overlap validation
- Backdating, half-day, notice, active employee, and balance validation

## Integration Events

The module queues enterprise events for `leave.request.created`, `leave.request.submitted`, `leave.request.approved`, `leave.request.rejected`, `leave.request.cancelled`, `leave.request.recalled`, `leave.request.extended`, `leave.balance.adjusted`, `leave.balance.carried_forward`, `leave.encashment.approved`, `leave.policy.assigned`, and `public.holiday.created`.

## Frontend

`/hrm/leave` now opens a live leave workspace with:

- Apply leave form
- Live calculation preview
- Request list and quick manager approval
- Balance cards
- Calendar/holiday counts
- Reports export entry point
- Existing admin module panels for policies, balances, holidays, carry-forward, and related records

## Validation

Smoke-tested:

- Policy creation and assignment
- Live calculation
- Leave request creation
- Manager approval
- Balance deduction
- Leave request detail
- Leave balances
- Calendar
- Reports

## Pending Hardening

- Replace current admin/manager permission shortcuts with final granular IAM permission claims.
- Add background schedulers for accrual, year-end carry-forward, expiry reminders, and status sync.
- Deepen leave-type-specific eligibility checks where local legal policy rules are finalized.
