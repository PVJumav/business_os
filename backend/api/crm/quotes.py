from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.api.crm.v6_workflows import SALES_DEPARTMENTS, _active_employee, _employee_name
from backend.models.crm import CRMDeal, CRMOpportunity, CRMQuotation
from backend.schemas.crm.quotations import QuotationCreate, QuotationResponse, QuotationUpdate


router = APIRouter(prefix="/crm/quotes", tags=["CRM Quotes"])


def _prepare_quote(db: Session, payload):
    data = payload.model_dump()
    deal = None
    if data.get("deal_id"):
        deal = db.query(CRMDeal).filter(CRMDeal.id == data["deal_id"]).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        if not data.get("quote_number"):
            data["quote_number"] = f"Q-{deal.business_id or str(deal.id)[:8]}"
        if not data.get("title"):
            data["title"] = f"Quote for {deal.deal_name}"
    elif not data.get("quote_number"):
        raise HTTPException(status_code=422, detail="Quote number is required when no deal is selected")
    return data, deal


def _apply_quote_workflow(db: Session, quote: CRMQuotation):
    submitted_states = {"submitted", "sent", "under_review"}
    if quote.deal_id and (quote.status or "").lower() in submitted_states:
        deal = db.query(CRMDeal).filter(CRMDeal.id == quote.deal_id).first()
        if deal:
            deal.deal_status = "under_review"
            deal.stage = "Stage 1.c RFP/Tender"


def _apply_employee_policy(db: Session, quote: CRMQuotation):
    if quote.owner_employee_id:
        owner = _active_employee(db, quote.owner_employee_id, allowed_departments=SALES_DEPARTMENTS)
        quote.created_by = quote.created_by or _employee_name(owner)
    if quote.approved_by_employee_id:
        approver = _active_employee(db, quote.approved_by_employee_id)
        quote.approved_by = _employee_name(approver)


@router.post("", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quote(quote: QuotationCreate, db: Session = Depends(get_db)):
    data, deal = _prepare_quote(db, quote)
    if quote.opportunity_id:
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == quote.opportunity_id
        ).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    new_quote = CRMQuotation(**data)
    _apply_employee_policy(db, new_quote)
    db.add(new_quote)
    db.flush()
    _apply_quote_workflow(db, new_quote)
    db.commit()
    db.refresh(new_quote)
    return new_quote


@router.get("", response_model=List[QuotationResponse])
def get_quotes(db: Session = Depends(get_db)):
    return db.query(CRMQuotation).order_by(CRMQuotation.created_at.desc()).all()


@router.get("/{quote_id}", response_model=QuotationResponse)
def get_quote(quote_id: UUID, db: Session = Depends(get_db)):
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.put("/{quote_id}", response_model=QuotationResponse)
def update_quote(
    quote_id: UUID,
    quote_update: QuotationUpdate,
    db: Session = Depends(get_db),
):
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    update_data = quote_update.model_dump(exclude_unset=True)
    if "deal_id" in update_data and update_data["deal_id"]:
        deal = db.query(CRMDeal).filter(CRMDeal.id == update_data["deal_id"]).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        if not update_data.get("quote_number") and not quote.quote_number:
            update_data["quote_number"] = f"Q-{deal.business_id or str(deal.id)[:8]}"
    if "opportunity_id" in update_data and update_data["opportunity_id"]:
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == update_data["opportunity_id"]
        ).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    for field, value in update_data.items():
        setattr(quote, field, value)

    _apply_employee_policy(db, quote)
    _apply_quote_workflow(db, quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(quote_id: UUID, db: Session = Depends(get_db)):
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    db.delete(quote)
    db.commit()
    return None
