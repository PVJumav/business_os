import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.crud import get_or_404
from backend.core.database import get_db
from backend.models.automation import EnterpriseEvent
from backend.models.enterprise import NotificationEvent
from backend.models.hrm import (
    HRMEmployee,
    HRMEmployeeLeaveOfAbsenceRecord,
    HRMEmployeeWorkSchedule,
    HRMHoliday,
    HRMLeave,
    HRMLeaveAuditLog,
    HRMLeaveBalance,
    HRMLeaveBalanceAdjustment,
    HRMLeaveBalanceTransaction,
    HRMLeaveCalendarEvent,
    HRMLeaveCancellationRecord,
    HRMLeaveCarryForwardRecord,
    HRMLeaveEncashment,
    HRMLeaveExtensionRecord,
    HRMLeavePolicy,
    HRMLeavePolicyAssignment,
    HRMLeaveRecallRecord,
    HRMLeaveRequestApproval,
    HRMLeaveRequestDay,
    HRMLeaveType,
)
from backend.schemas.auth import UserResponse
from backend.schemas.hrm.leave import (
    LeaveActionPayload,
    LeaveBalanceAdjustmentPayload,
    LeaveCalculationRequest,
    LeaveCreate,
    LeaveEncashmentPayload,
    LeavePolicyAssignmentPayload,
    LeavePolicyPayload,
    LeaveReportExportPayload,
    LeaveRequestCreate,
    LeaveResponse,
    LeaveUpdate,
    PublicHolidayPayload,
)


router = APIRouter(prefix="/hrm/leave", tags=["HRM Leave"])

ACTIVE_LEAVE_STATUSES = {"Submitted", "Pending Manager Approval", "Pending HR Review", "Approved", "In Progress"}


def _jsonable(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _row(row: Any) -> dict[str, Any]:
    return {column.name: _jsonable(getattr(row, column.name)) for column in row.__table__.columns}


def _require_hr(user: UserResponse) -> None:
    if user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Leave management action requires HR or manager permissions")


def _audit(db: Session, user: UserResponse, leave: HRMLeave | None, employee: HRMEmployee | None, action: str, summary: str, before: Any = None, after: Any = None) -> None:
    db.add(HRMLeaveAuditLog(leave_request_id=getattr(leave, "id", None), employee_id=getattr(employee, "id", None), actor_email=user.email, action=action, summary=summary, before_json=_jsonable(before), after_json=_jsonable(after)))


def _event(db: Session, user: UserResponse, event_type: str, employee: HRMEmployee | None, payload: dict[str, Any]) -> None:
    db.add(EnterpriseEvent(event_type=event_type, source_module="HRM", target_module="Enterprise", payload=_jsonable({"employee_id": getattr(employee, "id", None), **payload}), event_status="pending", created_by=user.full_name))


def _notify(db: Session, user: UserResponse, employee: HRMEmployee, subject: str, body: str) -> None:
    for recipient in ["Employee", "Manager", "HR"]:
        db.add(NotificationEvent(module="HRM", related_entity="Leave", related_id=employee.id, recipient_name=recipient, recipient_email=employee.email if recipient == "Employee" else None, subject=subject, body=body, status="queued", created_by=user.full_name))


def _leave_type_name(db: Session, leave_type_id: UUID | None, fallback: str | None = None) -> str:
    if leave_type_id:
        row = db.query(HRMLeaveType).filter(HRMLeaveType.id == leave_type_id).first()
        if row:
            return row.leave_name
    return fallback or "Annual Leave"


def _resolve_policy(db: Session, employee: HRMEmployee, payload: LeaveCalculationRequest) -> HRMLeavePolicy:
    if payload.policy_id:
        policy = db.query(HRMLeavePolicy).filter(HRMLeavePolicy.id == payload.policy_id).first()
        if policy:
            return policy
    if payload.leave_type_id:
        assignment = db.query(HRMLeavePolicyAssignment).join(HRMLeavePolicy, HRMLeavePolicy.id == HRMLeavePolicyAssignment.policy_id).filter(HRMLeavePolicyAssignment.employee_id == employee.id, HRMLeavePolicy.leave_type_id == payload.leave_type_id, HRMLeavePolicyAssignment.status == "active").order_by(HRMLeavePolicyAssignment.effective_from.desc()).first()
        if assignment:
            return db.query(HRMLeavePolicy).filter(HRMLeavePolicy.id == assignment.policy_id).first()
        policy = db.query(HRMLeavePolicy).filter(HRMLeavePolicy.leave_type_id == payload.leave_type_id, HRMLeavePolicy.status == "active").first()
        if policy:
            return policy
    policy = db.query(HRMLeavePolicy).filter(HRMLeavePolicy.status == "active").first()
    if not policy:
        leave_type = db.query(HRMLeaveType).filter(HRMLeaveType.leave_name == "Annual Leave").first()
        if not leave_type:
            leave_type = HRMLeaveType(leave_code="ANNUAL", leave_name="Annual Leave", paid=True)
            db.add(leave_type)
            db.flush()
        policy = HRMLeavePolicy(policy_name="Default Annual Leave Policy", leave_type_id=leave_type.id, annual_entitlement=Decimal("21"), requires_balance=True, requires_manager_approval=True, requires_hr_review=False)
        db.add(policy)
        db.flush()
    return policy


class LeaveCalculationService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_calendar_days(self, start_date: date, end_date: date) -> int:
        return (end_date - start_date).days + 1

    def resolve_employee_work_schedule(self, employee_id: UUID) -> set[int]:
        row = self.db.query(HRMEmployeeWorkSchedule).filter(or_(HRMEmployeeWorkSchedule.employee_id == employee_id, HRMEmployeeWorkSchedule.employee_id.is_(None)), HRMEmployeeWorkSchedule.status == "active").order_by(HRMEmployeeWorkSchedule.employee_id.desc().nullslast()).first()
        if row and row.working_days:
            return {int(day) for day in row.working_days}
        return {0, 1, 2, 3, 4}

    def resolve_public_holidays(self, employee: HRMEmployee, start_date: date, end_date: date) -> set[date]:
        rows = self.db.query(HRMHoliday).filter(HRMHoliday.holiday_date >= start_date, HRMHoliday.holiday_date <= end_date, HRMHoliday.status == "active").all()
        holidays = set()
        for row in rows:
            country_ok = not row.country or not employee.country or row.country.lower() == employee.country.lower()
            branch_ok = not row.branch or not employee.branch or row.branch.lower() == employee.branch.lower()
            if country_ok and branch_ok:
                holidays.add(row.holiday_date)
        return holidays

    def calculate_leave(self, payload: LeaveCalculationRequest) -> dict[str, Any]:
        employee = get_or_404(self.db, HRMEmployee, payload.employee_id, "Employee")
        if payload.end_date < payload.start_date:
            raise HTTPException(status_code=422, detail="Leave end date cannot be before start date")
        policy = _resolve_policy(self.db, employee, payload)
        calendar_days = self.calculate_calendar_days(payload.start_date, payload.end_date)
        working_days_set = self.resolve_employee_work_schedule(employee.id)
        holidays = self.resolve_public_holidays(employee, payload.start_date, payload.end_date)
        all_dates = [payload.start_date + timedelta(days=index) for index in range(calendar_days)]
        excluded_weekends = 0
        excluded_holidays = 0
        working_dates: list[date] = []
        request_days: list[dict[str, Any]] = []
        for current in all_dates:
            is_working = current.weekday() in working_days_set
            is_holiday = current in holidays
            if not is_working and policy.excludes_weekends:
                excluded_weekends += 1
                request_days.append({"date": current, "day_value": Decimal("0"), "is_working_day": False, "is_public_holiday": is_holiday})
                continue
            if is_holiday and policy.excludes_public_holidays:
                excluded_holidays += 1
                request_days.append({"date": current, "day_value": Decimal("0"), "is_working_day": is_working, "is_public_holiday": True})
                continue
            working_dates.append(current)
            request_days.append({"date": current, "day_value": Decimal("1"), "is_working_day": is_working, "is_public_holiday": is_holiday})
        leave_days = Decimal(len(working_dates))
        if payload.start_date == payload.end_date:
            leave_days = Decimal("1") if payload.start_day_type == "Full Day" else Decimal("0.5")
        else:
            if payload.start_day_type in {"First Half", "Second Half"}:
                leave_days -= Decimal("0.5")
            if payload.end_day_type in {"First Half", "Second Half"}:
                leave_days -= Decimal("0.5")
        leave_days = max(leave_days, Decimal("0.5"))
        return_date = payload.end_date + timedelta(days=1)
        while return_date.weekday() not in working_days_set or return_date in holidays:
            return_date += timedelta(days=1)
        balance_before = self.balance_before(employee.id, _leave_type_name(self.db, payload.leave_type_id, payload.leave_type))
        balance_after = balance_before - leave_days
        payroll = self.payroll_impact(policy, leave_days)
        blocking_errors = []
        validation_messages = []
        if employee.employment_status not in {"active", "probation", "confirmed"}:
            blocking_errors.append("Employee must be active, on probation, or confirmed to apply for leave")
        if payload.start_date < date.today() and not policy.allows_backdating:
            blocking_errors.append("Backdated leave is not allowed by policy")
        if payload.start_day_type != "Full Day" or payload.end_day_type != "Full Day":
            if not policy.allows_half_day:
                blocking_errors.append("Half-day leave is not allowed by policy")
        if policy.requires_balance and balance_after < 0 and not policy.allow_negative_balance:
            blocking_errors.append("Insufficient leave balance")
        if policy.minimum_notice_days and payload.start_date < date.today() + timedelta(days=policy.minimum_notice_days):
            validation_messages.append(f"Minimum notice is {policy.minimum_notice_days} days")
        if self.has_overlap(employee.id, payload.start_date, payload.end_date):
            blocking_errors.append("Leave overlaps an existing active request")
        return {
            "policy_id": str(policy.id),
            "leave_type": _leave_type_name(self.db, payload.leave_type_id, payload.leave_type),
            "calendar_days": calendar_days,
            "working_days": len(working_dates),
            "leave_days": float(leave_days),
            "excluded_weekends": excluded_weekends,
            "excluded_public_holidays": excluded_holidays,
            "return_to_work_date": return_date.isoformat(),
            "balance_before": float(balance_before),
            "balance_after": float(balance_after),
            "payroll_impact": payroll,
            "attendance_impact": {"excluded_dates": [item["date"].isoformat() for item in request_days if item["day_value"] > 0], "sync_required": bool(policy.attendance_exclusion_enabled)},
            "request_days": _jsonable(request_days),
            "validation_messages": validation_messages,
            "blocking_errors": blocking_errors,
        }

    def balance_before(self, employee_id: UUID, leave_type: str) -> Decimal:
        balance = self.db.query(HRMLeaveBalance).filter(HRMLeaveBalance.employee_id == employee_id, HRMLeaveBalance.leave_type == leave_type, HRMLeaveBalance.status == "active").order_by(HRMLeaveBalance.created_at.desc()).first()
        if not balance:
            return Decimal("0")
        return Decimal(str(balance.available_days or 0))

    def has_overlap(self, employee_id: UUID, start_date: date, end_date: date, exclude_id: UUID | None = None) -> bool:
        query = self.db.query(HRMLeave).filter(HRMLeave.employee_id == employee_id, HRMLeave.status.in_(ACTIVE_LEAVE_STATUSES), HRMLeave.start_date <= end_date, HRMLeave.end_date >= start_date)
        if exclude_id:
            query = query.filter(HRMLeave.id != exclude_id)
        return query.first() is not None

    def payroll_impact(self, policy: HRMLeavePolicy, leave_days: Decimal) -> dict[str, Any]:
        paid_percent = Decimal(str(policy.paid_percentage or 0))
        paid_days = leave_days * paid_percent / Decimal("100") if policy.paid_or_unpaid != "unpaid" else Decimal("0")
        unpaid_days = leave_days - paid_days
        return {"paid_days": float(paid_days), "unpaid_days": float(unpaid_days), "payroll_sync_required": bool(policy.payroll_impact_enabled)}


def _ensure_balance(db: Session, employee: HRMEmployee, leave_type: str, opening: Decimal = Decimal("21")) -> HRMLeaveBalance:
    balance = db.query(HRMLeaveBalance).filter(HRMLeaveBalance.employee_id == employee.id, HRMLeaveBalance.leave_type == leave_type, HRMLeaveBalance.fiscal_year == str(date.today().year), HRMLeaveBalance.status == "active").first()
    if not balance:
        balance = HRMLeaveBalance(employee_id=employee.id, leave_type=leave_type, fiscal_year=str(date.today().year), opening_balance=opening, accrued_days=Decimal("0"), used_days=Decimal("0"), adjusted_days=Decimal("0"), available_days=opening, status="active")
        db.add(balance)
        db.flush()
        db.add(HRMLeaveBalanceTransaction(employee_id=employee.id, leave_type=leave_type, transaction_type="Opening Balance", amount=opening, balance_before=Decimal("0"), balance_after=opening, reason="System initialized leave balance"))
    return balance


def _apply_balance(db: Session, employee: HRMEmployee, leave_type: str, request: HRMLeave | None, amount: Decimal, transaction_type: str, reason: str, user: UserResponse) -> None:
    balance = _ensure_balance(db, employee, leave_type)
    before = Decimal(str(balance.available_days or 0))
    after = before + amount
    balance.available_days = after
    if amount < 0:
        balance.used_days = Decimal(str(balance.used_days or 0)) + abs(amount)
    else:
        balance.adjusted_days = Decimal(str(balance.adjusted_days or 0)) + amount
    db.add(HRMLeaveBalanceTransaction(employee_id=employee.id, leave_type=leave_type, leave_request_id=getattr(request, "id", None), transaction_type=transaction_type, amount=amount, balance_before=before, balance_after=after, reason=reason, created_by=user.full_name))


@router.post("/calculate")
def calculate_leave(payload: LeaveCalculationRequest, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return LeaveCalculationService(db).calculate_leave(payload)


@router.post("/requests", status_code=status.HTTP_201_CREATED)
def create_leave_request(payload: LeaveRequestCreate, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, payload.employee_id, "Employee")
    result = LeaveCalculationService(db).calculate_leave(payload)
    if result["blocking_errors"]:
        raise HTTPException(status_code=422, detail=result["blocking_errors"])
    leave_type = result["leave_type"]
    request = HRMLeave(employee_id=employee.id, leave_type_id=payload.leave_type_id, policy_id=UUID(result["policy_id"]), leave_type=leave_type, start_date=payload.start_date, end_date=payload.end_date, start_day_type=payload.start_day_type, end_day_type=payload.end_day_type, calendar_days=Decimal(str(result["calendar_days"])), working_days=Decimal(str(result["working_days"])), leave_days=Decimal(str(result["leave_days"])), excluded_weekends_count=result["excluded_weekends"], excluded_public_holidays_count=result["excluded_public_holidays"], return_to_work_date=date.fromisoformat(result["return_to_work_date"]), total_days=Decimal(str(result["leave_days"])), reason=payload.reason, supporting_document_id=payload.supporting_document_id, status="Submitted" if payload.submit else "Draft", submitted_at=datetime.utcnow() if payload.submit else None, current_approver_id=employee.supervisor_id, created_by=user.full_name, payroll_impact=result["payroll_impact"], attendance_impact=result["attendance_impact"])
    db.add(request)
    db.flush()
    for item in result["request_days"]:
        db.add(HRMLeaveRequestDay(leave_request_id=request.id, employee_id=employee.id, leave_date=date.fromisoformat(item["date"]), day_value=Decimal(str(item["day_value"])), is_working_day=item["is_working_day"], is_public_holiday=item["is_public_holiday"]))
    if payload.submit:
        db.add(HRMLeaveRequestApproval(leave_request_id=request.id, employee_id=employee.id, approval_step="Manager Approval", approver_id=employee.supervisor_id, approval_status="Pending"))
    _audit(db, user, request, employee, "LEV-001_TO_008_LEAVE_REQUEST_CREATED", "Leave request created.", after=_row(request))
    _event(db, user, "leave.request.created", employee, {"leave_request_id": request.id, "leave_type": leave_type})
    _notify(db, user, employee, "Leave request submitted", f"{leave_type} request submitted for {result['leave_days']} days.")
    db.commit()
    db.refresh(request)
    return _row(request)


@router.get("/requests")
def list_leave_requests(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMLeave).order_by(HRMLeave.created_at.desc()).all()]


@router.get("/requests/{leave_id:uuid}")
def get_leave_request(leave_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    return _row(request) | {"approvals": [_row(row) for row in db.query(HRMLeaveRequestApproval).filter(HRMLeaveRequestApproval.leave_request_id == request.id).all()], "days": [_row(row) for row in db.query(HRMLeaveRequestDay).filter(HRMLeaveRequestDay.leave_request_id == request.id).all()]}


def _approve_leave(db: Session, request: HRMLeave, employee: HRMEmployee, user: UserResponse, status_value: str, action: str, comments: str | None = None) -> dict[str, Any]:
    before = _row(request)
    request.status = status_value
    request.approval_comments = comments
    if status_value == "Approved":
        request.approved_at = datetime.utcnow()
        request.approved_by = None
        request.attendance_sync_status = "queued"
        request.payroll_sync_status = "queued"
        _apply_balance(db, employee, request.leave_type, request, Decimal(str(request.leave_days or request.total_days or 0)) * Decimal("-1"), "Leave Deduction", "Approved leave deduction", user)
        db.add(HRMLeaveCalendarEvent(leave_request_id=request.id, employee_id=employee.id, event_type="leave", title=f"{request.leave_type} - {employee.first_name} {employee.last_name}", start_date=request.start_date, end_date=request.end_date, visibility="team"))
        if request.leave_type.lower() == "leave of absence":
            employee.employment_status = "leave_of_absence"
            db.add(HRMEmployeeLeaveOfAbsenceRecord(employee_id=employee.id, leave_type=request.leave_type, start_date=request.start_date, expected_return_date=request.return_to_work_date or request.end_date, reason=request.reason or "Approved leave of absence", created_by=user.full_name))
    _audit(db, user, request, employee, action, f"Leave request {status_value}.", before, _row(request))
    _event(db, user, f"leave.request.{status_value.lower().replace(' ', '_')}", employee, {"leave_request_id": request.id})
    _notify(db, user, employee, f"Leave {status_value}", comments or f"Leave request is now {status_value}.")
    db.commit()
    return _row(request)


@router.post("/requests/{leave_id:uuid}/submit")
def submit_leave(leave_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    employee = get_or_404(db, HRMEmployee, request.employee_id, "Employee")
    request.status = "Submitted"
    request.submitted_at = datetime.utcnow()
    db.add(HRMLeaveRequestApproval(leave_request_id=request.id, employee_id=employee.id, approval_step="Manager Approval", approver_id=employee.supervisor_id, approval_status="Pending"))
    _audit(db, user, request, employee, "LEV_SUBMIT", "Leave request submitted.", after=_row(request))
    _event(db, user, "leave.request.submitted", employee, {"leave_request_id": request.id})
    db.commit()
    return _row(request)


@router.post("/requests/{leave_id:uuid}/approve")
def manager_approve_leave(leave_id: UUID, payload: LeaveActionPayload = Body(default_factory=LeaveActionPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    employee = get_or_404(db, HRMEmployee, request.employee_id, "Employee")
    policy = _resolve_policy(db, employee, LeaveCalculationRequest(employee_id=employee.id, leave_type_id=request.leave_type_id, leave_type=request.leave_type, policy_id=request.policy_id, start_date=request.start_date, end_date=request.end_date, start_day_type=request.start_day_type, end_day_type=request.end_day_type))
    approval = db.query(HRMLeaveRequestApproval).filter(HRMLeaveRequestApproval.leave_request_id == request.id, HRMLeaveRequestApproval.approval_step == "Manager Approval").first()
    if approval:
        approval.approval_status = "Approved"
        approval.comments = payload.comments
        approval.approver_name = user.full_name
        approval.decided_at = datetime.utcnow()
    if policy.requires_hr_review:
        request.status = "Pending HR Review"
        db.add(HRMLeaveRequestApproval(leave_request_id=request.id, employee_id=employee.id, approval_step="HR Review", approval_status="Pending"))
        _audit(db, user, request, employee, "LEV-010_MANAGER_APPROVED", "Manager approved leave; HR review pending.", after=_row(request))
        db.commit()
        return _row(request)
    return _approve_leave(db, request, employee, user, "Approved", "LEV-010_MANAGER_APPROVED", payload.comments)


@router.post("/requests/{leave_id:uuid}/hr-review")
def hr_review_leave(leave_id: UUID, payload: LeaveActionPayload = Body(default_factory=LeaveActionPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    if user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="HR review requires HR permissions")
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    employee = get_or_404(db, HRMEmployee, request.employee_id, "Employee")
    approval = db.query(HRMLeaveRequestApproval).filter(HRMLeaveRequestApproval.leave_request_id == request.id, HRMLeaveRequestApproval.approval_step == "HR Review").first()
    if approval:
        approval.approval_status = "Approved"
        approval.approver_name = user.full_name
        approval.comments = payload.comments
        approval.decided_at = datetime.utcnow()
    return _approve_leave(db, request, employee, user, "Approved", "LEV-011_HR_REVIEW_APPROVED", payload.comments)


@router.post("/requests/{leave_id:uuid}/reject")
def reject_leave(leave_id: UUID, payload: LeaveActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    if not payload.reason:
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    employee = get_or_404(db, HRMEmployee, request.employee_id, "Employee")
    before = _row(request)
    request.status = "Rejected"
    request.rejected_at = datetime.utcnow()
    request.approval_comments = payload.reason
    _audit(db, user, request, employee, "LEV-012_LEAVE_REJECTED", "Leave request rejected.", before, _row(request))
    _event(db, user, "leave.request.rejected", employee, {"leave_request_id": request.id, "reason": payload.reason})
    _notify(db, user, employee, "Leave rejected", payload.reason)
    db.commit()
    return _row(request)


@router.post("/requests/{leave_id:uuid}/cancel")
def cancel_leave(leave_id: UUID, payload: LeaveActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    employee = get_or_404(db, HRMEmployee, request.employee_id, "Employee")
    if request.payroll_lock_status == "locked":
        raise HTTPException(status_code=423, detail="Cannot cancel after payroll lock")
    before = _row(request)
    if request.status == "Approved":
        _apply_balance(db, employee, request.leave_type, request, Decimal(str(request.leave_days or request.total_days or 0)), "Leave Reversal", "Leave cancellation reversal", user)
    request.status = "Cancelled"
    request.cancelled_at = datetime.utcnow()
    db.add(HRMLeaveCancellationRecord(leave_request_id=request.id, employee_id=employee.id, reason=payload.reason or "Cancelled", cancelled_by=user.full_name))
    _audit(db, user, request, employee, "LEV-009_LEAVE_CANCELLED", "Leave request cancelled.", before, _row(request))
    _event(db, user, "leave.request.cancelled", employee, {"leave_request_id": request.id})
    db.commit()
    return _row(request)


@router.post("/requests/{leave_id:uuid}/recall")
def recall_leave(leave_id: UUID, payload: LeaveActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    employee = get_or_404(db, HRMEmployee, request.employee_id, "Employee")
    if not payload.recall_date or not payload.reason:
        raise HTTPException(status_code=422, detail="Recall date and reason are required")
    if payload.recall_date < request.start_date or payload.recall_date > request.end_date:
        raise HTTPException(status_code=422, detail="Recall date must fall within leave period")
    used = LeaveCalculationService(db).calculate_leave(LeaveCalculationRequest(employee_id=employee.id, leave_type_id=request.leave_type_id, leave_type=request.leave_type, policy_id=request.policy_id, start_date=request.start_date, end_date=payload.recall_date))["leave_days"]
    restored = Decimal(str(request.leave_days or request.total_days or 0)) - Decimal(str(used))
    request.status = "Recalled"
    db.add(HRMLeaveRecallRecord(leave_request_id=request.id, employee_id=employee.id, recall_date=payload.recall_date, used_days=Decimal(str(used)), restored_days=restored, reason=payload.reason, recalled_by=user.full_name))
    if restored > 0:
        _apply_balance(db, employee, request.leave_type, request, restored, "Recall Restoration", payload.reason, user)
    _audit(db, user, request, employee, "LEV-013_LEAVE_RECALLED", "Employee recalled from leave.", after={"restored_days": restored})
    _event(db, user, "leave.request.recalled", employee, {"leave_request_id": request.id, "restored_days": restored})
    db.commit()
    return _row(request)


@router.post("/requests/{leave_id:uuid}/extend")
def extend_leave(leave_id: UUID, payload: LeaveActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    request = get_or_404(db, HRMLeave, leave_id, "Leave request")
    employee = get_or_404(db, HRMEmployee, request.employee_id, "Employee")
    if not payload.new_end_date or not payload.reason:
        raise HTTPException(status_code=422, detail="New end date and reason are required")
    if payload.new_end_date <= request.end_date:
        raise HTTPException(status_code=422, detail="New end date must be after current end date")
    result = LeaveCalculationService(db).calculate_leave(LeaveCalculationRequest(employee_id=employee.id, leave_type_id=request.leave_type_id, leave_type=request.leave_type, policy_id=request.policy_id, start_date=request.end_date + timedelta(days=1), end_date=payload.new_end_date))
    if result["blocking_errors"]:
        raise HTTPException(status_code=422, detail=result["blocking_errors"])
    old_end = request.end_date
    additional = Decimal(str(result["leave_days"]))
    request.end_date = payload.new_end_date
    request.leave_days = Decimal(str(request.leave_days or request.total_days or 0)) + additional
    request.total_days = request.leave_days
    request.status = "Extended"
    db.add(HRMLeaveExtensionRecord(leave_request_id=request.id, employee_id=employee.id, old_end_date=old_end, new_end_date=payload.new_end_date, additional_days=additional, reason=payload.reason, created_by=user.full_name))
    _apply_balance(db, employee, request.leave_type, request, additional * Decimal("-1"), "Extension Deduction", payload.reason, user)
    _audit(db, user, request, employee, "LEV-014_LEAVE_EXTENDED", "Leave request extended.", after=_row(request))
    _event(db, user, "leave.request.extended", employee, {"leave_request_id": request.id, "additional_days": additional})
    db.commit()
    return _row(request)


@router.get("/balances/{employee_id:uuid}")
def get_leave_balances(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    balances = db.query(HRMLeaveBalance).filter(HRMLeaveBalance.employee_id == employee.id).all()
    transactions = db.query(HRMLeaveBalanceTransaction).filter(HRMLeaveBalanceTransaction.employee_id == employee.id).order_by(HRMLeaveBalanceTransaction.created_at.desc()).limit(100).all()
    return {"balances": [_row(row) for row in balances], "transactions": [_row(row) for row in transactions]}


@router.post("/balances/{employee_id:uuid}/adjust")
def adjust_leave_balance(employee_id: UUID, payload: LeaveBalanceAdjustmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Leave balance adjustment requires HR admin")
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    db.add(HRMLeaveBalanceAdjustment(employee_id=employee.id, leave_type=payload.leave_type, adjustment_amount=payload.adjustment_amount, effective_date=payload.effective_date, reason=payload.reason, created_by=user.full_name))
    _apply_balance(db, employee, payload.leave_type, None, payload.adjustment_amount, "Adjustment", payload.reason, user)
    _audit(db, user, None, employee, "LEV-016_BALANCE_ADJUSTED", "Leave balance adjusted.", after=payload.model_dump())
    _event(db, user, "leave.balance.adjusted", employee, payload.model_dump())
    db.commit()
    return get_leave_balances(employee.id, db, user)


@router.post("/carry-forward/run")
def run_carry_forward(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Carry-forward requires HR admin")
    records = []
    for balance in db.query(HRMLeaveBalance).filter(HRMLeaveBalance.status == "active").all():
        employee = get_or_404(db, HRMEmployee, balance.employee_id, "Employee")
        policy = db.query(HRMLeavePolicy).filter(HRMLeavePolicy.status == "active").first()
        limit = Decimal(str(getattr(policy, "carry_forward_limit", 0) or 0))
        unused = Decimal(str(balance.available_days or 0))
        carried = min(unused, limit) if getattr(policy, "carry_forward_allowed", False) else Decimal("0")
        expired = max(unused - carried, Decimal("0"))
        record = HRMLeaveCarryForwardRecord(employee_id=balance.employee_id, leave_type=balance.leave_type, from_cycle=balance.fiscal_year, to_cycle=str(date.today().year + 1), carried_forward_days=carried, expired_days=expired, expiry_date=date.today() + timedelta(days=365), created_by=user.full_name)
        db.add(record)
        records.append(record)
        _event(db, user, "leave.balance.carried_forward", employee, {"leave_type": balance.leave_type, "carried": carried, "expired": expired})
    db.commit()
    return [_row(row) for row in records]


@router.post("/encashments")
def create_encashment(payload: LeaveEncashmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, payload.employee_id, "Employee")
    balance = _ensure_balance(db, employee, payload.leave_type)
    if Decimal(str(balance.available_days or 0)) < payload.encashed_days:
        raise HTTPException(status_code=422, detail="Encashment exceeds available balance")
    daily_rate = Decimal(str(employee.base_salary or 0)) / Decimal("22") if employee.base_salary else Decimal("0")
    amount = payload.encashed_days * daily_rate
    record = HRMLeaveEncashment(employee_id=employee.id, leave_type=payload.leave_type, encashed_days=payload.encashed_days, daily_rate=daily_rate, encashment_amount=amount, reason=payload.reason, created_by=user.full_name)
    db.add(record)
    _apply_balance(db, employee, payload.leave_type, None, payload.encashed_days * Decimal("-1"), "Encashment", payload.reason or "Leave encashment", user)
    _audit(db, user, None, employee, "LEV-018_LEAVE_ENCASHED", "Leave encashment approved.", after=_row(record))
    _event(db, user, "leave.encashment.approved", employee, _row(record))
    db.commit()
    return _row(record)


@router.get("/calendar")
def leave_calendar(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    leave_events = db.query(HRMLeaveCalendarEvent).order_by(HRMLeaveCalendarEvent.start_date.asc()).all()
    holidays = db.query(HRMHoliday).filter(HRMHoliday.status == "active").order_by(HRMHoliday.holiday_date.asc()).all()
    return {"leave": [_row(row) for row in leave_events], "public_holidays": [_row(row) for row in holidays]}


@router.get("/reports")
def leave_reports(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    requests = db.query(HRMLeave).all()
    pending = [row for row in requests if row.status in {"Submitted", "Pending Manager Approval", "Pending HR Review"}]
    approved = [row for row in requests if row.status in {"Approved", "In Progress", "Completed"}]
    unpaid = [row for row in requests if (row.payroll_impact or {}).get("unpaid_days", 0)]
    return {"pending_approvals": len(pending), "approved_requests": len(approved), "unpaid_leave_requests": len(unpaid), "leave_liability_days": sum(float(row.available_days or 0) for row in db.query(HRMLeaveBalance).all()), "requests": [_row(row) for row in requests[:200]]}


@router.post("/reports/export")
def export_leave_reports(payload: LeaveReportExportPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    rows = [_row(row) for row in db.query(HRMLeave).order_by(HRMLeave.created_at.desc()).all()]
    output = io.StringIO()
    columns = ["id", "employee_id", "leave_type", "start_date", "end_date", "leave_days", "status"]
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=leave-report.csv"})


@router.get("/policies")
def list_leave_policies(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMLeavePolicy).order_by(HRMLeavePolicy.created_at.desc()).all()]


@router.post("/policies", status_code=status.HTTP_201_CREATED)
def create_leave_policy(payload: LeavePolicyPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    row = HRMLeavePolicy(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row(row)


@router.put("/policies/{policy_id:uuid}")
def update_leave_policy(policy_id: UUID, payload: LeavePolicyPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    row = get_or_404(db, HRMLeavePolicy, policy_id, "Leave policy")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return _row(row)


@router.post("/policies/{policy_id:uuid}/assign")
def assign_leave_policy(policy_id: UUID, payload: LeavePolicyAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, payload.employee_id, "Employee")
    policy = get_or_404(db, HRMLeavePolicy, policy_id, "Leave policy")
    assignment = HRMLeavePolicyAssignment(employee_id=employee.id, policy_id=policy.id, effective_from=payload.effective_from, effective_to=payload.effective_to, assignment_reason=payload.assignment_reason, assigned_by=user.full_name)
    db.add(assignment)
    leave_type = _leave_type_name(db, policy.leave_type_id)
    _ensure_balance(db, employee, leave_type, Decimal(str(policy.annual_entitlement or 0)))
    _audit(db, user, None, employee, "LEV-022_POLICY_ASSIGNED", "Leave policy assigned.", after=_row(assignment))
    _event(db, user, "leave.policy.assigned", employee, _row(assignment))
    db.commit()
    return _row(assignment)


@router.get("/public-holidays")
def list_public_holidays(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMHoliday).order_by(HRMHoliday.holiday_date.desc()).all()]


@router.post("/public-holidays", status_code=status.HTTP_201_CREATED)
def create_public_holiday(payload: PublicHolidayPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    duplicate = db.query(HRMHoliday).filter(HRMHoliday.holiday_date == payload.holiday_date, HRMHoliday.country == payload.country, HRMHoliday.branch == payload.branch).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Public holiday already exists in this scope")
    row = HRMHoliday(**payload.model_dump())
    db.add(row)
    _event(db, user, "public.holiday.created", None, payload.model_dump())
    db.commit()
    return _row(row)


@router.put("/public-holidays/{holiday_id:uuid}")
def update_public_holiday(holiday_id: UUID, payload: PublicHolidayPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    row = get_or_404(db, HRMHoliday, holiday_id, "Public holiday")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return _row(row)


@router.delete("/public-holidays/{holiday_id:uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_public_holiday(holiday_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    row = get_or_404(db, HRMHoliday, holiday_id, "Public holiday")
    row.status = "deleted"
    db.commit()
    return None


# Backward-compatible legacy endpoints.
@router.post("", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def create_leave(leave: LeaveCreate, db: Session = Depends(get_db)):
    row = HRMLeave(**leave.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=List[LeaveResponse])
def get_leave_records(db: Session = Depends(get_db)):
    return db.query(HRMLeave).order_by(HRMLeave.created_at.desc()).all()


@router.get("/{leave_id:uuid}", response_model=LeaveResponse)
def get_leave(leave_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, HRMLeave, leave_id, "Leave record")


@router.put("/{leave_id:uuid}", response_model=LeaveResponse)
def update_leave(leave_id: UUID, leave_update: LeaveUpdate, db: Session = Depends(get_db)):
    leave = get_or_404(db, HRMLeave, leave_id, "Leave record")
    for field, value in leave_update.model_dump(exclude_unset=True).items():
        setattr(leave, field, value)
    db.commit()
    db.refresh(leave)
    return leave


@router.delete("/{leave_id:uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave(leave_id: UUID, db: Session = Depends(get_db)):
    leave = get_or_404(db, HRMLeave, leave_id, "Leave record")
    leave.status = "Cancelled"
    db.commit()
    return None
