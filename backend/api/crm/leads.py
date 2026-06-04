from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.api.crud import assign_business_id
from backend.api.crm.v6_workflows import (
    SALES_DEPARTMENTS,
    _active_employee,
    _duplicate_lead_reason,
    _employee_name,
)
from backend.models.crm import CRMAccount, CRMContact, CRMDeal, CRMLead
from backend.schemas.crm.leads import LeadCreate, LeadUpdate, LeadResponse


router = APIRouter(prefix="/crm/leads", tags=["CRM Leads"])


def _split_name(full_name: str):
    parts = (full_name or "").strip().split()
    if not parts:
        return "Unknown", "Contact"
    if len(parts) == 1:
        return parts[0], "Contact"
    return parts[0], " ".join(parts[1:])


def _should_convert(lead: CRMLead) -> bool:
    return bool(lead.status and lead.status.strip().lower() in {"qualified", "converted"})


def _sync_lead_account_and_contact(db: Session, lead: CRMLead):
    account = None
    if lead.company_name:
        account = db.query(CRMAccount).filter(CRMAccount.company_name.ilike(lead.company_name)).first()
    if not account:
        account = CRMAccount(
            company_name=lead.company_name or lead.contact_name,
            industry=lead.account_industry,
            website=lead.account_website,
            address=lead.account_address,
            account_manager=lead.assigned_to,
            country=lead.account_country,
            region=lead.account_region,
            vertical=lead.account_vertical,
            account_type=lead.account_type,
            email=lead.email,
            phone=lead.phone,
            account_status="active",
        )
        assign_business_id(db, CRMAccount, account)
        db.add(account)
        db.flush()
    else:
        account.industry = lead.account_industry or account.industry
        account.website = lead.account_website or account.website
        account.address = lead.account_address or account.address
        account.account_manager = lead.assigned_to or account.account_manager
        account.country = lead.account_country or account.country
        account.region = lead.account_region or account.region
        account.vertical = lead.account_vertical or account.vertical
        account.account_type = lead.account_type or account.account_type
        account.email = lead.email or account.email
        account.phone = lead.phone or account.phone

    first_name, last_name = _split_name(lead.contact_name)
    existing_contact = db.query(CRMContact).filter(CRMContact.account_id == account.id, CRMContact.email == lead.email).first() if lead.email else None
    if not existing_contact:
        db.add(
            CRMContact(
                account_id=account.id,
                first_name=first_name,
                last_name=last_name,
                job_title=lead.contact_job_title,
                department=lead.contact_department,
                email=lead.email,
                phone=lead.phone,
                notes=f"Created from lead {lead.business_id or lead.id}",
            )
        )
    else:
        existing_contact.first_name = first_name or existing_contact.first_name
        existing_contact.last_name = last_name or existing_contact.last_name
        existing_contact.job_title = lead.contact_job_title or existing_contact.job_title
        existing_contact.department = lead.contact_department or existing_contact.department
        existing_contact.phone = lead.phone or existing_contact.phone

    lead.converted_account_id = account.id
    return account


def _convert_lead(db: Session, lead: CRMLead):
    account = _sync_lead_account_and_contact(db, lead)
    if not _should_convert(lead):
        return

    deal_name = f"{lead.company_name or lead.contact_name} - {lead.service_scope or lead.arena or 'Opportunity'}"
    existing_deal = db.query(CRMDeal).filter(CRMDeal.account_id == account.id, CRMDeal.notes.ilike(f"%lead {lead.business_id or lead.id}%")).first()
    if not existing_deal:
        existing_deal = db.query(CRMDeal).filter(CRMDeal.account_id == account.id, CRMDeal.deal_name == deal_name).first()
    if not existing_deal:
        deal = CRMDeal(
            account_id=account.id,
            deal_name=deal_name,
            owner=lead.assigned_to,
            stage="Stage 1.a Discovery",
            deal_status="open",
            pipeline_type=lead.pipeline_type,
            arena=lead.arena,
            service_scope=lead.service_scope,
            country=lead.account_country,
            vertical=lead.account_vertical,
            revenue_amount=lead.estimated_value or 0,
            expected_close_date=lead.expected_close_date,
            renewal_date=lead.expected_renewal_date,
            notes=f"Automatically converted from lead {lead.business_id or lead.id}",
        )
        assign_business_id(db, CRMDeal, deal)
        db.add(deal)
    else:
        existing_deal.owner = lead.assigned_to or existing_deal.owner
        existing_deal.pipeline_type = lead.pipeline_type or existing_deal.pipeline_type
        existing_deal.arena = lead.arena or existing_deal.arena
        existing_deal.service_scope = lead.service_scope or existing_deal.service_scope
        existing_deal.country = lead.account_country or existing_deal.country
        existing_deal.vertical = lead.account_vertical or existing_deal.vertical
        existing_deal.revenue_amount = lead.estimated_value or existing_deal.revenue_amount
        existing_deal.expected_close_date = lead.expected_close_date or existing_deal.expected_close_date
        existing_deal.renewal_date = lead.expected_renewal_date or existing_deal.renewal_date

    lead.converted = True
    lead.converted_account_id = account.id
    lead.status = "Converted"


def _apply_owner_and_duplicate_policy(db: Session, lead: CRMLead):
    owner_id = lead.owner_employee_id or lead.assigned_employee_id
    if owner_id:
        owner = _active_employee(db, owner_id, allowed_departments=SALES_DEPARTMENTS)
        lead.owner_employee_id = owner.id
        lead.assigned_employee_id = lead.assigned_employee_id or owner.id
        lead.manager_employee_id = getattr(owner, "supervisor_id", None)
        lead.assigned_to = _employee_name(owner)
    duplicate_reason = _duplicate_lead_reason(
        db,
        {
            "email": lead.email,
            "phone": lead.phone,
            "company_name": lead.company_name,
            "account_website": lead.account_website,
        },
        exclude_id=lead.id,
    )
    lead.duplicate_flag = bool(duplicate_reason)
    lead.duplicate_reason = duplicate_reason


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    new_lead = CRMLead(**lead.model_dump())
    _apply_owner_and_duplicate_policy(db, new_lead)
    assign_business_id(db, CRMLead, new_lead)
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead


@router.get("", response_model=List[LeadResponse])
def get_leads(db: Session = Depends(get_db)):
    return db.query(CRMLead).order_by(CRMLead.created_at.desc()).all()


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: UUID, db: Session = Depends(get_db)):
    lead = db.query(CRMLead).filter(CRMLead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: UUID, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(CRMLead).filter(CRMLead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in lead_update.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    _apply_owner_and_duplicate_policy(db, lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
def delete_lead(lead_id: UUID, db: Session = Depends(get_db)):
    lead = db.query(CRMLead).filter(CRMLead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()

    return {"status": "success", "message": "Lead deleted successfully"}
