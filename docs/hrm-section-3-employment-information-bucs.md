# HRMS Section 3: Employment Information BUCs

Business OS v5.5 implements EMP-019 through EMP-030 as traceable routes under `/api/hrm/employment-info`. All changes are linked to a valid employee, write history, create audit logs, and emit integration events for IAM, Payroll, Finance, Projects, and Analytics.

## Common Enterprise Controls

- Actors: HR Admin initiates; HR Manager, Finance, Payroll, or Compensation users approve sensitive changes.
- Blocked employee states: draft, rejected, archived, exited, blacklisted, terminated, inactive.
- Required fields: employee ID, previous value, new value, effective date, reason, initiated by, status, timestamp, audit reference, optional support document.
- Sensitive fields: job grade, salary band, cost center. These require approval before activation.
- Future-dated changes are stored as `future_pending` and do not overwrite current data until activated by approval/scheduler support.
- Historical records are written to `hrm_employee_employment_history`; active records for the same field are closed before the new one becomes active.
- Cross-module event stubs are written to `EnterpriseEvent` for IAM, Payroll, Finance, Projects, and Analytics.
- Salary band visibility is restricted to Admin, HR, Payroll, Finance, and Compensation-style roles.

## BUC Catalog

### EMP-019 Assign Job Title
- Objective: assign the first approved job title.
- Preconditions: employee exists and is eligible; title exists in `hrm_job_titles` or `hrm_positions`; title belongs to employee department/function.
- Workflow: HR selects title, effective date, reason; system validates and applies immediately unless future dated.
- API: `POST /api/hrm/employment-info/{employee_id}/job-title/assign`.
- Acceptance: employee `job_title` updated, history row active, IAM/analytics sync events emitted.

### EMP-020 Change Job Title
- Objective: change title due to promotion, lateral movement, demotion, restructuring, reassignment, or correction.
- Rules: previous title must exist; new title must differ; reason and effective date required; backdating requires approval.
- API: `POST /api/hrm/employment-info/{employee_id}/job-title/change`.
- Acceptance: previous title retained in history, new title active after approval/effective date, IAM and project review events emitted.

### EMP-021 Assign Job Grade
- Objective: assign the first job grade.
- Rules: job title normally required; grade must exist in approved grade structure; grade affects salary, benefits, IAM authority.
- API: `POST /api/hrm/employment-info/{employee_id}/job-grade/assign`.
- Approval: HR Manager.
- Acceptance: grade request approved/applied; salary band eligibility review event emitted.

### EMP-022 Change Job Grade
- Objective: change grade for promotion, demotion, restructuring, performance, or correction.
- Rules: current grade must exist; new grade differs; reason required; increases/decreases require approval.
- API: `POST /api/hrm/employment-info/{employee_id}/job-grade/change`.
- Acceptance: grade history preserved; Payroll, Benefits, IAM and Finance events emitted.

### EMP-023 Assign Salary Band
- Objective: assign first salary band.
- Rules: employee must have job grade; salary band must match grade; confidential; approval required.
- API: `POST /api/hrm/employment-info/{employee_id}/salary-band/assign`.
- Acceptance: salary band hidden unless authorized; Payroll/Finance notified after approval.

### EMP-024 Update Salary Band
- Objective: update salary band due to promotion, market review, compensation review, restructuring, or correction.
- Rules: mandatory approval, reason, effective date, budget review event.
- API: `POST /api/hrm/employment-info/{employee_id}/salary-band/update`.
- Acceptance: old salary band retained; new band active only after approval.

### EMP-025 Assign Cost Center
- Objective: assign employee cost center for budget ownership and expense allocation.
- Rules: employee must be active/probation/onboarded; cost center must exist in HRM or Finance and be active.
- API: `POST /api/hrm/employment-info/{employee_id}/cost-center/assign`.
- Approval: Finance.
- Acceptance: Finance, Payroll and Analytics events emitted.

### EMP-026 Change Cost Center
- Objective: move employee cost allocation due to transfer, restructuring, project reassignment, or correction.
- Rules: current cost center exists; new cost center active; Finance approval required.
- API: `POST /api/hrm/employment-info/{employee_id}/cost-center/change`.
- Acceptance: historical allocation retained; active payroll/project allocation review events emitted.

### EMP-027 Assign Reporting Manager
- Objective: assign initial direct reporting manager.
- Rules: manager must be active; self-manager and circular hierarchy blocked.
- API: `POST /api/hrm/employment-info/{employee_id}/reporting-manager/assign`.
- Acceptance: `supervisor_id` updated, manager assignment active, IAM approval chain event emitted.

### EMP-028 Change Reporting Manager
- Objective: change line manager due to transfer, restructuring, resignation, promotion, or correction.
- Rules: current manager must exist unless correction; new manager active and different; circular hierarchy blocked; backdated change approval.
- API: `POST /api/hrm/employment-info/{employee_id}/reporting-manager/change`.
- Acceptance: old manager assignment closed, new manager active, workflow reassignment events emitted.

### EMP-029 Assign Functional Manager
- Objective: assign dotted-line functional manager such as technical lead or practice lead.
- Rules: manager active; scope required by policy; does not replace reporting manager.
- API: `POST /api/hrm/employment-info/{employee_id}/functional-manager/assign`.
- Acceptance: functional manager and scope stored; project/timesheet/performance events emitted.

### EMP-030 Change Functional Manager
- Objective: change functional manager.
- Rules: current functional manager exists unless correction; new manager active and different; authority scope reviewed.
- API: `POST /api/hrm/employment-info/{employee_id}/functional-manager/change`.
- Acceptance: previous functional manager retained; active workflows receive sync events.

## Data Model

- `hrm_job_titles`
- `hrm_salary_bands`
- `hrm_employee_employment_info`
- `hrm_employee_employment_history`
- `hrm_employee_manager_assignments`
- `hrm_employment_change_requests`
- `hrm_employment_approvals`
- `hrm_employment_audit_logs`

## Tests And Acceptance

Smoke-tested requirements:
- Backend imports successfully.
- Table updater creates new employment information structures.
- Employee employment info read endpoint returns current, pending, and history data.
- Individual BUC route structure is registered.

Recommended next hardening:
- Add scheduler to activate `future_pending` changes on effective date.
- Add formal pytest coverage for each BUC route with seeded master data.
- Add role/permission table seeding for `employment_info.*` permission labels.
