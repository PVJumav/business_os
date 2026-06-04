from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.automation import AuditLog, EnterpriseEvent
from backend.models.finance import FinanceCostCenter
from backend.models.hrm import (
    HRMAuditLog,
    HRMCostCenter,
    HRMEmployee,
    HRMEmployeeEmploymentHistory,
    HRMEmployeeEmploymentInfo,
    HRMEmployeeManagerAssignment,
    HRMEmploymentApproval,
    HRMEmploymentAuditLog,
    HRMEmploymentChangeRequest,
    HRMJobGrade,
    HRMJobTitle,
    HRMPosition,
    HRMSalaryBand,
)
from backend.policies.hrm import is_admin, is_hr, is_payroll
from backend.schemas.auth import UserResponse
from backend.schemas.hrm.employment_info import (
    EmploymentApprovalPayload,
    EmploymentChangePayload,
    EmploymentRejectPayload,
    ManagerChangePayload,
)


router = APIRouter(prefix="/hrm/employment-info", tags=["HRM Employment Information"])

BLOCKED_EMPLOYEE_STATUSES = {"draft", "rejected", "archived", "exited", "blacklisted", "terminated", "inactive"}
SENSITIVE_FIELDS = {"job_grade", "salary_band", "cost_center"}
FIELD_ATTRS = {
    "job_title": "job_title",
    "job_grade": "salary_grade",
    "salary_band": "salary_band",
    "cost_center": "cost_center_code",
    "reporting_manager": "supervisor_id",
    "functional_manager": "functional_manager_id",
}
BUC_RULES = {
    "EMP-019": {"field": "job_title", "approval": False, "event": "EmployeeJobTitleAssigned"},
    "EMP-020": {"field": "job_title", "approval": "conditional", "event": "EmployeeJobTitleChanged"},
    "EMP-021": {"field": "job_grade", "approval": True, "event": "EmployeeJobGradeAssigned"},
    "EMP-022": {"field": "job_grade", "approval": True, "event": "EmployeeJobGradeChanged"},
    "EMP-023": {"field": "salary_band", "approval": True, "event": "EmployeeSalaryBandAssigned"},
    "EMP-024": {"field": "salary_band", "approval": True, "event": "EmployeeSalaryBandUpdated"},
    "EMP-025": {"field": "cost_center", "approval": True, "event": "EmployeeCostCenterAssigned"},
    "EMP-026": {"field": "cost_center", "approval": True, "event": "EmployeeCostCenterChanged"},
    "EMP-027": {"field": "reporting_manager", "approval": False, "event": "EmployeeReportingManagerAssigned"},
    "EMP-028": {"field": "reporting_manager", "approval": "conditional", "event": "EmployeeReportingManagerChanged"},
    "EMP-029": {"field": "functional_manager", "approval": False, "event": "EmployeeFunctionalManagerAssigned"},
    "EMP-030": {"field": "functional_manager", "approval": "conditional", "event": "EmployeeFunctionalManagerChanged"},
}


def _require_employment_access(user: UserResponse, sensitive: bool = False, approval: bool = False):
    if is_admin(user):
        return
    if approval and is_hr(user):
        return
    if sensitive and (is_hr(user) or is_payroll(user)):
        return
    if not sensitive and is_hr(user):
        return
    raise HTTPException(status_code=403, detail="You do not have permission for this employment information action")


def _salary_visible(user: UserResponse) -> bool:
    return is_admin(user) or is_hr(user) or is_payroll(user)


def _serialize(record) -> dict[str, Any] | None:
    if not record:
        return None
    result = {}
    for column in record.__table__.columns:
        value = getattr(record, column.name)
        if isinstance(value, (date, datetime)):
            value = value.isoformat()
        elif isinstance(value, UUID):
            value = str(value)
        result[column.name] = value
    return result


def _employee(db: Session, employee_id: UUID) -> HRMEmployee:
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.employment_status in BLOCKED_EMPLOYEE_STATUSES:
        raise HTTPException(status_code=422, detail="Employment information cannot be assigned to this employee status")
    return employee


def _current_value(employee: HRMEmployee, field_type: str) -> str | None:
    value = getattr(employee, FIELD_ATTRS[field_type], None)
    return str(value) if value else None


def _ensure_info(db: Session, employee: HRMEmployee) -> HRMEmployeeEmploymentInfo:
    info = db.query(HRMEmployeeEmploymentInfo).filter(HRMEmployeeEmploymentInfo.employee_id == employee.id).first()
    if not info:
        info = HRMEmployeeEmploymentInfo(employee_id=employee.id)
        db.add(info)
        db.flush()
    return info


def _validate_master(db: Session, employee: HRMEmployee, field_type: str, new_value: str):
    if field_type == "job_title":
        title = db.query(HRMJobTitle).filter(HRMJobTitle.title_name.ilike(new_value), HRMJobTitle.status == "active").first()
        position = db.query(HRMPosition).filter(HRMPosition.position_title.ilike(new_value), HRMPosition.status == "active").first()
        if not title and not position:
            raise HTTPException(status_code=422, detail="Job title must exist in the approved job title or position master list")
        department = (title.department if title else position.department) or employee.department
        if department and employee.department and department.lower() != employee.department.lower():
            raise HTTPException(status_code=422, detail="Job title must belong to the employee department or function")
    if field_type == "job_grade":
        if not employee.job_title:
            raise HTTPException(status_code=422, detail="Employee must have a job title before job grade assignment")
        grade = db.query(HRMJobGrade).filter(or_(HRMJobGrade.grade_code.ilike(new_value), HRMJobGrade.grade_name.ilike(new_value)), HRMJobGrade.status == "active").first()
        if not grade:
            raise HTTPException(status_code=422, detail="Job grade must exist in the approved grade structure")
    if field_type == "salary_band":
        if not employee.salary_grade:
            raise HTTPException(status_code=422, detail="Employee must have a job grade before salary band assignment")
        band = db.query(HRMSalaryBand).filter(or_(HRMSalaryBand.band_code.ilike(new_value), HRMSalaryBand.band_name.ilike(new_value)), HRMSalaryBand.status == "active").first()
        if not band:
            raise HTTPException(status_code=422, detail="Salary band must exist in the approved salary band structure")
        if band.grade_code and employee.salary_grade and band.grade_code.lower() != employee.salary_grade.lower():
            raise HTTPException(status_code=422, detail="Salary band is not compatible with the employee job grade")
    if field_type == "cost_center":
        hrm_cc = db.query(HRMCostCenter).filter(HRMCostCenter.cost_center_code.ilike(new_value), HRMCostCenter.status == "active").first()
        finance_cc = db.query(FinanceCostCenter).filter(FinanceCostCenter.cost_center_code.ilike(new_value), FinanceCostCenter.status == "active").first()
        if not hrm_cc and not finance_cc:
            raise HTTPException(status_code=422, detail="Cost center must exist and be active in HRM or Finance master data")


def _manager(db: Session, employee: HRMEmployee, manager_id: UUID, field_type: str) -> HRMEmployee:
    if employee.id == manager_id:
        raise HTTPException(status_code=422, detail="Employee cannot be assigned as their own manager")
    manager = db.query(HRMEmployee).filter(HRMEmployee.id == manager_id).first()
    if not manager or manager.employment_status not in {"active", "probation", "on_leave"}:
        raise HTTPException(status_code=422, detail="Manager must be an active employee")
    if field_type == "reporting_manager" and _creates_cycle(db, employee.id, manager_id):
        raise HTTPException(status_code=422, detail="Circular reporting relationship is not allowed")
    return manager


def _creates_cycle(db: Session, employee_id: UUID, manager_id: UUID) -> bool:
    seen = {str(employee_id)}
    current = manager_id
    while current:
        if str(current) in seen:
            return True
        seen.add(str(current))
        manager = db.query(HRMEmployee).filter(HRMEmployee.id == current).first()
        current = manager.supervisor_id if manager else None
    return False


def _approval_required(buc_code: str, effective_date: date) -> bool:
    rule = BUC_RULES[buc_code]["approval"]
    if rule is True:
        return True
    if rule == "conditional":
        return effective_date < date.today()
    return effective_date > date.today()


def _audit(db: Session, user: UserResponse, employee: HRMEmployee, buc_code: str, action: str, previous: str | None, new: str, reason: str, request_id: UUID | None = None):
    payload = {"buc_code": buc_code, "employee_id": str(employee.id), "previous_value": previous, "new_value": new, "reason": reason, "request_id": str(request_id) if request_id else None}
    db.add(HRMEmploymentAuditLog(actor_email=user.email, employee_id=employee.id, buc_code=buc_code, action=action, previous_value=previous, new_value=new, approval_reference=request_id, reason=reason, metadata_json=payload))
    db.add(HRMAuditLog(actor_user_id=user.id if isinstance(user.id, UUID) else None, actor_email=user.email, action=f"{buc_code}_{action}", entity_type="HRMEmploymentInfo", entity_id=str(employee.id), sensitivity="restricted" if BUC_RULES[buc_code]["field"] in SENSITIVE_FIELDS else "internal", summary=f"{buc_code} {action} for {employee.employee_code}", before_json={"value": previous}, after_json={"value": new, "request_id": str(request_id) if request_id else None}))
    db.add(AuditLog(user_email=user.email, module="HRM", action=f"{buc_code}_{action}", entity_type="HRMEmploymentInfo", entity_id=employee.id, old_value={"value": previous}, new_value={"value": new, "request_id": str(request_id) if request_id else None}, result="success", created_by=user.full_name))


def _notify_and_event(db: Session, employee: HRMEmployee, user: UserResponse, buc_code: str, field_type: str, new_value: str, status_value: str):
    db.add(EnterpriseEvent(event_type=BUC_RULES[buc_code]["event"], source_module="HRM", target_module="Enterprise", payload={"employee_id": str(employee.id), "employee_code": employee.employee_code, "field_type": field_type, "new_value": new_value, "status": status_value}, status="pending", created_by=user.full_name))
    for target in ["IAM", "Payroll", "Finance", "Projects", "Analytics"]:
        db.add(EnterpriseEvent(event_type=f"{BUC_RULES[buc_code]['event']}SyncRequested", source_module="HRM", target_module=target, payload={"employee_id": str(employee.id), "field_type": field_type, "new_value": new_value}, status="pending", created_by=user.full_name))


def _close_active_history(db: Session, employee: HRMEmployee, field_type: str, effective_date: date):
    active_rows = db.query(HRMEmployeeEmploymentHistory).filter(HRMEmployeeEmploymentHistory.employee_id == employee.id, HRMEmployeeEmploymentHistory.field_type == field_type, HRMEmployeeEmploymentHistory.status == "active").all()
    for row in active_rows:
        row.status = "closed"
        row.effective_to = effective_date


def _apply_change(db: Session, employee: HRMEmployee, request: HRMEmploymentChangeRequest, user: UserResponse):
    field_type = request.field_type
    _close_active_history(db, employee, field_type, request.effective_date)
    attr = FIELD_ATTRS[field_type]
    if field_type in {"reporting_manager", "functional_manager"}:
        setattr(employee, attr, UUID(request.new_value))
        if field_type == "functional_manager":
            employee.functional_manager_scope = request.authority_scope
        assignment = HRMEmployeeManagerAssignment(employee_id=employee.id, manager_id=UUID(request.new_value), manager_type=field_type, authority_scope=request.authority_scope, effective_from=request.effective_date, status="active", reason=request.reason, initiated_by=request.requested_by, approved_by=request.approved_by, approval_date=request.approval_date)
        db.add(assignment)
    else:
        setattr(employee, attr, request.new_value)
        if field_type == "job_title":
            info_department = employee.department
            employee.job_title = request.new_value
            if info_department:
                employee.department = info_department
    info = _ensure_info(db, employee)
    info.job_title = employee.job_title
    info.job_grade = employee.salary_grade
    info.salary_band = employee.salary_band
    info.cost_center_code = employee.cost_center_code
    info.reporting_manager_id = employee.supervisor_id
    info.functional_manager_id = employee.functional_manager_id
    info.functional_manager_scope = employee.functional_manager_scope
    info.effective_from = request.effective_date
    info.updated_by = user.full_name
    history = HRMEmployeeEmploymentHistory(employee_id=employee.id, buc_code=request.buc_code, field_type=field_type, previous_value=request.previous_value, new_value=request.new_value, effective_from=request.effective_date, status="active", reason=request.reason, supporting_document_url=request.supporting_document_url, initiated_by=request.requested_by, approved_by=request.approved_by or user.full_name, approval_date=request.approval_date or datetime.utcnow(), audit_trail_reference=str(request.id))
    db.add(history)
    request.applied_at = datetime.utcnow()
    request.approval_status = "active"
    _notify_and_event(db, employee, user, request.buc_code, field_type, request.new_value, "active")


def _initiate_change(db: Session, employee_id: UUID, buc_code: str, payload: EmploymentChangePayload | ManagerChangePayload, user: UserResponse):
    field_type = BUC_RULES[buc_code]["field"]
    _require_employment_access(user, sensitive=field_type in SENSITIVE_FIELDS)
    employee = _employee(db, employee_id)
    new_value = str(payload.manager_id) if isinstance(payload, ManagerChangePayload) else payload.new_value.strip()
    previous = _current_value(employee, field_type)
    if previous and previous.lower() == new_value.lower():
        raise HTTPException(status_code=409, detail="New value must be different from current value")
    if field_type in {"job_title", "job_grade", "salary_band", "cost_center"}:
        _validate_master(db, employee, field_type, new_value)
    if field_type in {"reporting_manager", "functional_manager"} and isinstance(payload, ManagerChangePayload):
        _manager(db, employee, payload.manager_id, field_type)
    if buc_code in {"EMP-020", "EMP-022", "EMP-024", "EMP-026", "EMP-028", "EMP-030"} and not previous:
        raise HTTPException(status_code=422, detail="Previous value must exist before this change use case")
    duplicate = db.query(HRMEmploymentChangeRequest).filter(HRMEmploymentChangeRequest.employee_id == employee.id, HRMEmploymentChangeRequest.field_type == field_type, HRMEmploymentChangeRequest.approval_status.in_(["pending", "approved", "future_pending"])).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="A pending or future-dated change already exists for this employment category")
    request = HRMEmploymentChangeRequest(employee_id=employee.id, buc_code=buc_code, field_type=field_type, previous_value=previous, new_value=new_value, effective_date=payload.effective_date, reason=payload.reason, supporting_document_url=payload.supporting_document_url, authority_scope=getattr(payload, "authority_scope", None), requested_by=user.full_name)
    db.add(request)
    db.flush()
    needs_approval = _approval_required(buc_code, payload.effective_date)
    if needs_approval:
        request.approval_status = "pending"
        role = "Finance Approver" if field_type in {"cost_center", "salary_band"} else "HR Manager"
        db.add(HRMEmploymentApproval(request_id=request.id, approver_role=role))
        _audit(db, user, employee, buc_code, "REQUESTED", previous, new_value, payload.reason, request.id)
        _notify_and_event(db, employee, user, buc_code, field_type, new_value, "pending")
    elif payload.effective_date > date.today():
        request.approval_status = "future_pending"
        _audit(db, user, employee, buc_code, "FUTURE_DATED", previous, new_value, payload.reason, request.id)
        _notify_and_event(db, employee, user, buc_code, field_type, new_value, "future_pending")
    else:
        request.approved_by = user.full_name
        request.approval_date = datetime.utcnow()
        _apply_change(db, employee, request, user)
        _audit(db, user, employee, buc_code, "APPLIED", previous, new_value, payload.reason, request.id)
    db.commit()
    return {"request_id": request.id, "status": request.approval_status, "buc_code": buc_code, "field_type": field_type, "previous_value": previous, "new_value": new_value, "effective_date": payload.effective_date, "approval_required": needs_approval, "applied_at": request.applied_at}


def _approve_request(db: Session, request_id: UUID, user: UserResponse, approved: bool, comments: str | None):
    _require_employment_access(user, approval=True)
    request = db.query(HRMEmploymentChangeRequest).filter(HRMEmploymentChangeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Employment change request not found")
    employee = _employee(db, request.employee_id)
    approval = db.query(HRMEmploymentApproval).filter(HRMEmploymentApproval.request_id == request.id).first()
    if not approved:
        request.approval_status = "rejected"
        request.rejection_reason = comments
        if approval:
            approval.decision = "rejected"
            approval.approver_name = user.full_name
            approval.comments = comments
            approval.decided_at = datetime.utcnow()
        _audit(db, user, employee, request.buc_code, "REJECTED", request.previous_value, request.new_value, comments or request.reason, request.id)
        db.commit()
        return {"status": "rejected", "request_id": request.id}
    request.approval_status = "future_pending" if request.effective_date > date.today() else "approved"
    request.approved_by = user.full_name
    request.approval_date = datetime.utcnow()
    if approval:
        approval.decision = "approved"
        approval.approver_name = user.full_name
        approval.comments = comments
        approval.decided_at = datetime.utcnow()
    if request.effective_date <= date.today():
        _apply_change(db, employee, request, user)
    _audit(db, user, employee, request.buc_code, "APPROVED", request.previous_value, request.new_value, request.reason, request.id)
    db.commit()
    return {"status": request.approval_status, "request_id": request.id}


@router.get("/{employee_id:uuid}")
def get_employment_info(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee(db, employee_id)
    _require_employment_access(user)
    pending = db.query(HRMEmploymentChangeRequest).filter(HRMEmploymentChangeRequest.employee_id == employee.id, HRMEmploymentChangeRequest.approval_status.in_(["pending", "future_pending", "approved"])).order_by(HRMEmploymentChangeRequest.created_at.desc()).all()
    history = db.query(HRMEmployeeEmploymentHistory).filter(HRMEmployeeEmploymentHistory.employee_id == employee.id).order_by(HRMEmployeeEmploymentHistory.created_at.desc()).all()
    current = {
        "job_title": employee.job_title,
        "job_grade": employee.salary_grade,
        "salary_band": employee.salary_band if _salary_visible(user) else "Restricted",
        "cost_center_code": employee.cost_center_code,
        "reporting_manager_id": employee.supervisor_id,
        "functional_manager_id": employee.functional_manager_id,
        "functional_manager_scope": employee.functional_manager_scope,
    }
    return {"employee_id": employee.id, "current": current, "pending_changes": [_serialize(row) for row in pending], "history": [_serialize(row) for row in history], "salary_band_visible": _salary_visible(user)}


@router.get("/{employee_id:uuid}/history")
def get_employment_history(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _employee(db, employee_id)
    _require_employment_access(user)
    return [_serialize(row) for row in db.query(HRMEmployeeEmploymentHistory).filter(HRMEmployeeEmploymentHistory.employee_id == employee_id).order_by(HRMEmployeeEmploymentHistory.created_at.desc()).all()]


@router.get("/pending-approvals")
def get_pending_approvals(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_employment_access(user, approval=True)
    return [_serialize(row) for row in db.query(HRMEmploymentChangeRequest).filter(HRMEmploymentChangeRequest.approval_status == "pending").order_by(HRMEmploymentChangeRequest.created_at.desc()).all()]


@router.post("/approvals/{request_id}/approve")
def approve_employment_change(request_id: UUID, payload: EmploymentApprovalPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _approve_request(db, request_id, user, True, payload.comments)


@router.post("/approvals/{request_id}/reject")
def reject_employment_change(request_id: UUID, payload: EmploymentRejectPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _approve_request(db, request_id, user, False, payload.reason)


@router.post("/{employee_id:uuid}/job-title/assign", status_code=status.HTTP_201_CREATED)
def assign_job_title(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-019", payload, user)


@router.post("/{employee_id:uuid}/job-title/change", status_code=status.HTTP_201_CREATED)
def change_job_title(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-020", payload, user)


@router.post("/{employee_id:uuid}/job-grade/assign", status_code=status.HTTP_201_CREATED)
def assign_job_grade(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-021", payload, user)


@router.post("/{employee_id:uuid}/job-grade/change", status_code=status.HTTP_201_CREATED)
def change_job_grade(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-022", payload, user)


@router.post("/{employee_id:uuid}/salary-band/assign", status_code=status.HTTP_201_CREATED)
def assign_salary_band(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-023", payload, user)


@router.post("/{employee_id:uuid}/salary-band/update", status_code=status.HTTP_201_CREATED)
def update_salary_band(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-024", payload, user)


@router.post("/{employee_id:uuid}/cost-center/assign", status_code=status.HTTP_201_CREATED)
def assign_cost_center(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-025", payload, user)


@router.post("/{employee_id:uuid}/cost-center/change", status_code=status.HTTP_201_CREATED)
def change_cost_center(employee_id: UUID, payload: EmploymentChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-026", payload, user)


@router.post("/{employee_id:uuid}/reporting-manager/assign", status_code=status.HTTP_201_CREATED)
def assign_reporting_manager(employee_id: UUID, payload: ManagerChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-027", payload, user)


@router.post("/{employee_id:uuid}/reporting-manager/change", status_code=status.HTTP_201_CREATED)
def change_reporting_manager(employee_id: UUID, payload: ManagerChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-028", payload, user)


@router.post("/{employee_id:uuid}/functional-manager/assign", status_code=status.HTTP_201_CREATED)
def assign_functional_manager(employee_id: UUID, payload: ManagerChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-029", payload, user)


@router.post("/{employee_id:uuid}/functional-manager/change", status_code=status.HTTP_201_CREATED)
def change_functional_manager(employee_id: UUID, payload: ManagerChangePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _initiate_change(db, employee_id, "EMP-030", payload, user)
