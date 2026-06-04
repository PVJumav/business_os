from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.finance import (
    FinanceAccountCategory,
    FinanceApproval,
    FinanceAuditTrail,
    FinanceBill,
    FinanceBudget,
    FinanceBudgetApproval,
    FinanceBudgetLine,
    FinanceChartAccount,
    FinanceCostCenter,
    FinanceCreditNote,
    FinanceCurrency,
    FinanceDebitNote,
    FinanceDocument,
    FinanceExchangeRate,
    FinanceExpense,
    FinanceExpenseCategory,
    FinanceExpenseClaim,
    FinanceFinancialPeriod,
    FinanceIntegrationEvent,
    FinanceInvoice,
    FinanceInvoiceLineItem,
    FinanceJournalEntry,
    FinanceJournalLine,
    FinancePayment,
    FinancePayrollPosting,
    FinanceProjectFinancialRecord,
    FinancePurchaseOrder,
    FinancePurchaseRequest,
    FinanceReceipt,
    FinanceRevenueRecognitionRecord,
    FinanceTaxRule,
    FinanceVendor,
)
from backend.models.hrm import HRMEmployee
from backend.policies.finance import deny_closed_period, require_finance_access
from backend.schemas.auth import UserResponse
from backend.services.finance_sync import consolidated_finance_totals


RESOURCE_MAP = {
    "account-categories": FinanceAccountCategory,
    "chart-of-accounts": FinanceChartAccount,
    "cost-centers": FinanceCostCenter,
    "budgets": FinanceBudget,
    "budget-lines": FinanceBudgetLine,
    "budget-approvals": FinanceBudgetApproval,
    "expenses": FinanceExpense,
    "expense-categories": FinanceExpenseCategory,
    "expense-claims": FinanceExpenseClaim,
    "vendors": FinanceVendor,
    "vendor-invoices": FinanceBill,
    "customer-invoices": FinanceInvoice,
    "invoice-line-items": FinanceInvoiceLineItem,
    "payments": FinancePayment,
    "receipts": FinanceReceipt,
    "credit-notes": FinanceCreditNote,
    "debit-notes": FinanceDebitNote,
    "purchase-requests": FinancePurchaseRequest,
    "purchase-orders": FinancePurchaseOrder,
    "taxes": FinanceTaxRule,
    "tax-rules": FinanceTaxRule,
    "currencies": FinanceCurrency,
    "exchange-rates": FinanceExchangeRate,
    "financial-periods": FinanceFinancialPeriod,
    "journals": FinanceJournalEntry,
    "journal-lines": FinanceJournalLine,
    "payroll-postings": FinancePayrollPosting,
    "project-financials": FinanceProjectFinancialRecord,
    "revenue-recognition": FinanceRevenueRecognitionRecord,
    "approvals": FinanceApproval,
    "audit-logs": FinanceAuditTrail,
    "documents": FinanceDocument,
    "integration-events": FinanceIntegrationEvent,
}

APPROVAL_TRANSITIONS = {
    "submit": "submitted",
    "approve": "approved",
    "reject": "rejected",
    "post": "posted",
    "void": "void",
    "mark-paid": "paid",
    "reconcile": "reconciled",
}


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Finance resource not found")
    return model


def serialize(row) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (datetime,)):
            value = value.isoformat()
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        elif isinstance(value, UUID):
            value = str(value)
        result[column.name] = value
    return result


def clean_payload(model, data: dict[str, Any]) -> dict[str, Any]:
    blocked = {"id", "created_at", "updated_at", "deleted_at"}
    columns = {column.name for column in model.__table__.columns}
    return {key: value for key, value in data.items() if key in columns and key not in blocked and value not in ("", None)}


def audit(db: Session, user: UserResponse | None, action: str, entity_type: str, entity_id: str | None, before=None, after=None):
    summary = f"{action} finance {entity_type}"
    db.add(
        FinanceAuditTrail(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=getattr(user, "email", None),
            change_summary=summary,
        )
    )


def financial_period(db: Session, period_id: UUID | str | None) -> FinanceFinancialPeriod | None:
    if not period_id:
        return None
    period = db.query(FinanceFinancialPeriod).filter(FinanceFinancialPeriod.id == period_id).first()
    if not period:
        raise HTTPException(status_code=422, detail="Financial period does not exist")
    return period


def ensure_period_open(db: Session, data: dict[str, Any], record: Any | None = None) -> None:
    period_id = data.get("financial_period_id") or getattr(record, "financial_period_id", None)
    period = financial_period(db, period_id)
    if period:
        deny_closed_period(period.status)


def active_employee(db: Session, employee_id: UUID | str | None) -> HRMEmployee | None:
    if not employee_id:
        return None
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=422, detail="Employee expense data must reference HRM employee records")
    if employee.employment_status in {"inactive", "terminated", "suspended"}:
        raise HTTPException(status_code=422, detail="Finance records cannot be created for inactive employees")
    return employee


def get_record(db: Session, resource: str, record_id: UUID):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance record not found")
    return record


def list_records(db: Session, resource: str, user: UserResponse) -> list[dict[str, Any]]:
    model = model_for(resource)
    require_finance_access(db, user, "read", resource)
    query = db.query(model)
    if hasattr(model, "soft_deleted"):
        query = query.filter(model.soft_deleted.is_(False))
    if hasattr(model, "created_at"):
        query = query.order_by(model.created_at.desc())
    return [serialize(row) for row in query.limit(500).all()]


def validate(db: Session, resource: str, data: dict[str, Any], record: Any | None = None) -> None:
    ensure_period_open(db, data, record)
    if resource in {"expenses", "expense-claims"}:
        if not (data.get("category_id") or data.get("category")):
            raise HTTPException(status_code=422, detail="Expenses require a category")
        active_employee(db, data.get("claimant_employee_id") or data.get("employee_id"))
        if not (data.get("cost_center_id") or getattr(record, "cost_center_id", None) or data.get("department")):
            raise HTTPException(status_code=422, detail="Expenses require a cost center or department")
    if resource == "vendor-invoices" and not data.get("vendor_id"):
        raise HTTPException(status_code=422, detail="Vendor invoices must link to vendor records")
    if resource == "customer-invoices" and not data.get("invoice_number"):
        raise HTTPException(status_code=422, detail="Customer invoices require an invoice number")
    if resource == "payments":
        amount = Decimal(str(data.get("amount") or 0))
        bill_id = data.get("bill_id")
        if bill_id:
            bill = db.query(FinanceBill).filter(FinanceBill.id == bill_id).first()
            outstanding = Decimal(str(getattr(bill, "amount", 0) or 0)) - Decimal(str(getattr(bill, "paid_amount", 0) or 0)) if bill else Decimal("0")
            if bill and amount > outstanding:
                raise HTTPException(status_code=422, detail="Payment cannot exceed outstanding bill balance")
    if resource == "invoice-line-items":
        qty = Decimal(str(data.get("quantity") or 1))
        unit = Decimal(str(data.get("unit_price") or 0))
        discount = Decimal(str(data.get("discount_amount") or 0))
        tax_rate = Decimal(str(data.get("tax_rate") or 0))
        taxable = max(Decimal("0"), qty * unit - discount)
        data["tax_amount"] = taxable * tax_rate / Decimal("100")
        data["line_total"] = taxable + data["tax_amount"]


def recalculate_invoice(db: Session, invoice_id: UUID | str | None) -> None:
    if not invoice_id:
        return
    invoice = db.query(FinanceInvoice).filter(FinanceInvoice.id == invoice_id).first()
    if not invoice:
        return
    totals = db.query(
        func.coalesce(func.sum(FinanceInvoiceLineItem.line_total), 0),
        func.coalesce(func.sum(FinanceInvoiceLineItem.tax_amount), 0),
        func.coalesce(func.sum(FinanceInvoiceLineItem.discount_amount), 0),
    ).filter(FinanceInvoiceLineItem.invoice_id == invoice.id).first()
    total, tax, discount = totals
    invoice.total_amount = Decimal(str(total or 0))
    invoice.tax_amount = Decimal(str(tax or 0))
    invoice.discount_amount = Decimal(str(discount or 0))
    invoice.subtotal = invoice.total_amount - invoice.tax_amount + invoice.discount_amount


def create_record(db: Session, resource: str, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    require_finance_access(db, user, "create", resource)
    data = clean_payload(model, data)
    validate(db, resource, data)
    record = model(**data)
    db.add(record)
    db.flush()
    if resource == "invoice-line-items":
        recalculate_invoice(db, record.invoice_id)
    audit(db, user, "create", resource, str(record.id), after=serialize(record))
    db.commit()
    db.refresh(record)
    return serialize(record)


def update_record(db: Session, resource: str, record_id: UUID, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    record = get_record(db, resource, record_id)
    require_finance_access(db, user, "update", resource)
    if resource in {"customer-invoices", "vendor-invoices"} and getattr(record, "approval_status", "") == "approved":
        raise HTTPException(status_code=423, detail="Approved invoices cannot be edited directly; create a revision or credit/debit note")
    before = serialize(record)
    data = clean_payload(model, data)
    validate(db, resource, data, record)
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    if resource == "invoice-line-items":
        recalculate_invoice(db, record.invoice_id)
    audit(db, user, "update", resource, str(record_id), before=before, after=serialize(record))
    db.commit()
    db.refresh(record)
    return serialize(record)


def delete_record(db: Session, resource: str, record_id: UUID, user: UserResponse) -> None:
    record = get_record(db, resource, record_id)
    require_finance_access(db, user, "delete", resource)
    before = serialize(record)
    if hasattr(record, "soft_deleted"):
        record.soft_deleted = True
        record.deleted_at = datetime.now(timezone.utc)
    else:
        db.delete(record)
    audit(db, user, "delete", resource, str(record_id), before=before)
    db.commit()


def assert_journal_balanced(db: Session, journal: FinanceJournalEntry) -> None:
    lines = db.query(
        func.coalesce(func.sum(FinanceJournalLine.debit_amount), 0),
        func.coalesce(func.sum(FinanceJournalLine.credit_amount), 0),
    ).filter(FinanceJournalLine.journal_entry_id == journal.id).first()
    debit, credit = Decimal(str(lines[0] or journal.total_debit or 0)), Decimal(str(lines[1] or journal.total_credit or 0))
    if debit != credit:
        raise HTTPException(status_code=422, detail="Journal entries must balance: debit must equal credit")
    journal.total_debit = debit
    journal.total_credit = credit


def workflow(db: Session, resource: str, record_id: UUID, action: str, user: UserResponse, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    record = get_record(db, resource, record_id)
    require_finance_access(db, user, "update", resource)
    before = serialize(record)
    now = datetime.now(timezone.utc)
    payload = payload or {}
    if resource == "financial-periods":
        if action == "close-period":
            record.status = "closed"
            record.closed_by = user.email
            record.closed_at = now
        elif action == "reopen-period":
            if str(user.role).lower() not in {"admin", "finance_admin", "cfo"}:
                raise HTTPException(status_code=403, detail="Only admin/CFO policy can reopen financial periods")
            record.status = "open"
            record.closed_by = None
            record.closed_at = None
        else:
            raise HTTPException(status_code=422, detail="Unsupported financial period action")
    elif resource == "journals" and action == "post":
        assert_journal_balanced(db, record)
        record.status = "posted"
        record.posted_by = user.email
        record.posted_at = now
    elif action in APPROVAL_TRANSITIONS:
        next_status = APPROVAL_TRANSITIONS[action]
        if hasattr(record, "approval_status") and action in {"submit", "approve", "reject"}:
            record.approval_status = next_status
        if hasattr(record, "status"):
            record.status = next_status
        if action == "mark-paid" and hasattr(record, "paid_amount") and hasattr(record, "total_amount"):
            record.paid_amount = record.total_amount
    else:
        raise HTTPException(status_code=422, detail="Unsupported finance workflow action")
    db.flush()
    audit(db, user, action, resource, str(record_id), before=before, after=serialize(record))
    db.commit()
    db.refresh(record)
    return serialize(record)


def analytics_summary(db: Session) -> dict[str, Any]:
    totals = consolidated_finance_totals(db)
    return {
        "revenue": totals["recognized_revenue"],
        "outstanding_invoices": totals["outstanding_invoices"],
        "expenses": totals["total_expenses"],
        "profit_loss": totals["profit_loss"],
        "approved_budget": totals["approved_budget"],
        "project_profitability": totals["project_profitability"],
        "open_periods": db.query(FinanceFinancialPeriod).filter(FinanceFinancialPeriod.status == "open").count(),
        "unposted_journals": db.query(FinanceJournalEntry).filter(FinanceJournalEntry.status != "posted").count(),
    }
