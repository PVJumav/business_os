from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.crud import delete_record, get_or_404, update_record
from backend.core.database import get_db
from backend.models.automation import AuditLog
from backend.models.hrm import HRMAuditLog, HRMEmployee, HRMPayroll
from backend.schemas.auth import UserResponse
from backend.schemas.hrm.payroll import PayrollCreate, PayrollResponse, PayrollUpdate


router = APIRouter(prefix="/hrm/payroll", tags=["HRM Payroll"])


def _require_payroll_employee_ready(db: Session, employee_id: UUID) -> HRMEmployee:
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found for payroll record")
    if employee.employment_status != "active":
        raise HTTPException(status_code=422, detail="Payroll can only be processed for active employees")
    if employee.payroll_profile_status not in {"active", "created"}:
        raise HTTPException(status_code=422, detail="Employee payroll profile is not ready")
    if employee.employment_type_status in {"expired", "contract-expired", "inactive"}:
        raise HTTPException(status_code=422, detail="Expired or inactive engagement cannot receive payroll")
    return employee


def _audit_payroll_action(db: Session, payroll: HRMPayroll, employee: HRMEmployee, user: UserResponse, action: str):
    payload = {
        "payroll_id": str(payroll.id),
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "payroll_month": payroll.payroll_month,
        "gross_pay": str(payroll.gross_pay),
        "net_pay": str(payroll.net_pay),
        "payment_status": payroll.payment_status,
    }
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action=action,
            entity_type="HRMPayroll",
            entity_id=str(payroll.id),
            sensitivity="restricted",
            summary=f"Payroll record {payroll.payroll_month} touched for {employee.employee_code}.",
            after_json=payload,
        )
    )
    db.add(
        AuditLog(
            user_email=user.email,
            module="HRM",
            action=action,
            entity_type="HRMPayroll",
            entity_id=payroll.id,
            new_value=payload,
            result="success",
            created_by=user.full_name,
        )
    )


@router.post("", response_model=PayrollResponse, status_code=status.HTTP_201_CREATED)
def create_payroll(
    payroll: PayrollCreate,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    employee = _require_payroll_employee_ready(db, payroll.employee_id)
    record = HRMPayroll(**payroll.model_dump())
    db.add(record)
    db.flush()
    _audit_payroll_action(db, record, employee, user, "PAYROLL_RECORD_CREATED")
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=List[PayrollResponse])
def get_payroll_records(db: Session = Depends(get_db)):
    return db.query(HRMPayroll).order_by(HRMPayroll.created_at.desc()).all()


@router.get("/{payroll_id}", response_model=PayrollResponse)
def get_payroll(payroll_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, HRMPayroll, payroll_id, "Payroll record")


@router.put("/{payroll_id}", response_model=PayrollResponse)
def update_payroll(
    payroll_id: UUID,
    payroll_update: PayrollUpdate,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    payroll = get_or_404(db, HRMPayroll, payroll_id, "Payroll record")
    employee = _require_payroll_employee_ready(db, payroll.employee_id)
    record = update_record(db, payroll, payroll_update)
    _audit_payroll_action(db, record, employee, user, "PAYROLL_RECORD_UPDATED")
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payroll(payroll_id: UUID, db: Session = Depends(get_db)):
    payroll = get_or_404(db, HRMPayroll, payroll_id, "Payroll record")
    return delete_record(db, payroll)
