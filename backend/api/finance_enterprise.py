from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.auth import UserResponse
from backend.schemas.enterprise_phase1 import WorkflowPayload
from backend.services.finance_enterprise import (
    RESOURCE_MAP,
    analytics_summary,
    create_record,
    delete_record,
    get_record,
    list_records,
    serialize,
    update_record,
    workflow,
)


router = APIRouter(prefix="/finance", tags=["Finance Enterprise"])


@router.get("/enterprise/resources")
def resources():
    return {"resources": sorted(RESOURCE_MAP.keys())}


@router.get("/reports")
def reports(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return analytics_summary(db)


@router.get("/enterprise/analytics")
def analytics(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return analytics_summary(db)


@router.get("/{resource}")
def list_resource(resource: str, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return list_records(db, resource, current_user)


@router.post("/{resource}", status_code=status.HTTP_201_CREATED)
def create_resource(
    resource: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return create_record(db, resource, data, current_user)


@router.get("/{resource}/{record_id}")
def get_resource(
    resource: str,
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return serialize(get_record(db, resource, record_id))


@router.patch("/{resource}/{record_id}")
def patch_resource(
    resource: str,
    record_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, resource, record_id, data, current_user)


@router.delete("/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_resource(
    resource: str,
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    delete_record(db, resource, record_id, current_user)
    return None


@router.post("/{resource}/{record_id}/{action}")
def workflow_resource(
    resource: str,
    record_id: UUID,
    action: str,
    payload: WorkflowPayload | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return workflow(db, resource, record_id, action, current_user, payload.model_dump(exclude_none=True) if payload else {})
