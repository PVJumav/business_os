# BusinessOS Version 5.3 Backend

Version 5.3 builds on 5.2 and adds the Phase 1 Core Operations workflow layer across CRM, HRMS, Projects, Finance, and IAM.

## Main Lead-To-Cash Flow

1. CRM quote approval: `POST /api/phase1/integrations/crm/quotes/{quotation_id}/approve`
2. Customer quote acceptance: `POST /api/phase1/integrations/crm/quotes/{quotation_id}/accept`
3. Customer LPO upload and validation: `POST /api/phase1/integrations/crm/lpos/upload`
4. Contract generation from quote/LPO: `POST /api/phase1/integrations/crm/quotes/{quotation_id}/contract`
5. Contract activation and SLA creation: `POST /api/phase1/integrations/crm/contracts/{contract_id}/activate`
6. Closed-won opportunity orchestration: `POST /api/phase1/integrations/crm/opportunities/{opportunity_id}/closed-won`
7. Customer invoice payment and revenue recognition: `POST /api/phase1/integrations/finance/invoices/{invoice_id}/paid`
8. Project expense posting to Finance: `POST /api/phase1/integrations/projects/expenses/{expense_id}/approved`
9. Project customer signoff and final finance review: `POST /api/phase1/integrations/projects/{project_id}/signed-off`
10. SLA breach escalation to CRM: `POST /api/phase1/integrations/slas/tickets/{ticket_id}/breached`
11. Renewal opportunity generation: `POST /api/phase1/integrations/renewals/create-opportunities`

## Procurement Flow

1. Create purchase order from request: `POST /api/phase1/integrations/finance/purchase-requests/{request_id}/create-po`
2. Receive vendor invoice against PO: `POST /api/phase1/integrations/finance/purchase-orders/{po_id}/vendor-invoice`
3. Pay vendor invoice and update project cost: `POST /api/phase1/integrations/finance/vendor-invoices/{bill_id}/paid`

## HRMS and IAM Hooks

1. Provision IAM user from employee: `POST /api/phase1/integrations/hrms/employees/{employee_id}/created`
2. Disable IAM access after termination: `POST /api/phase1/integrations/hrms/employees/{employee_id}/terminated`
3. Post approved payroll summary to Finance: `POST /api/phase1/integrations/hrms/payroll-runs/{payroll_run_id}/approved`
4. Central policy check: `GET /api/phase1/integrations/policy/check?module=finance&action=approve`

## CRM LPO CRUD

Standard customer LPO endpoints are also available:

- `GET /api/crm/lpos`
- `POST /api/crm/lpos`
- `POST /api/crm/lpos/upload`
- `GET /api/crm/lpos/{lpo_id}`
- `PATCH /api/crm/lpos/{lpo_id}`
- `DELETE /api/crm/lpos/{lpo_id}`

## Reporting

- Phase 1 dashboard: `GET /api/phase1/integrations/dashboard`
- Integration events: `GET /api/phase1/integrations/events`
- CRM account 360 history: `GET /api/phase1/integrations/crm/accounts/{account_id}/history`

## Database Update

Run the table updater after switching to version 5.3:

```powershell
cd "C:\Users\PaulJuma\Downloads\Project Orion\business-os-version-5.3"
..\business-os-completed\.venv\Scripts\python.exe -m backend.core.create_tables
```
