from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.api.crm.v6_workflows import SALES_DEPARTMENTS, _active_employee, _employee_name
from backend.models.crm import CRMDeal, CRMQuotation, CRMOpportunity
from backend.schemas.crm.quotations import QuotationCreate, QuotationUpdate, QuotationResponse


router = APIRouter(prefix="/crm/quotations", tags=["CRM Quotations"])


def _prepare_quotation(db: Session, payload):
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
    return data


def _apply_quotation_workflow(db: Session, quotation: CRMQuotation):
    if quotation.deal_id and (quotation.status or "").lower() in {"submitted", "sent", "under_review"}:
        deal = db.query(CRMDeal).filter(CRMDeal.id == quotation.deal_id).first()
        if deal:
            deal.deal_status = "under_review"
            deal.stage = "Stage 1.c RFP/Tender"


def _apply_employee_policy(db: Session, quotation: CRMQuotation):
    if quotation.owner_employee_id:
        owner = _active_employee(db, quotation.owner_employee_id, allowed_departments=SALES_DEPARTMENTS)
        quotation.created_by = quotation.created_by or _employee_name(owner)
    if quotation.approved_by_employee_id:
        approver = _active_employee(db, quotation.approved_by_employee_id)
        quotation.approved_by = _employee_name(approver)


@router.post("", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(quotation: QuotationCreate, db: Session = Depends(get_db)):
    data = _prepare_quotation(db, quotation)
    if quotation.opportunity_id:
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == quotation.opportunity_id
        ).first()

        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    new_quotation = CRMQuotation(**data)
    _apply_employee_policy(db, new_quotation)
    db.add(new_quotation)
    db.flush()
    _apply_quotation_workflow(db, new_quotation)
    db.commit()
    db.refresh(new_quotation)
    return new_quotation


@router.get("", response_model=List[QuotationResponse])
def get_quotations(db: Session = Depends(get_db)):
    return db.query(CRMQuotation).order_by(CRMQuotation.created_at.desc()).all()


@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_quotation(quotation_id: UUID, db: Session = Depends(get_db)):
    quotation = db.query(CRMQuotation).filter(CRMQuotation.id == quotation_id).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    return quotation


@router.put("/{quotation_id}", response_model=QuotationResponse)
def update_quotation(
    quotation_id: UUID,
    quotation_update: QuotationUpdate,
    db: Session = Depends(get_db)
):
    quotation = db.query(CRMQuotation).filter(CRMQuotation.id == quotation_id).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    update_data = quotation_update.model_dump(exclude_unset=True)
    if "deal_id" in update_data and update_data["deal_id"]:
        deal = db.query(CRMDeal).filter(CRMDeal.id == update_data["deal_id"]).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        if not update_data.get("quote_number") and not quotation.quote_number:
            update_data["quote_number"] = f"Q-{deal.business_id or str(deal.id)[:8]}"

    if "opportunity_id" in update_data and update_data["opportunity_id"]:
        opportunity = db.query(CRMOpportunity).filter(
            CRMOpportunity.id == update_data["opportunity_id"]
        ).first()

        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    for field, value in update_data.items():
        setattr(quotation, field, value)

    _apply_employee_policy(db, quotation)
    _apply_quotation_workflow(db, quotation)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.delete("/{quotation_id}")
def delete_quotation(quotation_id: UUID, db: Session = Depends(get_db)):
    quotation = db.query(CRMQuotation).filter(CRMQuotation.id == quotation_id).first()

    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    db.delete(quotation)
    db.commit()

    return {"status": "success", "message": "Quotation deleted successfully"}
