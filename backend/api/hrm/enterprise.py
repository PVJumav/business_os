from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.auth import UserResponse
from backend.schemas.hrm.enterprise import WorkflowActionPayload
from backend.services.hrm_enterprise import (
    RESOURCE_MAP,
    analytics_summary,
    create_record,
    get_record,
    list_records,
    resource_analytics,
    serialize,
    soft_delete_record,
    transition_record,
    update_record,
)


router = APIRouter(prefix="/hrm/enterprise", tags=["HRM Enterprise"])


@router.get("/resources")
def get_supported_resources():
    return {"resources": sorted(RESOURCE_MAP.keys())}


@router.get("/analytics")
def get_hrm_enterprise_analytics(db: Session = Depends(get_db)):
    return analytics_summary(db)


@router.get("/{resource}")
def list_enterprise_records(
    resource: str,
    employee_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    records = list_records(db, resource, current_user)
    if employee_id:
        records = [record for record in records if record.get("employee_id") == str(employee_id)]
    return records


@router.get("/{resource}/__analytics")
def get_enterprise_resource_analytics(
    resource: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    list_records(db, resource, current_user)
    return resource_analytics(db, resource)


@router.post("/{resource}", status_code=status.HTTP_201_CREATED)
def create_enterprise_record(
    resource: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return create_record(db, resource, data, current_user)


@router.get("/{resource}/{record_id}")
def get_enterprise_record(
    resource: str,
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    record = get_record(db, resource, record_id)
    return serialize(record)


@router.patch("/{resource}/{record_id}")
def patch_enterprise_record(
    resource: str,
    record_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, resource, record_id, data, current_user)


@router.put("/{resource}/{record_id}")
def put_enterprise_record(
    resource: str,
    record_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, resource, record_id, data, current_user)


@router.delete("/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enterprise_record(
    resource: str,
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    soft_delete_record(db, resource, record_id, current_user)
    return None


@router.post("/{resource}/{record_id}/{action}")
def workflow_transition(
    resource: str,
    record_id: UUID,
    action: str,
    payload: WorkflowActionPayload | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    reason = None
    if payload:
        reason = payload.adjustment_reason or payload.reason or payload.comments
    return transition_record(db, resource, record_id, action, current_user, reason)
