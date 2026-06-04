from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.hrm.employees import _full_name, process_probation_reviews
from backend.core.database import get_db
from backend.models.hrm import HRMEmployee, HRMProbationRecord
from backend.schemas.auth import UserResponse


router = APIRouter(prefix="/hrm/probation", tags=["HRM Probation"])


@router.get("/due-for-review")
def get_probation_due_for_review(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    today = date.today()
    window_end = today + timedelta(days=30)
    rows = (
        db.query(HRMProbationRecord, HRMEmployee)
        .join(HRMEmployee, HRMEmployee.id == HRMProbationRecord.employee_id)
        .filter(
            HRMProbationRecord.probation_required == True,  # noqa: E712
            HRMProbationRecord.status.in_(["In Progress", "Due for Review", "Extended"]),
            HRMProbationRecord.end_date <= window_end,
        )
        .order_by(HRMProbationRecord.end_date.asc())
        .all()
    )
    return [
        {
            "employee_id": str(employee.id),
            "employee_code": employee.employee_code,
            "employee_name": _full_name(employee),
            "department": employee.department,
            "job_title": employee.job_title,
            "probation_status": record.status,
            "probation_end_date": record.end_date,
            "days_to_review": (record.end_date - today).days if record.end_date else None,
        }
        for record, employee in rows
    ]


@router.post("/daily-check")
def run_probation_daily_check(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return process_probation_reviews(db, user.full_name)
