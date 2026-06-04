from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.hrm import (
    HRMActivity,
    HRMAssetAssignment,
    HRMCompensation,
    HRMEmployeeRelationCase,
    HRMEmployeeImportBatch,
    HRMEmployeeImportRow,
    HRMGRCRecord,
    HRMLifecycleEvent,
    HRMLeaveBalance,
    HRMOnboardingTask,
    HRMPolicyAcknowledgement,
    HRMPosition,
    HRMSurvey,
)


router = APIRouter(prefix="/hrm", tags=["HRM Activities and GRC"])

RESOURCE_MAP = {
    "activities": HRMActivity,
    "grc": HRMGRCRecord,
    "positions": HRMPosition,
    "onboarding": HRMOnboardingTask,
    "leave-balances": HRMLeaveBalance,
    "compensation": HRMCompensation,
    "lifecycle": HRMLifecycleEvent,
    "policy-acknowledgements": HRMPolicyAcknowledgement,
    "employee-relations": HRMEmployeeRelationCase,
    "employee-import-batches": HRMEmployeeImportBatch,
    "employee-import-rows": HRMEmployeeImportRow,
    "surveys": HRMSurvey,
    "asset-assignments": HRMAssetAssignment,
}


def serialize(row):
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        result[column.name] = float(value) if isinstance(value, Decimal) else value
    return result


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="HRM resource not found")
    return model


@router.get("/{resource}")
def list_records(resource: str, db: Session = Depends(get_db)):
    model = model_for(resource)
    return [serialize(item) for item in db.query(model).order_by(model.created_at.desc()).all()]


@router.post("/{resource}", status_code=status.HTTP_201_CREATED)
def create_record(resource: str, payload: dict[str, Any], db: Session = Depends(get_db)):
    model = model_for(resource)
    record = model(**{key: value for key, value in payload.items() if value not in [None, ""]})
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize(record)


@router.put("/{resource}/{record_id}")
def update_record(resource: str, record_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db)):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="HRM record not found")
    for key, value in payload.items():
        if hasattr(record, key) and value not in [None, ""]:
            setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return serialize(record)


@router.delete("/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(resource: str, record_id: UUID, db: Session = Depends(get_db)):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="HRM record not found")
    db.delete(record)
    db.commit()
    return None
