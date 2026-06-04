from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.iam import IAMPermission, IAMRole, IAMRolePermission, IAMUserRole
from backend.schemas.auth import UserResponse


ADMIN_ROLES = {"admin", "system_admin", "super_admin"}


def is_admin(user: UserResponse | None) -> bool:
    return bool(user and str(user.role).lower() in ADMIN_ROLES)


def user_role_codes(db: Session, user: UserResponse | None) -> set[str]:
    if not user:
        return set()
    codes = {str(user.role).lower()}
    rows = (
        db.query(IAMRole.role_code)
        .join(IAMUserRole, IAMUserRole.role_id == IAMRole.id)
        .filter(IAMUserRole.user_id == user.id, IAMUserRole.status == "active", IAMRole.status == "active")
        .all()
    )
    codes.update(str(row[0]).lower() for row in rows)
    return codes


def has_permission(db: Session, user: UserResponse | None, module: str, resource: str, action: str) -> bool:
    if is_admin(user):
        return True
    if not user:
        return False
    role_ids = [
        row[0]
        for row in db.query(IAMUserRole.role_id)
        .filter(IAMUserRole.user_id == user.id, IAMUserRole.status == "active")
        .all()
    ]
    if not role_ids:
        return action == "read"
    return (
        db.query(IAMPermission)
        .join(IAMRolePermission, IAMRolePermission.permission_id == IAMPermission.id)
        .filter(
            IAMRolePermission.role_id.in_(role_ids),
            IAMPermission.module.in_([module, "enterprise", "*"]),
            IAMPermission.resource.in_([resource, "*"]),
            IAMPermission.action.in_([action, "*"]),
            IAMPermission.status == "active",
        )
        .first()
        is not None
    )


def effective_permissions(db: Session, user: UserResponse | None) -> list[str]:
    if not user:
        return []
    if is_admin(user):
        return ["*:*:*"]
    role_ids = [
        row[0]
        for row in db.query(IAMUserRole.role_id)
        .filter(IAMUserRole.user_id == user.id, IAMUserRole.status == "active")
        .all()
    ]
    if not role_ids:
        return ["*:read"]
    rows = (
        db.query(IAMPermission.module, IAMPermission.resource, IAMPermission.action, IAMPermission.permission_code)
        .join(IAMRolePermission, IAMRolePermission.permission_id == IAMPermission.id)
        .filter(
            IAMRolePermission.role_id.in_(role_ids),
            IAMPermission.status == "active",
        )
        .all()
    )
    permissions = {f"{module}:{resource}:{action}" for module, resource, action, _ in rows}
    permissions.update(str(code) for _, _, _, code in rows if code)
    return sorted(permissions)


def require_permission(db: Session, user: UserResponse | None, module: str, resource: str, action: str) -> None:
    if not has_permission(db, user, module, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have {action} access to {module}.{resource}",
        )
