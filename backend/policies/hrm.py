from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.hrm import HRMEmployee, HRMUserEmployeeLink
from backend.schemas.auth import UserResponse


HR_ROLES = {"admin", "hr", "hr_admin", "hr_manager", "people_admin"}
PAYROLL_ROLES = {"admin", "payroll", "payroll_admin", "finance_admin", "accountant", "cfo"}
MANAGER_ROLES = {"admin", "manager", "hr", "hr_admin", "hr_manager"}
ADMIN_ROLES = {"admin", "system_admin"}

SENSITIVE_RESOURCES = {
    "compensation",
    "salary-structures",
    "payroll",
    "payroll-periods",
    "payroll-runs",
    "payslips",
    "payroll-components",
    "payroll-adjustments",
    "employee-relations",
}


def normalized_role(user: UserResponse | None) -> str:
    return (getattr(user, "role", "") or "").strip().lower()


def is_admin(user: UserResponse | None) -> bool:
    return normalized_role(user) in ADMIN_ROLES


def is_hr(user: UserResponse | None) -> bool:
    return normalized_role(user) in HR_ROLES


def is_payroll(user: UserResponse | None) -> bool:
    return normalized_role(user) in PAYROLL_ROLES


def is_manager(user: UserResponse | None) -> bool:
    return normalized_role(user) in MANAGER_ROLES


def linked_employee(db: Session, user: UserResponse | None) -> HRMEmployee | None:
    if not user:
        return None

    link = (
        db.query(HRMUserEmployeeLink)
        .filter(
            HRMUserEmployeeLink.user_id == user.id,
            HRMUserEmployeeLink.status == "active",
        )
        .first()
    )
    if link:
        return db.query(HRMEmployee).filter(HRMEmployee.id == link.employee_id).first()

    return db.query(HRMEmployee).filter(HRMEmployee.email == user.email).first()


def can_view_employee(db: Session, user: UserResponse, employee_id: UUID | None) -> bool:
    if is_admin(user) or is_hr(user):
        return True
    employee = linked_employee(db, user)
    if not employee or not employee_id:
        return False
    if employee.id == employee_id:
        return True
    return is_manager(user) and db.query(HRMEmployee).filter(
        HRMEmployee.id == employee_id,
        HRMEmployee.supervisor_id == employee.id,
    ).first() is not None


def require_resource_access(
    db: Session,
    user: UserResponse,
    resource: str,
    action: str,
    employee_id: UUID | None = None,
) -> None:
    if is_admin(user):
        return

    if resource in SENSITIVE_RESOURCES:
        if action == "read" and (is_hr(user) or is_payroll(user)):
            return
        if is_payroll(user) and resource.startswith("payroll"):
            return
        if is_hr(user) and resource in {"compensation", "employee-relations"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to sensitive HR/payroll records",
        )

    if action in {"create", "update", "delete", "approve", "reject", "lock", "unlock"}:
        if is_hr(user) or (is_manager(user) and resource in {"leave", "overtime-requests", "timesheets"}):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this HR action",
        )

    if employee_id and not can_view_employee(db, user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own HR records or your direct reports",
        )
