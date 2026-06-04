from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.crm import CRMCampaign, CRMDeal, CRMInvoice
from backend.models.finance import (
    FinanceBudget,
    FinanceBill,
    FinanceExpense,
    FinanceExpenseClaim,
    FinanceInvoice,
    FinancePayrollPosting,
    FinanceProjectFinance,
    FinanceRevenueRecord,
)
from backend.models.hrm import HRMBenefit, HRMCompanyAsset, HRMPayroll, HRMPayrollRun, HRMTraining
from backend.models.projects import Project, ProjectBudget, ProjectExpense


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _record_date(*values: Any) -> date:
    for value in values:
        if not value:
            continue
        if hasattr(value, "date") and not isinstance(value, date):
            return value.date()
        return value
    return date.today()


def _upsert_revenue(
    db: Session,
    source_module: str,
    source_record_id,
    revenue_source: str,
    amount: Decimal,
    recognition_date: date,
    revenue_type: str = "operational",
    account_id=None,
    deal_id=None,
    invoice_id=None,
    customer_name: str | None = None,
    status: str = "recognized",
) -> bool:
    if amount <= 0:
        return False
    record = (
        db.query(FinanceRevenueRecord)
        .filter(FinanceRevenueRecord.source_module == source_module, FinanceRevenueRecord.source_record_id == source_record_id)
        .first()
    )
    if not record and deal_id:
        record = db.query(FinanceRevenueRecord).filter(FinanceRevenueRecord.deal_id == deal_id).first()
    if not record and invoice_id:
        record = db.query(FinanceRevenueRecord).filter(FinanceRevenueRecord.invoice_id == invoice_id).first()
    if not record:
        db.add(
            FinanceRevenueRecord(
                source_module=source_module,
                source_record_id=source_record_id,
                revenue_source=revenue_source,
                customer_name=customer_name,
                account_id=account_id,
                deal_id=deal_id,
                invoice_id=invoice_id,
                revenue_type=revenue_type,
                recognition_date=recognition_date,
                amount=amount,
                status=status,
            )
        )
        return True
    record.source_module = source_module
    record.source_record_id = source_record_id
    record.revenue_source = revenue_source
    record.customer_name = customer_name
    record.account_id = account_id
    record.deal_id = deal_id
    record.invoice_id = invoice_id
    record.revenue_type = revenue_type
    record.recognition_date = recognition_date
    record.amount = amount
    record.status = status
    return False


def _upsert_expense(
    db: Session,
    source_module: str,
    source_record_id,
    label: str,
    amount: Decimal,
    expense_date: date,
    category: str,
    department: str | None = None,
    project_id=None,
    claimant_employee_id=None,
    status: str = "posted",
    approval_status: str = "approved",
) -> bool:
    if amount <= 0:
        return False
    record = (
        db.query(FinanceExpense)
        .filter(FinanceExpense.source_module == source_module, FinanceExpense.source_record_id == source_record_id)
        .first()
    )
    if not record:
        db.add(
            FinanceExpense(
                expense_number=f"SYNC-{source_module.upper().replace('.', '-')}-{str(source_record_id)[:8]}",
                source_module=source_module,
                source_record_id=source_record_id,
                source_label=label,
                expense_date=expense_date,
                category=category,
                department=department,
                project_id=project_id,
                claimant_employee_id=claimant_employee_id,
                amount=amount,
                approval_status=approval_status,
                payment_status="paid" if status in {"posted", "paid", "recognized"} else "pending",
                status=status,
                notes=f"Synchronized from {source_module}",
            )
        )
        return True
    record.source_label = label
    record.expense_date = expense_date
    record.category = category
    record.department = department
    record.project_id = project_id
    record.claimant_employee_id = claimant_employee_id
    record.amount = amount
    record.approval_status = approval_status
    record.status = status
    record.payment_status = "paid" if status in {"posted", "paid", "recognized"} else "pending"
    return False


def _sync_crm(db: Session) -> dict[str, int]:
    created_or_updated = {"revenue": 0, "expenses": 0, "invoices": 0}
    for deal in db.query(CRMDeal).filter(CRMDeal.soft_deleted.is_(False)).all():
        total_cost = _money(deal.distributor_cost) + _money(deal.vendor_cost) + _money(deal.internal_cost)
        if deal.deal_status in {"closed_won", "won"}:
            if _upsert_revenue(
                db,
                "crm.deals.closed_won",
                deal.id,
                "Closed won deal",
                _money(deal.revenue_amount),
                _record_date(deal.closed_date, deal.expected_close_date, deal.created_at),
                deal.pipeline_type or "deal",
                account_id=deal.account_id,
                deal_id=deal.id,
                customer_name=deal.country or deal.owner,
            ):
                created_or_updated["revenue"] += 1
        cost_items = [
            ("crm.deals.distributor_cost", "Distributor cost", deal.distributor_cost),
            ("crm.deals.vendor_cost", "Vendor cost", deal.vendor_cost),
            ("crm.deals.internal_cost", "Internal sales/project cost", deal.internal_cost),
        ]
        for source, label, amount in cost_items:
            if _upsert_expense(
                db,
                source,
                deal.id,
                f"{deal.deal_name} - {label}",
                _money(amount),
                _record_date(deal.closed_date, deal.expected_close_date, deal.created_at),
                "CRM cost of sale",
                department="Sales",
                project_id=None,
                status="posted" if deal.deal_status in {"closed_won", "won"} else "committed",
            ):
                created_or_updated["expenses"] += 1
        expected_gp = _money(deal.revenue_amount) - total_cost
        deal.gross_profit = expected_gp

    for invoice in db.query(CRMInvoice).all():
        finance_invoice = db.query(FinanceInvoice).filter(FinanceInvoice.crm_invoice_id == invoice.id).first()
        total = _money(invoice.amount)
        paid = _money(invoice.paid_amount)
        status = "paid" if paid >= total and total > 0 else "partially_paid" if paid > 0 else invoice.status
        if not finance_invoice:
            finance_invoice = FinanceInvoice(
                crm_invoice_id=invoice.id,
                account_id=invoice.account_id,
                deal_id=invoice.deal_id,
                invoice_number=invoice.invoice_number,
                invoice_date=invoice.invoice_date,
                due_date=invoice.due_date,
            )
            db.add(finance_invoice)
            created_or_updated["invoices"] += 1
        finance_invoice.subtotal = total
        finance_invoice.total_amount = total
        finance_invoice.paid_amount = paid
        finance_invoice.approval_status = "approved" if invoice.status in {"sent", "paid", "partially_paid"} else "draft"
        finance_invoice.status = status
        finance_invoice.notes = invoice.notes
        if paid > 0:
            _upsert_revenue(
                db,
                "crm.invoices.paid",
                invoice.id,
                "Paid CRM invoice",
                paid,
                _record_date(invoice.invoice_date),
                "invoice",
                account_id=invoice.account_id,
                deal_id=invoice.deal_id,
                invoice_id=invoice.id,
            )

    for campaign in db.query(CRMCampaign).filter(CRMCampaign.soft_deleted.is_(False)).all():
        if _upsert_expense(
            db,
            "crm.campaigns.actual_cost",
            campaign.id,
            campaign.campaign_name,
            _money(campaign.actual_cost),
            _record_date(campaign.start_date, campaign.created_at),
            "Marketing campaign",
            department="Marketing",
            status="posted" if campaign.status in {"completed", "active"} else "committed",
        ):
            created_or_updated["expenses"] += 1
    return created_or_updated


def _sync_hrm(db: Session) -> dict[str, int]:
    counts = {"expenses": 0, "payroll_postings": 0}
    for payroll in db.query(HRMPayroll).all():
        if _upsert_expense(
            db,
            "hrm.payroll.net_pay",
            payroll.id,
            f"Payroll {payroll.payroll_month}",
            _money(payroll.net_pay),
            _record_date(payroll.payment_date, payroll.created_at),
            "Payroll",
            department="HR",
            claimant_employee_id=payroll.employee_id,
            status="posted" if payroll.payment_status in {"paid", "processed"} else "committed",
        ):
            counts["expenses"] += 1

    for benefit in db.query(HRMBenefit).all():
        if _upsert_expense(
            db,
            "hrm.benefits.employer_contribution",
            benefit.id,
            benefit.benefit_name,
            _money(benefit.employer_contribution),
            _record_date(benefit.start_date, benefit.created_at),
            "Employee benefits",
            department="HR",
            claimant_employee_id=benefit.employee_id,
            status="posted" if benefit.status == "active" else "committed",
        ):
            counts["expenses"] += 1

    for training in db.query(HRMTraining).all():
        if _upsert_expense(
            db,
            "hrm.training.cost",
            training.id,
            training.training_title,
            _money(training.cost),
            _record_date(training.start_date, training.created_at),
            "Training",
            department="HR",
            claimant_employee_id=training.employee_id,
            status="posted" if training.completion_status in {"completed", "in_progress"} else "committed",
        ):
            counts["expenses"] += 1

    for asset in db.query(HRMCompanyAsset).all():
        if _upsert_expense(
            db,
            "hrm.assets.purchase_cost",
            asset.id,
            asset.asset_name,
            _money(asset.purchase_cost),
            _record_date(asset.purchase_date, asset.created_at),
            "Employee asset",
            department="HR",
            claimant_employee_id=asset.custodian_employee_id,
            status="posted",
        ):
            counts["expenses"] += 1

    for run in db.query(HRMPayrollRun).filter(HRMPayrollRun.status.in_(["approved", "locked", "posted"])).all():
        posting = db.query(FinancePayrollPosting).filter(FinancePayrollPosting.payroll_run_id == run.id).first()
        if not posting:
            posting = FinancePayrollPosting(payroll_run_id=run.id, posting_number=f"PAY-{run.run_number or str(run.id)[:8]}")
            db.add(posting)
            counts["payroll_postings"] += 1
        posting.total_gross = run.total_gross or 0
        posting.total_net = run.total_net or 0
        posting.status = "posted" if run.status in {"locked", "posted"} else "draft"
    return counts


def _sync_projects(db: Session) -> dict[str, int]:
    counts = {"expenses": 0, "budgets": 0, "project_finance": 0}
    for project in db.query(Project).filter(Project.soft_deleted.is_(False)).all():
        finance_project = db.query(FinanceProjectFinance).filter(FinanceProjectFinance.project_id == project.id).first()
        if not finance_project:
            finance_project = FinanceProjectFinance(project_id=project.id, project_name=project.project_name)
            db.add(finance_project)
            counts["project_finance"] += 1
        expenses = db.query(func.coalesce(func.sum(ProjectExpense.amount), 0)).filter(ProjectExpense.project_id == project.id).scalar() or 0
        budget = db.query(func.coalesce(func.sum(ProjectBudget.approved_amount), 0)).filter(ProjectBudget.project_id == project.id).scalar() or 0
        finance_project.project_name = project.project_name
        finance_project.budget_amount = budget or project.approved_budget or 0
        finance_project.revenue_amount = project.invoiced_amount or 0
        finance_project.expense_amount = expenses or project.actual_cost or 0
        finance_project.profitability = _money(finance_project.revenue_amount) - _money(finance_project.expense_amount)
        finance_project.overrun_amount = max(_money(finance_project.expense_amount) - _money(finance_project.budget_amount), Decimal("0"))
        finance_project.status = project.lifecycle_status

        finance_budget = db.query(FinanceBudget).filter(FinanceBudget.project_id == project.id, FinanceBudget.budget_name == project.project_name).first()
        if not finance_budget and (project.approved_budget or budget):
            finance_budget = FinanceBudget(
                budget_name=project.project_name,
                budget_type="project",
                project_id=project.id,
                fiscal_year=str(date.today().year),
            )
            db.add(finance_budget)
            counts["budgets"] += 1
        if finance_budget:
            finance_budget.approved_amount = project.approved_budget or budget or 0
            finance_budget.actual_amount = expenses or project.actual_cost or 0
            finance_budget.approval_status = project.budget_approval_status
            finance_budget.status = "active" if project.lifecycle_status in {"approved", "planning", "in_progress"} else project.lifecycle_status

    for expense in db.query(ProjectExpense).all():
        if _upsert_expense(
            db,
            "projects.expenses",
            expense.id,
            expense.expense_category,
            _money(expense.amount),
            _record_date(expense.expense_date, expense.created_at),
            expense.expense_category,
            department="Projects",
            project_id=expense.project_id,
            claimant_employee_id=expense.incurred_by_employee_id,
            status="posted" if expense.approval_status == "approved" else "committed",
            approval_status=expense.approval_status,
        ):
            counts["expenses"] += 1
    return counts


def sync_finance_from_operations(db: Session) -> dict[str, Any]:
    crm = _sync_crm(db)
    hrm = _sync_hrm(db)
    projects = _sync_projects(db)
    db.commit()
    return {"status": "success", "crm": crm, "hrm": hrm, "projects": projects}


def consolidated_finance_totals(db: Session) -> dict[str, float]:
    sync_finance_from_operations(db)
    revenue = db.query(func.coalesce(func.sum(FinanceRevenueRecord.amount), 0)).scalar() or 0
    invoices = db.query(func.coalesce(func.sum(FinanceInvoice.total_amount), 0)).scalar() or 0
    paid = db.query(func.coalesce(func.sum(FinanceInvoice.paid_amount), 0)).scalar() or 0
    expenses = db.query(func.coalesce(func.sum(FinanceExpense.amount), 0)).scalar() or 0
    claims = db.query(func.coalesce(func.sum(FinanceExpenseClaim.amount), 0)).scalar() or 0
    bills = db.query(func.coalesce(func.sum(FinanceBill.amount), 0)).scalar() or 0
    budgets = db.query(func.coalesce(func.sum(FinanceBudget.approved_amount), 0)).scalar() or 0
    project_profitability = db.query(func.coalesce(func.sum(FinanceProjectFinance.profitability), 0)).scalar() or 0
    total_expenses = _money(expenses) + _money(claims) + _money(bills)
    return {
        "recognized_revenue": float(revenue),
        "invoice_total": float(invoices),
        "paid_amount": float(paid),
        "outstanding_invoices": float(max(_money(invoices) - _money(paid), Decimal("0"))),
        "operational_expenses": float(expenses),
        "expense_claims": float(claims),
        "vendor_bills": float(bills),
        "total_expenses": float(total_expenses),
        "profit_loss": float(_money(revenue) - total_expenses),
        "approved_budget": float(budgets),
        "project_profitability": float(project_profitability),
    }
