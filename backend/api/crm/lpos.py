from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.auth import UserResponse
from backend.services.crm_enterprise import create_record, delete_record, get_record, list_records, serialize, update_record, workflow
from backend.services.phase1_integrations import lpo_uploaded


router = APIRouter(prefix="/crm/lpos", tags=["CRM LPOs"])


@router.get("")
def list_lpos(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return list_records(db, "lpos", current_user)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_lpo(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return create_record(db, "lpos", data, current_user)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_lpo(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return lpo_uploaded(db, payload, current_user)


@router.get("/{lpo_id}")
def get_lpo(lpo_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return serialize(get_record(db, "lpos", lpo_id))


@router.patch("/{lpo_id}")
def patch_lpo(lpo_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, "lpos", lpo_id, data, current_user)


@router.put("/{lpo_id}")
def put_lpo(lpo_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, "lpos", lpo_id, data, current_user)


@router.delete("/{lpo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_lpo(lpo_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    delete_record(db, "lpos", lpo_id, current_user)
    return None


@router.post("/{lpo_id}/{action}")
def lpo_workflow(lpo_id: UUID, action: str, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return workflow(db, "lpos", lpo_id, action, current_user, payload or {})
