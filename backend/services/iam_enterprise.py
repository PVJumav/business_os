from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.auth import AuthUser
from backend.models.hrm import HRMEmployee, HRMUserEmployeeLink
from backend.models.iam import (
    IAMAPIKey,
    IAMAccessPolicy,
    IAMAuditLog,
    IAMApprovalDelegation,
    IAMBranchAccess,
    IAMDataAccessRule,
    IAMDepartmentAccess,
    IAMLoginHistory,
    IAMMFASetting,
    IAMPasswordResetToken,
    IAMPermission,
    IAMRole,
    IAMRolePermission,
    IAMServiceAccount,
    IAMSession,
    IAMTeam,
    IAMTeamMembership,
    IAMUserRole,
)
from backend.policies.iam import require_permission
from backend.schemas.auth import UserResponse


RESOURCE_MAP = {
    "users": AuthUser,
    "roles": IAMRole,
    "permissions": IAMPermission,
    "role-permissions": IAMRolePermission,
    "user-roles": IAMUserRole,
    "teams": IAMTeam,
    "team-memberships": IAMTeamMembership,
    "department-access": IAMDepartmentAccess,
    "branch-access": IAMBranchAccess,
    "sessions": IAMSession,
    "login-history": IAMLoginHistory,
    "mfa": IAMMFASetting,
    "password-reset-tokens": IAMPasswordResetToken,
    "api-keys": IAMAPIKey,
    "service-accounts": IAMServiceAccount,
    "audit-logs": IAMAuditLog,
    "access-policies": IAMAccessPolicy,
    "delegations": IAMApprovalDelegation,
    "data-access-rules": IAMDataAccessRule,
}

WORKFLOW_TRANSITIONS = {
    "activate-user": "active",
    "suspend-user": "suspended",
    "disable-user": "disabled",
    "assign-role": "active",
    "revoke-role": "revoked",
    "enable-mfa": "enabled",
    "disable-mfa": "disabled",
    "create-api-key": "active",
    "revoke-api-key": "revoked",
}


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="IAM resource not found")
    return model


def serialize(row) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (datetime,)):
            value = value.isoformat()
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        elif isinstance(value, UUID):
            value = str(value)
        result[column.name] = value
    if isinstance(row, AuthUser):
        result.pop("hashed_password", None)
        result["status"] = "active" if row.is_active else "disabled"
    return result


def clean_payload(model, data: dict[str, Any]) -> dict[str, Any]:
    blocked = {"id", "created_at", "updated_at", "deleted_at"}
    if model is AuthUser:
        blocked.add("hashed_password")
    columns = {column.name for column in model.__table__.columns}
    return {key: value for key, value in data.items() if key in columns and key not in blocked and value not in ("", None)}


def audit(db: Session, user: UserResponse | None, action: str, entity_type: str, entity_id: str | None, before=None, after=None):
    db.add(
        IAMAuditLog(
            actor_user_id=getattr(user, "id", None),
            actor_email=getattr(user, "email", None),
            module="iam",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=f"{action} IAM {entity_type}",
            before_json=before,
            after_json=after,
        )
    )


def get_record(db: Session, resource: str, record_id: UUID):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="IAM record not found")
    return record


def list_records(db: Session, resource: str, user: UserResponse) -> list[dict[str, Any]]:
    model = model_for(resource)
    require_permission(db, user, "iam", resource, "read")
    query = db.query(model)
    if hasattr(model, "soft_deleted"):
        query = query.filter(model.soft_deleted.is_(False))
    if hasattr(model, "created_at"):
        query = query.order_by(model.created_at.desc())
    return [serialize(row) for row in query.limit(500).all()]


def validate(data: dict[str, Any], resource: str, db: Session, record_id: UUID | None = None) -> None:
    if resource == "user-roles" and data.get("user_id") and data.get("role_id"):
        user = db.query(AuthUser).filter(AuthUser.id == data["user_id"]).first()
        role = db.query(IAMRole).filter(IAMRole.id == data["role_id"]).first()
        if not user or not role:
            raise HTTPException(status_code=422, detail="User role assignments require valid user and role records")
    if resource == "service-accounts" and data.get("employee_id"):
        raise HTTPException(status_code=422, detail="Service accounts must not be linked to employees")
    if resource == "api-keys" and not data.get("expires_at"):
        raise HTTPException(status_code=422, detail="API keys must have an expiry date")


def create_record(db: Session, resource: str, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    require_permission(db, user, "iam", resource, "create")
    if model is AuthUser:
        raise HTTPException(status_code=422, detail="Create users through /auth/register or IAM activation workflow")
    data = clean_payload(model, data)
    validate(data, resource, db)
    record = model(**data)
    db.add(record)
    db.flush()
    after = serialize(record)
    audit(db, user, "create", resource, str(record.id), after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def update_record(db: Session, resource: str, record_id: UUID, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    record = get_record(db, resource, record_id)
    require_permission(db, user, "iam", resource, "update")
    before = serialize(record)
    data = clean_payload(model, data)
    validate(data, resource, db, record_id)
    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    after = serialize(record)
    audit(db, user, "update", resource, str(record_id), before=before, after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def delete_record(db: Session, resource: str, record_id: UUID, user: UserResponse) -> None:
    record = get_record(db, resource, record_id)
    require_permission(db, user, "iam", resource, "delete")
    before = serialize(record)
    if hasattr(record, "soft_deleted"):
        record.soft_deleted = True
        if hasattr(record, "status"):
            record.status = "deleted"
    else:
        db.delete(record)
    audit(db, user, "delete", resource, str(record_id), before=before)
    db.commit()


def disable_user_for_employee_termination(db: Session, employee_id: UUID, actor: UserResponse | None = None) -> None:
    link = db.query(HRMUserEmployeeLink).filter(HRMUserEmployeeLink.employee_id == employee_id).first()
    if not link:
        return
    user = db.query(AuthUser).filter(AuthUser.id == link.user_id).first()
    if user:
        before = serialize(user)
        user.is_active = False
        audit(db, actor, "employee.terminated:disable-user", "users", str(user.id), before=before, after=serialize(user))


def workflow(db: Session, resource: str, record_id: UUID, action: str, user: UserResponse, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    record = get_record(db, resource, record_id)
    require_permission(db, user, "iam", resource, "update")
    before = serialize(record)
    payload = payload or {}
    now = datetime.now(timezone.utc)
    if resource == "users":
        if action == "activate-user":
            record.is_active = True
        elif action in {"suspend-user", "disable-user"}:
            record.is_active = False
        elif action == "reset-password":
            token = IAMPasswordResetToken(user_id=record.id, token_hash=f"reset-{record.id}-{int(now.timestamp())}", expires_at=now)
            db.add(token)
        else:
            raise HTTPException(status_code=422, detail="Unsupported user workflow action")
    elif resource == "mfa":
        record.enabled = action == "enable-mfa"
    elif resource in {"api-keys", "user-roles"} and action in {"revoke-api-key", "revoke-role"}:
        record.status = "revoked"
        if hasattr(record, "revoked_at"):
            record.revoked_at = now
    elif action in WORKFLOW_TRANSITIONS and hasattr(record, "status"):
        record.status = WORKFLOW_TRANSITIONS[action]
    else:
        raise HTTPException(status_code=422, detail="Unsupported IAM workflow action")
    db.flush()
    audit(db, user, action, resource, str(record_id), before=before, after=serialize(record))
    db.commit()
    db.refresh(record)
    return serialize(record)


def analytics_summary(db: Session) -> dict[str, Any]:
    return {
        "users": db.query(AuthUser).count(),
        "active_users": db.query(AuthUser).filter(AuthUser.is_active.is_(True)).count(),
        "roles": db.query(IAMRole).filter(IAMRole.status == "active").count(),
        "permissions": db.query(IAMPermission).count(),
        "active_sessions": db.query(IAMSession).filter(IAMSession.revoked_at.is_(None)).count(),
        "audit_events": db.query(IAMAuditLog).count(),
    }


def create_user_for_employee(db: Session, employee: HRMEmployee, user: UserResponse | None = None) -> AuthUser:
    existing = db.query(AuthUser).filter(AuthUser.email == employee.email).first()
    if existing:
        return existing
    auth_user = AuthUser(
        email=employee.email,
        full_name=f"{employee.first_name} {employee.last_name}",
        role="user",
        hashed_password="external-provisioning-required",
        is_active=employee.employment_status == "active",
    )
    db.add(auth_user)
    db.flush()
    audit(db, user, "employee.created:create-user", "users", str(auth_user.id), after=serialize(auth_user))
    return auth_user
