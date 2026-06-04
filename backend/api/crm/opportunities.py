from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.api.crud import assign_business_id
from backend.api.crm.v6_workflows import SALES_DEPARTMENTS, TECHNICAL_DEPARTMENTS, _active_employee, _employee_name
from backend.models.crm import CRMAccount, CRMLead, CRMOpportunity
from backend.schemas.crm.opportunities import OpportunityCreate, OpportunityUpdate, OpportunityResponse


router = APIRouter(prefix="/crm/opportunities", tags=["CRM Opportunities"])


def _is_qualified(opportunity: CRMOpportunity) -> bool:
    values = {
        (opportunity.status or "").strip().lower(),
        (opportunity.stage or "").strip().lower(),
    }
    return bool(values & {"qualified", "whitelisted", "lead", "converted_to_lead"})


def _lead_from_opportunity(db: Session, opportunity: CRMOpportunity):
    if not _is_qualified(opportunity):
        return

    existing = db.query(CRMLead).filter(CRMLead.notes.ilike(f"%Opportunity ID: {opportunity.id}%")).first()
    if existing:
        existing.company_name = existing.company_name or opportunity.title
        existing.assigned_to = opportunity.owner or existing.assigned_to
        existing.estimated_value = opportunity.opportunity_value or existing.estimated_value
        existing.expected_close_date = opportunity.expected_close_date or existing.expected_close_date
        existing.expected_renewal_date = opportunity.renewal_date or existing.expected_renewal_date
        existing.pipeline_type = opportunity.pipeline_type or existing.pipeline_type
        existing.arena = opportunity.arena or existing.arena
        existing.service_scope = opportunity.service_scope or existing.service_scope
        existing.account_country = opportunity.country or existing.account_country
        existing.account_vertical = opportunity.vertical or existing.account_vertical
        existing.status = "Qualified"
        from backend.api.crm.leads import _convert_lead

        _convert_lead(db, existing)
        return

    account = db.query(CRMAccount).filter(CRMAccount.id == opportunity.account_id).first() if opportunity.account_id else None
    lead = CRMLead(
        company_name=account.company_name if account else opportunity.title,
        account_industry=account.industry if account else None,
        account_website=account.website if account else None,
        account_address=account.address if account else None,
        account_country=opportunity.country or (account.country if account else None),
        account_region=account.region if account else None,
        account_vertical=opportunity.vertical or (account.vertical if account else None),
        account_type=account.account_type if account else opportunity.pipeline_type,
        contact_name=account.company_name if account else opportunity.title,
        email=account.email if account else None,
        phone=account.phone if account else None,
        lead_source="Opportunity whitelist",
        status="Qualified",
        assigned_to=opportunity.owner,
        estimated_value=opportunity.opportunity_value or 0,
        expected_close_date=opportunity.expected_close_date,
        expected_renewal_date=opportunity.renewal_date,
        pipeline_type=opportunity.pipeline_type,
        arena=opportunity.arena,
        service_scope=opportunity.service_scope,
        notes=f"Automatically created from qualified/whitelisted opportunity. Opportunity ID: {opportunity.id}",
    )
    assign_business_id(db, CRMLead, lead)
    db.add(lead)
    db.flush()
    from backend.api.crm.leads import _convert_lead

    _convert_lead(db, lead)


def _apply_employee_policy(db: Session, opportunity: CRMOpportunity):
    if opportunity.owner_employee_id:
        owner = _active_employee(db, opportunity.owner_employee_id, allowed_departments=SALES_DEPARTMENTS)
        opportunity.owner = _employee_name(owner)
        opportunity.manager_employee_id = getattr(owner, "supervisor_id", None)
    if opportunity.presales_employee_id:
        _active_employee(db, opportunity.presales_employee_id, allowed_departments=TECHNICAL_DEPARTMENTS)
    if opportunity.project_manager_employee_id:
        _active_employee(db, opportunity.project_manager_employee_id, require_crm_role=False)
    if opportunity.customer_success_owner_employee_id:
        _active_employee(db, opportunity.customer_success_owner_employee_id)
    if opportunity.technical_owner_employee_id:
        _active_employee(db, opportunity.technical_owner_employee_id, allowed_departments=TECHNICAL_DEPARTMENTS)


@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(opportunity: OpportunityCreate, db: Session = Depends(get_db)):
    if opportunity.account_id:
        account = db.query(CRMAccount).filter(CRMAccount.id == opportunity.account_id).first()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

    new_opportunity = CRMOpportunity(**opportunity.model_dump())
    _apply_employee_policy(db, new_opportunity)
    assign_business_id(db, CRMOpportunity, new_opportunity)
    db.add(new_opportunity)
    db.flush()
    _lead_from_opportunity(db, new_opportunity)
    db.commit()
    db.refresh(new_opportunity)
    return new_opportunity


@router.get("", response_model=List[OpportunityResponse])
def get_opportunities(db: Session = Depends(get_db)):
    return db.query(CRMOpportunity).order_by(CRMOpportunity.created_at.desc()).all()


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(opportunity_id: UUID, db: Session = Depends(get_db)):
    opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == opportunity_id).first()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return opportunity


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
def update_opportunity(
    opportunity_id: UUID,
    opportunity_update: OpportunityUpdate,
    db: Session = Depends(get_db)
):
    opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == opportunity_id).first()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update_data = opportunity_update.model_dump(exclude_unset=True)

    if "account_id" in update_data and update_data["account_id"]:
        account = db.query(CRMAccount).filter(CRMAccount.id == update_data["account_id"]).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

    for field, value in update_data.items():
        setattr(opportunity, field, value)

    _apply_employee_policy(db, opportunity)
    _lead_from_opportunity(db, opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.delete("/{opportunity_id}")
def delete_opportunity(opportunity_id: UUID, db: Session = Depends(get_db)):
    opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == opportunity_id).first()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    db.delete(opportunity)
    db.commit()

    return {"status": "success", "message": "Opportunity deleted successfully"}
