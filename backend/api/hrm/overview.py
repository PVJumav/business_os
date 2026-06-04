from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.hrm import (
    HRMDepartment,
    HRMEmployee,
    HRMLeave,
    HRMLeaveBalance,
    HRMOnboardingTask,
    HRMPayroll,
    HRMPerformance,
    HRMPolicyAcknowledgement,
    HRMPosition,
    HRMRecruitment,
    HRMTraining,
)
from backend.schemas.auth import UserResponse


router = APIRouter(prefix="/hrm/overview", tags=["HRM Overview"])


def _count(db: Session, model, *filters) -> int:
    query = db.query(model)
    if filters:
        query = query.filter(*filters)
    return query.count()


def _duplicate_count(db: Session, model, column) -> int:
    rows = (
        db.query(column, func.count(model.id))
        .filter(column.isnot(None), column != "")
        .group_by(column)
        .having(func.count(model.id) > 1)
        .all()
    )
    return sum(int(count) for _, count in rows)


@router.get("")
def get_hrm_overview(
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    active_employees = _count(db, HRMEmployee, HRMEmployee.employment_status == "active")
    departments = _count(db, HRMDepartment)
    open_positions = _count(db, HRMPosition, HRMPosition.status == "active")
    open_recruitment = _count(db, HRMRecruitment, HRMRecruitment.application_status.in_(["pending", "shortlisted", "interview"]))
    pending_onboarding = _count(db, HRMOnboardingTask, HRMOnboardingTask.status.in_(["pending", "in_progress", "blocked"]))
    pending_leave = _count(db, HRMLeave, HRMLeave.status == "pending")
    pending_payroll = _count(db, HRMPayroll, HRMPayroll.payment_status == "pending")
    pending_policy = _count(db, HRMPolicyAcknowledgement, HRMPolicyAcknowledgement.status.in_(["pending", "overdue"]))
    pending_confirmation = _count(
        db,
        HRMEmployee,
        HRMEmployee.employment_status.in_(["active", "probation"]),
        HRMEmployee.probation_status.in_(["Due for Review", "Extended", "Confirmed", "Closed"]),
        or_(
            HRMEmployee.confirmation_status.is_(None),
            HRMEmployee.confirmation_status.in_(["Pending Confirmation", "Confirmation Deferred"]),
        ),
    )
    overdue_onboarding = _count(db, HRMOnboardingTask, HRMOnboardingTask.status != "completed", HRMOnboardingTask.due_date < func.current_date())
    low_leave_balances = _count(db, HRMLeaveBalance, HRMLeaveBalance.available_days < 3)
    performance_reviews = _count(db, HRMPerformance)
    training_records = _count(db, HRMTraining)

    missing_core_fields = _count(
        db,
        HRMEmployee,
        or_(
            HRMEmployee.department.is_(None),
            HRMEmployee.department == "",
            HRMEmployee.job_title.is_(None),
            HRMEmployee.job_title == "",
            HRMEmployee.email.is_(None),
            HRMEmployee.email == "",
            HRMEmployee.employee_code.is_(None),
            HRMEmployee.employee_code == "",
        ),
    )
    duplicate_emails = _duplicate_count(db, HRMEmployee, HRMEmployee.email)
    duplicate_codes = _duplicate_count(db, HRMEmployee, HRMEmployee.employee_code)
    data_issues = missing_core_fields + duplicate_emails + duplicate_codes
    total_employees = max(_count(db, HRMEmployee), 1)
    data_quality_score = max(0, round(100 - ((data_issues / total_employees) * 25)))

    department_rows = (
        db.query(HRMEmployee.department, func.count(HRMEmployee.id))
        .filter(HRMEmployee.department.isnot(None), HRMEmployee.department != "")
        .group_by(HRMEmployee.department)
        .order_by(func.count(HRMEmployee.id).desc())
        .limit(8)
        .all()
    )

    return {
        "user_role": user.role,
        "company_profile": {
            "name": "Isols Group",
            "structure": ["CEO", "CFO", "CTO", "Sales Lead", "Country Managers", "Department Heads", "Team Leads", "Employees"],
            "departments": ["HR", "Sales", "Finance", "Technical", "PMO", "Bids", "Legal", "Operations", "Marketing"],
        },
        "kpis": {
            "active_employees": active_employees,
            "departments": departments,
            "open_positions": open_positions,
            "open_recruitment": open_recruitment,
            "pending_onboarding": pending_onboarding,
            "pending_leave": pending_leave,
            "pending_payroll": pending_payroll,
            "pending_policy": pending_policy,
            "pending_confirmation": pending_confirmation,
            "data_quality_score": data_quality_score,
        },
        "alerts": [
            {"label": "Missing core employee fields", "value": missing_core_fields, "severity": "high" if missing_core_fields else "good", "href": "/hrm/employees"},
            {"label": "Duplicate employee emails", "value": duplicate_emails, "severity": "critical" if duplicate_emails else "good", "href": "/hrm/employees"},
            {"label": "Duplicate employee codes", "value": duplicate_codes, "severity": "critical" if duplicate_codes else "good", "href": "/hrm/employees"},
            {"label": "Overdue onboarding tasks", "value": overdue_onboarding, "severity": "high" if overdue_onboarding else "good", "href": "/hrm/onboarding"},
            {"label": "Low leave balances", "value": low_leave_balances, "severity": "medium" if low_leave_balances else "good", "href": "/hrm/leave"},
            {"label": "Employees due for confirmation", "value": pending_confirmation, "severity": "medium" if pending_confirmation else "good", "href": "/hrm/employees"},
        ],
        "processes": [
            {"name": "Recruit to hire", "steps": ["Recruitment", "Offer", "Employee master", "Onboarding", "Policy acknowledgement"], "href": "/hrm/recruitment", "open_items": open_recruitment + pending_onboarding},
            {"name": "Employee master data", "steps": ["Employee record", "Department", "Position", "Role", "Line manager"], "href": "/hrm/employees", "open_items": missing_core_fields},
            {"name": "Time and leave", "steps": ["Attendance", "Leave request", "Approval", "Balance update", "Payroll signal"], "href": "/hrm/leave", "open_items": pending_leave},
            {"name": "Payroll and compensation", "steps": ["Compensation", "Payroll run", "Approval", "Payment", "Finance posting"], "href": "/hrm/payroll", "open_items": pending_payroll},
            {"name": "Performance and growth", "steps": ["Goals", "Review", "Training", "Certification", "Promotion"], "href": "/hrm/performance", "open_items": performance_reviews + training_records},
            {"name": "Governance and compliance", "steps": ["Policy", "Acknowledgement", "GRC evidence", "Employee relations", "Audit"], "href": "/hrm/grc", "open_items": pending_policy},
        ],
        "department_distribution": [
            {"name": department or "Unassigned", "employees": count}
            for department, count in department_rows
        ],
    }
