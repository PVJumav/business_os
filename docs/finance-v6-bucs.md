# Finance v6 BUC Implementation Notes

## Architecture

Finance now builds on the existing Business OS Finance resources instead of creating a separate module. The implementation keeps the current side navigation and resource pages, then adds explicit BUC action endpoints, formulas, audit logs, and CRM/HRMS integration sync paths.

Primary flow alignment:

- CRM -> Finance -> Projects
- HRMS -> Attendance/Payroll -> Finance
- Documents provide finance evidence.
- GRC/audit controls are recorded through finance audit trails and integration events.

## Implemented BUC Coverage

- FIN-001 to FIN-010: `/api/finance/control-center` provides dashboard KPIs, cash position, revenue forecast, budget utilization, AR/AP, tax exposure, project profitability, and approval queue.
- FIN-011 to FIN-018: General Ledger chart of accounts and accounting periods are implemented through exact `/api/finance/general-ledger/...` endpoints with account-code uniqueness, valid account types, parent hierarchy validation, circular-reference blocking, deactivate-only controls, open/close/reopen period workflows, and audit logs.
- FIN-019 to FIN-025: double-entry journals, source-system auto journals, posting, reversal, trial balance, balance sheet, profit and loss, and cash flow are implemented through the GL posting engine. Reports read posted journals only, and posting requires active accounts, open/reopened periods, and balanced debits/credits.
- FIN-026 to FIN-032: cost center create/update/assignment/allocation/expense tracking and department/branch cost reporting are implemented through exact `/api/finance/cost-center-management/...` endpoints with HRMS active-employee validation, historical assignment rows, allocation percentages totaling 100%, and audit logs.
- FIN-033 to FIN-042: Journal Management is implemented through exact `/api/finance/journals`, `/api/finance/recurring-journals`, `/api/finance/accrual-journals`, `/api/finance/adjustment-journals`, `/api/finance/fx-journals`, and `/api/finance/intercompany-journals` endpoints. Manual journals save as draft, approval validates balance, posting requires approved status, reversals require a reason, FX journals calculate base amount from exchange rate, and intercompany journals create reciprocal balanced lines.
- FIN-043 to FIN-055: Accounts Payable is implemented through exact vendor, onboarding, verification, supplier invoice, PO match, GRN match, approval, rejection, payment schedule/process/reverse, reconciliation, and aging endpoints. Approved supplier invoices generate AP liability journals, processed payments generate AP settlement journals, and payment reversals generate reversing AP journals.
- FIN-056 to FIN-067: Accounts Receivable is implemented through exact `/api/finance/ar/...` endpoints for CRM-linked customer billing profiles, won-opportunity invoice generation, invoice approval, sending, customer payments, payment allocation, partial payments, credit/debit notes, customer statements, collections, and AR aging. Invoice approval, customer payment, credit notes, and debit notes generate balanced GL journals.
- FIN-068 to FIN-076: Expense Management is implemented through exact `/api/finance/expenses...` endpoints for active-employee expense submission, budget validation, approval, rejection, reimbursement, mileage, per diem, travel calculation, and expense audit flags. Approved reimbursements generate balanced GL journals.
- FIN-077 to FIN-087: Budget Management is implemented through exact budget create/approve/revise/transfer/consumption/variance endpoints, with department, project, cost-center, salary/procurement-ready classifications, budget-owner references, consumption formulas, remaining budget checks, and green/amber/red variance status rules.
- FIN-088 to FIN-099: Procurement is implemented through exact `/api/finance/procurement/...` endpoints for employee PRs, manager approval, procurement review, RFQs, vendor scoring, vendor selection, PO creation/approval, GRNs, service acceptance, 3-way matching, and procurement reporting.
- FIN-100 to FIN-107: Bank & Cash is implemented through exact `/api/finance/bank-cash/...` endpoints for bank accounts, cash accounts, bank reconciliation, cash forecasting, cash transfers, petty cash, replenishment, and cash-flow projection. Cash transfers and replenishments generate balanced GL journals.
- FIN-108 to FIN-116: Tax Management is implemented through exact `/api/finance/tax/...` endpoints for tax type, VAT, WHT, PAYE configuration, tax validation, versioned tax calculations, filing preparation, tax reporting, and audit support.
- FIN-117 to FIN-126: Fixed Assets is implemented through exact `/api/finance/assets/...` endpoints for procurement-sourced acquisition, registration, categorization, assignment, transfer, revaluation, disposal, retirement, depreciation, and asset register reporting. Asset acquisition generates a balanced GL journal.
- FIN-127 to FIN-135: Project Finance is implemented through exact `/api/finance/project-finance/...` endpoints for CRM won-opportunity financial profiles, budget allocation, resource costing, cost/revenue tracking, billing, profitability, forecasting, and financial closure.
- FIN-136 to FIN-141: approval matrix resources, delegation/escalation/emergency decision states, multi-level fields, and audit trail are implemented.
- FIN-142 to FIN-150: finance document upload, invoice/vendor contract/PO/GRN/bank/tax document categories, versioning, archive, retention, and file retrieval are implemented.

## Critical Integrations

- CRM approved quotation creates deferred revenue forecast through `/api/finance/integrations/crm/sync`.
- CRM LPO received creates finance integration events for pending revenue and project initiation.
- CRM won opportunity creates a customer invoice, project financial profile, budget baseline, and revenue tracking.
- CRM customer contract creates deferred revenue and renewal forecast integration events.
- HRMS/payroll sync updates salary budget actuals and finance expense/posting records through `/api/finance/integrations/hrms/sync`.

## Formula Endpoints

- General Ledger: `/api/finance/general-ledger/journals`, `/api/finance/general-ledger/journals/{journal_id}/post`, `/api/finance/general-ledger/journals/{journal_id}/reverse`, `/api/finance/general-ledger/journals/auto-generate`
- GL reports: `/api/finance/general-ledger/reports/trial-balance`, `/api/finance/general-ledger/reports/balance-sheet`, `/api/finance/general-ledger/reports/profit-loss`, `/api/finance/general-ledger/reports/cash-flow`
- Cost centers: `/api/finance/cost-center-management/cost-centers`, `/api/finance/cost-center-management/allocations`, `/api/finance/cost-center-management/reports/departments`, `/api/finance/cost-center-management/reports/branches`
- Journal Management: `/api/finance/journals`, `/api/finance/journals/{journal_id}/approve`, `/api/finance/journals/{journal_id}/reject`, `/api/finance/journals/{journal_id}/post`, `/api/finance/journals/{journal_id}/reverse`, `/api/finance/recurring-journals`, `/api/finance/accrual-journals`, `/api/finance/adjustment-journals`, `/api/finance/fx-journals`, `/api/finance/intercompany-journals`
- Accounts Payable: `/api/finance/vendors`, `/api/finance/vendors/{vendor_id}/verify`, `/api/finance/vendor-onboarding`, `/api/finance/ap/invoices`, `/api/finance/ap/invoices/{bill_id}/match-po`, `/api/finance/ap/invoices/{bill_id}/match-grn`, `/api/finance/ap/invoices/{bill_id}/approve`, `/api/finance/ap/invoices/{bill_id}/reject`, `/api/finance/ap/payments/schedule`, `/api/finance/ap/payments/process`, `/api/finance/ap/payments/reverse`, `/api/finance/ap/vendor-reconciliations`, `/api/finance/ap/aging`
- Accounts Receivable: `/api/finance/ar/customers`, `/api/finance/ar/invoices`, `/api/finance/ar/invoices/{invoice_id}/approve`, `/api/finance/ar/invoices/{invoice_id}/send`, `/api/finance/ar/payments`, `/api/finance/ar/payments/allocate`, `/api/finance/ar/credit-notes`, `/api/finance/ar/debit-notes`, `/api/finance/ar/customers/{account_id}/statement`, `/api/finance/ar/collections/run`, `/api/finance/ar/aging`
- Expense Management: `/api/finance/expenses`, `/api/finance/expenses/{expense_id}/budget-validation`, `/api/finance/expenses/{expense_id}/approve`, `/api/finance/expenses/{expense_id}/reject`, `/api/finance/expenses/{expense_id}/reimburse`, `/api/finance/expenses/calculate`, `/api/finance/expenses/audit`
- Budget Management: `/api/finance/budgets`, `/api/finance/budgets/{budget_id}/approve`, `/api/finance/budgets/{budget_id}/revise`, `/api/finance/budgets/{budget_id}/transfer`, `/api/finance/budgets/{budget_id}/consumption`, `/api/finance/budget-variance`
- Procurement: `/api/finance/procurement/purchase-requests`, `/api/finance/procurement/purchase-requests/{request_id}/manager-approval`, `/api/finance/procurement/purchase-requests/{request_id}/review`, `/api/finance/procurement/rfqs`, `/api/finance/procurement/vendor-evaluations`, `/api/finance/procurement/vendor-evaluations/{evaluation_id}/select`, `/api/finance/procurement/purchase-orders`, `/api/finance/procurement/purchase-orders/{po_id}/approve`, `/api/finance/procurement/purchase-orders/{po_id}/goods-receipts`, `/api/finance/procurement/purchase-orders/{po_id}/service-acceptance`, `/api/finance/procurement/reports`
- Bank & Cash: `/api/finance/bank-cash/bank-accounts`, `/api/finance/bank-cash/cash-accounts`, `/api/finance/bank-cash/reconciliations`, `/api/finance/bank-cash/cash-forecast`, `/api/finance/bank-cash/transfers`, `/api/finance/bank-cash/petty-cash/expenses`, `/api/finance/bank-cash/petty-cash/replenish`, `/api/finance/bank-cash/cash-flow-projection`
- Tax: `/api/finance/tax/types`, `/api/finance/tax/vat`, `/api/finance/tax/withholding`, `/api/finance/tax/paye`, `/api/finance/tax/validate`, `/api/finance/tax/calculate-advanced`, `/api/finance/tax/filings/prepare`, `/api/finance/tax/reports`, `/api/finance/tax/audit-support`
- Fixed Assets: `/api/finance/assets/acquisitions`, `/api/finance/assets/register`, `/api/finance/assets/{asset_id}/categorize`, `/api/finance/assets/{asset_id}/assign`, `/api/finance/assets/{asset_id}/transfer`, `/api/finance/assets/{asset_id}/revalue`, `/api/finance/assets/{asset_id}/dispose`, `/api/finance/assets/{asset_id}/retire`, `/api/finance/assets/register`
- Project Finance: `/api/finance/project-finance/profiles`, `/api/finance/project-finance/{profile_id}/budget`, `/api/finance/project-finance/{profile_id}/resources`, `/api/finance/project-finance/{profile_id}/costs`, `/api/finance/project-finance/{profile_id}/revenue`, `/api/finance/project-finance/{profile_id}/billing`, `/api/finance/project-finance/{profile_id}/profitability`, `/api/finance/project-finance/{profile_id}/forecast`, `/api/finance/project-finance/{profile_id}/close`
- VAT: `/api/finance/tax/calculate`
- Mileage/per diem: `/api/finance/expense-claims/calculate`
- Budget variance: `/api/finance/budgets/{budget_id}/variance`
- Bank reconciliation: `/api/finance/bank-accounts/{bank_account_id}/reconcile`
- Asset depreciation: `/api/finance/fixed-assets/{asset_id}/depreciation`
- Project profitability: `/api/finance/project-finance/{project_finance_id}/profitability`

## Verification

- Finance source compile passed.
- Frontend production build passed.
- Database schema repair passed.
- API smoke passed for control center, tax calculation, expense mileage formula, budget variance, bank reconciliation, journal posting, journal reversal, GL trial balance/balance sheet/P&L/cash flow, cost center creation, cost center assignment, cost allocation, department reporting, Journal Management FIN-033 to FIN-042, AP FIN-043 to FIN-055, AR FIN-056 to FIN-067, Expense Management FIN-068 to FIN-076, Budget Management FIN-077 to FIN-087, Procurement FIN-088 to FIN-099, Bank & Cash FIN-100 to FIN-107, Tax FIN-108 to FIN-116, Fixed Assets FIN-117 to FIN-126, Project Finance FIN-127 to FIN-135, PO/GRN matching, and CRM sync.
