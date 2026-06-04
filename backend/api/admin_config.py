from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.config import AccessRight, OrganizationPolicy
from backend.schemas.auth import UserResponse


router = APIRouter(prefix="/admin", tags=["Admin Configuration"])

RESOURCE_MAP = {
    "policies": OrganizationPolicy,
    "access-rights": AccessRight,
}


def require_admin(user: UserResponse = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="System admin access is required")
    return user


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Admin configuration resource not found")
    return model


def serialize(row):
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        result[column.name] = float(value) if isinstance(value, Decimal) else value
    return result


def clean_payload(payload: dict[str, Any], user: UserResponse):
    cleaned = {key: value for key, value in payload.items() if value not in [None, ""]}
    cleaned.setdefault("created_by", user.full_name)
    return cleaned


@router.get("/{resource}")
def list_records(resource: str, db: Session = Depends(get_db), user: UserResponse = Depends(require_admin)):
    model = model_for(resource)
    return [serialize(item) for item in db.query(model).order_by(model.created_at.desc()).all()]


@router.post("/{resource}", status_code=status.HTTP_201_CREATED)
def create_record(
    resource: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: UserResponse = Depends(require_admin),
):
    model = model_for(resource)
    record = model(**clean_payload(payload, user))
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize(record)


@router.put("/{resource}/{record_id}")
def update_record(
    resource: str,
    record_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: UserResponse = Depends(require_admin),
):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Admin configuration record not found")
    for key, value in clean_payload(payload, user).items():
        if hasattr(record, key):
            setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return serialize(record)


@router.delete("/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    resource: str,
    record_id: UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(require_admin),
):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Admin configuration record not found")
    db.delete(record)
    db.commit()
    return None
