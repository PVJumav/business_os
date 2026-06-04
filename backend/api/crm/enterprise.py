from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.auth import UserResponse
from backend.schemas.crm.enterprise import CRMWorkflowPayload
from backend.services.crm_enterprise import (
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


router = APIRouter(prefix="/crm/enterprise", tags=["CRM Enterprise"])


@router.get("/resources")
def resources():
    return {"resources": sorted(RESOURCE_MAP.keys())}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    return analytics_summary(db)


@router.get("/{resource}")
def list_resource(
    resource: str,
    account_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    records = list_records(db, resource, current_user)
    if account_id:
        records = [record for record in records if record.get("account_id") == str(account_id)]
    return records


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
    record = get_record(db, resource, record_id)
    return serialize(record)


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


@router.put("/{resource}/{record_id}")
def put_resource(
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
def resource_workflow(
    resource: str,
    record_id: UUID,
    action: str,
    payload: CRMWorkflowPayload | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return workflow(db, resource, record_id, action, current_user, payload.model_dump(exclude_none=True) if payload else {})
