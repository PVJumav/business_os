from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.api.crm.v6_workflows import SALES_DEPARTMENTS, _active_employee, _employee_name
from backend.models.crm import CRMAccount
from backend.schemas.crm.accounts import AccountCreate, AccountUpdate, AccountOut

router = APIRouter(prefix="/crm/accounts", tags=["CRM Accounts"])


def _apply_owner_policy(db: Session, account: CRMAccount):
    if account.owner_employee_id:
        owner = _active_employee(db, account.owner_employee_id, allowed_departments=SALES_DEPARTMENTS)
        account.relationship_owner = account.relationship_owner or _employee_name(owner)
        account.account_manager = _employee_name(owner)
        account.manager_employee_id = getattr(owner, "supervisor_id", None)


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    account = CRMAccount(**payload.model_dump())
    _apply_owner_policy(db, account)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=List[AccountOut])
def get_accounts(db: Session = Depends(get_db)):
    return db.query(CRMAccount).order_by(CRMAccount.created_at.desc()).all()


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: UUID, db: Session = Depends(get_db)):
    account = db.query(CRMAccount).filter(CRMAccount.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account


@router.put("/{account_id}", response_model=AccountOut)
def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
):
    account = db.query(CRMAccount).filter(CRMAccount.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(account, key, value)

    _apply_owner_policy(db, account)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: UUID, db: Session = Depends(get_db)):
    account = db.query(CRMAccount).filter(CRMAccount.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    db.delete(account)
    db.commit()
    return None
