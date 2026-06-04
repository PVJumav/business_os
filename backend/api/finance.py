import base64
import os
import re
import uuid as uuid_module
from decimal import Decimal
from typing import Any
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.crud import assign_business_id
from backend.core.database import get_db
from backend.models.finance import (
    FinanceApproval,
    FinanceAuditTrail,
    FinanceBankAccount,
    FinanceBankTransaction,
    FinanceBill,
    FinanceBudget,
    FinanceChartAccount,
    FinanceCostCenter,
    FinanceCreditNote,
    FinanceDocument,
    FinanceExpense,
    FinanceExpenseClaim,
    FinanceFixedAsset,
    FinanceIntegrationEvent,
    FinanceInvoice,
    FinanceJournalEntry,
    FinanceJournalLine,
    FinancePayment,
    FinanceProjectFinance,
    FinancePurchaseOrder,
    FinancePurchaseRequest,
    FinanceReceipt,
    FinanceRevenueRecord,
    FinanceTaxRecord,
    FinanceVendor,
)
from backend.models.crm import CRMDeal, CRMInvoice
from backend.models.hrm import HRMBenefit, HRMPayroll, HRMTraining
from backend.services.finance_sync import consolidated_finance_totals, sync_finance_from_operations


router = APIRouter(prefix="/finance", tags=["Finance"])


RESOURCE_REGISTRY = {
    "chart-accounts": FinanceChartAccount,
    "cost-centers": FinanceCostCenter,
    "journal-entries": FinanceJournalEntry,
    "journal-lines": FinanceJournalLine,
    "vendors": FinanceVendor,
    "bills": FinanceBill,
    "payments": FinancePayment,
    "invoices": FinanceInvoice,
    "receipts": FinanceReceipt,
    "credit-notes": FinanceCreditNote,
    "expense-claims": FinanceExpenseClaim,
    "budgets": FinanceBudget,
    "purchase-requests": FinancePurchaseRequest,
    "purchase-orders": FinancePurchaseOrder,
    "bank-accounts": FinanceBankAccount,
    "bank-transactions": FinanceBankTransaction,
    "tax-records": FinanceTaxRecord,
    "fixed-assets": FinanceFixedAsset,
    "project-finance": FinanceProjectFinance,
    "revenue-records": FinanceRevenueRecord,
    "approvals": FinanceApproval,
    "audit-trails": FinanceAuditTrail,
    "documents": FinanceDocument,
    "integration-events": FinanceIntegrationEvent,
}

DEFAULT_TAX_RATES = {
    ("Kenya", "standard"): 16,
    ("Kenya", "zero_rated"): 0,
    ("Kenya", "exempt"): 0,
}


def _serialize_value(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    return value


def row_to_dict(row):
    return {column.name: _serialize_value(getattr(row, column.name)) for column in row.__table__.columns}


def model_for(resource: str):
    model = RESOURCE_REGISTRY.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Finance resource not found")
    return model


def clean_payload(payload: dict[str, Any]):
    return {key: value for key, value in payload.items() if value not in ["", None]}


def coerce_uuid_fields(model, payload: dict[str, Any]):
    cleaned = dict(payload)
    for column in model.__table__.columns:
      if "UUID" not in column.type.__class__.__name__.upper():
          continue
      value = cleaned.get(column.name)
      if value in [None, ""]:
          continue
      try:
          cleaned[column.name] = UUID(str(value))
      except ValueError as exc:
          if column.nullable:
              cleaned[column.name] = None
          else:
              raise HTTPException(
                  status_code=422,
                  detail=f"{column.name} must be selected from the system records.",
              ) from exc
    return cleaned


def tax_rate_for(country: str | None, region: str | None):
    normalized_country = country or "Kenya"
    normalized_region = (region or "standard").lower().replace(" ", "_").replace("-", "_")
    return DEFAULT_TAX_RATES.get((normalized_country, normalized_region), DEFAULT_TAX_RATES.get((normalized_country, "standard"), 0))


def automate_invoice_payload(payload: dict[str, Any]):
    subtotal = Decimal(str(payload.get("subtotal") or 0))
    discount = Decimal(str(payload.get("discount_amount") or 0))
    rate = Decimal(str(payload.get("tax_rate") or tax_rate_for(payload.get("tax_country"), payload.get("tax_region"))))
    tax = subtotal * rate / Decimal("100")
    total = subtotal + tax - discount
    paid = Decimal(str(payload.get("paid_amount") or 0))

    payload["tax_country"] = payload.get("tax_country") or "Kenya"
    payload["tax_region"] = payload.get("tax_region") or "standard"
    payload["tax_rate"] = float(rate)
    payload["tax_amount"] = float(tax)
    payload["total_amount"] = float(total)
    payload["paid_amount"] = float(paid)

    if total > 0 and paid >= total:
        payload["status"] = "paid"
    elif paid > 0:
        payload["status"] = payload.get("status") or "part_paid"
    return payload


def automate_expense_claim_payload(payload: dict[str, Any]):
    category = str(payload.get("expense_category") or "").lower()
    if "mileage" in category:
        payload["amount"] = float(Decimal(str(payload.get("distance") or 0)) * Decimal(str(payload.get("mileage_rate") or 0)))
    elif "per diem" in category or "per_diem" in category:
        payload["amount"] = float(Decimal(str(payload.get("per_diem_days") or 0)) * Decimal(str(payload.get("per_diem_rate") or 0)))
    return payload


def sync_system_revenue(db: Session):
    sync_finance_from_operations(db)
    return
    won_deals = db.query(CRMDeal).filter(CRMDeal.deal_status == "closed_won").all()
    for deal in won_deals:
        existing = db.query(FinanceRevenueRecord).filter(FinanceRevenueRecord.deal_id == deal.id).first()
        if not existing:
            db.add(
                FinanceRevenueRecord(
                    revenue_source="Closed won deal",
                    customer_name=deal.country or deal.owner,
                    deal_id=deal.id,
                    revenue_type=deal.pipeline_type or "Service",
                    recognition_date=deal.closed_date or deal.expected_close_date or deal.created_at.date(),
                    amount=deal.revenue_amount or deal.gross_profit or 0,
                    status="recognized",
                )
            )

    crm_paid_invoices = db.query(CRMInvoice).filter(CRMInvoice.status == "paid").all()
    for invoice in crm_paid_invoices:
        existing = db.query(FinanceRevenueRecord).filter(FinanceRevenueRecord.invoice_id == invoice.id).first()
        if not existing:
            db.add(
                FinanceRevenueRecord(
                    revenue_source="Paid CRM invoice",
                    invoice_id=invoice.id,
                    revenue_type="Invoice",
                    recognition_date=invoice.invoice_date,
                    amount=invoice.paid_amount or invoice.amount or 0,
                    status="recognized",
                )
            )

    finance_paid_invoices = db.query(FinanceInvoice).filter(FinanceInvoice.status == "paid").all()
    for invoice in finance_paid_invoices:
        existing = db.query(FinanceRevenueRecord).filter(FinanceRevenueRecord.invoice_id == invoice.id).first()
        if not existing:
            db.add(
                FinanceRevenueRecord(
                    revenue_source="Paid finance invoice",
                    account_id=invoice.account_id,
                    deal_id=invoice.deal_id,
                    invoice_id=invoice.id,
                    revenue_type="Invoice",
                    recognition_date=invoice.invoice_date,
                    amount=invoice.paid_amount or invoice.total_amount or 0,
                    status="recognized",
                )
            )
    db.commit()


def approval_candidates(db: Session):
    candidates = []
    sources = [
        ("Invoice", FinanceInvoice, "invoice_number", "total_amount", FinanceInvoice.approval_status.in_(["draft", "submitted", "pending"])),
        ("Bill", FinanceBill, "bill_number", "amount", FinanceBill.approval_status.in_(["draft", "submitted", "pending"])),
        ("Expense Claim", FinanceExpenseClaim, "claim_number", "amount", FinanceExpenseClaim.approval_status.in_(["submitted", "pending"])),
        ("Budget", FinanceBudget, "budget_name", "approved_amount", FinanceBudget.approval_status.in_(["draft", "submitted", "pending"])),
        ("Purchase Request", FinancePurchaseRequest, "request_number", "estimated_amount", FinancePurchaseRequest.approval_status.in_(["submitted", "pending"])),
        ("Purchase Order", FinancePurchaseOrder, "po_number", "total_amount", FinancePurchaseOrder.approval_status.in_(["draft", "submitted", "pending"])),
        ("Payment", FinancePayment, "payment_number", "amount", FinancePayment.status.in_(["pending", "submitted"])),
    ]
    for record_type, model, label_field, amount_field, criterion in sources:
        for row in db.query(model).filter(criterion).limit(50).all():
            candidates.append(
                {
                    "id": row.id,
                    "type": record_type,
                    "label": getattr(row, label_field),
                    "amount": float(getattr(row, amount_field) or 0),
                    "status": getattr(row, "approval_status", None) or getattr(row, "status", None),
                }
            )
    return candidates


def sum_column(db: Session, model, field: str):
    return float(db.query(func.coalesce(func.sum(getattr(model, field)), 0)).scalar() or 0)


@router.get("/dashboard")
def finance_dashboard(db: Session = Depends(get_db)):
    totals = consolidated_finance_totals(db)
    invoice_total = sum_column(db, FinanceInvoice, "total_amount")
    receipt_total = sum_column(db, FinanceReceipt, "amount")
    bill_total = sum_column(db, FinanceBill, "amount")
    bill_paid = sum_column(db, FinanceBill, "paid_amount")
    expense_total = sum_column(db, FinanceExpenseClaim, "amount")
    synced_expense_total = sum_column(db, FinanceExpense, "amount")
    payroll_total = sum_column(db, HRMPayroll, "net_pay")
    benefits_total = sum_column(db, HRMBenefit, "employer_contribution")
    training_total = sum_column(db, HRMTraining, "cost")
    asset_value = sum_column(db, FinanceFixedAsset, "purchase_cost")
    bank_cash = sum_column(db, FinanceBankAccount, "current_balance")
    revenue_total = totals["recognized_revenue"] or invoice_total
    expenses_total = totals["total_expenses"]

    return {
        "total_revenue": revenue_total,
        "total_expenses": expenses_total,
        "profit_loss": revenue_total - expenses_total,
        "cash_position": bank_cash,
        "pending_payments": max(bill_total - bill_paid, 0),
        "outstanding_invoices": max(invoice_total - receipt_total, 0),
        "asset_value": asset_value,
        "counts": {
            "chart_accounts": db.query(FinanceChartAccount).count(),
            "journal_entries": db.query(FinanceJournalEntry).count(),
            "vendors": db.query(FinanceVendor).count(),
            "bills": db.query(FinanceBill).count(),
            "invoices": db.query(FinanceInvoice).count(),
            "expense_claims": db.query(FinanceExpenseClaim).count(),
            "synced_expenses": db.query(FinanceExpense).count(),
            "budgets": db.query(FinanceBudget).count(),
            "purchase_orders": db.query(FinancePurchaseOrder).count(),
            "bank_accounts": db.query(FinanceBankAccount).count(),
            "tax_records": db.query(FinanceTaxRecord).count(),
            "assets": db.query(FinanceFixedAsset).count(),
            "approvals": db.query(FinanceApproval).filter(FinanceApproval.status == "pending").count(),
        },
        "department_budgets": [
            {"department": row.department or "Unassigned", "approved": float(row.approved or 0), "actual": float(row.actual or 0)}
            for row in (
                db.query(
                    FinanceBudget.department,
                    func.coalesce(func.sum(FinanceBudget.approved_amount), 0).label("approved"),
                    func.coalesce(func.sum(FinanceBudget.actual_amount), 0).label("actual"),
                )
                .group_by(FinanceBudget.department)
                .all()
            )
        ],
        "monthly_trends": [
            {"name": "Revenue", "value": revenue_total},
            {"name": "Expenses", "value": expenses_total},
            {"name": "Profit/Loss", "value": revenue_total - expenses_total},
            {"name": "Cash", "value": bank_cash},
        ],
        "source_reconciliation": {
            "recognized_revenue": totals["recognized_revenue"],
            "finance_invoice_total": totals["invoice_total"],
            "finance_paid_amount": totals["paid_amount"],
            "synced_operational_expenses": synced_expense_total,
            "expense_claims": expense_total,
            "vendor_bills": bill_total,
            "legacy_hrm_payroll_reference": payroll_total,
            "legacy_hrm_benefits_reference": benefits_total,
            "legacy_hrm_training_reference": training_total,
            "approved_budget": totals["approved_budget"],
            "project_profitability": totals["project_profitability"],
        },
    }


@router.get("/approval-candidates")
def get_approval_candidates(db: Session = Depends(get_db)):
    return approval_candidates(db)


@router.post("/sync/revenue")
def sync_revenue(db: Session = Depends(get_db)):
    result = sync_finance_from_operations(db)
    result["message"] = "Finance synchronized from CRM revenue/costs, HRMS payroll/benefits/training/assets, Projects budgets/expenses, and invoices."
    return result


@router.post("/sync/all")
def sync_all_finance(db: Session = Depends(get_db)):
    return sync_finance_from_operations(db)


@router.post("/documents/upload")
def upload_finance_document(payload: dict[str, Any]):
    file_name = str(payload.get("file_name") or "document")
    content_base64 = str(payload.get("content_base64") or "")
    if not content_base64:
        raise HTTPException(status_code=422, detail="Document content is required")

    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", file_name).strip("._") or "document"
    stored_name = f"{uuid_module.uuid4()}_{safe_name}"
    upload_dir = os.path.join("uploads", "finance")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)

    try:
        with open(file_path, "wb") as target:
            target.write(base64.b64decode(content_base64))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Could not store uploaded document") from exc

    return {
        "file_name": file_name,
        "file_url": f"/uploads/finance/{stored_name}",
        "mime_type": payload.get("mime_type"),
    }


@router.get("/documents/file/{record_id}")
def get_finance_document_file(record_id: UUID, db: Session = Depends(get_db)):
    record = db.query(FinanceDocument).filter(FinanceDocument.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance document not found")

    candidate_paths = []
    if record.file_url and record.file_url.startswith("/uploads/"):
        candidate_paths.append(record.file_url.lstrip("/").replace("/", os.sep))
    if record.file_name:
        upload_dir = os.path.join("uploads", "finance")
        if os.path.isdir(upload_dir):
            for name in os.listdir(upload_dir):
                if name == record.file_name or name.endswith(f"_{record.file_name}"):
                    candidate_paths.append(os.path.join(upload_dir, name))

    for path in candidate_paths:
        if path and os.path.exists(path):
            return FileResponse(path, filename=record.file_name or os.path.basename(path))

    raise HTTPException(
        status_code=404,
        detail="The uploaded file is not available on the server. Re-upload the document or update the cloud link.",
    )


@router.get("/{resource}")
def list_records(resource: str, db: Session = Depends(get_db)):
    model = model_for(resource)
    if resource == "revenue-records":
        sync_system_revenue(db)
    order_column = getattr(model, "created_at", None)
    query = db.query(model)
    if order_column is not None:
        query = query.order_by(order_column.desc())
    return [row_to_dict(item) for item in query.all()]


@router.post("/{resource}", status_code=status.HTTP_201_CREATED)
def create_record(resource: str, payload: dict[str, Any], db: Session = Depends(get_db)):
    model = model_for(resource)
    payload = clean_payload(payload)
    if resource == "invoices":
        payload = automate_invoice_payload(payload)
    if resource == "expense-claims":
        payload = automate_expense_claim_payload(payload)
    payload = coerce_uuid_fields(model, payload)
    record = model(**payload)
    assign_business_id(db, model, record)
    db.add(record)
    db.commit()
    db.refresh(record)
    return row_to_dict(record)


@router.get("/{resource}/{record_id}")
def get_record(resource: str, record_id: UUID, db: Session = Depends(get_db)):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance record not found")
    return row_to_dict(record)


@router.put("/{resource}/{record_id}")
def update_record(resource: str, record_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db)):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance record not found")
    payload = clean_payload(payload)
    if resource == "invoices":
        current = row_to_dict(record)
        current.update(payload)
        payload = automate_invoice_payload(current)
    if resource == "expense-claims":
        current = row_to_dict(record)
        current.update(payload)
        payload = automate_expense_claim_payload(current)
    payload = coerce_uuid_fields(model, payload)
    for key, value in payload.items():
        if hasattr(record, key):
            setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return row_to_dict(record)


@router.post("/{resource}/{record_id}/{action}")
def workflow_record(resource: str, record_id: UUID, action: str, payload: dict[str, Any] | None = None, db: Session = Depends(get_db)):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance record not found")
    payload = payload or {}

    if resource == "chart-accounts":
        if action == "deactivate":
            record.is_active = False
        elif action == "activate":
            record.is_active = True
        else:
            raise HTTPException(status_code=422, detail="Unsupported chart account action")
    elif resource == "journal-entries":
        if action == "approve":
            record.status = "approved"
            record.approved_by = payload.get("approved_by") or "Finance"
        elif action == "reject":
            record.status = "rejected"
            record.rejection_reason = payload.get("reason") or payload.get("comments")
        elif action == "post":
            debit = Decimal(str(record.total_debit or 0))
            credit = Decimal(str(record.total_credit or 0))
            if debit != credit:
                raise HTTPException(status_code=422, detail="Journal debit and credit must balance before posting")
            record.status = "posted"
            record.posted_by = payload.get("posted_by") or "Finance"
            record.posted_at = datetime.now(timezone.utc)
        elif action == "reverse":
            record.status = "reversed"
            record.reversal_reason = payload.get("reason") or payload.get("comments") or "Reversed"
        else:
            raise HTTPException(status_code=422, detail="Unsupported journal action")
    elif resource in {"bills", "invoices", "budgets", "purchase-requests", "purchase-orders"}:
        if action in {"approve", "submit", "reject"}:
            if hasattr(record, "approval_status"):
                record.approval_status = {"approve": "approved", "submit": "submitted", "reject": "rejected"}[action]
        elif action == "send" and resource == "invoices":
            record.status = "sent"
            record.sent_at = datetime.now(timezone.utc)
        elif action in {"mark-paid", "pay"}:
            if hasattr(record, "paid_amount") and hasattr(record, "total_amount"):
                record.paid_amount = record.total_amount
            if hasattr(record, "paid_amount") and hasattr(record, "amount"):
                record.paid_amount = record.amount
            if hasattr(record, "status"):
                record.status = "paid"
        elif action == "receive" and resource == "purchase-orders":
            record.goods_received_status = "received"
        elif action == "accept-service" and resource == "purchase-orders":
            record.service_acceptance_status = "accepted"
        else:
            raise HTTPException(status_code=422, detail="Unsupported finance action")
    elif resource == "expense-claims":
        if action == "approve":
            record.approval_status = "approved"
        elif action == "reject":
            record.approval_status = "rejected"
            record.notes = f"{record.notes or ''}\nRejected: {payload.get('reason') or payload.get('comments') or ''}".strip()
        elif action in {"reimburse", "mark-paid"}:
            if record.approval_status != "approved":
                raise HTTPException(status_code=422, detail="Only approved claims can be reimbursed")
            record.reimbursement_status = "paid"
        else:
            raise HTTPException(status_code=422, detail="Unsupported expense action")
    elif resource == "documents":
        if action == "archive":
            record.status = "archived"
            record.archived_at = datetime.now(timezone.utc)
            record.archive_reason = payload.get("reason") or payload.get("comments") or "Archived"
        elif action == "new-version":
            record.version_number = (record.version_number or 1) + 1
        else:
            raise HTTPException(status_code=422, detail="Unsupported document action")
    elif resource == "payments":
        if action == "approve":
            record.status = "approved"
            record.approved_by = payload.get("approved_by") or "Finance"
        elif action in {"mark-paid", "pay"}:
            record.status = "paid"
        elif action == "reverse":
            record.status = "reversed"
        else:
            raise HTTPException(status_code=422, detail="Unsupported payment action")
    else:
        if not hasattr(record, "status"):
            raise HTTPException(status_code=422, detail="Workflow action is not supported for this resource")
        record.status = action.replace("-", "_")

    db.add(FinanceAuditTrail(entity_type=resource, entity_id=record_id, action=action, actor="Finance", change_summary=f"{action} {resource}"))
    db.commit()
    db.refresh(record)
    return row_to_dict(record)


@router.delete("/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(resource: str, record_id: UUID, db: Session = Depends(get_db)):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance record not found")
    db.delete(record)
    db.commit()
    return None
