from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.crm import CRMAccount, CRMContract, CRMCustomerLPO, CRMOpportunity, CRMQuotation
from backend.models.finance import (
    FinanceApproval,
    FinanceApprovalDelegation,
    FinanceApprovalHistory,
    FinanceApprovalMatrix,
    FinanceAPReconciliation,
    FinanceAssetMovement,
    FinanceAuditTrail,
    FinanceBankAccount,
    FinanceBankReconciliation,
    FinanceBankTransaction,
    FinanceBill,
    FinanceBudget,
    FinanceChartAccount,
    FinanceBudgetRevision,
    FinanceCollectionAction,
    FinanceCostCenterAllocation,
    FinanceCostCenterAssignment,
    FinanceCustomerBillingProfile,
    FinanceCostCenter,
    FinanceCreditNote,
    FinanceDebitNote,
    FinanceDeferredRevenueSchedule,
    FinanceDocument,
    FinanceDocumentRetentionRule,
    FinanceExpense,
    FinanceExpenseClaim,
    FinanceFinancialPeriod,
    FinanceFixedAsset,
    FinanceGLMappingRule,
    FinanceGoodsReceipt,
    FinanceIntegrationEvent,
    FinanceInvoice,
    FinanceInvoiceLineItem,
    FinanceJournalEntry,
    FinanceJournalLine,
    FinancePayment,
    FinanceProjectFinance,
    FinancePurchaseOrder,
    FinancePurchaseRequest,
    FinanceRFQ,
    FinanceRecurringJournal,
    FinanceReceipt,
    FinanceReceiptAllocation,
    FinanceRevenueRecord,
    FinanceTaxRecord,
    FinanceTaxRule,
    FinanceVendor,
    FinanceVendorEvaluation,
    FinanceVendorOnboarding,
    FinanceVendorVerification,
)
from backend.models.hrm import HRMEmployee, HRMPayroll
from backend.policies.finance import require_finance_access
from backend.schemas.auth import UserResponse
from backend.services.finance_sync import consolidated_finance_totals, sync_finance_from_operations


router = APIRouter(prefix="/finance", tags=["Finance BUCs"])


def money(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def as_float(value: Any) -> float:
    return float(money(value))


def serialize(row) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, UUID):
            value = str(value)
        result[column.name] = value
    return result


def audit(db: Session, user: UserResponse | None, action: str, entity_type: str, entity_id: UUID | None, summary: str) -> None:
    db.add(
        FinanceAuditTrail(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=getattr(user, "email", None),
            change_summary=summary,
        )
    )


def event(db: Session, source: str, event_type: str, record_type: str, record_id: UUID | None, payload: dict[str, Any]) -> None:
    db.add(
        FinanceIntegrationEvent(
            source_module=source,
            target_module="Finance",
            event_type=event_type,
            related_record_type=record_type,
            related_record_id=record_id,
            payload_summary=str(payload)[:4000],
            status="processed",
            processed_at=datetime.now(timezone.utc),
        )
    )


def get_or_404(db: Session, model, record_id: UUID, label: str):
    row = db.query(model).filter(model.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return row


def active_employee(db: Session, employee_id: UUID | str | None) -> HRMEmployee | None:
    if not employee_id:
        return None
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=422, detail="Employee must exist in HRMS")
    if (employee.employment_status or "").lower() in {"inactive", "suspended", "terminated", "exited", "retired", "deceased"}:
        raise HTTPException(status_code=422, detail="Inactive employees cannot initiate or own finance workflows")
    return employee


def next_number(prefix: str) -> str:
    return f"{prefix}-{date.today().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"


def current_ar(db: Session) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(FinanceInvoice.total_amount - FinanceInvoice.paid_amount), 0))
        .filter(FinanceInvoice.status.notin_(["cancelled", "reversed", "rejected"]))
        .scalar()
    )
    return money(total)


def current_ap(db: Session) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(FinanceBill.amount - FinanceBill.paid_amount), 0))
        .filter(FinanceBill.status.notin_(["cancelled", "reversed", "rejected"]), FinanceBill.approval_status.in_(["approved", "posted", "paid"]))
        .scalar()
    )
    return money(total)


def stale_warning(last_updated: datetime | None) -> str | None:
    if not last_updated:
        return "No source transactions found yet."
    age = datetime.now(timezone.utc) - (last_updated if last_updated.tzinfo else last_updated.replace(tzinfo=timezone.utc))
    if age > timedelta(hours=24):
        return "Some finance source data is older than 24 hours."
    return None


def filter_meta(
    date_from: date | None = None,
    date_to: date | None = None,
    company: str | None = None,
    branch: str | None = None,
    department: str | None = None,
    business_unit: str | None = None,
    cost_center: str | None = None,
    project_id: UUID | None = None,
    currency: str | None = None,
    customer: str | None = None,
    vendor: str | None = None,
    approval_status: str | None = None,
    posted_status: str | None = None,
    budget_period: str | None = None,
    financial_year: str | None = None,
    accounting_period: str | None = None,
) -> dict[str, Any]:
    return {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "company": company,
        "branch": branch,
        "department": department,
        "business_unit": business_unit,
        "cost_center": cost_center,
        "project_id": str(project_id) if project_id else None,
        "currency": currency,
        "customer": customer,
        "vendor": vendor,
        "approval_status": approval_status,
        "posted_status": posted_status,
        "budget_period": budget_period,
        "financial_year": financial_year,
        "accounting_period": accounting_period,
    }


def control_center_context(db: Session, user: UserResponse, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    require_finance_access(db, user, "read", "control-center")
    filters = filters or {}
    totals = consolidated_finance_totals(db)

    invoice_query = db.query(FinanceInvoice).filter(FinanceInvoice.status.notin_(["cancelled", "reversed", "rejected"]))
    bill_query = db.query(FinanceBill).filter(FinanceBill.status.notin_(["cancelled", "reversed", "rejected"]))
    expense_query = db.query(FinanceExpense).filter(FinanceExpense.status.notin_(["cancelled", "reversed", "rejected"]))
    budget_query = db.query(FinanceBudget).filter(FinanceBudget.status.notin_(["cancelled", "rejected"]))
    if filters.get("department"):
        bill_query = bill_query.filter(FinanceBill.department == filters["department"])
        expense_query = expense_query.filter(FinanceExpense.department == filters["department"])
        budget_query = budget_query.filter(FinanceBudget.department == filters["department"])
    if filters.get("project_id"):
        invoice_query = invoice_query.filter(FinanceInvoice.project_id == filters["project_id"])
        bill_query = bill_query.filter(FinanceBill.project_id == filters["project_id"])
        expense_query = expense_query.filter(FinanceExpense.project_id == filters["project_id"])
        budget_query = budget_query.filter(FinanceBudget.project_id == filters["project_id"])
    if filters.get("approval_status"):
        invoice_query = invoice_query.filter(FinanceInvoice.approval_status == filters["approval_status"])
        bill_query = bill_query.filter(FinanceBill.approval_status == filters["approval_status"])
        budget_query = budget_query.filter(FinanceBudget.approval_status == filters["approval_status"])
    if filters.get("financial_year"):
        budget_query = budget_query.filter(FinanceBudget.fiscal_year == filters["financial_year"])
    if filters.get("budget_period"):
        budget_query = budget_query.filter(FinanceBudget.period_label == filters["budget_period"])

    revenue = money(invoice_query.filter(FinanceInvoice.approval_status.in_(["approved", "posted", "sent", "paid"])).with_entities(func.coalesce(func.sum(FinanceInvoice.total_amount), 0)).scalar())
    recognized_revenue = money(totals["recognized_revenue"]) or revenue
    expense_total = money(expense_query.with_entities(func.coalesce(func.sum(FinanceExpense.amount), 0)).scalar()) + money(db.query(func.coalesce(func.sum(FinanceExpenseClaim.amount), 0)).filter(FinanceExpenseClaim.approval_status == "approved").scalar())
    expenses = money(totals["total_expenses"]) or expense_total
    bank_cash = money(db.query(func.coalesce(func.sum(FinanceBankAccount.current_balance), 0)).filter(FinanceBankAccount.status == "active").scalar())
    receipts_pending = money(db.query(func.coalesce(func.sum(FinanceReceipt.amount), 0)).scalar())
    pending_payments = money(db.query(func.coalesce(func.sum(FinancePayment.amount), 0)).filter(FinancePayment.status.in_(["pending", "approved", "scheduled"])).scalar())
    cash_position = bank_cash + receipts_pending - pending_payments

    budget = money(budget_query.filter(FinanceBudget.approval_status == "approved").with_entities(func.coalesce(func.sum(FinanceBudget.approved_amount), 0)).scalar())
    actual = money(budget_query.with_entities(func.coalesce(func.sum(FinanceBudget.actual_amount), 0)).scalar())
    committed = money(db.query(func.coalesce(func.sum(FinancePurchaseOrder.total_amount), 0)).filter(FinancePurchaseOrder.approval_status == "approved", FinancePurchaseOrder.status.notin_(["cancelled", "closed"])).scalar())
    utilization = (actual / budget * Decimal("100")) if budget else Decimal("0")
    variance = actual - budget
    variance_percent = (variance / budget * Decimal("100")) if budget else Decimal("0")

    ar = money(invoice_query.with_entities(func.coalesce(func.sum(FinanceInvoice.total_amount - FinanceInvoice.paid_amount), 0)).scalar())
    ap = money(bill_query.filter(FinanceBill.approval_status.in_(["approved", "posted", "paid"])).with_entities(func.coalesce(func.sum(FinanceBill.amount - FinanceBill.paid_amount), 0)).scalar())
    tax = money(db.query(func.coalesce(func.sum(FinanceTaxRecord.tax_amount), 0)).filter(FinanceTaxRecord.filing_status.notin_(["filed", "cancelled", "reversed"])).scalar())
    pipeline = money(db.query(func.coalesce(func.sum(CRMOpportunity.opportunity_value * CRMOpportunity.probability / 100), 0)).filter(CRMOpportunity.status.notin_(["closed_lost", "lost", "cancelled"]), CRMOpportunity.stage != "Stage 6.b Closed as Lost").scalar())
    deferred = money(db.query(func.coalesce(func.sum(FinanceRevenueRecord.amount), 0)).filter(FinanceRevenueRecord.status == "deferred").scalar())
    forecast = pipeline + deferred
    payroll = money(db.query(func.coalesce(func.sum(HRMPayroll.gross_pay), 0)).filter(HRMPayroll.payment_status.in_(["approved", "processed", "paid"])).scalar())
    procurement_spend = money(db.query(func.coalesce(func.sum(FinancePurchaseOrder.total_amount), 0)).filter(FinancePurchaseOrder.approval_status == "approved").scalar())
    depreciation = money(db.query(func.coalesce(func.sum(FinanceFixedAsset.accumulated_depreciation), 0)).scalar())
    gross_profit = recognized_revenue - expenses
    gross_margin = (gross_profit / recognized_revenue * Decimal("100")) if recognized_revenue else Decimal("0")
    ebitda = gross_profit + depreciation
    net_profit = recognized_revenue - expenses - tax
    dso = (ar / recognized_revenue * Decimal("30")) if recognized_revenue else Decimal("0")
    dpo = (ap / procurement_spend * Decimal("30")) if procurement_spend else Decimal("0")
    payroll_ratio = (payroll / recognized_revenue * Decimal("100")) if recognized_revenue else Decimal("0")

    last_updated = db.query(func.max(FinanceAuditTrail.created_at)).scalar()
    now = datetime.now(timezone.utc)
    return {
        "filters": filters,
        "last_refreshed_at": now.isoformat(),
        "data_stale": bool(stale_warning(last_updated)),
        "warning": stale_warning(last_updated),
        "notes": [
            "Dashboard values are based on approved, posted, or validated transactions.",
            "Forecast values may include CRM opportunities and project billing estimates.",
            "Restricted financial data is visible only to authorized users.",
        ],
        "kpis": {
            "revenue": as_float(recognized_revenue),
            "gross_profit": as_float(gross_profit),
            "gross_margin_percent": as_float(gross_margin),
            "operating_expenses": as_float(expenses),
            "ebitda": as_float(ebitda),
            "net_profit": as_float(net_profit),
            "budget_variance": as_float(variance),
            "budget_variance_percent": as_float(variance_percent),
            "days_sales_outstanding": as_float(dso),
            "days_payable_outstanding": as_float(dpo),
            "payroll_cost_ratio": as_float(payroll_ratio),
            "project_margin_percent": as_float((money(totals["project_profitability"]) / recognized_revenue * Decimal("100")) if recognized_revenue else Decimal("0")),
        },
        "cash_position": {
            "bank_and_cash_balance": as_float(bank_cash),
            "expected_receipts": as_float(receipts_pending),
            "scheduled_payments": as_float(pending_payments),
            "cash_position": as_float(cash_position),
            "available_cash": as_float(cash_position),
            "negative_cash_alert": cash_position < 0,
        },
        "revenue_forecast": {
            "weighted_pipeline_revenue": as_float(pipeline),
            "deferred_revenue_forecast": as_float(deferred),
            "expected_revenue": as_float(forecast + revenue),
            "incomplete_forecast_count": db.query(CRMOpportunity).filter(CRMOpportunity.expected_close_date.is_(None), CRMOpportunity.status.notin_(["closed_lost", "lost"])).count(),
        },
        "budget_utilization": {
            "approved_budget": as_float(budget),
            "actual_spend": as_float(actual),
            "committed_spend": as_float(committed),
            "total_consumption": as_float(actual + committed),
            "remaining_budget": as_float(budget - actual - committed),
            "budget_utilization_percent": as_float(utilization),
            "variance": as_float(variance),
            "variance_percent": as_float(variance_percent),
            "over_budget_alert": actual + committed > budget if budget else False,
        },
        "ar_summary": {
            "accounts_receivable": as_float(ar),
            "collection_rate_percent": as_float((money(db.query(func.coalesce(func.sum(FinanceInvoice.paid_amount), 0)).scalar()) / revenue * Decimal("100")) if revenue else Decimal("0")),
            "overdue_count": invoice_query.filter(FinanceInvoice.due_date < date.today(), FinanceInvoice.total_amount > FinanceInvoice.paid_amount).count(),
            "missing_due_date_count": invoice_query.filter(FinanceInvoice.due_date.is_(None)).count(),
        },
        "ap_summary": {
            "accounts_payable": as_float(ap),
            "upcoming_payments": as_float(pending_payments),
            "overdue_count": bill_query.filter(FinanceBill.due_date < date.today(), FinanceBill.amount > FinanceBill.paid_amount).count(),
            "pending_approval_count": bill_query.filter(FinanceBill.approval_status.in_(["draft", "submitted", "pending"])).count(),
        },
        "tax_exposure": {
            "total_tax_exposure": as_float(tax),
            "pending_filings": db.query(FinanceTaxRecord).filter(FinanceTaxRecord.filing_status.in_(["pending", "submitted"])).count(),
            "missing_tax_code_count": invoice_query.filter(FinanceInvoice.tax_rate.is_(None)).count(),
        },
        "project_profitability": [
            {
                **serialize(row),
                "margin_percent": as_float((money(row.profitability) / money(row.revenue_amount) * Decimal("100")) if money(row.revenue_amount) else Decimal("0")),
                "negative_margin_alert": money(row.profitability) < 0,
            }
            for row in db.query(FinanceProjectFinance).order_by(FinanceProjectFinance.created_at.desc()).limit(50).all()
        ],
        "approval_queue": [
            serialize(row) for row in db.query(FinanceApproval).filter(FinanceApproval.status == "pending").order_by(FinanceApproval.created_at.desc()).limit(100).all()
        ],
    }


def invoice_tax_payload(subtotal: Decimal, discount: Decimal = Decimal("0"), vat_percent: Decimal = Decimal("16")) -> dict[str, Decimal]:
    taxable = max(Decimal("0"), subtotal - discount)
    tax = taxable * vat_percent / Decimal("100")
    return {"taxable": taxable, "tax": tax, "total": taxable + tax}


def project_profitability(project: FinanceProjectFinance) -> None:
    revenue = money(project.revenue_amount)
    cost = money(project.expense_amount)
    project.profitability = revenue - cost
    project.overrun_amount = max(cost - money(project.budget_amount), Decimal("0"))


def create_revenue_forecast(db: Session, quote: CRMQuotation) -> FinanceRevenueRecord:
    existing = (
        db.query(FinanceRevenueRecord)
        .filter(FinanceRevenueRecord.source_module == "crm.quotation", FinanceRevenueRecord.source_record_id == quote.id)
        .first()
    )
    amount = money(quote.total_amount or quote.subtotal)
    if existing:
        existing.amount = amount
        existing.status = "deferred"
        return existing
    record = FinanceRevenueRecord(
        source_module="crm.quotation",
        source_record_id=quote.id,
        revenue_source="CRM approved quotation",
        account_id=getattr(quote.opportunity, "account_id", None),
        deal_id=quote.deal_id,
        invoice_id=None,
        revenue_type="Forecast",
        recognition_date=date.today(),
        amount=amount,
        status="deferred",
    )
    db.add(record)
    return record


def generate_invoice_from_opportunity(db: Session, opportunity: CRMOpportunity) -> FinanceInvoice:
    existing = db.query(FinanceInvoice).filter(FinanceInvoice.crm_opportunity_id == opportunity.id).first()
    if existing:
        return existing
    quote = (
        db.query(CRMQuotation)
        .filter(CRMQuotation.opportunity_id == opportunity.id)
        .order_by(CRMQuotation.created_at.desc())
        .first()
    )
    subtotal = money(getattr(quote, "subtotal", None) or opportunity.opportunity_value)
    discount = money(getattr(quote, "discount_amount", 0))
    vat_percent = Decimal("16")
    tax = invoice_tax_payload(subtotal, discount, vat_percent)
    invoice = FinanceInvoice(
        crm_opportunity_id=opportunity.id,
        quotation_id=getattr(quote, "id", None),
        account_id=opportunity.account_id,
        source_module="crm.opportunity.won",
        source_record_id=opportunity.id,
        invoice_number=next_number("FIN-INV"),
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=subtotal,
        discount_amount=discount,
        tax_rate=vat_percent,
        tax_amount=tax["tax"],
        total_amount=tax["total"],
        approval_status="draft",
        status="draft",
        notes="Auto-generated from CRM won opportunity.",
    )
    db.add(invoice)
    return invoice


def create_project_financial_profile(db: Session, opportunity: CRMOpportunity) -> FinanceProjectFinance:
    existing = db.query(FinanceProjectFinance).filter(FinanceProjectFinance.project_id == opportunity.id).first()
    if existing:
        return existing
    cost = money(opportunity.distributor_cost) + money(opportunity.vendor_cost) + money(opportunity.internal_cost)
    profile = FinanceProjectFinance(
        project_id=opportunity.id,
        project_name=opportunity.title,
        client_name=None,
        budget_amount=cost,
        revenue_amount=money(opportunity.opportunity_value),
        expense_amount=cost,
        status="active",
        milestone_billing="Created from CRM won opportunity.",
    )
    project_profitability(profile)
    db.add(profile)
    return profile


def parse_date(value: Any, label: str, required: bool = False) -> date | None:
    if value in (None, ""):
        if required:
            raise HTTPException(status_code=422, detail=f"{label} is required")
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{label} must be a valid date") from exc


def approval_history(
    db: Session,
    approval: FinanceApproval | None,
    decision: str,
    comments: str | None = None,
    delegation_id: UUID | None = None,
    escalation_level: int = 0,
    actor: str | None = None,
) -> FinanceApprovalHistory:
    row = FinanceApprovalHistory(
        approval_id=getattr(approval, "id", None),
        source_module=(getattr(approval, "approval_type", None) or "").split(":", 1)[0] or None,
        source_record_type=getattr(approval, "related_record_type", None),
        source_record_id=getattr(approval, "related_record_id", None),
        requestor=getattr(approval, "requested_by", None),
        approver=actor or getattr(approval, "approver", None),
        decision=decision,
        comments=comments,
        delegation_id=delegation_id,
        escalation_level=escalation_level,
    )
    db.add(row)
    return row


def default_retention_years(document_type: str) -> int:
    key = document_type.lower()
    if "contract" in key:
        return 10
    if "tax" in key or "invoice" in key or "statement" in key:
        return 7
    return 5


def document_buc(document_type: str) -> str:
    key = document_type.lower()
    if "vendor contract" in key or "contract" in key:
        return "FIN-143"
    if "purchase order" in key or key in {"po", "purchase_order"}:
        return "FIN-144"
    if "grn" in key or "goods receipt" in key:
        return "FIN-145"
    if "bank statement" in key:
        return "FIN-146"
    if "tax" in key or "vat" in key or "wht" in key or "paye" in key:
        return "FIN-147"
    return "FIN-142"


def ensure_document_requirements(payload: dict[str, Any]) -> None:
    document_type = str(payload.get("document_type") or "").lower()
    if not document_type:
        raise HTTPException(status_code=422, detail="Document type is required")
    if "invoice" in document_type and not (payload.get("document_number") or payload.get("invoice_number")):
        raise HTTPException(status_code=422, detail="Invoice number is required")
    if "contract" in document_type and not (payload.get("owner") or payload.get("party_name")):
        raise HTTPException(status_code=422, detail="Contract owner is required")
    if ("purchase order" in document_type or document_type in {"po", "purchase_order"}) and not payload.get("related_record_id"):
        raise HTTPException(status_code=422, detail="Purchase order document must link to a PO record")
    if ("grn" in document_type or "goods receipt" in document_type) and not payload.get("related_record_id"):
        raise HTTPException(status_code=422, detail="GRN document must link to a goods receipt record")
    if "bank statement" in document_type and not (payload.get("document_date") or payload.get("statement_date")):
        raise HTTPException(status_code=422, detail="Statement date is required")
    if any(token in document_type for token in ["tax", "vat", "wht", "paye"]) and not payload.get("filing_period"):
        raise HTTPException(status_code=422, detail="Filing period is required for tax documents")


def create_pending_revenue_from_lpo(db: Session, lpo: CRMCustomerLPO) -> FinanceRevenueRecord:
    existing = (
        db.query(FinanceRevenueRecord)
        .filter(FinanceRevenueRecord.source_module == "crm.lpo", FinanceRevenueRecord.source_record_id == lpo.id)
        .first()
    )
    amount = money(lpo.total_amount or lpo.subtotal)
    if existing:
        existing.amount = amount
        existing.status = "pending"
        return existing
    row = FinanceRevenueRecord(
        source_module="crm.lpo",
        source_record_id=lpo.id,
        revenue_source="CRM LPO received",
        account_id=lpo.account_id,
        deal_id=lpo.opportunity_id,
        revenue_type="Pending Revenue",
        recognition_date=lpo.lpo_date or date.today(),
        amount=amount,
        status="pending",
    )
    db.add(row)
    return row


def create_deferred_revenue_schedule(db: Session, contract: CRMContract) -> list[FinanceDeferredRevenueSchedule]:
    if not contract.end_date:
        return []
    existing = db.query(FinanceDeferredRevenueSchedule).filter(FinanceDeferredRevenueSchedule.contract_id == contract.id).all()
    if existing:
        return existing
    start = contract.start_date
    end = contract.end_date
    months = max((end.year - start.year) * 12 + end.month - start.month + 1, 1)
    monthly_amount = money(contract.contract_value) / Decimal(months)
    rows: list[FinanceDeferredRevenueSchedule] = []
    year, month = start.year, start.month
    for _ in range(months):
        period = date(year, month, 1)
        row = FinanceDeferredRevenueSchedule(
            contract_id=contract.id,
            account_id=contract.account_id,
            schedule_period=period,
            amount=monthly_amount,
            recognition_status="deferred",
            renewal_date=contract.renewal_date,
        )
        db.add(row)
        rows.append(row)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return rows


ACCOUNT_TYPES = {"asset", "liability", "equity", "revenue", "expense", "contra"}
NORMAL_BALANCES = {"asset": "debit", "expense": "debit", "contra": "credit", "liability": "credit", "equity": "credit", "revenue": "credit"}


def account_type_key(value: Any) -> str:
    key = str(value or "").strip().lower()
    if key.endswith("s"):
        key = key[:-1]
    if key not in ACCOUNT_TYPES:
        raise HTTPException(status_code=422, detail="Invalid account type")
    return key


def account_payload(payload: dict[str, Any]) -> dict[str, Any]:
    account_type = account_type_key(payload.get("account_type"))
    normal_balance = str(payload.get("normal_balance") or NORMAL_BALANCES[account_type]).lower()
    if normal_balance not in {"debit", "credit"}:
        raise HTTPException(status_code=422, detail="Normal balance must be debit or credit")
    return {
        "account_code": str(payload.get("account_code") or "").strip(),
        "account_name": str(payload.get("account_name") or "").strip(),
        "account_type": account_type,
        "parent_account_id": payload.get("parent_account_id"),
        "currency": payload.get("currency") or "KES",
        "reporting_category": payload.get("reporting_category"),
        "normal_balance": normal_balance,
        "accounting_basis": payload.get("accounting_basis") or "accrual",
        "is_system_account": bool(payload.get("is_system_account", False)),
        "is_active": bool(payload.get("is_active", True)),
        "description": payload.get("description"),
    }


def validate_account_hierarchy(db: Session, account_id: UUID | None, parent_id: UUID | str | None) -> None:
    if not parent_id:
        return
    parent_uuid = UUID(str(parent_id))
    if account_id and parent_uuid == account_id:
        raise HTTPException(status_code=422, detail="Account cannot be its own parent")
    seen: set[UUID] = set()
    current = db.query(FinanceChartAccount).filter(FinanceChartAccount.id == parent_uuid).first()
    if not current:
        raise HTTPException(status_code=422, detail="Parent account does not exist")
    while current:
        if current.id in seen:
            raise HTTPException(status_code=422, detail="Circular account hierarchy is not allowed")
        if account_id and current.id == account_id:
            raise HTTPException(status_code=422, detail="Circular account hierarchy is not allowed")
        seen.add(current.id)
        current = db.query(FinanceChartAccount).filter(FinanceChartAccount.id == current.parent_account_id).first() if current.parent_account_id else None


def open_period_for_date(db: Session, entry_date: date) -> FinanceFinancialPeriod:
    period = (
        db.query(FinanceFinancialPeriod)
        .filter(FinanceFinancialPeriod.start_date <= entry_date, FinanceFinancialPeriod.end_date >= entry_date)
        .order_by(FinanceFinancialPeriod.start_date.desc())
        .first()
    )
    if not period:
        raise HTTPException(status_code=422, detail="No accounting period covers the journal date")
    if period.status not in {"open", "reopened"}:
        raise HTTPException(status_code=422, detail="Accounting period is not open")
    return period


def active_account(db: Session, account_id: UUID | str) -> FinanceChartAccount:
    account = get_or_404(db, FinanceChartAccount, UUID(str(account_id)), "Chart account")
    if not account.is_active:
        raise HTTPException(status_code=422, detail=f"Account {account.account_code} is inactive")
    return account


def posted_journal_query(db: Session):
    return (
        db.query(
            FinanceChartAccount.id.label("account_id"),
            FinanceChartAccount.account_code,
            FinanceChartAccount.account_name,
            FinanceChartAccount.account_type,
            FinanceChartAccount.reporting_category,
            FinanceChartAccount.normal_balance,
            func.coalesce(func.sum(FinanceJournalLine.debit_amount), 0).label("debit"),
            func.coalesce(func.sum(FinanceJournalLine.credit_amount), 0).label("credit"),
        )
        .join(FinanceJournalLine, FinanceJournalLine.account_id == FinanceChartAccount.id)
        .join(FinanceJournalEntry, FinanceJournalEntry.id == FinanceJournalLine.journal_entry_id)
        .filter(FinanceJournalEntry.status == "posted")
        .group_by(
            FinanceChartAccount.id,
            FinanceChartAccount.account_code,
            FinanceChartAccount.account_name,
            FinanceChartAccount.account_type,
            FinanceChartAccount.reporting_category,
            FinanceChartAccount.normal_balance,
        )
    )


def build_journal(db: Session, payload: dict[str, Any], current_user: UserResponse, *, journal_type: str = "manual") -> FinanceJournalEntry:
    entry_date = date.fromisoformat(str(payload.get("entry_date") or date.today().isoformat()))
    period = open_period_for_date(db, entry_date)
    lines = payload.get("lines") or []
    if len(lines) < 2:
        raise HTTPException(status_code=422, detail="Journal requires at least two lines")
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    clean_lines: list[dict[str, Any]] = []
    for item in lines:
        account = active_account(db, item.get("account_id"))
        debit = money(item.get("debit_amount"))
        credit = money(item.get("credit_amount"))
        if debit < 0 or credit < 0:
            raise HTTPException(status_code=422, detail="Debit and credit amounts cannot be negative")
        if debit and credit:
            raise HTTPException(status_code=422, detail="A journal line cannot contain both debit and credit")
        if not debit and not credit:
            raise HTTPException(status_code=422, detail="Each journal line requires a debit or credit amount")
        total_debit += debit
        total_credit += credit
        clean_lines.append(
            {
                "account_id": account.id,
                "line_description": item.get("line_description") or payload.get("description"),
                "debit_amount": debit,
                "credit_amount": credit,
                "department": item.get("department") or payload.get("department"),
                "cost_center_id": UUID(str(item.get("cost_center_id") or payload.get("cost_center_id"))) if (item.get("cost_center_id") or payload.get("cost_center_id")) else None,
                "project_id": UUID(str(item.get("project_id") or payload.get("project_id"))) if (item.get("project_id") or payload.get("project_id")) else None,
            }
        )
    if total_debit != total_credit:
        raise HTTPException(status_code=422, detail="Total debits must equal total credits")
    journal = FinanceJournalEntry(
        entry_number=payload.get("entry_number") or next_number("JRN"),
        entry_date=entry_date,
        fiscal_period=period.period_name,
        source_module=payload.get("source_module"),
        reference_type=payload.get("reference_type"),
        reference_id=UUID(str(payload.get("reference_id"))) if payload.get("reference_id") else None,
        description=payload.get("description"),
        total_debit=total_debit,
        total_credit=total_credit,
        status=payload.get("status") or "draft",
        journal_type=journal_type,
    )
    db.add(journal)
    db.flush()
    for line in clean_lines:
        db.add(FinanceJournalLine(journal_entry_id=journal.id, **line))
    audit(db, current_user, "FIN-019_JOURNAL_CREATED", "journal_entries", journal.id, f"{journal_type} journal created")
    return journal


def post_journal_core(db: Session, journal: FinanceJournalEntry, current_user: UserResponse, *, require_approved: bool = True) -> FinanceJournalEntry:
    if require_approved and journal.status != "approved":
        raise HTTPException(status_code=422, detail="Only approved journals can be posted")
    open_period_for_date(db, journal.entry_date)
    debit = money(db.query(func.coalesce(func.sum(FinanceJournalLine.debit_amount), 0)).filter(FinanceJournalLine.journal_entry_id == journal.id).scalar())
    credit = money(db.query(func.coalesce(func.sum(FinanceJournalLine.credit_amount), 0)).filter(FinanceJournalLine.journal_entry_id == journal.id).scalar())
    if debit != credit:
        raise HTTPException(status_code=422, detail="Journal debit and credit must balance before posting")
    for line in db.query(FinanceJournalLine).filter(FinanceJournalLine.journal_entry_id == journal.id).all():
        active_account(db, line.account_id)
    journal.total_debit = debit
    journal.total_credit = credit
    journal.status = "posted"
    journal.posted_by = current_user.email
    journal.posted_at = datetime.now(timezone.utc)
    audit(db, current_user, "FIN-019_JOURNAL_POSTED", "journal_entries", journal.id, "Journal posted to ledger")
    return journal


def default_account(db: Session, account_type: str, category_terms: list[str]) -> FinanceChartAccount:
    query = db.query(FinanceChartAccount).filter(FinanceChartAccount.account_type == account_type, FinanceChartAccount.is_active.is_(True))
    for term in category_terms:
        row = query.filter((FinanceChartAccount.reporting_category.ilike(f"%{term}%")) | (FinanceChartAccount.account_name.ilike(f"%{term}%"))).first()
        if row:
            return row
    row = query.first()
    if not row:
        raise HTTPException(status_code=422, detail=f"Missing active {account_type} account mapping")
    return row


def ap_accounts(db: Session, payload: dict[str, Any]) -> tuple[FinanceChartAccount, FinanceChartAccount]:
    debit = active_account(db, payload["debit_account_id"]) if payload.get("debit_account_id") else default_account(db, "expense", ["expense", "cost", "asset"])
    credit = active_account(db, payload["credit_account_id"]) if payload.get("credit_account_id") else default_account(db, "liability", ["payable", "ap"])
    return debit, credit


def payment_accounts(db: Session, payload: dict[str, Any]) -> tuple[FinanceChartAccount, FinanceChartAccount]:
    debit = active_account(db, payload["debit_account_id"]) if payload.get("debit_account_id") else default_account(db, "liability", ["payable", "ap"])
    credit = active_account(db, payload["credit_account_id"]) if payload.get("credit_account_id") else default_account(db, "asset", ["bank", "cash"])
    return debit, credit


def ar_accounts(db: Session, profile: FinanceCustomerBillingProfile | None, payload: dict[str, Any] | None = None) -> tuple[FinanceChartAccount, FinanceChartAccount]:
    payload = payload or {}
    ar = active_account(db, payload["ar_account_id"]) if payload.get("ar_account_id") else active_account(db, profile.ar_account_id) if profile and profile.ar_account_id else default_account(db, "asset", ["receivable", "ar"])
    revenue = active_account(db, payload["revenue_account_id"]) if payload.get("revenue_account_id") else active_account(db, profile.revenue_account_id) if profile and profile.revenue_account_id else default_account(db, "revenue", ["revenue", "sales"])
    return ar, revenue


def payment_terms_due_date(invoice_date: date, terms: str | None) -> date:
    text = str(terms or "Net 30").lower()
    if "7" in text:
        return invoice_date + timedelta(days=7)
    if "14" in text:
        return invoice_date + timedelta(days=14)
    if "60" in text:
        return invoice_date + timedelta(days=60)
    if "90" in text:
        return invoice_date + timedelta(days=90)
    return invoice_date + timedelta(days=30)


def invoice_outstanding(invoice: FinanceInvoice) -> Decimal:
    return max(money(invoice.total_amount) - money(invoice.paid_amount), Decimal("0"))


def aging_bucket(days: int) -> str:
    if days <= 0:
        return "current"
    if days <= 30:
        return "1_30"
    if days <= 60:
        return "31_60"
    if days <= 90:
        return "61_90"
    return "90_plus"


def budget_actual_spend(db: Session, budget: FinanceBudget) -> Decimal:
    actual = money(budget.actual_amount)
    if budget.department:
        actual += money(db.query(func.coalesce(func.sum(FinanceExpense.amount), 0)).filter(FinanceExpense.department == budget.department, FinanceExpense.status.notin_(["rejected", "cancelled"])).scalar())
        actual += money(db.query(func.coalesce(func.sum(FinanceExpenseClaim.amount), 0)).filter(FinanceExpenseClaim.department == budget.department, FinanceExpenseClaim.approval_status == "approved").scalar())
    if budget.project_id:
        actual += money(db.query(func.coalesce(func.sum(FinanceExpense.amount), 0)).filter(FinanceExpense.project_id == budget.project_id, FinanceExpense.status.notin_(["rejected", "cancelled"])).scalar())
        actual += money(db.query(func.coalesce(func.sum(FinanceBill.amount), 0)).filter(FinanceBill.project_id == budget.project_id, FinanceBill.approval_status == "approved").scalar())
    if budget.cost_center_id:
        actual += cost_center_spend(db, budget.cost_center_id)
    return actual


def budget_committed_spend(db: Session, budget: FinanceBudget) -> Decimal:
    committed = money(budget.committed_amount)
    po_query = db.query(FinancePurchaseOrder).filter(FinancePurchaseOrder.approval_status == "approved", FinancePurchaseOrder.status.notin_(["closed", "cancelled"]))
    if budget.project_id:
        po_query = po_query.filter(FinancePurchaseOrder.bill_id.is_(None))
    committed += money(po_query.with_entities(func.coalesce(func.sum(FinancePurchaseOrder.total_amount), 0)).scalar())
    return committed


def available_budget_for(db: Session, *, department: str | None = None, project_id: UUID | None = None, cost_center_id: UUID | None = None) -> tuple[FinanceBudget | None, Decimal]:
    query = db.query(FinanceBudget).filter(FinanceBudget.approval_status == "approved", FinanceBudget.status == "active")
    if department:
        query = query.filter(FinanceBudget.department == department)
    if project_id:
        query = query.filter(FinanceBudget.project_id == project_id)
    if cost_center_id:
        query = query.filter(FinanceBudget.cost_center_id == cost_center_id)
    budget = query.first()
    if not budget:
        return None, Decimal("0")
    available = money(budget.approved_amount) - budget_actual_spend(db, budget) - budget_committed_spend(db, budget)
    return budget, available


def tax_amounts(taxable: Decimal, rate: Decimal, tax_type: str) -> dict[str, Decimal]:
    tax = taxable * rate / Decimal("100")
    if tax_type.lower() == "vat":
        return {"tax": tax, "gross": taxable + tax}
    return {"tax": tax, "gross": taxable - tax if tax_type.lower() == "wht" else taxable}


def create_balanced_two_line_journal(
    db: Session,
    current_user: UserResponse,
    *,
    amount: Decimal,
    debit_account_id: UUID,
    credit_account_id: UUID,
    description: str,
    entry_date: date | None = None,
    source_module: str | None = None,
    reference_type: str | None = None,
    reference_id: UUID | None = None,
    journal_type: str = "auto",
    auto_post: bool = True,
) -> FinanceJournalEntry:
    journal = build_journal(
        db,
        {
            "entry_number": next_number("JRN"),
            "entry_date": (entry_date or date.today()).isoformat(),
            "description": description,
            "source_module": source_module,
            "reference_type": reference_type,
            "reference_id": str(reference_id) if reference_id else None,
            "status": "approved" if auto_post else "draft",
            "lines": [
                {"account_id": str(debit_account_id), "debit_amount": as_float(amount), "credit_amount": 0},
                {"account_id": str(credit_account_id), "debit_amount": 0, "credit_amount": as_float(amount)},
            ],
        },
        current_user,
        journal_type=journal_type,
    )
    if auto_post:
        post_journal_core(db, journal, current_user, require_approved=True)
    return journal


def account_balance(row) -> Decimal:
    balance = money(row.debit) - money(row.credit)
    if str(row.normal_balance).lower() == "credit":
        balance = -balance
    return balance


def cost_center_spend(db: Session, cost_center_id: UUID) -> Decimal:
    journal_spend = (
        db.query(func.coalesce(func.sum(FinanceJournalLine.debit_amount - FinanceJournalLine.credit_amount), 0))
        .join(FinanceJournalEntry, FinanceJournalEntry.id == FinanceJournalLine.journal_entry_id)
        .filter(FinanceJournalEntry.status == "posted", FinanceJournalLine.cost_center_id == cost_center_id)
        .scalar()
    )
    expense_spend = db.query(func.coalesce(func.sum(FinanceExpense.amount), 0)).filter(FinanceExpense.cost_center_id == cost_center_id, FinanceExpense.status.notin_(["cancelled", "rejected"])).scalar()
    allocation_spend = db.query(func.coalesce(func.sum(FinanceCostCenterAllocation.allocation_amount), 0)).filter(FinanceCostCenterAllocation.cost_center_id == cost_center_id).scalar()
    return money(journal_spend) + money(expense_spend) + money(allocation_spend)


def section1_filters(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    company: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    department: str | None = Query(default=None),
    business_unit: str | None = Query(default=None),
    cost_center: str | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    currency: str | None = Query(default=None),
    customer: str | None = Query(default=None),
    vendor: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    posted_status: str | None = Query(default=None),
    budget_period: str | None = Query(default=None),
    financial_year: str | None = Query(default=None),
    accounting_period: str | None = Query(default=None),
) -> dict[str, Any]:
    return filter_meta(
        date_from=date_from,
        date_to=date_to,
        company=company,
        branch=branch,
        department=department,
        business_unit=business_unit,
        cost_center=cost_center,
        project_id=project_id,
        currency=currency,
        customer=customer,
        vendor=vendor,
        approval_status=approval_status,
        posted_status=posted_status,
        budget_period=budget_period,
        financial_year=financial_year,
        accounting_period=accounting_period,
    )


@router.get("/control-center")
def finance_control_center(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return control_center_context(db, current_user, filters)


@router.get("/control-center/dashboard")
def control_center_dashboard(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    data = control_center_context(db, current_user, filters)
    return {
        "buc": "FIN-001",
        "filters": data["filters"],
        "last_refreshed_at": data["last_refreshed_at"],
        "data_stale": data["data_stale"],
        "warning": data["warning"],
        "notes": data["notes"],
        "widgets": {
            "financial_kpis": data["kpis"],
            "cash_position": data["cash_position"],
            "revenue_forecast": data["revenue_forecast"],
            "budget_utilization": data["budget_utilization"],
            "ar_summary": data["ar_summary"],
            "ap_summary": data["ap_summary"],
            "tax_exposure": data["tax_exposure"],
            "project_profitability": data["project_profitability"],
            "approval_queue": data["approval_queue"],
        },
        "drill_downs": {
            "revenue": "/finance/invoices",
            "expenses": "/finance/expense-claims",
            "cash": "/finance/bank-accounts",
            "receivables": "/finance/invoices",
            "payables": "/finance/bills",
            "budgets": "/finance/budgets",
            "projects": "/finance/project-finance",
            "tax": "/finance/tax-records",
            "approvals": "/finance/approvals",
        },
    }


@router.get("/control-center/kpis")
def control_center_kpis(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "kpis")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-002", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], "kpis": data["kpis"]}


@router.get("/control-center/cash-position")
def control_center_cash_position(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "cash-position")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-003", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], **data["cash_position"]}


@router.get("/control-center/revenue-forecast")
def control_center_revenue_forecast(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "revenue-forecast")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-004", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], **data["revenue_forecast"]}


@router.get("/control-center/budget-utilization")
def control_center_budget_utilization(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "budgets")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-005", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], **data["budget_utilization"]}


@router.get("/control-center/ar-summary")
def control_center_ar_summary(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "receivables")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-006", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], **data["ar_summary"]}


@router.get("/control-center/ap-summary")
def control_center_ap_summary(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "payables")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-007", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], **data["ap_summary"]}


@router.get("/control-center/tax-exposure")
def control_center_tax_exposure(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "tax")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-008", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], **data["tax_exposure"]}


@router.get("/control-center/project-profitability")
def control_center_project_profitability(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "project-profitability")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-009", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], "projects": data["project_profitability"]}


@router.get("/control-center/approval-queue")
def control_center_approval_queue(filters: dict[str, Any] = Depends(section1_filters), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "approvals")
    data = control_center_context(db, current_user, filters)
    return {"buc": "FIN-010", "filters": data["filters"], "last_refreshed_at": data["last_refreshed_at"], "approvals": data["approval_queue"]}


@router.post("/control-center/export")
def export_control_center(payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "export", "control-center")
    filters = payload.get("filters") if payload else {}
    data = control_center_context(db, current_user, filters or {})
    audit(db, current_user, "FINANCE_DASHBOARD_EXPORT", "control_center", None, "Finance Control Center export generated")
    db.commit()
    return {"buc": "FIN-001_EXPORT", "format": (payload or {}).get("format", "json"), "exported_at": datetime.now(timezone.utc).isoformat(), "data": data}


@router.post("/general-ledger/chart-of-accounts")
def create_chart_account(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "create", "chart-accounts")
    data = account_payload(payload)
    if not data["account_code"] or not data["account_name"]:
        raise HTTPException(status_code=422, detail="Account code and account name are required")
    if db.query(FinanceChartAccount).filter(FinanceChartAccount.account_code == data["account_code"]).first():
        raise HTTPException(status_code=422, detail="Account code must be unique")
    validate_account_hierarchy(db, None, data["parent_account_id"])
    account = FinanceChartAccount(**data)
    db.add(account)
    db.flush()
    audit(db, current_user, "FIN-011_ACCOUNT_CREATED", "chart_accounts", account.id, f"Created account {account.account_code}")
    db.commit()
    return {"buc": "FIN-011", **serialize(account)}


@router.put("/general-ledger/chart-of-accounts/{account_id}")
def update_chart_account(account_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "update", "chart-accounts")
    account = get_or_404(db, FinanceChartAccount, account_id, "Chart account")
    posted_lines = (
        db.query(FinanceJournalLine.id)
        .join(FinanceJournalEntry, FinanceJournalEntry.id == FinanceJournalLine.journal_entry_id)
        .filter(FinanceJournalLine.account_id == account.id, FinanceJournalEntry.status == "posted")
        .first()
    )
    if payload.get("account_code") and payload["account_code"] != account.account_code and posted_lines:
        raise HTTPException(status_code=422, detail="Account code cannot be changed after posted transactions exist")
    if payload.get("parent_account_id") is not None:
        validate_account_hierarchy(db, account.id, payload.get("parent_account_id"))
        account.parent_account_id = UUID(str(payload["parent_account_id"])) if payload.get("parent_account_id") else None
    for field in ["account_code", "account_name", "currency", "reporting_category", "accounting_basis", "description"]:
        if field in payload:
            setattr(account, field, payload[field])
    if "account_type" in payload:
        account.account_type = account_type_key(payload["account_type"])
        account.normal_balance = NORMAL_BALANCES[account.account_type]
    if "is_active" in payload:
        account.is_active = bool(payload["is_active"])
    audit(db, current_user, "FIN-012_ACCOUNT_UPDATED", "chart_accounts", account.id, "Updated chart account")
    db.commit()
    return {"buc": "FIN-012", **serialize(account)}


@router.post("/general-ledger/chart-of-accounts/{account_id}/deactivate")
def deactivate_chart_account(account_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "update", "chart-accounts")
    account = get_or_404(db, FinanceChartAccount, account_id, "Chart account")
    if account.is_system_account:
        raise HTTPException(status_code=422, detail="System accounts cannot be deactivated manually")
    pending = (
        db.query(FinanceJournalLine.id)
        .join(FinanceJournalEntry, FinanceJournalEntry.id == FinanceJournalLine.journal_entry_id)
        .filter(FinanceJournalLine.account_id == account.id, FinanceJournalEntry.status.in_(["draft", "submitted", "approved"]))
        .first()
    )
    if pending:
        raise HTTPException(status_code=422, detail="Account has pending transactions")
    account.is_active = False
    audit(db, current_user, "FIN-013_ACCOUNT_DEACTIVATED", "chart_accounts", account.id, (payload or {}).get("reason") or "Account deactivated")
    db.commit()
    return {"buc": "FIN-013", **serialize(account)}


@router.post("/general-ledger/chart-of-accounts/{account_id}/hierarchy")
def update_account_hierarchy(account_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    account = get_or_404(db, FinanceChartAccount, account_id, "Chart account")
    validate_account_hierarchy(db, account.id, payload.get("parent_account_id"))
    account.parent_account_id = UUID(str(payload["parent_account_id"])) if payload.get("parent_account_id") else None
    audit(db, current_user, "FIN-014_ACCOUNT_HIERARCHY_UPDATED", "chart_accounts", account.id, "Account hierarchy updated")
    db.commit()
    return {"buc": "FIN-014", **serialize(account)}


@router.post("/general-ledger/periods")
def create_accounting_period(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "create", "financial-periods")
    start = date.fromisoformat(str(payload.get("start_date")))
    end = date.fromisoformat(str(payload.get("end_date")))
    if end < start:
        raise HTTPException(status_code=422, detail="Period end date cannot be before start date")
    overlap = db.query(FinanceFinancialPeriod).filter(FinanceFinancialPeriod.start_date <= end, FinanceFinancialPeriod.end_date >= start).first()
    if overlap:
        raise HTTPException(status_code=422, detail="Accounting periods cannot overlap")
    period = FinanceFinancialPeriod(period_name=payload.get("period_name"), fiscal_year=payload.get("fiscal_year"), start_date=start, end_date=end, status=payload.get("status") or "draft")
    if not period.period_name or not period.fiscal_year:
        raise HTTPException(status_code=422, detail="Fiscal year and period name are required")
    db.add(period)
    db.flush()
    audit(db, current_user, "FIN-015_PERIOD_CREATED", "financial_periods", period.id, f"Created period {period.period_name}")
    db.commit()
    return {"buc": "FIN-015", **serialize(period)}


@router.post("/general-ledger/periods/{period_id}/open")
def open_accounting_period(period_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    period = get_or_404(db, FinanceFinancialPeriod, period_id, "Accounting period")
    period.status = "open"
    audit(db, current_user, "FIN-016_PERIOD_OPENED", "financial_periods", period.id, "Accounting period opened")
    db.commit()
    return {"buc": "FIN-016", **serialize(period)}


@router.post("/general-ledger/periods/{period_id}/close")
def close_accounting_period(period_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    period = get_or_404(db, FinanceFinancialPeriod, period_id, "Accounting period")
    pending = db.query(FinanceJournalEntry).filter(FinanceJournalEntry.entry_date >= period.start_date, FinanceJournalEntry.entry_date <= period.end_date, FinanceJournalEntry.status.in_(["draft", "submitted", "approved"])).count()
    if pending:
        raise HTTPException(status_code=422, detail="Cannot close period with unposted journals")
    period.status = "closed"
    period.closed_by = current_user.email
    period.closed_at = datetime.now(timezone.utc)
    audit(db, current_user, "FIN-017_PERIOD_CLOSED", "financial_periods", period.id, "Accounting period closed")
    db.commit()
    return {"buc": "FIN-017", **serialize(period)}


@router.post("/general-ledger/periods/{period_id}/reopen")
def reopen_accounting_period(period_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Reopening reason is required")
    period = get_or_404(db, FinanceFinancialPeriod, period_id, "Accounting period")
    period.status = "reopened"
    audit(db, current_user, "FIN-018_PERIOD_REOPENED", "financial_periods", period.id, reason)
    db.commit()
    return {"buc": "FIN-018", **serialize(period)}


@router.post("/general-ledger/journals")
def create_general_ledger_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "create", "journal-entries")
    journal = build_journal(db, payload, current_user, journal_type=payload.get("journal_type") or "manual")
    db.commit()
    return {"buc": "FIN-019", **serialize(journal)}


@router.post("/journals")
def create_manual_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "create", "journal-entries")
    if not payload.get("reference_number") and not payload.get("reference_id"):
        payload["reference_type"] = payload.get("reference_type") or "manual_reference"
    journal = build_journal(db, {**payload, "status": payload.get("status") or "draft"}, current_user, journal_type="manual")
    audit(db, current_user, "FIN-033_MANUAL_JOURNAL_DRAFTED", "journal_entries", journal.id, "Manual journal saved as draft")
    db.commit()
    return {"buc": "FIN-033", **serialize(journal)}


@router.post("/recurring-journals")
def create_recurring_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    frequency = str(payload.get("frequency") or "").lower()
    if frequency not in {"daily", "weekly", "monthly", "quarterly", "annual"}:
        raise HTTPException(status_code=422, detail="Invalid recurring journal frequency")
    debit = active_account(db, payload.get("debit_account_id"))
    credit = active_account(db, payload.get("credit_account_id"))
    amount = money(payload.get("amount"))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Recurring amount must be greater than zero")
    start = date.fromisoformat(str(payload.get("start_date") or date.today().isoformat()))
    schedule = FinanceRecurringJournal(
        schedule_name=payload.get("schedule_name") or payload.get("description") or "Recurring Journal",
        start_date=start,
        end_date=date.fromisoformat(str(payload.get("end_date"))) if payload.get("end_date") else None,
        frequency=frequency,
        amount=amount,
        debit_account_id=debit.id,
        credit_account_id=credit.id,
        next_run_date=start,
        approval_required=bool(payload.get("approval_required", True)),
        notes=payload.get("notes") or payload.get("description"),
    )
    db.add(schedule)
    db.flush()
    if payload.get("generate_now"):
        journal = create_balanced_two_line_journal(db, current_user, amount=amount, debit_account_id=debit.id, credit_account_id=credit.id, description=f"Recurring: {schedule.schedule_name}", entry_date=start, source_module="finance.recurring", reference_type="recurring_journal", reference_id=schedule.id, journal_type="recurring", auto_post=not schedule.approval_required)
        schedule.last_generated_journal_id = journal.id
    audit(db, current_user, "FIN-038_RECURRING_JOURNAL_CREATED", "recurring_journals", schedule.id, schedule.frequency)
    db.commit()
    return {"buc": "FIN-038", **serialize(schedule)}


@router.post("/accrual-journals")
def create_accrual_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    incurred = money(payload.get("expense_incurred") or payload.get("revenue_incurred") or payload.get("amount"))
    paid = money(payload.get("expense_paid") or payload.get("revenue_paid"))
    accrual_amount = incurred - paid
    if accrual_amount <= 0:
        raise HTTPException(status_code=422, detail="Accrual amount must be greater than zero")
    debit, credit = ap_accounts(db, payload)
    journal = create_balanced_two_line_journal(db, current_user, amount=accrual_amount, debit_account_id=debit.id, credit_account_id=credit.id, description=payload.get("description") or "Accrual journal", entry_date=date.fromisoformat(str(payload.get("entry_date") or date.today().isoformat())), source_module=payload.get("source_module") or "finance.accrual", reference_type="accrual", reference_id=UUID(str(payload["source_record_id"])) if payload.get("source_record_id") else None, journal_type="accrual", auto_post=False)
    audit(db, current_user, "FIN-039_ACCRUAL_JOURNAL_CREATED", "journal_entries", journal.id, f"Accrual amount {accrual_amount}")
    db.commit()
    return {"buc": "FIN-039", "accrual_amount": as_float(accrual_amount), **serialize(journal)}


@router.post("/adjustment-journals")
def create_adjustment_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Adjustment reason is required")
    journal = build_journal(db, {**payload, "description": payload.get("description") or f"Adjustment: {payload['reason']}", "status": "draft"}, current_user, journal_type="adjustment")
    audit(db, current_user, "FIN-040_ADJUSTMENT_JOURNAL_CREATED", "journal_entries", journal.id, payload["reason"])
    db.commit()
    return {"buc": "FIN-040", **serialize(journal)}


@router.post("/fx-journals")
def create_fx_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    foreign_amount = money(payload.get("foreign_amount"))
    exchange_rate = money(payload.get("exchange_rate"))
    if foreign_amount <= 0 or exchange_rate <= 0:
        raise HTTPException(status_code=422, detail="Foreign amount and exchange rate are required")
    base_amount = foreign_amount * exchange_rate
    debit = active_account(db, payload.get("debit_account_id"))
    credit = active_account(db, payload.get("credit_account_id"))
    journal = create_balanced_two_line_journal(db, current_user, amount=base_amount, debit_account_id=debit.id, credit_account_id=credit.id, description=payload.get("description") or f"FX journal {payload.get('transaction_currency')} to {payload.get('base_currency')}", entry_date=date.fromisoformat(str(payload.get("entry_date") or date.today().isoformat())), source_module="finance.fx", reference_type="foreign_currency", journal_type="foreign_currency", auto_post=False)
    journal.description = f"{journal.description or ''} | {foreign_amount} {payload.get('transaction_currency')} x {exchange_rate} = {base_amount} {payload.get('base_currency')}"
    audit(db, current_user, "FIN-041_FX_JOURNAL_CREATED", "journal_entries", journal.id, f"Base amount {base_amount}")
    db.commit()
    return {"buc": "FIN-041", "base_amount": as_float(base_amount), **serialize(journal)}


@router.post("/intercompany-journals")
def create_intercompany_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    amount = money(payload.get("amount"))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Intercompany amount must be greater than zero")
    required = ["entity_a_receivable_account_id", "entity_a_revenue_account_id", "entity_b_expense_account_id", "entity_b_payable_account_id"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing intercompany accounts: {', '.join(missing)}")
    journal = build_journal(
        db,
        {
            "entry_number": next_number("JRN-IC"),
            "entry_date": payload.get("entry_date") or date.today().isoformat(),
            "description": payload.get("description") or f"Intercompany journal {payload.get('entity_a')} / {payload.get('entity_b')}",
            "source_module": "finance.intercompany",
            "reference_type": "intercompany",
            "status": "draft",
            "lines": [
                {"account_id": payload["entity_a_receivable_account_id"], "debit_amount": as_float(amount), "credit_amount": 0, "line_description": "Entity A receivable"},
                {"account_id": payload["entity_a_revenue_account_id"], "debit_amount": 0, "credit_amount": as_float(amount), "line_description": "Entity A revenue"},
                {"account_id": payload["entity_b_expense_account_id"], "debit_amount": as_float(amount), "credit_amount": 0, "line_description": "Entity B expense"},
                {"account_id": payload["entity_b_payable_account_id"], "debit_amount": 0, "credit_amount": as_float(amount), "line_description": "Entity B payable"},
            ],
        },
        current_user,
        journal_type="intercompany",
    )
    audit(db, current_user, "FIN-042_INTERCOMPANY_JOURNAL_CREATED", "journal_entries", journal.id, "Intercompany reciprocal journal created")
    db.commit()
    return {"buc": "FIN-042", **serialize(journal)}


@router.post("/general-ledger/journals/{journal_id}/post")
def post_general_ledger_journal(journal_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    journal = get_or_404(db, FinanceJournalEntry, journal_id, "Journal")
    post_journal_core(db, journal, current_user, require_approved=True)
    db.commit()
    return {"buc": "FIN-019", **serialize(journal)}


@router.post("/general-ledger/journals/{journal_id}/reverse")
def reverse_general_ledger_journal(journal_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Reversal reason is required")
    journal = get_or_404(db, FinanceJournalEntry, journal_id, "Journal")
    if journal.status != "posted":
        raise HTTPException(status_code=422, detail="Only posted journals can be reversed")
    reversal_lines = [
        {
            "account_id": str(line.account_id),
            "debit_amount": as_float(line.credit_amount),
            "credit_amount": as_float(line.debit_amount),
            "line_description": f"Reversal: {line.line_description or journal.description or journal.entry_number}",
            "department": line.department,
            "cost_center_id": str(line.cost_center_id) if line.cost_center_id else None,
            "project_id": str(line.project_id) if line.project_id else None,
        }
        for line in db.query(FinanceJournalLine).filter(FinanceJournalLine.journal_entry_id == journal.id).all()
    ]
    reversal = build_journal(
        db,
        {
            "entry_number": next_number("JRN-REV"),
            "entry_date": payload.get("entry_date") or journal.entry_date.isoformat(),
            "description": f"Reversal of {journal.entry_number}: {reason}",
            "source_module": journal.source_module,
            "reference_type": "journal_reversal",
            "reference_id": str(journal.id),
            "lines": reversal_lines,
            "status": "draft",
        },
        current_user,
        journal_type="reversal",
    )
    reversal.reversed_entry_id = journal.id
    reversal.reversal_reason = reason
    post_journal_core(db, reversal, current_user, require_approved=False)
    journal.status = "reversed"
    audit(db, current_user, "FIN-020_JOURNAL_REVERSED", "journal_entries", journal.id, reason)
    db.commit()
    return {"buc": "FIN-020", "reversal": serialize(reversal), "original": serialize(journal)}


@router.post("/general-ledger/journals/auto-generate")
def auto_generate_general_ledger_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    amount = money(payload.get("amount"))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be greater than zero")
    debit_account_id = payload.get("debit_account_id")
    credit_account_id = payload.get("credit_account_id")
    if not debit_account_id or not credit_account_id:
        rule = (
            db.query(FinanceGLMappingRule)
            .filter(FinanceGLMappingRule.source_module == payload.get("source_module"), FinanceGLMappingRule.transaction_type == payload.get("transaction_type"), FinanceGLMappingRule.status == "active")
            .first()
        )
        if not rule:
            raise HTTPException(status_code=422, detail="Missing GL mapping for source transaction")
        debit_account_id = rule.debit_account_id
        credit_account_id = rule.credit_account_id
    journal = build_journal(
        db,
        {
            "entry_number": next_number("JRN-AUTO"),
            "entry_date": payload.get("entry_date") or date.today().isoformat(),
            "description": payload.get("description") or f"Auto journal from {payload.get('source_module')}",
            "source_module": payload.get("source_module"),
            "reference_type": payload.get("transaction_type"),
            "reference_id": payload.get("source_record_id"),
            "cost_center_id": payload.get("cost_center_id"),
            "project_id": payload.get("project_id"),
            "lines": [
                {"account_id": str(debit_account_id), "debit_amount": as_float(amount), "credit_amount": 0},
                {"account_id": str(credit_account_id), "debit_amount": 0, "credit_amount": as_float(amount)},
            ],
            "status": "draft",
        },
        current_user,
        journal_type="auto",
    )
    if payload.get("auto_post"):
        journal.status = "approved"
        post_journal_core(db, journal, current_user, require_approved=True)
    event(db, payload.get("source_module") or "system", "finance.journal.auto_generated", "journal_entries", journal.id, payload)
    audit(db, current_user, "FIN-021_AUTO_JOURNAL_GENERATED", "journal_entries", journal.id, "Auto journal generated through GL posting engine")
    db.commit()
    return {"buc": "FIN-021", **serialize(journal)}


@router.get("/general-ledger/reports/trial-balance")
def general_ledger_trial_balance(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = posted_journal_query(db).order_by(FinanceChartAccount.account_code).all()
    result = [
        {
            "account_id": str(row.account_id),
            "account_code": row.account_code,
            "account_name": row.account_name,
            "account_type": row.account_type,
            "debit": as_float(row.debit),
            "credit": as_float(row.credit),
            "balance": as_float(money(row.debit) - money(row.credit)),
        }
        for row in rows
    ]
    debit_total = sum(row["debit"] for row in result)
    credit_total = sum(row["credit"] for row in result)
    return {"buc": "FIN-022", "rows": result, "total_debit": debit_total, "total_credit": credit_total, "balanced": round(debit_total, 2) == round(credit_total, 2)}


@router.get("/general-ledger/reports/balance-sheet")
def general_ledger_balance_sheet(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = posted_journal_query(db).all()
    assets = sum(account_balance(row) for row in rows if row.account_type == "asset")
    liabilities = sum(account_balance(row) for row in rows if row.account_type == "liability")
    equity = sum(account_balance(row) for row in rows if row.account_type == "equity")
    return {"buc": "FIN-023", "assets": as_float(assets), "liabilities": as_float(liabilities), "equity": as_float(equity), "balanced": round(as_float(assets), 2) == round(as_float(liabilities + equity), 2)}


@router.get("/general-ledger/reports/profit-loss")
def general_ledger_profit_loss(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = posted_journal_query(db).all()
    revenue = sum(account_balance(row) for row in rows if row.account_type == "revenue")
    expenses = sum(account_balance(row) for row in rows if row.account_type == "expense")
    gross_profit = revenue - expenses
    return {"buc": "FIN-024", "revenue": as_float(revenue), "operating_expenses": as_float(expenses), "gross_profit": as_float(gross_profit), "operating_profit": as_float(gross_profit), "net_profit": as_float(gross_profit)}


@router.get("/general-ledger/reports/cash-flow")
def general_ledger_cash_flow(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = posted_journal_query(db).filter((FinanceChartAccount.reporting_category.ilike("%cash%")) | (FinanceChartAccount.account_name.ilike("%cash%")) | (FinanceChartAccount.account_name.ilike("%bank%"))).all()
    inflow = sum(money(row.debit) for row in rows)
    outflow = sum(money(row.credit) for row in rows)
    return {"buc": "FIN-025", "opening_cash": 0, "cash_inflows": as_float(inflow), "cash_outflows": as_float(outflow), "closing_cash": as_float(inflow - outflow)}


@router.post("/cost-center-management/cost-centers")
def create_cost_center(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "create", "cost-centers")
    code = str(payload.get("code") or payload.get("cost_center_code") or "").strip()
    name = str(payload.get("name") or payload.get("cost_center_name") or "").strip()
    if not code or not name or not payload.get("department"):
        raise HTTPException(status_code=422, detail="Cost center code, name, and department are required")
    if db.query(FinanceCostCenter).filter(FinanceCostCenter.cost_center_code == code).first():
        raise HTTPException(status_code=422, detail="Cost center code must be unique")
    manager_id = payload.get("manager_employee_id") or payload.get("owner_employee_id")
    if manager_id:
        active_employee(db, manager_id)
    center = FinanceCostCenter(cost_center_code=code, cost_center_name=name, department=payload.get("department"), branch=payload.get("branch"), owner_employee_id=payload.get("owner_employee_id") or manager_id, manager_employee_id=manager_id, status=payload.get("status") or "active")
    db.add(center)
    db.flush()
    audit(db, current_user, "FIN-026_COST_CENTER_CREATED", "cost_centers", center.id, f"Created cost center {center.cost_center_code}")
    db.commit()
    return {"buc": "FIN-026", **serialize(center)}


@router.put("/cost-center-management/cost-centers/{cost_center_id}")
def update_cost_center(cost_center_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    center = get_or_404(db, FinanceCostCenter, cost_center_id, "Cost center")
    manager_id = payload.get("manager_employee_id")
    if manager_id:
        active_employee(db, manager_id)
    for field, attr in {"cost_center_name": "cost_center_name", "name": "cost_center_name", "department": "department", "branch": "branch", "manager_employee_id": "manager_employee_id", "owner_employee_id": "owner_employee_id", "status": "status"}.items():
        if field in payload:
            setattr(center, attr, payload[field])
    audit(db, current_user, "FIN-027_COST_CENTER_UPDATED", "cost_centers", center.id, "Updated cost center")
    db.commit()
    return {"buc": "FIN-027", **serialize(center)}


@router.post("/cost-center-management/cost-centers/{cost_center_id}/assign")
def assign_cost_center(cost_center_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    center = get_or_404(db, FinanceCostCenter, cost_center_id, "Cost center")
    if center.status != "active":
        raise HTTPException(status_code=422, detail="Only active cost centers can be assigned")
    employee = active_employee(db, payload.get("employee_id")) if payload.get("employee_id") else None
    effective_from = date.fromisoformat(str(payload.get("effective_from") or date.today().isoformat()))
    if employee:
        existing = db.query(FinanceCostCenterAssignment).filter(FinanceCostCenterAssignment.employee_id == employee.id, FinanceCostCenterAssignment.status == "active", FinanceCostCenterAssignment.effective_to.is_(None)).all()
        for item in existing:
            item.effective_to = effective_from
            item.status = "closed"
        employee.cost_center_code = center.cost_center_code
        employee.finance_mapping_status = "mapped"
    assignment = FinanceCostCenterAssignment(
        cost_center_id=center.id,
        employee_id=getattr(employee, "id", None),
        source_record_type=payload.get("source_record_type"),
        source_record_id=UUID(str(payload.get("source_record_id"))) if payload.get("source_record_id") else None,
        effective_from=effective_from,
        effective_to=date.fromisoformat(str(payload.get("effective_to"))) if payload.get("effective_to") else None,
        allocation_percent=money(payload.get("allocation_percent") or 100),
        reason=payload.get("reason"),
    )
    db.add(assignment)
    db.flush()
    audit(db, current_user, "FIN-028_COST_CENTER_ASSIGNED", "cost_center_assignments", assignment.id, f"Assigned {center.cost_center_code}")
    db.commit()
    return {"buc": "FIN-028", "assignment": serialize(assignment), "cost_center": serialize(center)}


@router.post("/cost-center-management/allocations")
def allocate_cost_center_expense(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    allocations = payload.get("allocations") or []
    if not allocations:
        raise HTTPException(status_code=422, detail="At least one allocation is required")
    percent_total = sum(money(item.get("allocation_percent")) for item in allocations)
    if percent_total != Decimal("100"):
        raise HTTPException(status_code=422, detail="Allocation percentages must total 100%")
    base_amount = money(payload.get("amount"))
    source_record_type = payload.get("source_record_type") or "manual"
    source_record_id = UUID(str(payload.get("source_record_id"))) if payload.get("source_record_id") else None
    if not base_amount and source_record_type == "expense" and source_record_id:
        base_amount = money(get_or_404(db, FinanceExpense, UUID(str(source_record_id)), "Expense").amount)
    if not base_amount and source_record_type == "expense_claim" and source_record_id:
        base_amount = money(get_or_404(db, FinanceExpenseClaim, UUID(str(source_record_id)), "Expense claim").amount)
    if base_amount <= 0:
        raise HTTPException(status_code=422, detail="Allocation amount must be greater than zero")
    rows = []
    for item in allocations:
        center = get_or_404(db, FinanceCostCenter, UUID(str(item.get("cost_center_id"))), "Cost center")
        amount = base_amount * money(item.get("allocation_percent")) / Decimal("100")
        allocation = FinanceCostCenterAllocation(cost_center_id=center.id, source_record_type=source_record_type, source_record_id=source_record_id, allocation_percent=money(item.get("allocation_percent")), allocation_amount=amount)
        db.add(allocation)
        db.flush()
        rows.append(serialize(allocation))
    audit(db, current_user, "FIN-029_COST_CENTER_ALLOCATED", "cost_center_allocations", None, f"Allocated {base_amount}")
    db.commit()
    return {"buc": "FIN-029", "base_amount": as_float(base_amount), "allocations": rows}


@router.get("/cost-center-management/cost-centers/{cost_center_id}/expenses")
def cost_center_expense_tracking(cost_center_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    center = get_or_404(db, FinanceCostCenter, cost_center_id, "Cost center")
    spend = cost_center_spend(db, center.id)
    return {"buc": "FIN-030", "cost_center": serialize(center), "spend": as_float(spend)}


@router.get("/cost-center-management/reports/departments")
def department_cost_reporting(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = []
    for department, in db.query(FinanceCostCenter.department).filter(FinanceCostCenter.department.isnot(None)).distinct().all():
        centers = db.query(FinanceCostCenter).filter(FinanceCostCenter.department == department).all()
        cost = sum(cost_center_spend(db, center.id) for center in centers)
        rows.append({"department": department, "cost_center_count": len(centers), "department_cost": as_float(cost)})
    return {"buc": "FIN-031", "departments": rows}


@router.get("/cost-center-management/reports/branches")
def branch_cost_reporting(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = []
    for branch, in db.query(FinanceCostCenter.branch).filter(FinanceCostCenter.branch.isnot(None)).distinct().all():
        centers = db.query(FinanceCostCenter).filter(FinanceCostCenter.branch == branch).all()
        cost = sum(cost_center_spend(db, center.id) for center in centers)
        revenue = money(db.query(func.coalesce(func.sum(FinanceRevenueRecord.amount), 0)).filter(FinanceRevenueRecord.status == "recognized").scalar())
        margin = revenue - cost
        rows.append({"branch": branch, "cost_center_count": len(centers), "branch_cost": as_float(cost), "branch_revenue": as_float(revenue), "branch_margin": as_float(margin), "branch_margin_percent": as_float((margin / revenue * Decimal("100")) if revenue else Decimal("0"))})
    return {"buc": "FIN-032", "branches": rows}


@router.get("/reports/trial-balance")
def trial_balance(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = (
        db.query(
            FinanceChartAccount.account_code,
            FinanceChartAccount.account_name,
            FinanceChartAccount.account_type,
            func.coalesce(func.sum(FinanceJournalLine.debit_amount), 0).label("debit"),
            func.coalesce(func.sum(FinanceJournalLine.credit_amount), 0).label("credit"),
        )
        .outerjoin(FinanceJournalLine, FinanceJournalLine.account_id == FinanceChartAccount.id)
        .group_by(FinanceChartAccount.account_code, FinanceChartAccount.account_name, FinanceChartAccount.account_type)
        .order_by(FinanceChartAccount.account_code)
        .all()
    )
    return [{"account_code": r.account_code, "account_name": r.account_name, "account_type": r.account_type, "debit": as_float(r.debit), "credit": as_float(r.credit), "balance": as_float(money(r.debit) - money(r.credit))} for r in rows]


@router.get("/reports/balance-sheet")
def balance_sheet(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    tb = trial_balance(db, current_user)
    assets = sum(row["balance"] for row in tb if str(row["account_type"]).lower() == "asset")
    liabilities = -sum(row["balance"] for row in tb if str(row["account_type"]).lower() == "liability")
    equity = -sum(row["balance"] for row in tb if str(row["account_type"]).lower() == "equity")
    return {"assets": assets, "liabilities": liabilities, "equity": equity, "balanced": round(assets, 2) == round(liabilities + equity, 2)}


@router.get("/reports/profit-loss")
def profit_loss(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    revenue = money(db.query(func.coalesce(func.sum(FinanceRevenueRecord.amount), 0)).filter(FinanceRevenueRecord.status == "recognized").scalar())
    expenses = money(db.query(func.coalesce(func.sum(FinanceExpense.amount), 0)).scalar()) + money(db.query(func.coalesce(func.sum(FinanceExpenseClaim.amount), 0)).scalar())
    gross_profit = revenue - expenses
    return {"revenue": as_float(revenue), "operating_expenses": as_float(expenses), "gross_profit": as_float(gross_profit), "ebitda": as_float(gross_profit)}


@router.get("/reports/cash-flow")
def cash_flow(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    inflow = money(db.query(func.coalesce(func.sum(FinanceReceipt.amount), 0)).scalar())
    outflow = money(db.query(func.coalesce(func.sum(FinancePayment.amount), 0)).scalar())
    transfers = money(db.query(func.coalesce(func.sum(FinanceBankTransaction.amount), 0)).filter(FinanceBankTransaction.transaction_type == "Transfer").scalar())
    return {"cash_inflow": as_float(inflow), "cash_outflow": as_float(outflow), "net_cash_flow": as_float(inflow - outflow), "transfers": as_float(transfers)}


@router.post("/journals/{journal_id}/approve")
def approve_journal(journal_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    journal = get_or_404(db, FinanceJournalEntry, journal_id, "Journal")
    debit = money(db.query(func.coalesce(func.sum(FinanceJournalLine.debit_amount), 0)).filter(FinanceJournalLine.journal_entry_id == journal.id).scalar() or journal.total_debit)
    credit = money(db.query(func.coalesce(func.sum(FinanceJournalLine.credit_amount), 0)).filter(FinanceJournalLine.journal_entry_id == journal.id).scalar() or journal.total_credit)
    if debit != credit:
        raise HTTPException(status_code=422, detail="Journal debit and credit must balance before approval")
    journal.status = "approved"
    journal.approved_by = current_user.email
    audit(db, current_user, "FIN-034_JOURNAL_APPROVED", "journal_entries", journal.id, "Journal approved")
    db.commit()
    return serialize(journal)


@router.post("/journals/{journal_id}/reject")
def reject_journal(journal_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    journal = get_or_404(db, FinanceJournalEntry, journal_id, "Journal")
    journal.status = "rejected"
    journal.rejection_reason = reason
    audit(db, current_user, "FIN-035_JOURNAL_REJECTED", "journal_entries", journal.id, reason)
    db.commit()
    return serialize(journal)


@router.post("/journals/{journal_id}/post")
def post_journal(journal_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    journal = get_or_404(db, FinanceJournalEntry, journal_id, "Journal")
    post_journal_core(db, journal, current_user, require_approved=True)
    db.commit()
    return serialize(journal)


@router.post("/journals/{journal_id}/reverse")
def reverse_journal(journal_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    journal = get_or_404(db, FinanceJournalEntry, journal_id, "Journal")
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Reversal reason is required")
    reversal = FinanceJournalEntry(
        entry_number=next_number("JRN-REV"),
        entry_date=date.fromisoformat(str(payload.get("entry_date"))) if payload.get("entry_date") else journal.entry_date,
        fiscal_period=journal.fiscal_period,
        source_module=journal.source_module,
        reference_type="journal_reversal",
        reference_id=journal.id,
        description=f"Reversal of {journal.entry_number}: {reason}",
        total_debit=journal.total_credit,
        total_credit=journal.total_debit,
        status="posted",
        posted_by=current_user.email,
        posted_at=datetime.now(timezone.utc),
        reversed_entry_id=journal.id,
        reversal_reason=reason,
        journal_type="reversal",
    )
    db.add(reversal)
    db.flush()
    for line in db.query(FinanceJournalLine).filter(FinanceJournalLine.journal_entry_id == journal.id).all():
        db.add(FinanceJournalLine(journal_entry_id=reversal.id, account_id=line.account_id, line_description=f"Reversal: {line.line_description or ''}", debit_amount=line.credit_amount, credit_amount=line.debit_amount, department=line.department, cost_center_id=line.cost_center_id, project_id=line.project_id))
    journal.status = "reversed"
    audit(db, current_user, "FIN-037_JOURNAL_REVERSED", "journal_entries", journal.id, reason)
    db.commit()
    return serialize(reversal)


@router.post("/journals/auto-generate")
def auto_generate_journal(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    source_module = payload.get("source_module") or "system"
    amount = money(payload.get("amount"))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be greater than zero")
    journal = FinanceJournalEntry(entry_number=next_number("JRN-AUTO"), entry_date=date.today(), source_module=source_module, description=payload.get("description") or "Auto-generated journal", total_debit=amount, total_credit=amount, status="draft", journal_type=payload.get("journal_type") or "auto")
    db.add(journal)
    audit(db, current_user, "FIN-021_AUTO_JOURNAL_GENERATED", "journal_entries", journal.id, source_module)
    db.commit()
    return serialize(journal)


@router.post("/expense-claims/calculate")
def calculate_expense_claim(payload: dict[str, Any]):
    category = str(payload.get("expense_category") or "").lower()
    amount = money(payload.get("amount"))
    if "mileage" in category:
        amount = money(payload.get("distance")) * money(payload.get("rate") or payload.get("mileage_rate"))
    elif "per diem" in category or "per_diem" in category:
        amount = money(payload.get("days") or payload.get("per_diem_days")) * money(payload.get("rate") or payload.get("per_diem_rate"))
    return {"amount": as_float(amount), "formula": "distance * rate" if "mileage" in category else "days * rate" if "per" in category else "manual"}


@router.post("/expense-claims/{claim_id}/approve")
def approve_expense_claim(claim_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    claim = get_or_404(db, FinanceExpenseClaim, claim_id, "Expense claim")
    active_employee(db, claim.employee_id)
    claim.approval_status = "approved"
    audit(db, current_user, "FIN-069_EXPENSE_APPROVED", "expense_claims", claim.id, "Expense claim approved")
    db.commit()
    return serialize(claim)


@router.post("/expense-claims/{claim_id}/reject")
def reject_expense_claim(claim_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    claim = get_or_404(db, FinanceExpenseClaim, claim_id, "Expense claim")
    claim.approval_status = "rejected"
    claim.notes = f"{claim.notes or ''}\nRejected: {payload['reason']}".strip()
    audit(db, current_user, "FIN-070_EXPENSE_REJECTED", "expense_claims", claim.id, payload["reason"])
    db.commit()
    return serialize(claim)


@router.post("/expense-claims/{claim_id}/reimburse")
def reimburse_expense_claim(claim_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    claim = get_or_404(db, FinanceExpenseClaim, claim_id, "Expense claim")
    if claim.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Only approved expense claims can be reimbursed")
    claim.reimbursement_status = "paid"
    db.add(FinancePayment(payment_number=next_number("EXP-PAY"), payment_type="Expense", payment_date=date.today(), amount=claim.amount, status="paid", approved_by=current_user.email, notes=f"Reimbursement for {claim.claim_number}"))
    audit(db, current_user, "FIN-071_EXPENSE_REIMBURSED", "expense_claims", claim.id, "Expense reimbursed")
    db.commit()
    return serialize(claim)


@router.get("/budgets/{budget_id}/variance")
def budget_variance(budget_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    budget = get_or_404(db, FinanceBudget, budget_id, "Budget")
    variance = money(budget.actual_amount) - money(budget.approved_amount)
    variance_percent = (variance / money(budget.approved_amount) * Decimal("100")) if money(budget.approved_amount) else Decimal("0")
    return {"budget_id": str(budget.id), "budget": as_float(budget.approved_amount), "actual": as_float(budget.actual_amount), "variance": as_float(variance), "variance_percent": as_float(variance_percent)}


@router.post("/budgets/{budget_id}/approve")
def approve_budget(budget_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    budget = get_or_404(db, FinanceBudget, budget_id, "Budget")
    budget.approval_status = "approved"
    budget.status = "active"
    audit(db, current_user, "FIN-083_BUDGET_APPROVED", "budgets", budget.id, "Budget approved")
    db.commit()
    return serialize(budget)


@router.post("/budgets/{budget_id}/transfer")
def transfer_budget(budget_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    source = get_or_404(db, FinanceBudget, budget_id, "Source budget")
    target = get_or_404(db, FinanceBudget, UUID(str(payload.get("target_budget_id"))), "Target budget")
    amount = money(payload.get("amount"))
    if amount <= 0 or amount > money(source.approved_amount):
        raise HTTPException(status_code=422, detail="Transfer amount must be positive and available in source budget")
    source.approved_amount = money(source.approved_amount) - amount
    target.approved_amount = money(target.approved_amount) + amount
    audit(db, current_user, "FIN-085_BUDGET_TRANSFERRED", "budgets", source.id, f"Transferred {amount} to {target.budget_name}")
    db.commit()
    return {"source": serialize(source), "target": serialize(target)}


@router.post("/purchase-orders/{po_id}/three-way-match")
def three_way_match(po_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    po = get_or_404(db, FinancePurchaseOrder, po_id, "Purchase order")
    bill = get_or_404(db, FinanceBill, UUID(str(payload.get("bill_id") or po.bill_id)), "Supplier invoice")
    grn_received = payload.get("grn_received", po.goods_received_status in {"received", "partial"})
    amount_match = money(po.total_amount) == money(bill.amount)
    po.bill_id = bill.id
    po.goods_received_status = "received" if grn_received else po.goods_received_status
    po.invoice_match_status = "matched" if amount_match and grn_received else "exception"
    audit(db, current_user, "FIN-098_PROCUREMENT_3WAY_MATCH", "purchase_orders", po.id, po.invoice_match_status)
    db.commit()
    return {"po": serialize(po), "bill": serialize(bill), "matched": amount_match and bool(grn_received)}


@router.post("/vendors")
def create_vendor(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "create", "vendors")
    vendor_code = str(payload.get("vendor_code") or next_number("VEN")).strip()
    vendor_name = str(payload.get("vendor_name") or "").strip()
    if not vendor_name:
        raise HTTPException(status_code=422, detail="Vendor name is required")
    duplicate_query = db.query(FinanceVendor).filter((FinanceVendor.vendor_code == vendor_code) | (FinanceVendor.vendor_name.ilike(vendor_name)))
    duplicate = duplicate_query.first()
    if not duplicate and payload.get("tax_pin"):
        duplicate = db.query(FinanceVendor).filter(FinanceVendor.tax_pin == payload.get("tax_pin")).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Potential duplicate vendor detected")
    vendor = FinanceVendor(
        vendor_code=vendor_code,
        vendor_name=vendor_name,
        vendor_type=payload.get("vendor_type"),
        tax_pin=payload.get("tax_pin"),
        address=payload.get("address"),
        contact_person=payload.get("contact_person"),
        email=payload.get("email"),
        phone=payload.get("phone"),
        bank_details=payload.get("bank_details"),
        payment_terms=payload.get("payment_terms"),
        onboarding_status="draft",
        verification_status="pending",
        status=payload.get("status") or "inactive",
        notes=payload.get("notes"),
    )
    db.add(vendor)
    db.flush()
    audit(db, current_user, "FIN-043_VENDOR_CREATED", "vendors", vendor.id, f"Vendor {vendor.vendor_name} created")
    db.commit()
    return {"buc": "FIN-043", **serialize(vendor)}


@router.post("/vendor-onboarding")
def vendor_onboarding(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    vendor = get_or_404(db, FinanceVendor, UUID(str(payload.get("vendor_id"))), "Vendor")
    required = payload.get("required_documents") or ["Certificate of Incorporation", "Tax PIN", "VAT Certificate", "Bank Letter", "Contracts"]
    submitted = payload.get("submitted_documents") or []
    missing = [doc for doc in required if doc not in submitted]
    status_value = "complete" if not missing else "incomplete"
    vendor.onboarding_status = status_value
    vendor.risk_profile = payload.get("risk_profile") or vendor.risk_profile
    if status_value == "complete" and vendor.verification_status == "verified":
        vendor.status = "active"
    record = FinanceVendorOnboarding(
        vendor_id=vendor.id,
        required_documents=", ".join(required),
        submitted_documents=", ".join(submitted),
        compliance_status="ready" if not missing else "missing_documents",
        risk_profile=vendor.risk_profile,
        status=status_value,
        reviewed_by=current_user.email,
        reviewed_at=datetime.now(timezone.utc),
        notes=f"Missing: {', '.join(missing)}" if missing else payload.get("notes"),
    )
    db.add(record)
    db.flush()
    audit(db, current_user, "FIN-044_VENDOR_ONBOARDING", "vendor_onboarding", record.id, record.status)
    db.commit()
    return {"buc": "FIN-044", "vendor": serialize(vendor), "onboarding": serialize(record), "missing_documents": missing}


@router.post("/vendors/{vendor_id}/verify")
def verify_vendor(vendor_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    vendor = get_or_404(db, FinanceVendor, vendor_id, "Vendor")
    statuses = {
        "tax_status": payload.get("tax_status") or "passed",
        "sanctions_status": payload.get("sanctions_status") or "passed",
        "blacklist_status": payload.get("blacklist_status") or "passed",
        "document_status": payload.get("document_status") or "passed",
    }
    failed = [name for name, value in statuses.items() if str(value).lower() in {"failed", "blocked", "invalid"}]
    result = "failed" if failed else "verified"
    vendor.verification_status = result
    vendor.verified_by = current_user.email
    vendor.verified_at = datetime.now(timezone.utc)
    if result == "verified" and vendor.onboarding_status == "complete":
        vendor.status = "active"
    elif result == "failed":
        vendor.status = "blocked"
    verification = FinanceVendorVerification(vendor_id=vendor.id, result=result, reviewed_by=current_user.email, reviewed_at=datetime.now(timezone.utc), next_review_date=date.fromisoformat(str(payload.get("next_review_date"))) if payload.get("next_review_date") else None, notes=payload.get("notes"), **statuses)
    db.add(verification)
    db.flush()
    audit(db, current_user, "FIN-045_VENDOR_VERIFIED", "vendor_verifications", verification.id, result)
    db.commit()
    return {"buc": "FIN-045", "vendor": serialize(vendor), "verification": serialize(verification), "failed_checks": failed}


@router.post("/ap/invoices")
def receive_supplier_invoice(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    vendor = get_or_404(db, FinanceVendor, UUID(str(payload.get("vendor_id"))), "Vendor")
    if vendor.status in {"blocked", "inactive"} and not payload.get("allow_inactive_vendor"):
        raise HTTPException(status_code=422, detail="Vendor must be active or explicitly allowed for invoice capture")
    bill_number = str(payload.get("invoice_number") or payload.get("bill_number") or "").strip()
    if not bill_number:
        raise HTTPException(status_code=422, detail="Supplier invoice number is required")
    if db.query(FinanceBill).filter(FinanceBill.vendor_id == vendor.id, FinanceBill.bill_number == bill_number).first():
        raise HTTPException(status_code=409, detail="Duplicate supplier invoice detected")
    document_id = payload.get("document_id")
    if not document_id and not payload.get("file_url") and not payload.get("attachment_url"):
        raise HTTPException(status_code=422, detail="Invoice attachment is required")
    document = None
    if not document_id:
        document = FinanceDocument(document_title=f"Supplier Invoice {bill_number}", document_type="Supplier Invoice", related_record_type="bill", file_name=payload.get("file_name") or bill_number, file_url=payload.get("file_url") or payload.get("attachment_url"), uploaded_by=current_user.email)
        db.add(document)
        db.flush()
        document_id = document.id
    bill = FinanceBill(
        vendor_id=vendor.id,
        purchase_order_id=UUID(str(payload.get("purchase_order_id"))) if payload.get("purchase_order_id") else None,
        document_id=UUID(str(document_id)),
        bill_number=bill_number,
        bill_date=date.fromisoformat(str(payload.get("invoice_date") or payload.get("bill_date") or date.today().isoformat())),
        due_date=date.fromisoformat(str(payload.get("due_date"))) if payload.get("due_date") else None,
        amount=money(payload.get("amount")),
        tax_amount=money(payload.get("tax_amount")),
        currency=payload.get("currency") or "KES",
        invoice_quantity=money(payload.get("invoice_quantity")),
        status="pending_matching",
        approval_status="submitted",
        department=payload.get("department"),
        project_id=UUID(str(payload.get("project_id"))) if payload.get("project_id") else None,
        notes=payload.get("notes"),
    )
    db.add(bill)
    db.flush()
    if document:
        document.related_record_id = bill.id
    audit(db, current_user, "FIN-046_SUPPLIER_INVOICE_RECEIVED", "bills", bill.id, f"Supplier invoice {bill.bill_number} received")
    db.commit()
    return {"buc": "FIN-046", **serialize(bill)}


@router.post("/ap/invoices/{bill_id}/match-po")
def match_invoice_to_po(bill_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    bill = get_or_404(db, FinanceBill, bill_id, "Supplier invoice")
    po_id = payload.get("purchase_order_id") or bill.purchase_order_id
    if not po_id:
        raise HTTPException(status_code=422, detail="Purchase order reference is required")
    po = get_or_404(db, FinancePurchaseOrder, UUID(str(po_id)), "Purchase order")
    if po.status in {"closed", "cancelled"}:
        raise HTTPException(status_code=422, detail="Closed or cancelled PO cannot be matched")
    already_billed = money(db.query(func.coalesce(func.sum(FinanceBill.amount), 0)).filter(FinanceBill.purchase_order_id == po.id, FinanceBill.id != bill.id, FinanceBill.status.notin_(["rejected", "cancelled"])).scalar())
    remaining = money(po.total_amount) - already_billed
    tolerance = money(payload.get("variance_tolerance") or 0)
    matched = money(bill.amount) <= remaining + tolerance
    bill.purchase_order_id = po.id
    bill.po_match_status = "matched" if matched else "exception"
    po.invoice_match_status = "matched" if matched else "exception"
    audit(db, current_user, "FIN-047_INVOICE_PO_MATCH", "bills", bill.id, bill.po_match_status)
    db.commit()
    return {"buc": "FIN-047", "matched": matched, "remaining_po_balance": as_float(remaining), "bill": serialize(bill), "purchase_order": serialize(po)}


@router.post("/ap/invoices/{bill_id}/match-grn")
def match_invoice_to_grn(bill_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    bill = get_or_404(db, FinanceBill, bill_id, "Supplier invoice")
    po = get_or_404(db, FinancePurchaseOrder, UUID(str(payload.get("purchase_order_id") or bill.purchase_order_id)), "Purchase order")
    grn_quantity = money(payload.get("grn_quantity") or po.received_quantity)
    invoice_quantity = money(payload.get("invoice_quantity") or bill.invoice_quantity or 1)
    matched = invoice_quantity <= grn_quantity and po.goods_received_status in {"received", "partial", "accepted"}
    bill.grn_match_status = "matched" if matched else "exception"
    po.goods_received_status = po.goods_received_status or ("received" if matched else "pending")
    audit(db, current_user, "FIN-048_INVOICE_GRN_MATCH", "bills", bill.id, bill.grn_match_status)
    db.commit()
    return {"buc": "FIN-048", "matched": matched, "invoice_quantity": as_float(invoice_quantity), "grn_quantity": as_float(grn_quantity), "bill": serialize(bill)}


@router.post("/ap/invoices/{bill_id}/approve")
def approve_supplier_invoice(bill_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    bill = get_or_404(db, FinanceBill, bill_id, "Supplier invoice")
    vendor = get_or_404(db, FinanceVendor, bill.vendor_id, "Vendor") if bill.vendor_id else None
    if vendor and vendor.verification_status != "verified":
        raise HTTPException(status_code=422, detail="Vendor must be verified before invoice approval")
    if bill.po_match_status == "exception" or bill.grn_match_status == "exception":
        raise HTTPException(status_code=422, detail="Matching exception requires resolution before approval")
    debit, credit = ap_accounts(db, payload)
    journal = create_balanced_two_line_journal(db, current_user, amount=money(bill.amount), debit_account_id=debit.id, credit_account_id=credit.id, description=f"AP liability for {bill.bill_number}", entry_date=bill.bill_date, source_module="finance.ap", reference_type="supplier_invoice", reference_id=bill.id, journal_type="ap_invoice", auto_post=True)
    bill.approval_status = "approved"
    bill.status = "approved"
    bill.journal_entry_id = journal.id
    audit(db, current_user, "FIN-049_SUPPLIER_INVOICE_APPROVED", "bills", bill.id, "AP liability journal created")
    db.commit()
    return {"buc": "FIN-049", "bill": serialize(bill), "journal": serialize(journal)}


@router.post("/ap/invoices/{bill_id}/reject")
def reject_supplier_invoice(bill_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    bill = get_or_404(db, FinanceBill, bill_id, "Supplier invoice")
    bill.approval_status = "rejected"
    bill.status = "rejected"
    bill.rejection_reason = reason
    audit(db, current_user, "FIN-050_SUPPLIER_INVOICE_REJECTED", "bills", bill.id, reason)
    db.commit()
    return {"buc": "FIN-050", **serialize(bill)}


@router.post("/ap/payments/schedule")
def schedule_ap_payment(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    bill = get_or_404(db, FinanceBill, UUID(str(payload.get("bill_id"))), "Supplier invoice")
    if bill.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Only approved supplier invoices can be scheduled for payment")
    amount = money(payload.get("amount") or (money(bill.amount) - money(bill.paid_amount)))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Scheduled payment amount must be greater than zero")
    payment = FinancePayment(payment_number=next_number("AP-PAY"), payment_type="Vendor", vendor_id=bill.vendor_id, bill_id=bill.id, payment_date=date.fromisoformat(str(payload.get("payment_date") or payload.get("due_date") or date.today().isoformat())), scheduled_date=date.fromisoformat(str(payload.get("due_date") or payload.get("scheduled_date") or date.today().isoformat())), amount=amount, payment_method=payload.get("payment_method"), bank_account_id=UUID(str(payload.get("bank_account_id"))) if payload.get("bank_account_id") else None, status="scheduled", notes=payload.get("notes"))
    db.add(payment)
    db.flush()
    audit(db, current_user, "FIN-051_PAYMENT_SCHEDULED", "payments", payment.id, f"Scheduled AP payment {payment.payment_number}")
    db.commit()
    return {"buc": "FIN-051", **serialize(payment)}


@router.post("/ap/payments/process")
def process_ap_payment(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payment = get_or_404(db, FinancePayment, UUID(str(payload.get("payment_id"))), "Payment")
    bill = get_or_404(db, FinanceBill, payment.bill_id, "Supplier invoice") if payment.bill_id else None
    vendor = get_or_404(db, FinanceVendor, payment.vendor_id, "Vendor") if payment.vendor_id else None
    if vendor and vendor.verification_status != "verified":
        raise HTTPException(status_code=422, detail="Vendor must be verified before payment")
    bank_account_id = payload.get("bank_account_id") or payment.bank_account_id
    if not bank_account_id:
        raise HTTPException(status_code=422, detail="Bank account is required for payment processing")
    debit, credit = payment_accounts(db, payload)
    journal = create_balanced_two_line_journal(db, current_user, amount=money(payment.amount), debit_account_id=debit.id, credit_account_id=credit.id, description=f"AP payment {payment.payment_number}", entry_date=date.fromisoformat(str(payload.get("payment_date") or payment.payment_date.isoformat())), source_module="finance.ap", reference_type="vendor_payment", reference_id=payment.id, journal_type="ap_payment", auto_post=True)
    payment.status = "paid"
    payment.bank_account_id = UUID(str(bank_account_id))
    payment.journal_entry_id = journal.id
    payment.approved_by = current_user.email
    if bill:
        bill.paid_amount = money(bill.paid_amount) + money(payment.amount)
        bill.status = "paid" if money(bill.paid_amount) >= money(bill.amount) else "partial"
    audit(db, current_user, "FIN-052_PAYMENT_PROCESSED", "payments", payment.id, "AP payment journal created")
    db.commit()
    return {"buc": "FIN-052", "payment": serialize(payment), "bill": serialize(bill) if bill else None, "journal": serialize(journal)}


@router.post("/ap/payments/reverse")
def reverse_ap_payment(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Reversal reason is required")
    payment = get_or_404(db, FinancePayment, UUID(str(payload.get("payment_id"))), "Payment")
    if payment.status != "paid":
        raise HTTPException(status_code=422, detail="Only paid payments can be reversed")
    bank_debit = active_account(db, payload["debit_account_id"]) if payload.get("debit_account_id") else default_account(db, "asset", ["bank", "cash"])
    ap_credit = active_account(db, payload["credit_account_id"]) if payload.get("credit_account_id") else default_account(db, "liability", ["payable", "ap"])
    journal = create_balanced_two_line_journal(db, current_user, amount=money(payment.amount), debit_account_id=bank_debit.id, credit_account_id=ap_credit.id, description=f"AP payment reversal {payment.payment_number}: {reason}", entry_date=date.fromisoformat(str(payload.get("entry_date") or payment.payment_date.isoformat())), source_module="finance.ap", reference_type="payment_reversal", reference_id=payment.id, journal_type="ap_payment_reversal", auto_post=True)
    reversal = FinancePayment(payment_number=next_number("AP-REV"), payment_type="Vendor Reversal", vendor_id=payment.vendor_id, bill_id=payment.bill_id, payment_date=date.today(), amount=payment.amount, payment_method=payment.payment_method, bank_account_id=payment.bank_account_id, journal_entry_id=journal.id, reversed_payment_id=payment.id, reversal_reason=reason, status="reversed", approved_by=current_user.email, notes=f"Reversal of {payment.payment_number}")
    payment.status = "reversed"
    db.add(reversal)
    if payment.bill_id:
        bill = get_or_404(db, FinanceBill, payment.bill_id, "Supplier invoice")
        bill.paid_amount = max(money(bill.paid_amount) - money(payment.amount), Decimal("0"))
        bill.status = "approved" if bill.paid_amount == 0 else "partial"
    audit(db, current_user, "FIN-053_PAYMENT_REVERSED", "payments", payment.id, reason)
    db.commit()
    return {"buc": "FIN-053", "original_payment": serialize(payment), "reversal_payment": serialize(reversal), "journal": serialize(journal)}


@router.post("/ap/vendor-reconciliations")
def reconcile_vendor_statement(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    vendor = get_or_404(db, FinanceVendor, UUID(str(payload.get("vendor_id"))), "Vendor")
    invoices = money(db.query(func.coalesce(func.sum(FinanceBill.amount), 0)).filter(FinanceBill.vendor_id == vendor.id, FinanceBill.approval_status == "approved").scalar())
    payments = money(db.query(func.coalesce(func.sum(FinancePayment.amount), 0)).filter(FinancePayment.vendor_id == vendor.id, FinancePayment.status == "paid").scalar())
    system_balance = invoices - payments
    statement_balance = money(payload.get("statement_balance"))
    variance = system_balance - statement_balance
    reconciliation = FinanceAPReconciliation(vendor_id=vendor.id, statement_balance=statement_balance, system_balance=system_balance, variance_amount=variance, status="matched" if variance == 0 else "variance", notes=payload.get("notes"))
    db.add(reconciliation)
    db.flush()
    audit(db, current_user, "FIN-054_VENDOR_RECONCILIATION", "ap_reconciliations", reconciliation.id, reconciliation.status)
    db.commit()
    return {"buc": "FIN-054", **serialize(reconciliation)}


@router.get("/ap/aging")
def ap_aging(vendor_id: UUID | None = Query(default=None), department: str | None = Query(default=None), project_id: UUID | None = Query(default=None), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    query = db.query(FinanceBill).filter(FinanceBill.approval_status == "approved", FinanceBill.status.notin_(["paid", "rejected", "cancelled"]))
    if vendor_id:
        query = query.filter(FinanceBill.vendor_id == vendor_id)
    if department:
        query = query.filter(FinanceBill.department == department)
    if project_id:
        query = query.filter(FinanceBill.project_id == project_id)
    buckets = {"current": Decimal("0"), "1_30": Decimal("0"), "31_60": Decimal("0"), "61_90": Decimal("0"), "90_plus": Decimal("0")}
    rows = []
    for bill in query.all():
        outstanding = money(bill.amount) - money(bill.paid_amount)
        due = bill.due_date or bill.bill_date
        days = (date.today() - due).days
        key = "current" if days <= 0 else "1_30" if days <= 30 else "31_60" if days <= 60 else "61_90" if days <= 90 else "90_plus"
        buckets[key] += outstanding
        rows.append({"bill_id": str(bill.id), "bill_number": bill.bill_number, "vendor_id": str(bill.vendor_id) if bill.vendor_id else None, "due_date": due.isoformat(), "aging_days": days, "outstanding": as_float(outstanding), "bucket": key})
    total = sum(buckets.values(), Decimal("0"))
    return {"buc": "FIN-055", "buckets": {key: as_float(value) for key, value in buckets.items()}, "total_payables": as_float(total), "overdue_payables": as_float(buckets["1_30"] + buckets["31_60"] + buckets["61_90"] + buckets["90_plus"]), "rows": rows}


@router.post("/ar/customers")
def create_customer_billing_profile(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    account = get_or_404(db, CRMAccount, UUID(str(payload.get("account_id"))), "CRM account")
    customer_code = str(payload.get("customer_code") or getattr(account, "business_id", None) or next_number("CUS")).strip()
    if db.query(FinanceCustomerBillingProfile).filter(FinanceCustomerBillingProfile.customer_code == customer_code).first():
        raise HTTPException(status_code=409, detail="Customer code must be unique")
    if db.query(FinanceCustomerBillingProfile).filter(FinanceCustomerBillingProfile.account_id == account.id).first():
        raise HTTPException(status_code=409, detail="CRM account already has a billing profile")
    if not payload.get("payment_terms"):
        raise HTTPException(status_code=422, detail="Payment terms are mandatory")
    profile = FinanceCustomerBillingProfile(
        account_id=account.id,
        customer_code=customer_code,
        customer_name=payload.get("customer_name") or account.company_name,
        billing_address=payload.get("billing_address") or account.billing_address or account.address,
        tax_registration_number=payload.get("tax_registration_number"),
        currency=payload.get("currency") or "KES",
        payment_terms=payload["payment_terms"],
        credit_limit=money(payload.get("credit_limit")),
        ar_account_id=UUID(str(payload["ar_account_id"])) if payload.get("ar_account_id") else None,
        revenue_account_id=UUID(str(payload["revenue_account_id"])) if payload.get("revenue_account_id") else None,
        status=payload.get("status") or "active",
    )
    db.add(profile)
    db.flush()
    audit(db, current_user, "FIN-056_CUSTOMER_BILLING_PROFILE_CREATED", "customer_billing_profiles", profile.id, f"Billing profile {profile.customer_code}")
    db.commit()
    return {"buc": "FIN-056", **serialize(profile)}


@router.post("/ar/invoices")
def generate_ar_invoice(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = db.query(FinanceCustomerBillingProfile).filter(FinanceCustomerBillingProfile.account_id == UUID(str(payload.get("account_id"))), FinanceCustomerBillingProfile.status == "active").first()
    if not profile:
        raise HTTPException(status_code=422, detail="Active customer billing profile is required before invoicing")
    source_record_id = UUID(str(payload.get("opportunity_id") or payload.get("source_record_id"))) if (payload.get("opportunity_id") or payload.get("source_record_id")) else None
    if source_record_id and db.query(FinanceInvoice).filter(FinanceInvoice.source_module == "crm.opportunity.won", FinanceInvoice.source_record_id == source_record_id).first():
        raise HTTPException(status_code=409, detail="Invoice already exists for this opportunity")
    invoice_date = date.fromisoformat(str(payload.get("invoice_date") or date.today().isoformat()))
    subtotal = money(payload.get("subtotal"))
    line_items = payload.get("line_items") or []
    if not subtotal and line_items:
        subtotal = sum((money(item.get("quantity") or 1) * money(item.get("unit_price")) - money(item.get("discount_amount"))) for item in line_items)
    tax_amount = money(payload.get("tax_amount"))
    if not tax_amount:
        tax_amount = subtotal * money(payload.get("tax_rate") or 16) / Decimal("100")
    discount = money(payload.get("discount_amount"))
    total = subtotal + tax_amount - discount
    ar_account, revenue_account = ar_accounts(db, profile, payload)
    invoice = FinanceInvoice(
        account_id=profile.account_id,
        crm_opportunity_id=source_record_id,
        source_module="crm.opportunity.won" if source_record_id else payload.get("source_module"),
        source_record_id=source_record_id,
        customer_code=profile.customer_code,
        ar_account_id=ar_account.id,
        revenue_account_id=revenue_account.id,
        invoice_number=payload.get("invoice_number") or next_number("AR-INV"),
        invoice_date=invoice_date,
        due_date=date.fromisoformat(str(payload.get("due_date"))) if payload.get("due_date") else payment_terms_due_date(invoice_date, profile.payment_terms),
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=discount,
        total_amount=total,
        paid_amount=0,
        tax_rate=money(payload.get("tax_rate") or 16),
        approval_status="draft",
        status="draft",
        notes=payload.get("notes"),
    )
    db.add(invoice)
    db.flush()
    for item in line_items:
        quantity = money(item.get("quantity") or 1)
        unit_price = money(item.get("unit_price"))
        line_discount = money(item.get("discount_amount"))
        line_tax = money(item.get("tax_amount") or ((quantity * unit_price - line_discount) * money(item.get("tax_rate") or 0) / Decimal("100")))
        db.add(FinanceInvoiceLineItem(invoice_id=invoice.id, description=item.get("description") or "Invoice item", quantity=quantity, unit_price=unit_price, discount_amount=line_discount, tax_rate=money(item.get("tax_rate")), tax_amount=line_tax, line_total=quantity * unit_price - line_discount + line_tax))
    audit(db, current_user, "FIN-057_INVOICE_GENERATED", "invoices", invoice.id, f"Invoice {invoice.invoice_number} generated")
    db.commit()
    return {"buc": "FIN-057", **serialize(invoice)}


@router.post("/ar/invoices/{invoice_id}/approve")
def approve_ar_invoice(invoice_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    invoice = get_or_404(db, FinanceInvoice, invoice_id, "Invoice")
    if invoice.total_amount <= 0:
        raise HTTPException(status_code=422, detail="Invoice must have a positive total")
    profile = db.query(FinanceCustomerBillingProfile).filter(FinanceCustomerBillingProfile.account_id == invoice.account_id).first()
    ar_account, revenue_account = ar_accounts(db, profile, {"ar_account_id": payload.get("ar_account_id") or invoice.ar_account_id, "revenue_account_id": payload.get("revenue_account_id") or invoice.revenue_account_id})
    journal = create_balanced_two_line_journal(db, current_user, amount=money(invoice.total_amount), debit_account_id=ar_account.id, credit_account_id=revenue_account.id, description=f"AR invoice {invoice.invoice_number}", entry_date=invoice.invoice_date, source_module="finance.ar", reference_type="customer_invoice", reference_id=invoice.id, journal_type="ar_invoice", auto_post=True)
    invoice.approval_status = "approved"
    invoice.status = "approved"
    invoice.ar_account_id = ar_account.id
    invoice.revenue_account_id = revenue_account.id
    invoice.journal_entry_id = journal.id
    audit(db, current_user, "FIN-058_INVOICE_APPROVED", "invoices", invoice.id, "Revenue journal created")
    db.commit()
    return {"buc": "FIN-058", "invoice": serialize(invoice), "journal": serialize(journal)}


@router.post("/ar/invoices/{invoice_id}/send")
def send_ar_invoice(invoice_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    invoice = get_or_404(db, FinanceInvoice, invoice_id, "Invoice")
    if invoice.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Only approved invoices can be sent")
    invoice.status = "sent"
    invoice.sent_at = datetime.now(timezone.utc)
    invoice.delivery_method = payload.get("delivery_method") or "email"
    audit(db, current_user, "FIN-059_INVOICE_SENT", "invoices", invoice.id, invoice.delivery_method)
    db.commit()
    return {"buc": "FIN-059", **serialize(invoice)}


@router.post("/ar/payments")
def receive_ar_payment(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("payment_reference"):
        raise HTTPException(status_code=422, detail="Payment reference is mandatory")
    invoice = db.query(FinanceInvoice).filter(FinanceInvoice.id == UUID(str(payload.get("invoice_id")))).first() if payload.get("invoice_id") else None
    profile = db.query(FinanceCustomerBillingProfile).filter(FinanceCustomerBillingProfile.account_id == UUID(str(payload.get("account_id") or getattr(invoice, "account_id", "")))).first() if (payload.get("account_id") or invoice) else None
    if not profile and not invoice:
        raise HTTPException(status_code=422, detail="Customer or invoice is required")
    amount = money(payload.get("amount"))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Payment amount must be greater than zero")
    bank_account = active_account(db, payload["bank_account_id"]) if payload.get("bank_account_id") else default_account(db, "asset", ["bank", "cash"])
    ar_account, _ = ar_accounts(db, profile, {"ar_account_id": getattr(invoice, "ar_account_id", None)})
    journal = create_balanced_two_line_journal(db, current_user, amount=amount, debit_account_id=bank_account.id, credit_account_id=ar_account.id, description=f"Customer payment {payload['payment_reference']}", entry_date=date.fromisoformat(str(payload.get("receipt_date") or date.today().isoformat())), source_module="finance.ar", reference_type="customer_payment", journal_type="ar_payment", auto_post=True)
    receipt = FinanceReceipt(receipt_number=payload.get("receipt_number") or next_number("AR-RCT"), invoice_id=getattr(invoice, "id", None), account_id=getattr(profile, "account_id", None) or getattr(invoice, "account_id", None), receipt_date=date.fromisoformat(str(payload.get("receipt_date") or date.today().isoformat())), amount=amount, allocated_amount=0, currency=payload.get("currency") or getattr(profile, "currency", None) or "KES", payment_method=payload.get("payment_method"), payment_reference=payload["payment_reference"], received_from=payload.get("received_from") or getattr(profile, "customer_name", None), bank_account_id=bank_account.id, journal_entry_id=journal.id, status="received", notes=payload.get("notes"))
    db.add(receipt)
    db.flush()
    audit(db, current_user, "FIN-060_PAYMENT_RECEIVED", "receipts", receipt.id, f"Receipt {receipt.receipt_number}")
    db.commit()
    return {"buc": "FIN-060", "receipt": serialize(receipt), "journal": serialize(journal)}


@router.post("/ar/payments/allocate")
def allocate_ar_payment(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    receipt = get_or_404(db, FinanceReceipt, UUID(str(payload.get("receipt_id"))), "Receipt")
    allocations = payload.get("allocations") or []
    if not allocations and receipt.invoice_id:
        allocations = [{"invoice_id": str(receipt.invoice_id), "amount": as_float(money(receipt.amount) - money(receipt.allocated_amount))}]
    remaining = money(receipt.amount) - money(receipt.allocated_amount)
    rows = []
    for item in allocations:
        invoice = get_or_404(db, FinanceInvoice, UUID(str(item.get("invoice_id"))), "Invoice")
        amount = money(item.get("amount"))
        if amount <= 0 or amount > remaining:
            raise HTTPException(status_code=422, detail="Allocation amount exceeds remaining payment")
        if amount > invoice_outstanding(invoice):
            raise HTTPException(status_code=422, detail="Allocation cannot exceed invoice balance")
        allocation = FinanceReceiptAllocation(receipt_id=receipt.id, invoice_id=invoice.id, allocated_amount=amount)
        invoice.paid_amount = money(invoice.paid_amount) + amount
        invoice.status = "paid" if invoice_outstanding(invoice) == 0 else "partial"
        receipt.allocated_amount = money(receipt.allocated_amount) + amount
        remaining -= amount
        db.add(allocation)
        db.flush()
        rows.append(serialize(allocation))
    receipt.status = "allocated" if remaining == 0 else "partially_allocated"
    audit(db, current_user, "FIN-061_PAYMENT_ALLOCATED", "receipts", receipt.id, f"Remaining payment {remaining}")
    db.commit()
    return {"buc": "FIN-061", "receipt": serialize(receipt), "remaining_payment": as_float(remaining), "allocations": rows}


@router.post("/ar/credit-notes")
def create_ar_credit_note(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    invoice = get_or_404(db, FinanceInvoice, UUID(str(payload.get("invoice_id"))), "Invoice")
    amount = money(payload.get("amount"))
    if amount <= 0 or amount > invoice_outstanding(invoice):
        raise HTTPException(status_code=422, detail="Credit amount must be positive and cannot exceed invoice balance")
    profile = db.query(FinanceCustomerBillingProfile).filter(FinanceCustomerBillingProfile.account_id == invoice.account_id).first()
    ar_account, revenue_account = ar_accounts(db, profile, {"ar_account_id": invoice.ar_account_id, "revenue_account_id": invoice.revenue_account_id})
    journal = create_balanced_two_line_journal(db, current_user, amount=amount, debit_account_id=revenue_account.id, credit_account_id=ar_account.id, description=f"Credit note for {invoice.invoice_number}", entry_date=date.fromisoformat(str(payload.get("issue_date") or date.today().isoformat())), source_module="finance.ar", reference_type="credit_note", journal_type="credit_note", auto_post=True)
    credit = FinanceCreditNote(credit_note_number=payload.get("credit_note_number") or next_number("AR-CN"), invoice_id=invoice.id, issue_date=date.fromisoformat(str(payload.get("issue_date") or date.today().isoformat())), amount=amount, journal_entry_id=journal.id, reason=payload.get("reason"), status="issued")
    invoice.paid_amount = money(invoice.paid_amount) + amount
    invoice.status = "paid" if invoice_outstanding(invoice) == 0 else "partial"
    db.add(credit)
    db.flush()
    audit(db, current_user, "FIN-063_CREDIT_NOTE_ISSUED", "credit_notes", credit.id, credit.reason or "Credit note")
    db.commit()
    return {"buc": "FIN-063", "credit_note": serialize(credit), "journal": serialize(journal)}


@router.post("/ar/debit-notes")
def create_ar_debit_note(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    invoice = get_or_404(db, FinanceInvoice, UUID(str(payload.get("invoice_id"))), "Invoice")
    amount = money(payload.get("amount"))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Debit note amount must be greater than zero")
    profile = db.query(FinanceCustomerBillingProfile).filter(FinanceCustomerBillingProfile.account_id == invoice.account_id).first()
    ar_account, revenue_account = ar_accounts(db, profile, {"ar_account_id": invoice.ar_account_id, "revenue_account_id": invoice.revenue_account_id})
    journal = create_balanced_two_line_journal(db, current_user, amount=amount, debit_account_id=ar_account.id, credit_account_id=revenue_account.id, description=f"Debit note for {invoice.invoice_number}", entry_date=date.fromisoformat(str(payload.get("note_date") or date.today().isoformat())), source_module="finance.ar", reference_type="debit_note", journal_type="debit_note", auto_post=True)
    note = FinanceDebitNote(debit_note_number=payload.get("debit_note_number") or next_number("AR-DN"), invoice_id=invoice.id, note_date=date.fromisoformat(str(payload.get("note_date") or date.today().isoformat())), amount=amount, journal_entry_id=journal.id, reason=payload.get("reason"), status="issued")
    invoice.total_amount = money(invoice.total_amount) + amount
    invoice.status = "sent" if invoice.status == "paid" else invoice.status
    db.add(note)
    db.flush()
    audit(db, current_user, "FIN-064_DEBIT_NOTE_ISSUED", "debit_notes", note.id, note.reason or "Debit note")
    db.commit()
    return {"buc": "FIN-064", "debit_note": serialize(note), "journal": serialize(journal)}


@router.get("/ar/customers/{account_id}/statement")
def customer_statement(account_id: UUID, date_from: date | None = Query(default=None), date_to: date | None = Query(default=None), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    invoices_q = db.query(FinanceInvoice).filter(FinanceInvoice.account_id == account_id)
    receipts_q = db.query(FinanceReceipt).filter(FinanceReceipt.account_id == account_id)
    if date_from:
        invoices_q = invoices_q.filter(FinanceInvoice.invoice_date >= date_from)
        receipts_q = receipts_q.filter(FinanceReceipt.receipt_date >= date_from)
    if date_to:
        invoices_q = invoices_q.filter(FinanceInvoice.invoice_date <= date_to)
        receipts_q = receipts_q.filter(FinanceReceipt.receipt_date <= date_to)
    invoices = invoices_q.all()
    receipts = receipts_q.all()
    invoice_total = sum(money(item.total_amount) for item in invoices)
    payments = sum(money(item.allocated_amount or item.amount) for item in receipts)
    credit_total = money(db.query(func.coalesce(func.sum(FinanceCreditNote.amount), 0)).join(FinanceInvoice, FinanceInvoice.id == FinanceCreditNote.invoice_id).filter(FinanceInvoice.account_id == account_id).scalar())
    debit_total = money(db.query(func.coalesce(func.sum(FinanceDebitNote.amount), 0)).join(FinanceInvoice, FinanceInvoice.id == FinanceDebitNote.invoice_id).filter(FinanceInvoice.account_id == account_id).scalar())
    closing = invoice_total + debit_total - payments - credit_total
    return {"buc": "FIN-065", "account_id": str(account_id), "opening_balance": 0, "invoices": [serialize(item) for item in invoices], "payments": [serialize(item) for item in receipts], "credit_notes": as_float(credit_total), "debit_notes": as_float(debit_total), "closing_balance": as_float(closing)}


@router.post("/ar/collections/run")
def run_collections_management(payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    created = []
    invoices = db.query(FinanceInvoice).filter(FinanceInvoice.status.in_(["sent", "partial", "approved"]), FinanceInvoice.total_amount > FinanceInvoice.paid_amount).all()
    for invoice in invoices:
        due = invoice.due_date or invoice.invoice_date
        days = (date.today() - due).days
        bucket = aging_bucket(days)
        if bucket == "current":
            continue
        action = FinanceCollectionAction(invoice_id=invoice.id, account_id=invoice.account_id, aging_bucket=bucket, action_type=payload.get("action_type") or "reminder", assigned_to=payload.get("assigned_to"), notes=f"Overdue by {days} days")
        db.add(action)
        db.flush()
        created.append(serialize(action))
    audit(db, current_user, "FIN-066_COLLECTIONS_RUN", "collection_actions", None, f"Created {len(created)} collection actions")
    db.commit()
    return {"buc": "FIN-066", "created": created}


@router.get("/ar/aging")
def ar_aging(customer_id: UUID | None = Query(default=None), project_id: UUID | None = Query(default=None), branch: str | None = Query(default=None), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    query = db.query(FinanceInvoice).filter(FinanceInvoice.status.notin_(["paid", "cancelled", "rejected"]), FinanceInvoice.total_amount > FinanceInvoice.paid_amount)
    if customer_id:
        query = query.filter(FinanceInvoice.account_id == customer_id)
    if project_id:
        query = query.filter(FinanceInvoice.project_id == project_id)
    buckets = {"current": Decimal("0"), "1_30": Decimal("0"), "31_60": Decimal("0"), "61_90": Decimal("0"), "90_plus": Decimal("0")}
    rows = []
    credit_sales = money(db.query(func.coalesce(func.sum(FinanceInvoice.total_amount), 0)).filter(FinanceInvoice.approval_status == "approved").scalar())
    paid_sales = money(db.query(func.coalesce(func.sum(FinanceInvoice.paid_amount), 0)).scalar())
    for invoice in query.all():
        outstanding = invoice_outstanding(invoice)
        days = (date.today() - (invoice.due_date or invoice.invoice_date)).days
        bucket = aging_bucket(days)
        buckets[bucket] += outstanding
        rows.append({"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number, "account_id": str(invoice.account_id) if invoice.account_id else None, "aging_days": days, "outstanding": as_float(outstanding), "bucket": bucket})
    ar_total = sum(buckets.values(), Decimal("0"))
    dso = (ar_total / credit_sales * Decimal("30")) if credit_sales else Decimal("0")
    return {"buc": "FIN-067", "buckets": {key: as_float(value) for key, value in buckets.items()}, "outstanding_receivables": as_float(ar_total), "overdue_receivables": as_float(buckets["1_30"] + buckets["31_60"] + buckets["61_90"] + buckets["90_plus"]), "collection_rate": as_float((paid_sales / credit_sales * Decimal("100")) if credit_sales else Decimal("0")), "dso": as_float(dso), "rows": rows}


@router.post("/expenses")
def submit_expense(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    employee = active_employee(db, payload.get("employee_id") or payload.get("claimant_employee_id"))
    if not payload.get("receipt_url") and not payload.get("allow_missing_receipt"):
        raise HTTPException(status_code=422, detail="Receipt is required")
    expense_date = date.fromisoformat(str(payload.get("expense_date") or date.today().isoformat()))
    category = str(payload.get("category") or payload.get("expense_type") or "General")
    amount = money(payload.get("amount"))
    lower = category.lower()
    if "mileage" in lower:
        amount = money(payload.get("distance")) * money(payload.get("rate") or payload.get("mileage_rate"))
    elif "per diem" in lower or "per_diem" in lower:
        amount = money(payload.get("days") or payload.get("per_diem_days")) * money(payload.get("rate") or payload.get("per_diem_rate"))
    elif "travel" in lower:
        amount = money(payload.get("transport")) + money(payload.get("accommodation")) + money(payload.get("meals")) + money(payload.get("incidentals"))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Expense amount must be greater than zero")
    expense = FinanceExpense(
        expense_number=payload.get("expense_number") or next_number("EXP"),
        expense_date=expense_date,
        category=category,
        claimant_employee_id=employee.id if employee else None,
        cost_center_id=UUID(str(payload.get("cost_center_id"))) if payload.get("cost_center_id") else None,
        project_id=UUID(str(payload.get("project_id"))) if payload.get("project_id") else None,
        department=payload.get("department") or getattr(employee, "department", None),
        amount=amount,
        currency=payload.get("currency") or "KES",
        approval_status="submitted",
        payment_status="unpaid",
        status="submitted",
        notes=payload.get("notes") or payload.get("reason"),
    )
    db.add(expense)
    db.flush()
    audit(db, current_user, "FIN-068_EXPENSE_SUBMITTED", "expenses", expense.id, f"{category} expense submitted")
    db.commit()
    return {"buc": "FIN-068", **serialize(expense)}


@router.post("/expenses/{expense_id}/budget-validation")
def validate_expense_budget(expense_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    expense = get_or_404(db, FinanceExpense, expense_id, "Expense")
    budget_query = db.query(FinanceBudget).filter(FinanceBudget.approval_status == "approved", FinanceBudget.status == "active")
    if expense.department:
        budget_query = budget_query.filter(FinanceBudget.department == expense.department)
    if expense.project_id:
        budget_query = budget_query.filter(FinanceBudget.project_id == expense.project_id)
    if expense.cost_center_id:
        budget_query = budget_query.filter(FinanceBudget.cost_center_id == expense.cost_center_id)
    budget = budget_query.first()
    if not budget:
        return {"buc": "FIN-075", "valid": False, "reason": "No approved budget found"}
    actual = budget_actual_spend(db, budget)
    committed = budget_committed_spend(db, budget)
    remaining = money(budget.approved_amount) - actual - committed
    valid = money(expense.amount) <= remaining
    return {"buc": "FIN-075", "valid": valid, "budget_id": str(budget.id), "remaining_budget": as_float(remaining), "expense_amount": as_float(expense.amount)}


@router.post("/expenses/{expense_id}/approve")
def approve_expense(expense_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    expense = get_or_404(db, FinanceExpense, expense_id, "Expense")
    validation = validate_expense_budget(expense_id, payload, db, current_user)
    if not validation["valid"] and not payload.get("override_budget"):
        raise HTTPException(status_code=422, detail="Expense exceeds available budget")
    expense.approval_status = "approved"
    expense.status = "approved"
    audit(db, current_user, "FIN-069_EXPENSE_APPROVED", "expenses", expense.id, "Expense approved")
    db.commit()
    return {"buc": "FIN-069", **serialize(expense)}


@router.post("/expenses/{expense_id}/reject")
def reject_expense(expense_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    expense = get_or_404(db, FinanceExpense, expense_id, "Expense")
    expense.approval_status = "rejected"
    expense.status = "rejected"
    expense.notes = f"{expense.notes or ''}\nRejected: {payload['reason']}".strip()
    audit(db, current_user, "FIN-070_EXPENSE_REJECTED", "expenses", expense.id, payload["reason"])
    db.commit()
    return {"buc": "FIN-070", **serialize(expense)}


@router.post("/expenses/{expense_id}/reimburse")
def reimburse_expense(expense_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    expense = get_or_404(db, FinanceExpense, expense_id, "Expense")
    if expense.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Only approved expenses can be reimbursed")
    if not payload.get("payment_reference"):
        raise HTTPException(status_code=422, detail="Payment reference is required")
    debit = active_account(db, payload["debit_account_id"]) if payload.get("debit_account_id") else default_account(db, "expense", ["expense", "cost"])
    credit = active_account(db, payload["credit_account_id"]) if payload.get("credit_account_id") else default_account(db, "asset", ["bank", "cash"])
    journal = create_balanced_two_line_journal(db, current_user, amount=money(expense.amount), debit_account_id=debit.id, credit_account_id=credit.id, description=f"Expense reimbursement {expense.expense_number}", entry_date=date.fromisoformat(str(payload.get("payment_date") or date.today().isoformat())), source_module="finance.expenses", reference_type="expense_reimbursement", reference_id=expense.id, journal_type="expense_reimbursement", auto_post=True)
    expense.payment_status = "paid"
    expense.status = "paid"
    payment = FinancePayment(payment_number=payload.get("payment_reference") or next_number("EXP-PAY"), payment_type="Expense", payment_date=date.today(), amount=expense.amount, payment_method=payload.get("payment_method"), bank_account_id=credit.id, journal_entry_id=journal.id, status="paid", approved_by=current_user.email, notes=f"Reimbursement for {expense.expense_number}")
    db.add(payment)
    audit(db, current_user, "FIN-071_EXPENSE_REIMBURSED", "expenses", expense.id, "Expense reimbursement journal created")
    db.commit()
    return {"buc": "FIN-071", "expense": serialize(expense), "payment": serialize(payment), "journal": serialize(journal)}


@router.post("/expenses/calculate")
def calculate_expense(payload: dict[str, Any]):
    kind = str(payload.get("expense_type") or payload.get("category") or "").lower()
    if "mileage" in kind:
        amount = money(payload.get("distance")) * money(payload.get("rate"))
        return {"buc": "FIN-072", "amount": as_float(amount), "formula": "distance * rate"}
    if "per diem" in kind or "per_diem" in kind:
        amount = money(payload.get("daily_rate")) * money(payload.get("days"))
        return {"buc": "FIN-073", "amount": as_float(amount), "formula": "daily_rate * days"}
    if "travel" in kind:
        amount = money(payload.get("transport")) + money(payload.get("accommodation")) + money(payload.get("meals")) + money(payload.get("incidentals"))
        return {"buc": "FIN-074", "amount": as_float(amount), "formula": "transport + accommodation + meals + incidentals"}
    return {"amount": as_float(money(payload.get("amount"))), "formula": "manual"}


@router.get("/expenses/audit")
def expense_audit(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = []
    seen: set[tuple[str | None, Decimal, date]] = set()
    for expense in db.query(FinanceExpense).filter(FinanceExpense.status.notin_(["rejected", "cancelled"])).order_by(FinanceExpense.created_at.desc()).limit(500).all():
        flags = []
        key = (expense.source_label, money(expense.amount), expense.expense_date)
        if key in seen:
            flags.append("duplicate_claim_pattern")
        seen.add(key)
        if money(expense.amount) > Decimal("100000"):
            flags.append("excessive_spend")
        if not expense.cost_center_id:
            flags.append("missing_cost_center")
        if flags:
            rows.append({"expense": serialize(expense), "flags": flags})
    return {"buc": "FIN-076", "flags": rows}


@router.post("/budgets")
def create_budget(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("fiscal_year") or not payload.get("period_label"):
        raise HTTPException(status_code=422, detail="Budget fiscal year and period are required")
    if payload.get("owner_employee_id"):
        active_employee(db, payload["owner_employee_id"])
    budget = FinanceBudget(budget_name=payload.get("budget_name") or f"{payload.get('budget_type', 'Budget')} {payload['fiscal_year']}", budget_type=payload.get("budget_type") or payload.get("category") or "Master", department=payload.get("department"), branch=payload.get("branch"), project_id=UUID(str(payload.get("project_id"))) if payload.get("project_id") else None, cost_center_id=UUID(str(payload.get("cost_center_id"))) if payload.get("cost_center_id") else None, owner_employee_id=UUID(str(payload.get("owner_employee_id"))) if payload.get("owner_employee_id") else None, fiscal_year=str(payload["fiscal_year"]), period_label=payload.get("period_label"), approved_amount=money(payload.get("amount") or payload.get("approved_amount")), actual_amount=0, committed_amount=0, threshold_percent=money(payload.get("threshold_percent") or 100), approval_status="draft", status="draft", notes=payload.get("notes"))
    db.add(budget)
    db.flush()
    audit(db, current_user, "FIN-077_BUDGET_CREATED", "budgets", budget.id, f"Budget {budget.budget_name}")
    db.commit()
    return {"buc": "FIN-077", **serialize(budget)}


@router.post("/budgets/{budget_id}/revise")
def revise_budget(budget_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Revision reason is required")
    budget = get_or_404(db, FinanceBudget, budget_id, "Budget")
    new_amount = money(payload.get("new_amount") or payload.get("approved_amount"))
    revision = FinanceBudgetRevision(budget_id=budget.id, old_amount=budget.approved_amount, new_amount=new_amount, reason=reason, approval_status="pending", created_by=current_user.email)
    budget.approved_amount = new_amount
    budget.approval_status = "pending_revision"
    db.add(revision)
    db.flush()
    audit(db, current_user, "FIN-084_BUDGET_REVISED", "budget_revisions", revision.id, reason)
    db.commit()
    return {"buc": "FIN-084", "budget": serialize(budget), "revision": serialize(revision)}


@router.get("/budgets/{budget_id}/consumption")
def budget_consumption(budget_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    budget = get_or_404(db, FinanceBudget, budget_id, "Budget")
    actual = budget_actual_spend(db, budget)
    committed = budget_committed_spend(db, budget)
    approved = money(budget.approved_amount)
    remaining = approved - actual - committed
    consumption = (actual / approved * Decimal("100")) if approved else Decimal("0")
    return {"buc": "FIN-086", "budget": serialize(budget), "actual_spend": as_float(actual), "committed_spend": as_float(committed), "remaining_budget": as_float(remaining), "consumption_percent": as_float(consumption)}


@router.get("/budget-variance")
def budget_variance_report(scope: str | None = Query(default=None), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = []
    for budget in db.query(FinanceBudget).filter(FinanceBudget.status.notin_(["cancelled", "rejected"])).all():
        actual = budget_actual_spend(db, budget)
        approved = money(budget.approved_amount)
        variance = actual - approved
        variance_percent = (variance / approved * Decimal("100")) if approved else Decimal("0")
        status_value = "green" if abs(variance_percent) < 5 else "amber" if abs(variance_percent) <= 10 else "red"
        rows.append({"budget_id": str(budget.id), "budget_name": budget.budget_name, "budget_type": budget.budget_type, "department": budget.department, "branch": budget.branch, "project_id": str(budget.project_id) if budget.project_id else None, "cost_center_id": str(budget.cost_center_id) if budget.cost_center_id else None, "budget": as_float(approved), "actual": as_float(actual), "variance": as_float(variance), "variance_percent": as_float(variance_percent), "status": status_value})
    return {"buc": "FIN-087", "rows": rows}


@router.post("/procurement/purchase-requests")
def create_purchase_request(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    employee = active_employee(db, payload.get("employee_id")) if payload.get("employee_id") else None
    cost_center_id = UUID(str(payload.get("cost_center_id"))) if payload.get("cost_center_id") else None
    if not cost_center_id:
        raise HTTPException(status_code=422, detail="Cost center is required")
    get_or_404(db, FinanceCostCenter, cost_center_id, "Cost center")
    _, available = available_budget_for(db, department=payload.get("department") or getattr(employee, "department", None), cost_center_id=cost_center_id)
    amount = money(payload.get("estimated_amount"))
    if amount > available and not payload.get("override_budget"):
        raise HTTPException(status_code=422, detail="Budget exhausted or unavailable")
    pr = FinancePurchaseRequest(request_number=payload.get("request_number") or next_number("PR"), requested_by=getattr(employee, "email", None) or current_user.email, department=payload.get("department") or getattr(employee, "department", None), request_date=date.fromisoformat(str(payload.get("request_date") or date.today().isoformat())), required_date=date.fromisoformat(str(payload.get("required_date"))) if payload.get("required_date") else None, description=payload.get("description") or "Purchase request", estimated_amount=amount, approval_status="submitted", status="pending_manager_approval")
    db.add(pr); db.flush()
    audit(db, current_user, "FIN-088_PURCHASE_REQUEST_CREATED", "purchase_requests", pr.id, f"Available budget {available}")
    db.commit()
    return {"buc": "FIN-088", **serialize(pr)}


@router.post("/procurement/purchase-requests/{request_id}/manager-approval")
def manager_approve_pr(request_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    pr = get_or_404(db, FinancePurchaseRequest, request_id, "Purchase request")
    decision = payload.get("decision", "approved")
    if decision == "rejected" and not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Rejection reason is mandatory")
    pr.approval_status = decision
    pr.status = "manager_approved" if decision == "approved" else decision
    audit(db, current_user, "FIN-089_PR_MANAGER_DECISION", "purchase_requests", pr.id, payload.get("reason") or decision)
    db.commit()
    return {"buc": "FIN-089", **serialize(pr)}


@router.post("/procurement/purchase-requests/{request_id}/review")
def procurement_review(request_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    pr = get_or_404(db, FinancePurchaseRequest, request_id, "Purchase request")
    if pr.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Manager approval is required before procurement review")
    pr.status = "procurement_reviewed"
    audit(db, current_user, "FIN-090_PROCUREMENT_REVIEWED", "purchase_requests", pr.id, payload.get("notes") or "Reviewed")
    db.commit()
    return {"buc": "FIN-090", **serialize(pr)}


@router.post("/procurement/rfqs")
def create_rfq(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    pr = get_or_404(db, FinancePurchaseRequest, UUID(str(payload.get("purchase_request_id"))), "Purchase request") if payload.get("purchase_request_id") else None
    if pr and pr.status != "procurement_reviewed":
        raise HTTPException(status_code=422, detail="Procurement review is required before RFQ")
    closing = date.fromisoformat(str(payload.get("closing_date")))
    if closing < date.today():
        raise HTTPException(status_code=422, detail="RFQ closing date cannot be in the past")
    rfq = FinanceRFQ(rfq_number=payload.get("rfq_number") or next_number("RFQ"), purchase_request_id=getattr(pr, "id", None), vendor_list=", ".join(payload.get("vendor_list") or []), requested_items=str(payload.get("requested_items") or payload.get("items") or ""), closing_date=closing, status="open")
    db.add(rfq); db.flush()
    audit(db, current_user, "FIN-091_RFQ_CREATED", "rfqs", rfq.id, "RFQ created")
    db.commit()
    return {"buc": "FIN-091", **serialize(rfq)}


@router.post("/procurement/vendor-evaluations")
def evaluate_vendor(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    vendor = get_or_404(db, FinanceVendor, UUID(str(payload.get("vendor_id"))), "Vendor")
    weights = payload.get("weights") or {"price": 0.35, "quality": 0.25, "delivery": 0.2, "compliance": 0.2}
    score = money(payload.get("price_score")) * money(weights.get("price")) + money(payload.get("quality_score")) * money(weights.get("quality")) + money(payload.get("delivery_score")) * money(weights.get("delivery")) + money(payload.get("compliance_score")) * money(weights.get("compliance"))
    evaluation = FinanceVendorEvaluation(rfq_id=UUID(str(payload.get("rfq_id"))) if payload.get("rfq_id") else None, vendor_id=vendor.id, price_score=money(payload.get("price_score")), quality_score=money(payload.get("quality_score")), delivery_score=money(payload.get("delivery_score")), compliance_score=money(payload.get("compliance_score")), risk_score=money(payload.get("risk_score")), weighted_score=score)
    db.add(evaluation); db.flush()
    audit(db, current_user, "FIN-092_VENDOR_EVALUATED", "vendor_evaluations", evaluation.id, f"Score {score}")
    db.commit()
    return {"buc": "FIN-092", **serialize(evaluation)}


@router.post("/procurement/vendor-evaluations/{evaluation_id}/select")
def select_vendor(evaluation_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    evaluation = get_or_404(db, FinanceVendorEvaluation, evaluation_id, "Vendor evaluation")
    best = db.query(func.max(FinanceVendorEvaluation.weighted_score)).filter(FinanceVendorEvaluation.rfq_id == evaluation.rfq_id).scalar()
    if best and money(evaluation.weighted_score) < money(best) and not payload.get("justification"):
        raise HTTPException(status_code=422, detail="Justification is required when not selecting the highest score")
    evaluation.selected = True
    evaluation.selection_reason = payload.get("justification") or "Highest score selected"
    evaluation.status = "selected"
    audit(db, current_user, "FIN-093_VENDOR_SELECTED", "vendor_evaluations", evaluation.id, evaluation.selection_reason)
    db.commit()
    return {"buc": "FIN-093", **serialize(evaluation)}


@router.post("/procurement/purchase-orders")
def create_procurement_po(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    pr = get_or_404(db, FinancePurchaseRequest, UUID(str(payload.get("purchase_request_id"))), "Purchase request")
    vendor = get_or_404(db, FinanceVendor, UUID(str(payload.get("vendor_id"))), "Vendor")
    if vendor.status != "active":
        raise HTTPException(status_code=422, detail="Vendor must be approved and active")
    lines = payload.get("items") or []
    total = sum(money(item.get("quantity") or 1) * money(item.get("unit_price")) for item in lines) + money(payload.get("taxes")) - money(payload.get("discounts"))
    po = FinancePurchaseOrder(po_number=payload.get("po_number") or next_number("PO"), purchase_request_id=pr.id, vendor_id=vendor.id, po_date=date.today(), expected_delivery_date=date.fromisoformat(str(payload.get("expected_delivery_date"))) if payload.get("expected_delivery_date") else None, total_amount=total, approval_status="draft", status="draft", notes=payload.get("delivery_terms"))
    db.add(po); db.flush()
    audit(db, current_user, "FIN-094_PO_CREATED", "purchase_orders", po.id, f"PO total {total}")
    db.commit()
    return {"buc": "FIN-094", **serialize(po)}


@router.post("/procurement/purchase-orders/{po_id}/approve")
def approve_procurement_po(po_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    po = get_or_404(db, FinancePurchaseOrder, po_id, "Purchase order")
    po.approval_status = "approved"
    po.status = "approved"
    audit(db, current_user, "FIN-095_PO_APPROVED", "purchase_orders", po.id, "PO approved")
    db.commit()
    return {"buc": "FIN-095", **serialize(po)}


@router.post("/procurement/purchase-orders/{po_id}/goods-receipts")
def receive_goods(po_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    po = get_or_404(db, FinancePurchaseOrder, po_id, "Purchase order")
    qty = money(payload.get("received_quantity"))
    if qty + money(po.received_quantity) > money(payload.get("ordered_quantity") or qty + money(po.received_quantity)):
        raise HTTPException(status_code=422, detail="Received quantity cannot exceed ordered quantity")
    value = qty * money(payload.get("unit_cost") or (money(po.total_amount) / max(qty, Decimal("1"))))
    grn = FinanceGoodsReceipt(grn_number=payload.get("grn_number") or next_number("GRN"), purchase_order_id=po.id, received_quantity=qty, unit_cost=money(payload.get("unit_cost")), received_value=value, notes=payload.get("notes"))
    po.received_quantity = money(po.received_quantity) + qty
    po.goods_received_status = "received"
    db.add(grn); db.flush()
    audit(db, current_user, "FIN-096_GOODS_RECEIVED", "goods_receipts", grn.id, f"Value {value}")
    db.commit()
    return {"buc": "FIN-096", "grn": serialize(grn), "purchase_order": serialize(po)}


@router.post("/procurement/purchase-orders/{po_id}/service-acceptance")
def accept_service(po_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("evidence"):
        raise HTTPException(status_code=422, detail="Service completion evidence is required")
    po = get_or_404(db, FinancePurchaseOrder, po_id, "Purchase order")
    po.service_acceptance_status = "accepted"
    audit(db, current_user, "FIN-097_SERVICE_ACCEPTED", "purchase_orders", po.id, payload["evidence"])
    db.commit()
    return {"buc": "FIN-097", **serialize(po)}


@router.get("/procurement/reports")
def procurement_reporting(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    spend = money(db.query(func.coalesce(func.sum(FinancePurchaseOrder.total_amount), 0)).filter(FinancePurchaseOrder.approval_status == "approved").scalar())
    return {"buc": "FIN-099", "procurement_spend": as_float(spend), "open_prs": db.query(FinancePurchaseRequest).filter(FinancePurchaseRequest.status.notin_(["closed", "rejected"])).count(), "open_pos": db.query(FinancePurchaseOrder).filter(FinancePurchaseOrder.status.notin_(["closed", "cancelled"])).count(), "vendor_count": db.query(FinanceVendor).count()}


@router.post("/bank-cash/bank-accounts")
def create_bank_account(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("gl_account_id"):
        raise HTTPException(status_code=422, detail="GL account mapping is required")
    if db.query(FinanceBankAccount).filter(FinanceBankAccount.account_number == payload.get("account_number")).first():
        raise HTTPException(status_code=409, detail="Bank account number must be unique")
    active_account(db, payload["gl_account_id"])
    account = FinanceBankAccount(account_name=payload.get("account_name") or payload.get("bank_name"), bank_name=payload.get("bank_name"), account_number=payload.get("account_number"), account_type="bank", currency=payload.get("currency") or "KES", opening_balance=money(payload.get("opening_balance")), current_balance=money(payload.get("opening_balance")), status="active")
    db.add(account); db.flush()
    audit(db, current_user, "FIN-100_BANK_ACCOUNT_CREATED", "bank_accounts", account.id, "Bank account created")
    db.commit()
    return {"buc": "FIN-100", **serialize(account)}


@router.post("/bank-cash/cash-accounts")
def setup_cash_account(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("custodian"):
        raise HTTPException(status_code=422, detail="Responsible custodian is required")
    if not payload.get("gl_account_id"):
        raise HTTPException(status_code=422, detail="GL mapping is mandatory")
    active_account(db, payload["gl_account_id"])
    account = FinanceBankAccount(account_name=payload.get("account_name") or payload.get("cash_type") or "Cash Account", bank_name="Cash", account_number=payload.get("account_number") or next_number("CASH"), account_type=payload.get("cash_type") or "petty_cash", currency=payload.get("currency") or "KES", opening_balance=money(payload.get("opening_balance")), current_balance=money(payload.get("opening_balance")), status="active")
    db.add(account); db.flush()
    audit(db, current_user, "FIN-101_CASH_ACCOUNT_CREATED", "bank_accounts", account.id, payload["custodian"])
    db.commit()
    return {"buc": "FIN-101", **serialize(account)}


@router.post("/bank-cash/reconciliations")
def bank_reconciliation(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    account = get_or_404(db, FinanceBankAccount, UUID(str(payload.get("bank_account_id"))), "Bank account")
    adjusted_book = money(account.current_balance) + money(payload.get("deposits_in_transit")) - money(payload.get("outstanding_cheques"))
    adjusted_bank = money(payload.get("bank_statement_balance")) + money(payload.get("bank_errors")) - money(payload.get("outstanding_items"))
    difference = adjusted_book - adjusted_bank
    rec = FinanceBankReconciliation(bank_account_id=account.id, book_balance=account.current_balance, deposits_in_transit=money(payload.get("deposits_in_transit")), outstanding_cheques=money(payload.get("outstanding_cheques")), bank_statement_balance=money(payload.get("bank_statement_balance")), bank_errors=money(payload.get("bank_errors")), outstanding_items=money(payload.get("outstanding_items")), difference=difference, status="matched" if difference == 0 else "variance")
    db.add(rec); db.flush()
    audit(db, current_user, "FIN-102_BANK_RECONCILIATION", "bank_reconciliations", rec.id, rec.status)
    db.commit()
    return {"buc": "FIN-102", "adjusted_book_balance": as_float(adjusted_book), "adjusted_bank_balance": as_float(adjusted_bank), **serialize(rec)}


@router.get("/bank-cash/cash-forecast")
def cash_forecast(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    opening = money(db.query(func.coalesce(func.sum(FinanceBankAccount.current_balance), 0)).filter(FinanceBankAccount.status == "active").scalar())
    receipts = current_ar(db)
    payments = current_ap(db) + money(db.query(func.coalesce(func.sum(FinancePayment.amount), 0)).filter(FinancePayment.status.in_(["scheduled", "approved"])).scalar())
    return {"buc": "FIN-103", "opening_balance": as_float(opening), "expected_receipts": as_float(receipts), "expected_payments": as_float(payments), "forecast_cash": as_float(opening + receipts - payments)}


@router.post("/bank-cash/transfers")
def cash_transfer(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    source = active_account(db, payload.get("source_account_id"))
    target = active_account(db, payload.get("target_account_id"))
    amount = money(payload.get("amount"))
    journal = create_balanced_two_line_journal(db, current_user, amount=amount, debit_account_id=target.id, credit_account_id=source.id, description="Cash transfer", source_module="finance.bank_cash", reference_type="cash_transfer", journal_type="cash_transfer", auto_post=True)
    audit(db, current_user, "FIN-104_CASH_TRANSFERRED", "journal_entries", journal.id, f"{amount}")
    db.commit()
    return {"buc": "FIN-104", "journal": serialize(journal)}


@router.post("/bank-cash/petty-cash/expenses")
def petty_cash_expense(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("custodian") or not payload.get("receipt_url"):
        raise HTTPException(status_code=422, detail="Custodian and receipt are required")
    expense = FinanceExpense(expense_number=next_number("PETTY"), expense_date=date.today(), category="Petty Cash", amount=money(payload.get("amount")), approval_status="approved", payment_status="paid", status="paid", notes=payload.get("notes"))
    db.add(expense); db.flush()
    audit(db, current_user, "FIN-105_PETTY_CASH_EXPENSE", "expenses", expense.id, payload["custodian"])
    db.commit()
    return {"buc": "FIN-105", **serialize(expense)}


@router.post("/bank-cash/petty-cash/replenish")
def petty_cash_replenish(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    debit = active_account(db, payload.get("expense_account_id")) if payload.get("expense_account_id") else default_account(db, "expense", ["expense"])
    credit = active_account(db, payload.get("bank_account_id")) if payload.get("bank_account_id") else default_account(db, "asset", ["bank"])
    amount = money(payload.get("amount"))
    journal = create_balanced_two_line_journal(db, current_user, amount=amount, debit_account_id=debit.id, credit_account_id=credit.id, description="Petty cash replenishment", source_module="finance.bank_cash", reference_type="petty_cash_replenishment", journal_type="petty_cash", auto_post=True)
    db.commit()
    return {"buc": "FIN-106", "journal": serialize(journal), "replenishment_amount": as_float(amount)}


@router.get("/bank-cash/cash-flow-projection")
def cash_flow_projection(scenario: str = Query(default="expected"), db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    forecast = cash_forecast(db, current_user)
    factor = Decimal("1.2") if scenario == "best" else Decimal("0.8") if scenario == "worst" else Decimal("1")
    projected = money(forecast["opening_balance"]) + money(forecast["expected_receipts"]) * factor - money(forecast["expected_payments"])
    return {**forecast, "buc": "FIN-107", "scenario": scenario, "projected_cash": as_float(projected)}


@router.post("/tax/types")
def configure_tax_type(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("effective_from"):
        raise HTTPException(status_code=422, detail="Effective date is required")
    rule = FinanceTaxRule(tax_name=payload.get("tax_name") or payload.get("tax_type"), country=payload.get("country") or "Kenya", region=payload.get("region"), tax_type=payload.get("tax_type"), rate=money(payload.get("rate")), effective_from=date.fromisoformat(str(payload.get("effective_from"))), effective_to=date.fromisoformat(str(payload.get("effective_to"))) if payload.get("effective_to") else None, status="active")
    db.add(rule); db.flush()
    audit(db, current_user, "FIN-108_TAX_TYPE_CONFIGURED", "tax_rules", rule.id, rule.tax_type)
    db.commit()
    return {"buc": "FIN-108", **serialize(rule)}


@router.post("/tax/vat")
def configure_vat(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = {**payload, "tax_type": "VAT", "tax_name": payload.get("tax_name") or "VAT"}
    result = configure_tax_type(payload, db, current_user)
    result["buc"] = "FIN-109"
    return result


@router.post("/tax/withholding")
def configure_wht(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = {**payload, "tax_type": "WHT", "tax_name": payload.get("tax_name") or "Withholding Tax"}
    result = configure_tax_type(payload, db, current_user)
    result["buc"] = "FIN-110"
    return result


@router.post("/tax/paye")
def configure_paye(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = {**payload, "tax_type": "PAYE", "tax_name": payload.get("tax_name") or "PAYE"}
    result = configure_tax_type(payload, db, current_user)
    result["buc"] = "FIN-111"
    return result


@router.post("/tax/validate")
def validate_tax(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    missing = []
    if not payload.get("tax_code") and not payload.get("tax_type"):
        missing.append("missing_tax_code")
    if payload.get("tax_rate") is None:
        missing.append("missing_tax_rate")
    valid = not missing
    return {"buc": "FIN-112", "valid": valid, "exceptions": missing}


@router.post("/tax/calculate-advanced")
def calculate_tax_advanced(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    taxable = money(payload.get("net_amount") or payload.get("taxable_amount"))
    tax_type = str(payload.get("tax_type") or "VAT")
    rate = money(payload.get("rate"))
    if not rate:
        rule = db.query(FinanceTaxRule).filter(FinanceTaxRule.tax_type == tax_type, FinanceTaxRule.status == "active").order_by(FinanceTaxRule.effective_from.desc()).first()
        rate = money(getattr(rule, "rate", 0))
    amounts = tax_amounts(taxable, rate, tax_type)
    record = FinanceTaxRecord(tax_type=tax_type, tax_period=payload.get("tax_period") or str(date.today().year), taxable_amount=taxable, tax_amount=amounts["tax"], due_date=date.fromisoformat(str(payload.get("due_date"))) if payload.get("due_date") else None, filing_status="calculated", notes=f"Gross {amounts['gross']}")
    db.add(record); db.flush()
    audit(db, current_user, "FIN-113_TAX_CALCULATED", "tax_records", record.id, tax_type)
    db.commit()
    return {"buc": "FIN-113", "gross_amount": as_float(amounts["gross"]), **serialize(record)}


@router.post("/tax/filings/prepare")
def prepare_tax_filing(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    tax_type = payload.get("tax_type")
    period = payload.get("tax_period")
    query = db.query(FinanceTaxRecord).filter(FinanceTaxRecord.filing_status.in_(["pending", "calculated", "submitted"]))
    if tax_type:
        query = query.filter(FinanceTaxRecord.tax_type == tax_type)
    if period:
        query = query.filter(FinanceTaxRecord.tax_period == period)
    total = money(query.with_entities(func.coalesce(func.sum(FinanceTaxRecord.tax_amount), 0)).scalar())
    audit(db, current_user, "FIN-114_TAX_FILING_PREPARED", "tax_records", None, f"{tax_type or 'All'} {period or ''}")
    db.commit()
    return {"buc": "FIN-114", "tax_type": tax_type, "tax_period": period, "tax_payable": as_float(total)}


@router.get("/tax/reports")
def tax_reporting(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = db.query(FinanceTaxRecord.tax_type, func.coalesce(func.sum(FinanceTaxRecord.tax_amount), 0)).group_by(FinanceTaxRecord.tax_type).all()
    return {"buc": "FIN-115", "summary": [{"tax_type": r[0], "tax_amount": as_float(r[1])} for r in rows]}


@router.get("/tax/audit-support")
def tax_audit_support(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return {"buc": "FIN-116", "tax_records": [serialize(r) for r in db.query(FinanceTaxRecord).order_by(FinanceTaxRecord.created_at.desc()).limit(100).all()], "audit_trail": [serialize(r) for r in db.query(FinanceAuditTrail).filter(FinanceAuditTrail.entity_type.in_(["tax_records", "tax_rules"])).limit(100).all()]}


@router.post("/assets/acquisitions")
def acquire_asset(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    po = get_or_404(db, FinancePurchaseOrder, UUID(str(payload.get("purchase_order_id"))), "Purchase order")
    threshold = money(payload.get("capitalization_threshold") or 0)
    cost = money(payload.get("cost") or po.total_amount)
    if cost < threshold:
        raise HTTPException(status_code=422, detail="Asset cost is below capitalization threshold")
    debit = active_account(db, payload.get("asset_account_id")) if payload.get("asset_account_id") else default_account(db, "asset", ["asset", "fixed"])
    credit = active_account(db, payload.get("ap_account_id")) if payload.get("ap_account_id") else default_account(db, "liability", ["payable", "ap"])
    journal = create_balanced_two_line_journal(db, current_user, amount=cost, debit_account_id=debit.id, credit_account_id=credit.id, description="Asset acquisition", source_module="finance.assets", reference_type="asset_acquisition", reference_id=po.id, journal_type="asset_acquisition", auto_post=True)
    asset = FinanceFixedAsset(asset_code=payload.get("asset_number") or next_number("AST"), asset_name=payload.get("asset_name") or f"Asset from {po.po_number}", asset_category=payload.get("category"), purchase_date=date.today(), purchase_cost=cost, current_book_value=cost, source_purchase_order_id=po.id, journal_entry_id=journal.id, status="active")
    db.add(asset); db.flush()
    audit(db, current_user, "FIN-117_ASSET_ACQUIRED", "fixed_assets", asset.id, "Asset from procurement")
    db.commit()
    return {"buc": "FIN-117", "asset": serialize(asset), "journal": serialize(journal)}


@router.post("/assets/register")
def register_asset(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if db.query(FinanceFixedAsset).filter(FinanceFixedAsset.asset_code == payload.get("asset_number")).first():
        raise HTTPException(status_code=409, detail="Asset number must be unique")
    asset = FinanceFixedAsset(asset_code=payload.get("asset_number") or next_number("AST"), asset_name=payload.get("asset_name"), asset_category=payload.get("category"), purchase_date=date.fromisoformat(str(payload.get("acquisition_date") or date.today().isoformat())), purchase_cost=money(payload.get("cost")), current_book_value=money(payload.get("cost")), custodian=payload.get("custodian"), location=payload.get("location"), depreciation_method=payload.get("depreciation_method"), residual_value=money(payload.get("residual_value")), useful_life_years=money(payload.get("useful_life_years")), status="active")
    db.add(asset); db.flush()
    audit(db, current_user, "FIN-118_ASSET_REGISTERED", "fixed_assets", asset.id, asset.asset_code)
    db.commit()
    return {"buc": "FIN-118", **serialize(asset)}


@router.post("/assets/{asset_id}/categorize")
def categorize_asset(asset_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    asset = get_or_404(db, FinanceFixedAsset, asset_id, "Asset")
    asset.asset_category = payload.get("category")
    asset.depreciation_method = payload.get("depreciation_method") or asset.depreciation_method
    audit(db, current_user, "FIN-119_ASSET_CATEGORIZED", "fixed_assets", asset.id, asset.asset_category)
    db.commit()
    return {"buc": "FIN-119", **serialize(asset)}


@router.post("/assets/{asset_id}/assign")
def assign_asset(asset_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    employee = active_employee(db, payload.get("employee_id"))
    asset = get_or_404(db, FinanceFixedAsset, asset_id, "Asset")
    movement = FinanceAssetMovement(asset_id=asset.id, movement_type="assignment", from_custodian=asset.custodian, to_custodian=employee.email, reason=payload.get("reason"))
    asset.owner_employee_id = employee.id
    asset.custodian = employee.email
    db.add(movement); db.flush()
    audit(db, current_user, "FIN-120_ASSET_ASSIGNED", "asset_movements", movement.id, employee.email)
    db.commit()
    return {"buc": "FIN-120", "asset": serialize(asset), "movement": serialize(movement)}


@router.post("/assets/{asset_id}/transfer")
def transfer_asset(asset_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    asset = get_or_404(db, FinanceFixedAsset, asset_id, "Asset")
    movement = FinanceAssetMovement(asset_id=asset.id, movement_type="transfer", from_location=asset.location, to_location=payload.get("to_location"), from_custodian=asset.custodian, to_custodian=payload.get("to_custodian"), reason=payload.get("reason"))
    asset.location = payload.get("to_location") or asset.location
    asset.custodian = payload.get("to_custodian") or asset.custodian
    db.add(movement); db.flush()
    audit(db, current_user, "FIN-121_ASSET_TRANSFERRED", "asset_movements", movement.id, movement.reason or "Transfer")
    db.commit()
    return {"buc": "FIN-121", "asset": serialize(asset), "movement": serialize(movement)}


@router.post("/assets/{asset_id}/revalue")
def revalue_asset(asset_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    asset = get_or_404(db, FinanceFixedAsset, asset_id, "Asset")
    gain_loss = money(payload.get("new_value")) - (money(asset.current_book_value) or money(asset.purchase_cost) - money(asset.accumulated_depreciation))
    asset.current_book_value = money(payload.get("new_value"))
    movement = FinanceAssetMovement(asset_id=asset.id, movement_type="revaluation", amount=gain_loss, reason=payload.get("reason"))
    db.add(movement); db.flush()
    audit(db, current_user, "FIN-122_ASSET_REVALUED", "asset_movements", movement.id, f"Gain/loss {gain_loss}")
    db.commit()
    return {"buc": "FIN-122", "gain_loss": as_float(gain_loss), "asset": serialize(asset)}


@router.post("/assets/{asset_id}/dispose")
def dispose_asset(asset_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    asset = get_or_404(db, FinanceFixedAsset, asset_id, "Asset")
    book = money(asset.current_book_value) or money(asset.purchase_cost) - money(asset.accumulated_depreciation)
    gain_loss = money(payload.get("sale_proceeds")) - book
    asset.status = "disposed"
    asset.disposal_date = date.today()
    movement = FinanceAssetMovement(asset_id=asset.id, movement_type="disposal", amount=gain_loss, reason=payload.get("reason"))
    db.add(movement); db.flush()
    audit(db, current_user, "FIN-123_ASSET_DISPOSED", "asset_movements", movement.id, f"Gain/loss {gain_loss}")
    db.commit()
    return {"buc": "FIN-123", "gain_loss": as_float(gain_loss), "asset": serialize(asset)}


@router.post("/assets/{asset_id}/retire")
def retire_asset(asset_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Retirement reason is mandatory")
    asset = get_or_404(db, FinanceFixedAsset, asset_id, "Asset")
    asset.status = "retired"
    movement = FinanceAssetMovement(asset_id=asset.id, movement_type="retirement", reason=payload["reason"])
    db.add(movement); db.flush()
    audit(db, current_user, "FIN-124_ASSET_RETIRED", "asset_movements", movement.id, payload["reason"])
    db.commit()
    return {"buc": "FIN-124", "asset": serialize(asset), "movement": serialize(movement)}


@router.get("/assets/register")
def fixed_asset_register(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return {"buc": "FIN-126", "assets": [serialize(a) for a in db.query(FinanceFixedAsset).order_by(FinanceFixedAsset.created_at.desc()).limit(500).all()], "movements": [serialize(m) for m in db.query(FinanceAssetMovement).order_by(FinanceAssetMovement.created_at.desc()).limit(200).all()]}


@router.post("/project-finance/profiles")
def create_project_profile(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    opp = get_or_404(db, CRMOpportunity, UUID(str(payload.get("opportunity_id"))), "CRM opportunity") if payload.get("opportunity_id") else None
    profile = FinanceProjectFinance(project_id=getattr(opp, "id", None) or (UUID(str(payload.get("project_id"))) if payload.get("project_id") else uuid4()), project_name=payload.get("project_name") or getattr(opp, "title", "Project"), client_name=payload.get("customer"), budget_amount=money(payload.get("budget") or payload.get("budget_amount")), revenue_amount=money(payload.get("contract_value") or getattr(opp, "opportunity_value", 0)), expense_amount=0, milestone_billing=str(payload.get("billing_milestones") or ""), cost_centers=str(payload.get("cost_centers") or ""), status="active")
    project_profitability(profile)
    db.add(profile); db.flush()
    audit(db, current_user, "FIN-127_PROJECT_PROFILE_CREATED", "project_finance", profile.id, profile.project_name)
    db.commit()
    return {"buc": "FIN-127", **serialize(profile)}


@router.post("/project-finance/{profile_id}/budget")
def allocate_project_budget(profile_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    amount = money(payload.get("amount"))
    if amount > money(profile.budget_amount):
        raise HTTPException(status_code=422, detail="Allocated budget cannot exceed approved budget")
    profile.budget_amount = amount
    audit(db, current_user, "FIN-128_PROJECT_BUDGET_ALLOCATED", "project_finance", profile.id, f"{amount}")
    db.commit()
    return {"buc": "FIN-128", **serialize(profile)}


@router.post("/project-finance/{profile_id}/resources")
def allocate_project_resource(profile_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    employee = active_employee(db, payload.get("employee_id"))
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    cost = money(payload.get("hours")) * money(payload.get("hourly_rate"))
    profile.expense_amount = money(profile.expense_amount) + cost
    project_profitability(profile)
    audit(db, current_user, "FIN-129_PROJECT_RESOURCE_ALLOCATED", "project_finance", profile.id, f"{employee.email} cost {cost}")
    db.commit()
    return {"buc": "FIN-129", "resource_cost": as_float(cost), "profile": serialize(profile)}


@router.post("/project-finance/{profile_id}/costs")
def track_project_cost(profile_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    cost = money(payload.get("labor")) + money(payload.get("procurement")) + money(payload.get("expenses")) + money(payload.get("contractors"))
    profile.expense_amount = money(profile.expense_amount) + cost
    project_profitability(profile)
    db.commit()
    return {"buc": "FIN-130", "total_cost": as_float(cost), "profile": serialize(profile)}


@router.post("/project-finance/{profile_id}/revenue")
def track_project_revenue(profile_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    revenue = money(payload.get("invoices")) + money(payload.get("recognized_revenue"))
    profile.revenue_amount = money(profile.revenue_amount) + revenue
    project_profitability(profile)
    db.commit()
    return {"buc": "FIN-131", "revenue": as_float(revenue), "profile": serialize(profile)}


@router.post("/project-finance/{profile_id}/billing")
def project_billing(profile_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    amount = money(payload.get("milestone_value")) or money(payload.get("hours")) * money(payload.get("rate")) or money(payload.get("fixed_fee"))
    invoice = FinanceInvoice(invoice_number=next_number("PROJ-INV"), invoice_date=date.today(), due_date=date.today() + timedelta(days=30), project_id=profile.project_id, subtotal=amount, total_amount=amount, approval_status="draft", status="draft", notes=f"Project billing {profile.project_name}")
    db.add(invoice); db.flush()
    audit(db, current_user, "FIN-132_PROJECT_BILLING_CREATED", "invoices", invoice.id, f"{amount}")
    db.commit()
    return {"buc": "FIN-132", "invoice": serialize(invoice)}


@router.get("/project-finance/{profile_id}/profitability")
def project_profitability_report(profile_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    project_profitability(profile)
    margin = (money(profile.profitability) / money(profile.revenue_amount) * Decimal("100")) if money(profile.revenue_amount) else Decimal("0")
    return {"buc": "FIN-133", "profit": as_float(profile.profitability), "margin_percent": as_float(margin), "budget_variance": as_float(money(profile.expense_amount) - money(profile.budget_amount)), "negative_margin_alert": money(profile.profitability) < 0, "profile": serialize(profile)}


@router.post("/project-finance/{profile_id}/forecast")
def project_forecast(profile_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    profile.forecast_revenue = money(payload.get("forecast_revenue"))
    profile.forecast_cost = money(payload.get("forecast_cost"))
    db.commit()
    return {"buc": "FIN-134", "forecast_margin": as_float(money(profile.forecast_revenue) - money(profile.forecast_cost)), "profile": serialize(profile)}


@router.post("/project-finance/{profile_id}/close")
def close_project_finance(profile_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, profile_id, "Project finance profile")
    if not payload.get("approval"):
        raise HTTPException(status_code=422, detail="Closure approval is required")
    profile.status = "closed"
    audit(db, current_user, "FIN-135_PROJECT_FINANCE_CLOSED", "project_finance", profile.id, "Financial closure completed")
    db.commit()
    return {"buc": "FIN-135", **serialize(profile)}

@router.post("/bank-accounts/{bank_account_id}/reconcile")
def reconcile_bank(bank_account_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    account = get_or_404(db, FinanceBankAccount, bank_account_id, "Bank account")
    book_balance = money(account.current_balance)
    deposits = money(payload.get("deposits_in_transit"))
    outstanding = money(payload.get("outstanding_cheques"))
    bank_balance = money(payload.get("bank_balance"))
    expected = book_balance + deposits - outstanding
    reconciled = expected == bank_balance
    audit(db, current_user, "FIN-102_BANK_RECONCILIATION", "bank_accounts", account.id, f"Reconciled={reconciled}")
    db.commit()
    return {"book_balance": as_float(book_balance), "deposits_in_transit": as_float(deposits), "outstanding_cheques": as_float(outstanding), "expected_bank_balance": as_float(expected), "bank_balance": as_float(bank_balance), "reconciled": reconciled}


@router.post("/tax/calculate")
def calculate_tax(payload: dict[str, Any]):
    net = money(payload.get("net_amount") or payload.get("taxable_amount"))
    rate = money(payload.get("rate") or payload.get("vat_percent"))
    return {"taxable_amount": as_float(net), "rate": as_float(rate), "tax_amount": as_float(net * rate / Decimal("100"))}


@router.post("/fixed-assets/{asset_id}/depreciation")
def calculate_depreciation(asset_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    asset = get_or_404(db, FinanceFixedAsset, asset_id, "Fixed asset")
    method = str(payload.get("method") or asset.depreciation_method or "straight_line").lower()
    if "reducing" in method:
        amount = (money(asset.purchase_cost) - money(asset.accumulated_depreciation)) * money(payload.get("rate")) / Decimal("100")
    else:
        amount = (money(asset.purchase_cost) - money(payload.get("residual_value"))) / max(money(payload.get("useful_life") or 1), Decimal("1"))
    asset.accumulated_depreciation = money(asset.accumulated_depreciation) + amount
    audit(db, current_user, "FIN-125_DEPRECIATION_CALCULATED", "fixed_assets", asset.id, f"Depreciation {amount}")
    db.commit()
    return {"asset": serialize(asset), "depreciation": as_float(amount)}


@router.get("/project-finance/{project_finance_id}/profitability")
def get_project_profitability(project_finance_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    profile = get_or_404(db, FinanceProjectFinance, project_finance_id, "Project finance profile")
    project_profitability(profile)
    revenue = money(profile.revenue_amount)
    profit = money(profile.profitability)
    margin = (profit / revenue * Decimal("100")) if revenue else Decimal("0")
    db.commit()
    return {"profit": as_float(profit), "margin_percent": as_float(margin), "profile": serialize(profile)}


@router.post("/approvals/matrix")
def create_approval_matrix(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "admin", "approvals")
    levels = payload.get("approval_levels")
    if not levels:
        raise HTTPException(status_code=422, detail="Approval levels are required")
    module = str(payload.get("module") or "").strip()
    transaction_type = str(payload.get("transaction_type") or "").strip()
    if not module or not transaction_type:
        raise HTTPException(status_code=422, detail="Module and transaction type are required")
    min_amount = money(payload.get("min_amount"))
    max_amount = payload.get("max_amount")
    max_amount_decimal = money(max_amount) if max_amount not in (None, "") else None
    overlap_query = db.query(FinanceApprovalMatrix).filter(
        FinanceApprovalMatrix.module == module,
        FinanceApprovalMatrix.transaction_type == transaction_type,
        FinanceApprovalMatrix.status == "active",
    )
    for matrix in overlap_query.all():
        existing_min = money(matrix.min_amount)
        existing_max = money(matrix.max_amount) if matrix.max_amount is not None else None
        left_ok = existing_max is None or min_amount <= existing_max
        right_ok = max_amount_decimal is None or existing_min <= max_amount_decimal
        if left_ok and right_ok:
            raise HTTPException(status_code=409, detail="Approval matrix amount range overlaps an active matrix")
    clone_from_id = payload.get("clone_from_id")
    version = 1
    if clone_from_id:
        source = get_or_404(db, FinanceApprovalMatrix, clone_from_id, "Approval matrix")
        version = (source.version_number or 1) + 1
    matrix = FinanceApprovalMatrix(
        matrix_name=payload.get("matrix_name") or payload.get("name") or f"{module} {transaction_type} Matrix",
        module=module,
        transaction_type=transaction_type,
        min_amount=min_amount,
        max_amount=max_amount_decimal,
        approval_levels=str(levels),
        effective_date=parse_date(payload.get("effective_date"), "Effective date", required=True),
        version_number=version,
        status=payload.get("status") or "active",
        created_by=current_user.email,
    )
    db.add(matrix)
    audit(db, current_user, "FIN-136_APPROVAL_MATRIX_CREATED", "approval_matrices", matrix.id, f"{module}/{transaction_type}")
    event(db, "Finance", "approval.matrix.created", "approval_matrix", matrix.id, {"module": module, "transaction_type": transaction_type})
    db.commit()
    return {"buc": "FIN-136", "matrix": serialize(matrix)}


@router.post("/approvals/delegate")
def create_approval_delegation(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "admin", "approvals")
    delegate = active_employee(db, payload.get("delegate_employee_id"))
    delegator_id = payload.get("delegator_employee_id")
    if delegator_id:
        active_employee(db, delegator_id)
    effective_from = parse_date(payload.get("effective_from"), "Effective from", required=True)
    effective_to = parse_date(payload.get("effective_to"), "Effective to", required=True)
    if effective_to < effective_from:
        raise HTTPException(status_code=422, detail="Delegation expiry must be after the start date")
    delegation = FinanceApprovalDelegation(
        delegator_employee_id=delegator_id,
        delegate_employee_id=delegate.id,
        module=payload.get("module"),
        transaction_type=payload.get("transaction_type"),
        effective_from=effective_from,
        effective_to=effective_to,
        reason=payload.get("reason"),
        status="active",
        created_by=current_user.email,
    )
    db.add(delegation)
    audit(db, current_user, "FIN-137_APPROVAL_DELEGATED", "approval_delegations", delegation.id, payload.get("reason") or "Delegation activated")
    event(db, "Finance", "approval.delegated", "approval_delegation", delegation.id, {"delegate_employee_id": str(delegate.id)})
    db.commit()
    return {"buc": "FIN-137", "delegation": serialize(delegation)}


@router.post("/approvals/escalate")
def escalate_approval(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "update", "approvals")
    approval = get_or_404(db, FinanceApproval, payload.get("approval_id"), "Approval")
    if approval.status not in {"pending", "delegated", "escalated"}:
        raise HTTPException(status_code=409, detail="Only active approvals can be escalated")
    level = int(payload.get("escalation_level") or (approval.approval_level or 1) + 1)
    approval.status = "escalated"
    approval.approval_level = level
    approval.approver = payload.get("next_approver") or approval.approver
    approval.comments = payload.get("reason") or payload.get("comments") or "Approval escalated"
    approval_history(db, approval, "escalated", approval.comments, escalation_level=level, actor=current_user.email)
    audit(db, current_user, "FIN-138_APPROVAL_ESCALATED", "approvals", approval.id, approval.comments)
    event(db, "Finance", "approval.escalated", "approval", approval.id, {"approval_level": level, "approver": approval.approver})
    db.commit()
    return {"buc": "FIN-138", "approval": serialize(approval)}


@router.post("/approvals/emergency")
def create_emergency_approval(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "admin", "approvals")
    justification = payload.get("justification")
    if not justification:
        raise HTTPException(status_code=422, detail="Emergency justification is required")
    approval = FinanceApproval(
        approval_type=payload.get("approval_type") or "emergency",
        related_record_type=payload.get("related_record_type") or "emergency_transaction",
        related_record_id=payload.get("related_record_id"),
        requested_by=payload.get("requested_by") or current_user.email,
        approver=payload.get("approver") or current_user.email,
        approval_level=1,
        status="emergency_approved",
        comments=justification,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(approval)
    approval_history(db, approval, "emergency_approved", justification, actor=current_user.email)
    audit(db, current_user, "FIN-140_EMERGENCY_APPROVAL", "approvals", approval.id, justification)
    event(db, "Finance", "approval.completed", "approval", approval.id, {"decision": "emergency_approved", "post_review_required": True})
    db.commit()
    return {"buc": "FIN-140", "approval": serialize(approval), "post_review_required": True}


@router.get("/approvals/history")
def get_approval_history(
    source_module: str | None = Query(default=None),
    source_record_type: str | None = Query(default=None),
    approver: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    require_finance_access(db, current_user, "read", "approvals")
    query = db.query(FinanceApprovalHistory)
    if source_module:
        query = query.filter(FinanceApprovalHistory.source_module == source_module)
    if source_record_type:
        query = query.filter(FinanceApprovalHistory.source_record_type == source_record_type)
    if approver:
        query = query.filter(FinanceApprovalHistory.approver == approver)
    history = query.order_by(FinanceApprovalHistory.created_at.desc()).limit(300).all()
    return {"buc": "FIN-141", "history": [serialize(row) for row in history]}


@router.post("/approvals/{approval_id}/decide")
def decide_approval(approval_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    approval = get_or_404(db, FinanceApproval, approval_id, "Approval")
    decision = payload.get("decision")
    if decision not in {"approved", "rejected", "delegated", "escalated", "emergency_approved"}:
        raise HTTPException(status_code=422, detail="Invalid approval decision")
    if decision == "rejected" and not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    approval.status = decision
    approval.comments = payload.get("reason") or payload.get("comments")
    approval.decided_at = datetime.now(timezone.utc)
    approval_history(db, approval, decision, approval.comments, actor=current_user.email)
    audit(db, current_user, f"FIN_APPROVAL_{decision.upper()}", "approvals", approval.id, approval.comments or decision)
    event_type = "approval.rejected" if decision == "rejected" else "approval.completed"
    event(db, "Finance", event_type, "approval", approval.id, {"decision": decision})
    db.commit()
    return serialize(approval)


@router.post("/documents/upload")
def upload_finance_document(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "create", "documents")
    ensure_document_requirements(payload)
    document_type = str(payload.get("document_type"))
    document_number = payload.get("document_number") or payload.get("invoice_number") or payload.get("contract_number") or payload.get("po_number")
    file_hash = payload.get("file_hash")
    duplicate_query = db.query(FinanceDocument).filter(FinanceDocument.status != "archived")
    if file_hash:
        duplicate = duplicate_query.filter(FinanceDocument.file_hash == file_hash).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Duplicate finance document detected")
    if document_number:
        duplicate = duplicate_query.filter(FinanceDocument.document_type == document_type, FinanceDocument.document_number == document_number).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Duplicate document number detected")
    document_date = parse_date(payload.get("document_date") or payload.get("statement_date"), "Document date")
    retention_years = int(payload.get("retention_years") or default_retention_years(document_type))
    retention_until = parse_date(payload.get("retention_until"), "Retention until") or (document_date or date.today()).replace(year=(document_date or date.today()).year + retention_years)
    document = FinanceDocument(
        document_title=payload.get("document_title") or payload.get("title") or f"{document_type} {document_number or ''}".strip(),
        document_type=document_type,
        related_record_type=payload.get("related_record_type"),
        related_record_id=payload.get("related_record_id"),
        document_number=document_number,
        party_name=payload.get("party_name") or payload.get("vendor") or payload.get("customer") or payload.get("owner"),
        amount=money(payload.get("amount")),
        currency=payload.get("currency") or "KES",
        document_date=document_date,
        expiry_date=parse_date(payload.get("expiry_date"), "Expiry date"),
        file_name=payload.get("file_name"),
        file_url=payload.get("file_url"),
        file_hash=file_hash,
        ocr_text=payload.get("ocr_text") or ("OCR pending" if payload.get("ocr_requested", True) else None),
        change_comments=payload.get("comments"),
        version_number=1,
        retention_until=retention_until,
        retention_policy=payload.get("retention_policy") or f"{retention_years}_years",
        legal_hold=bool(payload.get("legal_hold", False)),
        confidentiality_level=payload.get("confidentiality_level") or "finance",
        status="active",
        uploaded_by=current_user.email,
    )
    db.add(document)
    buc = document_buc(document_type)
    audit(db, current_user, f"{buc}_DOCUMENT_UPLOADED", "documents", document.id, document.document_title)
    event(db, "Finance", "finance.document.uploaded", "document", document.id, {"document_type": document_type, "buc": buc})
    db.commit()
    return {"buc": buc, "document": serialize(document)}


@router.post("/documents/version")
def version_finance_document(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "update", "documents")
    if not payload.get("change_comments"):
        raise HTTPException(status_code=422, detail="Change comments are required")
    document = get_or_404(db, FinanceDocument, payload.get("document_id"), "Finance document")
    new_document = FinanceDocument(
        document_title=payload.get("document_title") or document.document_title,
        document_type=document.document_type,
        related_record_type=document.related_record_type,
        related_record_id=document.related_record_id,
        document_number=document.document_number,
        party_name=document.party_name,
        amount=document.amount,
        currency=document.currency,
        document_date=document.document_date,
        expiry_date=parse_date(payload.get("expiry_date"), "Expiry date") or document.expiry_date,
        file_name=payload.get("file_name") or document.file_name,
        file_url=payload.get("file_url") or document.file_url,
        file_hash=payload.get("file_hash") or document.file_hash,
        ocr_text=payload.get("ocr_text") or document.ocr_text,
        change_comments=payload.get("change_comments"),
        version_number=(document.version_number or 1) + 1,
        retention_until=document.retention_until,
        retention_policy=document.retention_policy,
        legal_hold=document.legal_hold,
        confidentiality_level=document.confidentiality_level,
        uploaded_by=current_user.email,
    )
    document.status = "superseded"
    db.add(new_document)
    audit(db, current_user, "FIN-148_DOCUMENT_VERSIONED", "documents", document.id, payload["change_comments"])
    event(db, "Finance", "finance.document.versioned", "document", new_document.id, {"previous_document_id": str(document.id)})
    db.commit()
    return {"buc": "FIN-148", "document": serialize(new_document), "previous_version": serialize(document)}


@router.post("/documents/archive")
def archive_finance_document(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "update", "documents")
    document = get_or_404(db, FinanceDocument, payload.get("document_id"), "Finance document")
    if document.legal_hold:
        raise HTTPException(status_code=409, detail="Document under legal hold cannot be archived")
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Archive reason is required")
    document.status = "archived"
    document.archived_at = datetime.now(timezone.utc)
    document.archive_reason = payload["reason"]
    audit(db, current_user, "FIN-149_DOCUMENT_ARCHIVED", "documents", document.id, payload["reason"])
    event(db, "Finance", "finance.document.archived", "document", document.id, {"reason": payload["reason"]})
    db.commit()
    return {"buc": "FIN-149", "document": serialize(document)}


@router.get("/documents")
def list_finance_documents(
    document_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    related_record_type: str | None = Query(default=None),
    expiring_days: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    require_finance_access(db, current_user, "read", "documents")
    query = db.query(FinanceDocument)
    if document_type:
        query = query.filter(FinanceDocument.document_type == document_type)
    if status_filter:
        query = query.filter(FinanceDocument.status == status_filter)
    if related_record_type:
        query = query.filter(FinanceDocument.related_record_type == related_record_type)
    if expiring_days is not None:
        query = query.filter(FinanceDocument.expiry_date <= date.today() + timedelta(days=expiring_days), FinanceDocument.expiry_date >= date.today())
    documents = query.order_by(FinanceDocument.created_at.desc()).limit(300).all()
    return {"documents": [serialize(row) for row in documents]}


@router.post("/documents/retention")
def upsert_document_retention_rule(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "admin", "documents")
    document_type = payload.get("document_type")
    retention_years = payload.get("retention_years")
    if not document_type or retention_years is None:
        raise HTTPException(status_code=422, detail="Document type and retention years are required")
    rule = db.query(FinanceDocumentRetentionRule).filter(FinanceDocumentRetentionRule.document_type == document_type).first()
    if not rule:
        rule = FinanceDocumentRetentionRule(document_type=document_type, retention_years=int(retention_years))
        db.add(rule)
    rule.retention_years = int(retention_years)
    rule.legal_hold = bool(payload.get("legal_hold", rule.legal_hold))
    rule.auto_archive = bool(payload.get("auto_archive", rule.auto_archive))
    rule.status = payload.get("status") or rule.status
    audit(db, current_user, "FIN-150_RETENTION_POLICY_UPDATED", "document_retention_rules", rule.id, document_type)
    db.commit()
    return {"buc": "FIN-150", "rule": serialize(rule)}


@router.post("/documents/{document_id}/archive")
def archive_document(document_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    document = get_or_404(db, FinanceDocument, document_id, "Finance document")
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Archive reason is required")
    document.status = "archived"
    document.archived_at = datetime.now(timezone.utc)
    document.archive_reason = payload["reason"]
    audit(db, current_user, "FIN-149_DOCUMENT_ARCHIVED", "documents", document.id, payload["reason"])
    db.commit()
    return serialize(document)


@router.post("/documents/{document_id}/new-version")
def version_document(document_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    document = get_or_404(db, FinanceDocument, document_id, "Finance document")
    new_document = FinanceDocument(
        document_title=payload.get("document_title") or document.document_title,
        document_type=document.document_type,
        related_record_type=document.related_record_type,
        related_record_id=document.related_record_id,
        file_name=payload.get("file_name") or document.file_name,
        file_url=payload.get("file_url") or document.file_url,
        version_number=(document.version_number or 1) + 1,
        confidentiality_level=document.confidentiality_level,
        uploaded_by=current_user.email,
    )
    db.add(new_document)
    audit(db, current_user, "FIN-148_DOCUMENT_VERSIONED", "documents", document.id, "New document version created")
    db.commit()
    return serialize(new_document)


@router.get("/crm-integrations/revenue-forecast")
def crm_revenue_forecast(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "revenue-forecast")
    created_or_updated = 0
    quotes = db.query(CRMQuotation).filter(CRMQuotation.approval_status.in_(["approved", "not_required"]), CRMQuotation.soft_deleted.is_(False)).all()
    for quote in quotes:
        create_revenue_forecast(db, quote)
        created_or_updated += 1
        event(db, "CRM", "crm.revenue.forecast.created", "crm_quotation", quote.id, {"forecast_source": "approved_quotation"})
    db.commit()
    records = (
        db.query(FinanceRevenueRecord)
        .filter(FinanceRevenueRecord.source_module == "crm.quotation")
        .order_by(FinanceRevenueRecord.created_at.desc())
        .limit(300)
        .all()
    )
    return {"source_buc": "CRM-014", "target_buc": "FIN-004", "created_or_updated": created_or_updated, "forecasts": [serialize(row) for row in records]}


@router.get("/crm-integrations/pending-revenue")
def crm_pending_revenue(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "revenue-forecast")
    created_or_updated = 0
    lpos = db.query(CRMCustomerLPO).filter(CRMCustomerLPO.status.in_(["received", "approved", "submitted"]), CRMCustomerLPO.soft_deleted.is_(False)).all()
    for lpo in lpos:
        create_pending_revenue_from_lpo(db, lpo)
        created_or_updated += 1
        event(db, "CRM", "crm.pending.revenue.created", "crm_lpo", lpo.id, {"project_candidate": True})
        if lpo.opportunity_id:
            opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == lpo.opportunity_id).first()
            if opportunity:
                create_project_financial_profile(db, opportunity)
                event(db, "CRM", "crm.project.finance.created", "crm_opportunity", opportunity.id, {"source": "lpo_received"})
    db.commit()
    records = (
        db.query(FinanceRevenueRecord)
        .filter(FinanceRevenueRecord.source_module == "crm.lpo")
        .order_by(FinanceRevenueRecord.created_at.desc())
        .limit(300)
        .all()
    )
    return {"source_buc": "CRM-018", "target_bucs": ["FIN-004", "FIN-127"], "created_or_updated": created_or_updated, "pending_revenue": [serialize(row) for row in records]}


@router.get("/crm-integrations/deferred-revenue")
def crm_deferred_revenue(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    require_finance_access(db, current_user, "read", "project-finance")
    created_or_existing = 0
    contracts = db.query(CRMContract).filter(CRMContract.status.in_(["active", "signed", "renewed"]), CRMContract.soft_deleted.is_(False)).all()
    for contract in contracts:
        rows = create_deferred_revenue_schedule(db, contract)
        created_or_existing += len(rows)
        if rows:
            event(db, "CRM", "crm.customer_contract.signed", "crm_contract", contract.id, {"deferred_revenue_lines": len(rows), "renewal_date": str(contract.renewal_date)})
    db.commit()
    schedules = db.query(FinanceDeferredRevenueSchedule).order_by(FinanceDeferredRevenueSchedule.schedule_period.asc()).limit(500).all()
    return {"source_buc": "CRM_CUSTOMER_CONTRACT", "target_bucs": ["FIN-131", "FIN-132", "FIN-134"], "schedule_count": created_or_existing, "deferred_revenue": [serialize(row) for row in schedules]}


@router.post("/integrations/crm/sync")
def sync_crm_to_finance(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    sync_result = sync_finance_from_operations(db)
    created = {"forecasts": 0, "invoices": 0, "project_profiles": 0, "contracts": 0}
    for quote in db.query(CRMQuotation).filter(CRMQuotation.approval_status.in_(["approved", "not_required"]), CRMQuotation.soft_deleted.is_(False)).all():
        create_revenue_forecast(db, quote)
        created["forecasts"] += 1
        event(db, "CRM", "crm.revenue.forecast.created", "crm_quotation", quote.id, {"finance_result": "revenue_forecast"})
    for lpo in db.query(CRMCustomerLPO).filter(CRMCustomerLPO.status.in_(["received", "approved", "submitted"])).all():
        create_pending_revenue_from_lpo(db, lpo)
        event(db, "CRM", "crm.pending.revenue.created", "crm_lpo", lpo.id, {"finance_result": "pending_revenue_project_candidate"})
    won_statuses = {"closed_won", "won"}
    for opportunity in db.query(CRMOpportunity).filter(CRMOpportunity.status.in_(won_statuses)).all():
        generate_invoice_from_opportunity(db, opportunity)
        create_project_financial_profile(db, opportunity)
        created["invoices"] += 1
        created["project_profiles"] += 1
        event(db, "CRM", "crm.opportunity.won", "crm_opportunity", opportunity.id, {"finance_result": "invoice_project_budget_revenue_tracking"})
    for contract in db.query(CRMContract).filter(CRMContract.status.in_(["active", "signed", "renewed"])).all():
        rows = create_deferred_revenue_schedule(db, contract)
        event(db, "CRM", "crm.customer_contract.signed", "crm_contract", contract.id, {"finance_result": "deferred_revenue_renewal_forecast", "schedule_lines": len(rows)})
        created["contracts"] += 1
    audit(db, current_user, "FIN_CRM_SYNC", "integration_events", None, "CRM to Finance sync completed")
    db.commit()
    return {"message": "CRM -> Finance sync completed", "created_or_updated": created, "operational_sync": sync_result}


@router.post("/integrations/hrms/sync")
def sync_hrms_to_finance(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    result = sync_finance_from_operations(db)
    payroll = money(db.query(func.coalesce(func.sum(HRMPayroll.gross_pay), 0)).scalar())
    existing = db.query(FinanceBudget).filter(FinanceBudget.budget_type == "Salary", FinanceBudget.fiscal_year == str(date.today().year)).first()
    if not existing:
        existing = FinanceBudget(budget_name=f"Salary Budget {date.today().year}", budget_type="Salary", department="HR", fiscal_year=str(date.today().year), approval_status="draft", status="active")
        db.add(existing)
    existing.actual_amount = payroll
    event(db, "HRMS", "EMPLOYEE_PAYROLL_FINANCE_SYNC", "hrm_payroll", None, {"salary_budget_actual": as_float(payroll)})
    audit(db, current_user, "FIN_HRMS_SYNC", "integration_events", None, "HRMS to Finance sync completed")
    db.commit()
    return {"message": "HRMS -> Finance sync completed", "salary_budget_actual": as_float(payroll), "operational_sync": result}
