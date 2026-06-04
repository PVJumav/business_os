from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.policies.iam import is_admin, require_permission, user_role_codes
from backend.schemas.auth import UserResponse


FINANCE_ROLES = {"finance", "finance_admin", "accountant", "cfo", "finance_manager", "auditor"}
PAYROLL_FINANCE_ROLES = FINANCE_ROLES | {"payroll", "payroll_admin", "hr_admin"}


def require_finance_access(db: Session, user: UserResponse, action: str, resource: str) -> None:
    if is_admin(user):
        return
    roles = user_role_codes(db, user)
    token_role = str(getattr(user, "role", "") or "").lower()
    allowed = PAYROLL_FINANCE_ROLES if resource == "payroll-postings" else FINANCE_ROLES
    if roles & allowed or token_role in allowed:
        return
    if action == "read" and str(user.role).lower() in {"manager", "user"}:
        return
    require_permission(db, user, "finance", resource, action)


def deny_closed_period(status_value: str | None) -> None:
    if status_value in {"closed", "locked"}:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Closed financial periods cannot be edited")
