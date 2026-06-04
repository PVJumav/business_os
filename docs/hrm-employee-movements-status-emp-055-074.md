# HRMS Employee Movements and Status Management, EMP-055 to EMP-074

Business OS v5.5 now supports employee movements and employee status workflows as auditable employee lifecycle records.

## Implemented BUCs

- EMP-055 Promote Employee: `POST /api/hrm/employees/{id}/promote`
- EMP-056 Demote Employee: `POST /api/hrm/employees/{id}/demote`
- EMP-057 Transfer Employee: `POST /api/hrm/employees/{id}/transfer`
- EMP-058 Change Job Role: `POST /api/hrm/employees/{id}/change-role`
- EMP-059 Acting Appointment: `POST /api/hrm/employees/{id}/acting-appointment`
- EMP-060 Secondment: `POST /api/hrm/employees/{id}/secondment`
- EMP-061 Internal Transfer: `POST /api/hrm/employees/{id}/internal-transfer`
- EMP-062 Temporary Assignment: `POST /api/hrm/employees/{id}/temporary-assignment`
- EMP-063 Return From Assignment: `POST /api/hrm/employees/{id}/return-from-assignment`
- EMP-064 Place On Probation: `POST /api/hrm/employees/{id}/probation/place`
- EMP-065 Confirm Probation: `POST /api/hrm/employees/{id}/probation/confirm`
- EMP-066 Extend Probation: `POST /api/hrm/employees/{id}/probation/extend`
- EMP-067 Suspend Employee: `POST /api/hrm/employees/{id}/suspend`
- EMP-068 Reinstate Employee: `POST /api/hrm/employees/{id}/reinstate`
- EMP-069 Leave Of Absence: `POST /api/hrm/employees/{id}/leave-of-absence`
- EMP-070 Return From Leave Of Absence: `POST /api/hrm/employees/{id}/return-from-leave-of-absence`
- EMP-071 Mark Inactive: `POST /api/hrm/employees/{id}/mark-inactive`
- EMP-072 Terminate Employee: `POST /api/hrm/employees/{id}/terminate`
- EMP-073 Process Retirement: `POST /api/hrm/employees/{id}/retire`
- EMP-074 Record Death In Service: `POST /api/hrm/employees/{id}/death-in-service`

## History Endpoints

- `GET /api/hrm/employees/{id}/movements`
- `GET /api/hrm/employees/{id}/status-history`

## Data Ownership

HRMS remains the source of truth for employee movement and employee status. Each action creates lifecycle history and queues downstream events for Payroll, IAM, Finance, Leave, Attendance, Projects, Assets, and Reporting.

## Database Tables

- `hrm_employee_movements`
- `hrm_employee_movement_approvals`
- `hrm_employee_status_history`
- `hrm_employee_suspension_records`
- `hrm_employee_reinstatement_records`
- `hrm_employee_leave_of_absence_records`
- `hrm_employee_retirement_records`
- `hrm_employee_death_records`
- Existing `hrm_lifecycle_events`, `hrm_employee_assignment_history`, `hrm_termination_records`, `hrm_audit_logs`, and `notification_events`

## Frontend

The employee profile Actions section now exposes compact movement and status action panels plus movement/status history tables. The employee profile remains lean; deeper module-owned records continue to live in their own HRM side-nav modules.

## Notes

Approval records are created as approved HR-admin prototype approvals. A later policy engine pass can route these through multi-level approval matrices without changing the endpoint contracts.
