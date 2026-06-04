from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.finance import FinanceIntegrationEvent
from backend.schemas.auth import UserResponse
from backend.services.phase1_integrations import (
    account_history,
    activate_contract,
    central_policy_check,
    contract_from_quote_lpo,
    employee_created,
    employee_terminated,
    finance_invoice_paid,
    lpo_uploaded,
    operational_dashboard,
    opportunity_closed_won,
    payroll_approved,
    project_expense_approved,
    project_signed_off,
    purchase_order_from_request,
    quote_accepted,
    quote_approved,
    renewal_opportunities,
    sla_breached,
    vendor_invoice_paid,
    vendor_invoice_received,
)


router = APIRouter(prefix="/phase1/integrations", tags=["Phase 1 Core Operations"])


@router.get("/dashboard")
def phase1_dashboard(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return operational_dashboard(db)


@router.get("/events")
def integration_events(
    module: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    query = db.query(FinanceIntegrationEvent)
    if module:
        query = query.filter((FinanceIntegrationEvent.source_module == module) | (FinanceIntegrationEvent.target_module == module))
    if event_type:
        query = query.filter(FinanceIntegrationEvent.event_type == event_type)
    rows = query.order_by(FinanceIntegrationEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(row.id),
            "source_module": row.source_module,
            "target_module": row.target_module,
            "event_type": row.event_type,
            "record_type": row.related_record_type,
            "record_id": str(row.related_record_id) if row.related_record_id else None,
            "status": row.status,
            "summary": row.payload_summary,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "processed_at": row.processed_at.isoformat() if row.processed_at else None,
        }
        for row in rows
    ]


@router.get("/policy/check")
def policy_check(
    module: str,
    action: str,
    record_owner: str | None = None,
    current_user: UserResponse = Depends(get_current_user),
):
    return central_policy_check(current_user, module, action, record_owner)


@router.get("/crm/accounts/{account_id}/history")
def crm_account_history(account_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return account_history(db, account_id)


@router.post("/hrms/employees/{employee_id}/created")
def hr_employee_created(employee_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return employee_created(db, employee_id, current_user)


@router.post("/hrms/employees/{employee_id}/terminated")
def hr_employee_terminated(employee_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return employee_terminated(db, employee_id, current_user)


@router.post("/crm/quotes/{quotation_id}/approve")
def crm_quote_approved(quotation_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return quote_approved(db, quotation_id, current_user)


@router.post("/crm/quotes/{quotation_id}/accept")
def crm_quote_accepted(quotation_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return quote_accepted(db, quotation_id, current_user)


@router.post("/crm/lpos/upload")
def crm_lpo_uploaded(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return lpo_uploaded(db, payload, current_user)


@router.post("/crm/quotes/{quotation_id}/contract")
def crm_contract_from_quote(
    quotation_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return contract_from_quote_lpo(db, quotation_id, UUID(payload["lpo_id"]) if payload and payload.get("lpo_id") else None, current_user)


@router.post("/crm/contracts/{contract_id}/activate")
def crm_contract_activate(contract_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return activate_contract(db, contract_id, current_user)


@router.post("/crm/opportunities/{opportunity_id}/closed-won")
def crm_opportunity_closed_won(
    opportunity_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return opportunity_closed_won(db, opportunity_id, current_user, payload or {})


@router.post("/finance/invoices/{invoice_id}/paid")
def finance_invoice_mark_paid(
    invoice_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return finance_invoice_paid(db, invoice_id, payload or {}, current_user)


@router.post("/finance/purchase-requests/{request_id}/create-po")
def finance_create_po(
    request_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return purchase_order_from_request(db, request_id, payload or {}, current_user)


@router.post("/finance/purchase-orders/{po_id}/vendor-invoice")
def finance_receive_vendor_invoice(
    po_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return vendor_invoice_received(db, po_id, payload or {}, current_user)


@router.post("/finance/vendor-invoices/{bill_id}/paid")
def finance_vendor_invoice_paid(
    bill_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return vendor_invoice_paid(db, bill_id, payload or {}, current_user)


@router.post("/projects/expenses/{expense_id}/approved")
def project_expense_posted(expense_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return project_expense_approved(db, expense_id, current_user)


@router.post("/projects/{project_id}/signed-off")
def project_signoff(
    project_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return project_signed_off(db, project_id, payload or {}, current_user)


@router.post("/slas/tickets/{ticket_id}/breached")
def project_sla_breached(ticket_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return sla_breached(db, ticket_id, current_user)


@router.post("/renewals/create-opportunities")
def create_renewal_opportunities(
    days: int = Query(default=60, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return renewal_opportunities(db, days, current_user)


@router.post("/hrms/payroll-runs/{payroll_run_id}/approved")
def hr_payroll_approved(payroll_run_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return payroll_approved(db, payroll_run_id, current_user)
