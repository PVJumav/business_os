from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.api.crm.v6_workflows import _active_employee
from backend.models.crm import CRMAccount, CRMContact
from backend.schemas.crm.contacts import ContactCreate, ContactUpdate, ContactResponse


router = APIRouter(prefix="/crm/contacts", tags=["CRM Contacts"])


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    if not db.query(CRMAccount).filter(CRMAccount.id == contact.account_id).first():
        raise HTTPException(status_code=404, detail="Account not found. Contacts must be linked to an account.")
    new_contact = CRMContact(**contact.model_dump())
    if new_contact.owner_employee_id:
        _active_employee(db, new_contact.owner_employee_id)
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


@router.get("", response_model=List[ContactResponse])
def get_contacts(db: Session = Depends(get_db)):
    return db.query(CRMContact).order_by(CRMContact.created_at.desc()).all()


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: UUID, db: Session = Depends(get_db)):
    contact = db.query(CRMContact).filter(CRMContact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: UUID, contact_update: ContactUpdate, db: Session = Depends(get_db)):
    contact = db.query(CRMContact).filter(CRMContact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = contact_update.model_dump(exclude_unset=True)
    if "account_id" in update_data and update_data["account_id"]:
        if not db.query(CRMAccount).filter(CRMAccount.id == update_data["account_id"]).first():
            raise HTTPException(status_code=404, detail="Account not found. Contacts must be linked to an account.")
    if update_data.get("owner_employee_id"):
        _active_employee(db, update_data["owner_employee_id"])

    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
def delete_contact(contact_id: UUID, db: Session = Depends(get_db)):
    contact = db.query(CRMContact).filter(CRMContact.id == contact_id).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()

    return {"status": "success", "message": "Contact deleted successfully"}
