from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.auth import UserResponse
from backend.services.automation_enterprise import (
    RESOURCE_MAP,
    approval_action,
    create_record,
    dashboard,
    delete_record,
    get_record,
    list_records,
    seed_defaults,
    serialize,
    start_sla,
    update_record,
    workflow_action,
)


router = APIRouter(tags=["Business OS 5.5 Enterprise Automation"])


class FlexiblePayload(BaseModel):
    model_config = ConfigDict(extra="allow")


@router.get("/automation/resources")
def resources():
    return {"resources": sorted(RESOURCE_MAP.keys())}


@router.get("/automation/dashboard")
def automation_dashboard(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return dashboard(db)


@router.post("/automation/seed", status_code=status.HTTP_201_CREATED)
def seed_automation(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return seed_defaults(db)


def _list_resource(
    resource: str,
    query: str | None = Query(default=None),
    record_status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return list_records(db, resource, current_user, query=query, status=record_status, limit=limit, offset=offset)


def _create_resource(
    resource: str,
    payload: FlexiblePayload,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return create_record(db, resource, payload.model_dump(exclude_unset=True), current_user)


def _get_resource(resource: str, record_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return serialize(get_record(db, resource, record_id))


def _put_resource(
    resource: str,
    record_id: UUID,
    payload: FlexiblePayload,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return update_record(db, resource, record_id, payload.model_dump(exclude_unset=True), current_user)


def _delete_resource(resource: str, record_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    delete_record(db, resource, record_id, current_user)
    return None


def _register_resource_routes(path: str, resource: str) -> None:
    async def list_endpoint(
        query: str | None = Query(default=None),
        record_status: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(get_db),
        current_user: UserResponse = Depends(get_current_user),
    ):
        return list_records(db, resource, current_user, query=query, status=record_status, limit=limit, offset=offset)

    async def create_endpoint(payload: FlexiblePayload, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
        return create_record(db, resource, payload.model_dump(exclude_unset=True), current_user)

    async def get_endpoint(record_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
        return serialize(get_record(db, resource, record_id))

    async def put_endpoint(record_id: UUID, payload: FlexiblePayload, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
        return update_record(db, resource, record_id, payload.model_dump(exclude_unset=True), current_user)

    async def delete_endpoint(record_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
        delete_record(db, resource, record_id, current_user)
        return None

    router.add_api_route(path, list_endpoint, methods=["GET"], name=f"list_{resource}")
    router.add_api_route(path, create_endpoint, methods=["POST"], status_code=status.HTTP_201_CREATED, name=f"create_{resource}")
    router.add_api_route(f"{path}/{{record_id}}", get_endpoint, methods=["GET"], name=f"get_{resource}")
    router.add_api_route(f"{path}/{{record_id}}", put_endpoint, methods=["PUT"], name=f"update_{resource}")
    router.add_api_route(f"{path}/{{record_id}}", delete_endpoint, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT, name=f"delete_{resource}")


@router.post("/workflows/instances/{record_id}/actions/{action}")
def workflow_transition(
    record_id: UUID,
    action: str,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return workflow_action(db, record_id, action, current_user, payload or {})


@router.post("/approvals/requests/{request_id}/actions/{action}")
def approval_transition(
    request_id: UUID,
    action: str,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return approval_action(db, request_id, action, current_user, (payload or {}).get("comments"))


@router.post("/sla/policies/{policy_id}/start")
def start_sla_instance(
    policy_id: UUID,
    payload: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return start_sla(db, policy_id, payload or {}, current_user)


for route_path, resource_key in [
    ("/governance/categories", "governance/categories"),
    ("/governance/policies", "governance/policies"),
    ("/governance/policy-versions", "governance/policy-versions"),
    ("/governance/exceptions", "governance/exceptions"),
    ("/governance/acknowledgements", "governance/acknowledgements"),
    ("/sops", "sops"),
    ("/sop-steps", "sop-steps"),
    ("/sops/{sop_id}/steps", "sop-steps"),
    ("/workflows/templates", "workflows/templates"),
    ("/workflows/stages", "workflows/stages"),
    ("/workflows/instances", "workflows/instances"),
    ("/workflows/tasks", "workflows/tasks"),
    ("/approvals/matrix", "approvals/matrix"),
    ("/approvals/requests", "approvals/requests"),
    ("/approvals/actions", "approvals/actions"),
    ("/events", "events"),
    ("/audit/logs", "audit/logs"),
    ("/sla/policies", "sla/policies"),
    ("/sla/instances", "sla/instances"),
    ("/escalations", "escalations"),
    ("/iam/access-profiles", "iam/access-profiles"),
    ("/iam/access-reviews", "iam/access-reviews"),
    ("/compliance/controls", "compliance/controls"),
    ("/risk/register", "risk/register"),
    ("/kpis", "kpis"),
    ("/kpis/results", "kpis/results"),
    ("/corrective-actions", "corrective-actions"),
]:
    if "{" not in route_path:
        _register_resource_routes(route_path, resource_key)


@router.get("/sops/{sop_id}/steps")
def list_sop_steps(sop_id: UUID, db: Session = Depends(get_db)):
    return list_records(db, "sop-steps", filters={"sop_id": str(sop_id)})
