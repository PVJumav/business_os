from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.hrm import (
    HRMAttendancePeriod,
    HRMAuditLog,
    HRMBranch,
    HRMCandidate,
    HRMCertification,
    HRMClearanceChecklist,
    HRMCompany,
    HRMCompanyAsset,
    HRMCompetency,
    HRMCostCenter,
    HRMCourse,
    HRMEmergencyContact,
    HRMEmployee,
    HRMEmploymentContract,
    HRMExitInterview,
    HRMGoal,
    HRMHoliday,
    HRMInterviewFeedback,
    HRMInterviewStage,
    HRMJobGrade,
    HRMJobOpening,
    HRMJobRequisition,
    HRMKPI,
    HRMLeave,
    HRMLeaveBalance,
    HRMLeaveBlackoutDate,
    HRMLeavePolicy,
    HRMLeaveType,
    HRMMandatoryTrainingPolicy,
    HRMOfferLetter,
    HRMOffboardingApproval,
    HRMOvertimeRequest,
    HRMPayrollAdjustment,
    HRMPayrollComponent,
    HRMPayrollPeriod,
    HRMPayrollRun,
    HRMPayslip,
    HRMPermission,
    HRMPerformanceImprovementPlan,
    HRMReviewCycle,
    HRMRole,
    HRMRolePermission,
    HRMSalaryStructure,
    HRMShift,
    HRMTerminationRecord,
    HRMTimesheet,
    HRMTrainingSession,
    HRMUserEmployeeLink,
    HRMApplication,
)
from backend.policies.hrm import linked_employee, require_resource_access
from backend.schemas.auth import UserResponse


RESOURCE_MAP = {
    "employees": HRMEmployee,
    "companies": HRMCompany,
    "branches": HRMBranch,
    "cost-centers": HRMCostCenter,
    "job-grades": HRMJobGrade,
    "contracts": HRMEmploymentContract,
    "emergency-contacts": HRMEmergencyContact,
    "roles": HRMRole,
    "permissions": HRMPermission,
    "role-permissions": HRMRolePermission,
    "user-employee-links": HRMUserEmployeeLink,
    "audit-logs": HRMAuditLog,
    "leave-types": HRMLeaveType,
    "leave-policies": HRMLeavePolicy,
    "leave-blackout-dates": HRMLeaveBlackoutDate,
    "leave": HRMLeave,
    "leave-requests": HRMLeave,
    "shifts": HRMShift,
    "timesheets": HRMTimesheet,
    "overtime-requests": HRMOvertimeRequest,
    "holidays": HRMHoliday,
    "attendance-periods": HRMAttendancePeriod,
    "salary-structures": HRMSalaryStructure,
    "payroll-periods": HRMPayrollPeriod,
    "payroll-runs": HRMPayrollRun,
    "payslips": HRMPayslip,
    "payroll-components": HRMPayrollComponent,
    "payroll-adjustments": HRMPayrollAdjustment,
    "job-requisitions": HRMJobRequisition,
    "job-openings": HRMJobOpening,
    "candidates": HRMCandidate,
    "applications": HRMApplication,
    "interview-stages": HRMInterviewStage,
    "interview-feedback": HRMInterviewFeedback,
    "offer-letters": HRMOfferLetter,
    "goals": HRMGoal,
    "kpis": HRMKPI,
    "review-cycles": HRMReviewCycle,
    "competencies": HRMCompetency,
    "performance-improvement-plans": HRMPerformanceImprovementPlan,
    "courses": HRMCourse,
    "training-sessions": HRMTrainingSession,
    "certifications": HRMCertification,
    "mandatory-training-policies": HRMMandatoryTrainingPolicy,
    "company-assets": HRMCompanyAsset,
    "clearance-checklists": HRMClearanceChecklist,
    "exit-interviews": HRMExitInterview,
    "termination-records": HRMTerminationRecord,
    "offboarding-approvals": HRMOffboardingApproval,
}

WORKFLOW_TRANSITIONS = {
    "submit": "pending",
    "approve": "approved",
    "reject": "rejected",
    "cancel": "cancelled",
    "lock": "locked",
    "unlock": "open",
}

LOCKED_STATUSES = {"locked", "final_approved", "paid", "closed"}
INACTIVE_EMPLOYEE_STATUSES = {"inactive", "terminated", "suspended"}


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HRM resource not found")
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
    return result


def clean_payload(model, data: dict[str, Any]) -> dict[str, Any]:
    columns = {column.name for column in model.__table__.columns}
    return {key: value for key, value in data.items() if key in columns and value not in (None, "")}


def create_audit(
    db: Session,
    user: UserResponse | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    summary: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    sensitivity: str = "internal",
) -> None:
    db.add(
        HRMAuditLog(
            actor_user_id=getattr(user, "id", None),
            actor_email=getattr(user, "email", None),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            sensitivity=sensitivity,
            summary=summary,
            before_json=before,
            after_json=after,
        )
    )


def employee_id_from_payload(data: dict[str, Any]) -> UUID | None:
    value = data.get("employee_id")
    if not value:
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


def validate_employee_found(db: Session, employee_id: UUID | None) -> HRMEmployee | None:
    if not employee_id:
        return None
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=422, detail="Referenced employee does not exist")
    return employee


def validate_core_rules(db: Session, resource: str, data: dict[str, Any], record_id: UUID | None = None) -> None:
    employee_id = employee_id_from_payload(data)
    employee = validate_employee_found(db, employee_id)

    if resource in {"payroll-runs", "payslips", "salary-structures", "payroll-adjustments"} and employee:
        if employee.employment_status in INACTIVE_EMPLOYEE_STATUSES:
            raise HTTPException(status_code=422, detail="Payroll cannot be processed for inactive, suspended, or terminated employees")

    if resource == "contracts" and data.get("end_date") and data.get("start_date") and data["end_date"] < data["start_date"]:
        raise HTTPException(status_code=422, detail="Contract end date cannot be before start date")

    if resource == "leave" or resource == "leave-requests":
        validate_leave_request(db, data, record_id)


def validate_leave_request(db: Session, data: dict[str, Any], record_id: UUID | None = None) -> None:
    employee_id = employee_id_from_payload(data)
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    leave_type = data.get("leave_type") or data.get("leave_name")
    total_days = Decimal(str(data.get("total_days") or 0))

    if not employee_id or not start_date or not end_date:
        return
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="Leave end date cannot be before start date")

    overlap_query = db.query(HRMLeave).filter(
        HRMLeave.employee_id == employee_id,
        HRMLeave.status.in_(["pending", "approved"]),
        HRMLeave.start_date <= end_date,
        HRMLeave.end_date >= start_date,
    )
    if record_id:
        overlap_query = overlap_query.filter(HRMLeave.id != record_id)
    if overlap_query.first():
        raise HTTPException(status_code=409, detail="Leave request overlaps with an existing pending or approved leave")

    if leave_type:
        balance = (
            db.query(HRMLeaveBalance)
            .filter(HRMLeaveBalance.employee_id == employee_id, HRMLeaveBalance.leave_type == leave_type)
            .order_by(HRMLeaveBalance.created_at.desc())
            .first()
        )
        policy = db.query(HRMLeavePolicy).filter(HRMLeavePolicy.status == "active").first()
        allows_negative = bool(policy and policy.allow_negative_balance)
        if balance and Decimal(str(balance.available_days or 0)) < total_days and not allows_negative:
            raise HTTPException(status_code=422, detail="Leave request exceeds available leave balance")


def get_record(db: Session, resource: str, record_id: UUID):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HRM record not found")
    return record


def list_records(db: Session, resource: str, user: UserResponse) -> list[dict[str, Any]]:
    model = model_for(resource)
    require_resource_access(db, user, resource, "read")
    query = db.query(model)

    if hasattr(model, "soft_deleted"):
        query = query.filter(model.soft_deleted.is_(False))
    if hasattr(model, "created_at"):
        query = query.order_by(model.created_at.desc())

    return [serialize(item) for item in query.all()]


def create_record(db: Session, resource: str, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    employee_id = employee_id_from_payload(data)
    require_resource_access(db, user, resource, "create", employee_id)
    data = clean_payload(model, data)
    validate_core_rules(db, resource, data)

    record = model(**data)
    db.add(record)
    db.flush()
    after = serialize(record)
    create_audit(db, user, "create", resource, str(record.id), f"Created HRM {resource} record", after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def update_record(db: Session, resource: str, record_id: UUID, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    record = get_record(db, resource, record_id)
    if getattr(record, "status", None) in LOCKED_STATUSES:
        raise HTTPException(status_code=423, detail="This record is locked and requires an adjustment workflow")
    before = serialize(record)
    data = clean_payload(model, data)
    employee_id = employee_id_from_payload(data) or getattr(record, "employee_id", None)
    require_resource_access(db, user, resource, "update", employee_id)
    validate_core_rules(db, resource, data, record_id)

    for key, value in data.items():
        setattr(record, key, value)
    db.flush()
    after = serialize(record)
    create_audit(db, user, "update", resource, str(record.id), f"Updated HRM {resource} record", before=before, after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def soft_delete_record(db: Session, resource: str, record_id: UUID, user: UserResponse) -> None:
    record = get_record(db, resource, record_id)
    before = serialize(record)
    employee_id = getattr(record, "employee_id", None)
    require_resource_access(db, user, resource, "delete", employee_id)

    if hasattr(record, "soft_deleted"):
        record.soft_deleted = True
        record.deleted_at = datetime.now(timezone.utc)
        if hasattr(record, "status"):
            record.status = "deleted"
    else:
        db.delete(record)
    create_audit(db, user, "delete", resource, str(record_id), f"Deleted HRM {resource} record", before=before)
    db.commit()


def transition_record(
    db: Session,
    resource: str,
    record_id: UUID,
    action: str,
    user: UserResponse,
    reason: str | None = None,
) -> dict[str, Any]:
    if action not in WORKFLOW_TRANSITIONS:
        raise HTTPException(status_code=404, detail="Workflow action not supported")

    record = get_record(db, resource, record_id)
    employee_id = getattr(record, "employee_id", None)
    require_resource_access(db, user, resource, action, employee_id)

    actor_employee = linked_employee(db, user)
    if action in {"approve", "reject"} and actor_employee and employee_id == actor_employee.id:
        raise HTTPException(status_code=422, detail="Employees cannot approve or reject their own HR records")

    if getattr(record, "status", None) in LOCKED_STATUSES and action != "unlock":
        raise HTTPException(status_code=423, detail="Locked records cannot be changed without unlocking with a reason")
    if action == "unlock" and not reason:
        raise HTTPException(status_code=422, detail="Unlocking requires an adjustment reason")

    before = serialize(record)
    record.status = WORKFLOW_TRANSITIONS[action]
    if action == "lock" and hasattr(record, "locked_at"):
        record.locked_at = datetime.now(timezone.utc)
    if action == "unlock" and hasattr(record, "locked_at"):
        record.locked_at = None
    if action == "approve" and hasattr(record, "approved_by") and actor_employee:
        record.approved_by = actor_employee.id
    if hasattr(record, "approval_comments") and reason:
        record.approval_comments = reason
    elif hasattr(record, "comments") and reason:
        record.comments = reason

    db.flush()
    after = serialize(record)
    create_audit(
        db,
        user,
        action,
        resource,
        str(record.id),
        f"{action.title()} workflow action on HRM {resource} record",
        before=before,
        after=after,
        sensitivity="restricted" if resource.startswith("payroll") else "internal",
    )
    db.commit()
    db.refresh(record)
    return serialize(record)


def analytics_summary(db: Session) -> dict[str, Any]:
    total_employees = db.query(HRMEmployee).count()
    active_employees = db.query(HRMEmployee).filter(HRMEmployee.employment_status == "active").count()
    pending_leave = db.query(HRMLeave).filter(HRMLeave.status == "pending").count()
    open_requisitions = db.query(HRMJobRequisition).filter(HRMJobRequisition.status.in_(["draft", "pending", "approved"])).count()
    active_courses = db.query(HRMCourse).filter(HRMCourse.status == "active").count()
    assets_assigned = db.query(HRMCompanyAsset).filter(HRMCompanyAsset.status == "assigned").count()
    payroll_runs = db.query(HRMPayrollRun).count()
    return {
        "headcount": {"total": total_employees, "active": active_employees, "inactive": max(total_employees - active_employees, 0)},
        "leave": {"pending_requests": pending_leave},
        "recruitment": {"open_requisitions": open_requisitions},
        "training": {"active_courses": active_courses},
        "assets": {"assigned": assets_assigned},
        "payroll": {"runs": payroll_runs},
    }


def resource_analytics(db: Session, resource: str) -> dict[str, Any]:
    model = model_for(resource)
    query = db.query(model)
    total = query.count()
    by_status: dict[str, int] = {}
    if hasattr(model, "status"):
        for row in db.query(model.status).all():
            status_value = str(row[0] or "unknown")
            by_status[status_value] = by_status.get(status_value, 0) + 1
    return {
        "resource": resource,
        "total": total,
        "active": by_status.get("active", 0),
        "inactive": total - by_status.get("active", 0) if by_status else 0,
        "by_status": by_status,
    }
