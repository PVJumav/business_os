import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.crud import get_or_404
from backend.core.database import get_db
from backend.models.automation import EnterpriseEvent
from backend.models.enterprise import NotificationEvent
from backend.models.hrm import (
    HRMAuditLog,
    HRMBenefit,
    HRMClearanceChecklist,
    HRMCompensation,
    HRMDocument,
    HRMEmployee,
    HRMEmployeeAccessLog,
    HRMEmployeeAccessRequest,
    HRMEmployeeAccountStatus,
    HRMEmployeeAllowance,
    HRMEmployeeAssetRecovery,
    HRMEmployeeBenefitAssignment,
    HRMEmployeeCertificationTracking,
    HRMEmployeeComplianceRecord,
    HRMEmployeeContractTracking,
    HRMEmployeeExitDocument,
    HRMEmployeeFinalSettlement,
    HRMEmployeeInsurancePlan,
    HRMEmployeeOffboardingCase,
    HRMEmployeePassportRecord,
    HRMEmployeeReportExport,
    HRMEmployeeSalaryHistory,
    HRMEmployeeStatutoryIdentifier,
    HRMEmployeeSystemRole,
    HRMEmployeeVisaRecord,
    HRMEmployeeWorkPermit,
    HRMEmployeeChangeRequest,
    HRMEmployeeMovement,
    HRMEmployeeStatusHistory,
)
from backend.schemas.auth import UserResponse
from backend.schemas.hrm.employee_capabilities import (
    AccessActionPayload,
    AccessRequestPayload,
    AllowancePayload,
    BenefitPayload,
    CertificationTrackingPayload,
    ContractTrackingPayload,
    ExportPayload,
    InsurancePlanPayload,
    OffboardingPayload,
    PassportPayload,
    RemovePayload,
    SalaryAdjustmentPayload,
    SalaryPayload,
    SelfServiceChangeRequestPayload,
    StatutoryIdentifierPayload,
    SystemRolePayload,
    VisaPayload,
    WorkPermitPayload,
)


router = APIRouter(prefix="/hrm", tags=["HRM Employee Capabilities"])


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
        raise HTTPException(status_code=403, detail="HRM employee capability access requires HR permissions")


def _require_admin(user: UserResponse) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="This sensitive employee action requires admin rights")


def _full_name(employee: HRMEmployee) -> str:
    return " ".join(part for part in [employee.first_name, employee.middle_name, employee.last_name] if part) or employee.email


def _audit(db: Session, user: UserResponse, employee: HRMEmployee, action: str, summary: str, before: Any = None, after: Any = None, sensitivity: str = "internal") -> None:
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action=action,
            entity_type="HRMEmployee",
            entity_id=str(employee.id),
            sensitivity=sensitivity,
            summary=summary,
            before_json=_jsonable(before),
            after_json=_jsonable(after),
        )
    )


def _event(db: Session, employee: HRMEmployee, user: UserResponse, event_type: str, target: str, payload: dict[str, Any]) -> None:
    db.add(
        EnterpriseEvent(
            event_type=event_type,
            source_module="HRM",
            target_module=target,
            payload=_jsonable({"employee_id": employee.id, "employee_code": employee.employee_code, **payload}),
            event_status="pending",
            created_by=user.full_name,
        )
    )


def _notify(db: Session, employee: HRMEmployee, user: UserResponse, subject: str, body: str, recipient: str = "HR") -> None:
    db.add(
        NotificationEvent(
            module="HRM",
            related_entity="Employee",
            related_id=employee.id,
            recipient_name=recipient,
            recipient_email=employee.email if recipient == "Employee" else None,
            subject=subject,
            body=body,
            status="queued",
            created_by=user.full_name,
        )
    )


def _expiry_status(expiry_date: date | None) -> str:
    if not expiry_date:
        return "missing"
    today = date.today()
    if expiry_date < today:
        return "expired"
    if expiry_date <= today + timedelta(days=90):
        return "expiring_soon"
    return "valid"


def _active_docs(db: Session, employee_id: UUID) -> list[HRMDocument]:
    return db.query(HRMDocument).filter(HRMDocument.employee_id == employee_id, HRMDocument.status == "active", HRMDocument.current_version == True).all()  # noqa: E712


def _document_status(docs: list[HRMDocument], document_type: str) -> str:
    matches = [doc for doc in docs if (doc.document_type or "").upper() == document_type]
    if not matches:
        return "Missing"
    if any(doc.verification_status == "Verified" for doc in matches):
        return "Verified"
    if any(doc.verification_status == "Rejected" for doc in matches):
        return "Rejected"
    return "Pending Verification"


def _validate_compliance(db: Session, employee: HRMEmployee, user: UserResponse | None = None) -> dict[str, Any]:
    docs = _active_docs(db, employee.id)
    missing: list[str] = []
    expired: list[str] = []
    pending: list[str] = []

    checks = {
        "Tax PIN": bool(employee.tax_pin),
        "National ID or Passport": bool(employee.national_id or employee.passport_number),
        "Employment Contract": employee.contract_signed or _document_status(docs, "EMPLOYMENT_CONTRACT") == "Verified",
    }
    if employee.payroll_profile_status != "not_required":
        checks["Tax Document"] = _document_status(docs, "TAX_DOCUMENT") == "Verified"
    if (employee.country or "").lower() not in {"", "kenya"} or (employee.nationality or "").lower() not in {"", "kenyan", "kenya"}:
        checks["Valid Passport"] = bool(employee.passport_number)
        checks["Valid Work Permit"] = bool(db.query(HRMEmployeeWorkPermit).filter(HRMEmployeeWorkPermit.employee_id == employee.id, HRMEmployeeWorkPermit.status == "active", HRMEmployeeWorkPermit.expiry_date >= date.today()).first())

    for label, ok in checks.items():
        if not ok:
            missing.append(label)

    expiring_docs = [doc for doc in docs if doc.expiry_date and doc.expiry_date <= date.today() + timedelta(days=90)]
    for doc in expiring_docs:
        status = _expiry_status(doc.expiry_date)
        item = f"{doc.document_type}: {doc.expiry_date}"
        if status == "expired":
            expired.append(item)
        else:
            pending.append(f"Expiring soon - {item}")

    for model, label in [
        (HRMEmployeePassportRecord, "Passport"),
        (HRMEmployeeVisaRecord, "Visa"),
        (HRMEmployeeWorkPermit, "Work Permit"),
        (HRMEmployeeContractTracking, "Contract"),
        (HRMEmployeeCertificationTracking, "Certification"),
    ]:
        rows = db.query(model).filter(model.employee_id == employee.id, model.status == "active").all()
        for item in rows:
            status = _expiry_status(getattr(item, "expiry_date", None) or getattr(item, "contract_end_date", None))
            if status == "expired":
                expired.append(label)
            elif status == "expiring_soon":
                pending.append(f"Expiring soon - {label}")

    verified_count = len(checks) - len(missing)
    score = round((verified_count / max(len(checks), 1)) * 100, 2)
    if expired:
        compliance_status = "Expired Documents"
    elif missing:
        compliance_status = "Missing Mandatory Data"
    elif pending:
        compliance_status = "Pending Verification"
    elif score >= 95:
        compliance_status = "Compliant"
    else:
        compliance_status = "Partially Compliant"

    result = {
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "compliance_score": score,
        "compliance_status": compliance_status,
        "missing_items": missing,
        "expired_items": expired,
        "pending_verification_items": pending,
        "payroll_readiness": "ready" if not missing and not expired else "incomplete",
        "activation_readiness": "ready" if not missing and not expired else "incomplete",
        "access_readiness": "ready" if employee.iam_request_status in {"provisioned", "reactivation_review", "pending", "queued"} and not expired else "review_required",
    }
    record = db.query(HRMEmployeeComplianceRecord).filter(HRMEmployeeComplianceRecord.employee_id == employee.id).first()
    if not record:
        record = HRMEmployeeComplianceRecord(employee_id=employee.id)
        db.add(record)
    record.compliance_score = Decimal(str(score))
    record.compliance_status = compliance_status
    record.missing_items = missing
    record.expired_items = expired
    record.pending_verification_items = pending
    record.payroll_readiness = result["payroll_readiness"]
    record.activation_readiness = result["activation_readiness"]
    record.access_readiness = result["access_readiness"]
    if user:
        record.validated_by = user.full_name
        record.validated_at = datetime.utcnow()
    return result


def _upsert_statutory(db: Session, employee: HRMEmployee, user: UserResponse, identifier_type: str, payload: StatutoryIdentifierPayload):
    duplicate = db.query(HRMEmployeeStatutoryIdentifier).filter(
        HRMEmployeeStatutoryIdentifier.identifier_type == identifier_type,
        HRMEmployeeStatutoryIdentifier.identifier_value == payload.identifier_value,
        HRMEmployeeStatutoryIdentifier.employee_id != employee.id,
        HRMEmployeeStatutoryIdentifier.status == "active",
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail=f"{identifier_type} already exists for another employee")
    before = {"tax_pin": employee.tax_pin, "identifier_type": identifier_type}
    if identifier_type == "TAX_PIN":
        employee.tax_pin = payload.identifier_value
    elif identifier_type == "NSSF":
        employee.skills = employee.skills or ""
    elif identifier_type in {"SHA", "NHIF"}:
        employee.certifications_summary = employee.certifications_summary or ""
    record = HRMEmployeeStatutoryIdentifier(
        employee_id=employee.id,
        identifier_type=identifier_type,
        identifier_value=payload.identifier_value,
        country=payload.country,
        document_id=payload.document_id,
        verification_status=payload.verification_status,
        created_by=user.full_name,
    )
    db.add(record)
    _audit(db, user, employee, f"EMP-{ {'TAX_PIN':'075','NSSF':'076','SHA':'077','NHIF':'077'}[identifier_type] }_{identifier_type}_CAPTURED", f"{identifier_type} captured for {_full_name(employee)}.", before, _row(record))
    _event(db, employee, user, f"Employee{identifier_type.title().replace('_', '')}Updated", "Payroll", {"identifier_type": identifier_type})
    db.commit()
    db.refresh(record)
    return _row(record)


@router.post("/employees/{employee_id:uuid}/compliance/tax-pin")
def capture_tax_pin(employee_id: UUID, payload: StatutoryIdentifierPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    return _upsert_statutory(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, "TAX_PIN", payload)


@router.post("/employees/{employee_id:uuid}/compliance/nssf")
def capture_nssf(employee_id: UUID, payload: StatutoryIdentifierPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    return _upsert_statutory(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, "NSSF", payload)


@router.post("/employees/{employee_id:uuid}/compliance/health-insurance")
def capture_health_insurance(employee_id: UUID, payload: StatutoryIdentifierPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    identifier_type = "SHA" if (payload.country or "Kenya").lower() == "kenya" else "NHIF"
    return _upsert_statutory(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, identifier_type, payload)


@router.post("/employees/{employee_id:uuid}/compliance/passport")
def capture_passport(employee_id: UUID, payload: PassportPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    employee.passport_number = payload.passport_number
    record = HRMEmployeePassportRecord(employee_id=employee.id, passport_number=payload.passport_number, passport_country=payload.passport_country, issue_date=payload.issue_date, expiry_date=payload.expiry_date, document_id=payload.document_id, verification_status=payload.verification_status, expiry_status=_expiry_status(payload.expiry_date), created_by=user.full_name)
    db.add(record)
    _audit(db, user, employee, "EMP-078_PASSPORT_CAPTURED", "Passport information captured.", after=_row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/compliance/visa")
def capture_visa(employee_id: UUID, payload: VisaPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = HRMEmployeeVisaRecord(employee_id=employee.id, visa_type=payload.visa_type, visa_number=payload.visa_number, visa_country=payload.visa_country, issue_date=payload.issue_date, expiry_date=payload.expiry_date, visa_status=_expiry_status(payload.expiry_date), document_id=payload.document_id, created_by=user.full_name)
    db.add(record)
    _audit(db, user, employee, "EMP-079_VISA_CAPTURED", "Visa information captured.", after=_row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/compliance/work-permit")
def track_work_permit(employee_id: UUID, payload: WorkPermitPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = HRMEmployeeWorkPermit(employee_id=employee.id, work_permit_number=payload.work_permit_number, work_permit_type=payload.work_permit_type, issue_date=payload.issue_date, expiry_date=payload.expiry_date, document_id=payload.document_id, expiry_status=_expiry_status(payload.expiry_date), created_by=user.full_name)
    db.add(record)
    _audit(db, user, employee, "EMP-080_WORK_PERMIT_TRACKED", "Work permit expiry tracked.", after=_row(record))
    _event(db, employee, user, "EmployeeWorkPermitTracked", "IAM", {"expiry_date": payload.expiry_date})
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/compliance/contract")
def track_contract(employee_id: UUID, payload: ContractTrackingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    if payload.contract_end_date < payload.contract_start_date:
        raise HTTPException(status_code=422, detail="Contract end date cannot be before start date")
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    employee.employment_start_date = payload.contract_start_date
    employee.employment_end_date = payload.contract_end_date
    record = HRMEmployeeContractTracking(employee_id=employee.id, contract_start_date=payload.contract_start_date, contract_end_date=payload.contract_end_date, contract_status=_expiry_status(payload.contract_end_date), contract_document_id=payload.contract_document_id, renewal_status=payload.renewal_status, created_by=user.full_name)
    db.add(record)
    _audit(db, user, employee, "EMP-081_CONTRACT_EXPIRY_TRACKED", "Contract expiry tracked.", after=_row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/compliance/certifications")
def track_certification(employee_id: UUID, payload: CertificationTrackingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = HRMEmployeeCertificationTracking(employee_id=employee.id, certification_name=payload.certification_name, issuing_body=payload.issuing_body, certificate_number=payload.certificate_number, issue_date=payload.issue_date, expiry_date=payload.expiry_date, document_id=payload.document_id, status=_expiry_status(payload.expiry_date) if payload.expiry_date else "active", created_by=user.full_name)
    db.add(record)
    _audit(db, user, employee, "EMP-082_CERTIFICATION_TRACKED", "Certification expiry tracked.", after=_row(record))
    db.commit()
    return _row(record)


@router.get("/employees/{employee_id:uuid}/compliance")
def get_employee_compliance(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    result = _validate_compliance(db, employee)
    db.commit()
    return result


@router.post("/employees/{employee_id:uuid}/compliance/validate")
def validate_employee_compliance(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    result = _validate_compliance(db, employee, user)
    _audit(db, user, employee, "EMP-083_COMPLIANCE_VALIDATED", "Employee compliance validated.", after=result)
    db.commit()
    return result


@router.get("/compliance/non-compliant")
def non_compliant_employees(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employees = db.query(HRMEmployee).all()
    rows = []
    for employee in employees:
        result = _validate_compliance(db, employee)
        if result["compliance_status"] != "Compliant":
            rows.append(result)
    db.commit()
    return rows


@router.get("/compliance/expiring")
def expiring_compliance(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    threshold = date.today() + timedelta(days=90)
    return {
        "documents": [_row(row) for row in db.query(HRMDocument).filter(HRMDocument.expiry_date.isnot(None), HRMDocument.expiry_date <= threshold, HRMDocument.status == "active").all()],
        "work_permits": [_row(row) for row in db.query(HRMEmployeeWorkPermit).filter(HRMEmployeeWorkPermit.expiry_date <= threshold, HRMEmployeeWorkPermit.status == "active").all()],
        "contracts": [_row(row) for row in db.query(HRMEmployeeContractTracking).filter(HRMEmployeeContractTracking.contract_end_date <= threshold, HRMEmployeeContractTracking.status == "active").all()],
        "certifications": [_row(row) for row in db.query(HRMEmployeeCertificationTracking).filter(HRMEmployeeCertificationTracking.expiry_date <= threshold, HRMEmployeeCertificationTracking.status == "active").all()],
    }


@router.post("/employees/{employee_id:uuid}/access/account-request")
def create_account_request(employee_id: UUID, payload: AccessRequestPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    if employee.employment_status not in {"active", "pending_activation", "probation", "confirmed"}:
        raise HTTPException(status_code=422, detail="Only active or pending activation employees may have account requests")
    if not payload.access_expiry_date and employee.employment_type in {"Contract", "Consultant", "Internship", "Casual"}:
        payload.access_expiry_date = employee.employment_end_date
    record = HRMEmployeeAccessRequest(employee_id=employee.id, request_type=payload.request_type, requested_systems=payload.requested_systems, requested_roles=payload.requested_roles, business_justification=payload.business_justification, requested_by=user.full_name, access_expiry_date=payload.access_expiry_date)
    employee.iam_request_status = "queued"
    db.add(record)
    _audit(db, user, employee, "EMP-084_ACCOUNT_REQUEST_CREATED", "IAM account request created.", after=_row(record))
    _event(db, employee, user, "EmployeeAccountProvisioningRequested", "IAM", _row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/access/roles")
def assign_system_role(employee_id: UUID, payload: SystemRolePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    approval = "pending" if payload.access_level in {"admin", "privileged", "super_admin"} else "approved"
    record = HRMEmployeeSystemRole(employee_id=employee.id, system_name=payload.system_name, role_name=payload.role_name, access_level=payload.access_level, effective_from=payload.effective_from, effective_to=payload.effective_to, assigned_by=user.full_name, approval_status=approval)
    db.add(record)
    _audit(db, user, employee, "EMP-085_SYSTEM_ROLE_ASSIGNED", "System role assigned.", after=_row(record), sensitivity="restricted")
    _event(db, employee, user, "EmployeeSystemRoleAssigned", "IAM", _row(record))
    db.commit()
    return _row(record)


@router.put("/employees/{employee_id:uuid}/access/roles/{role_id:uuid}")
def update_system_role(employee_id: UUID, role_id: UUID, payload: SystemRolePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = get_or_404(db, HRMEmployeeSystemRole, role_id, "System role")
    before = _row(record)
    record.system_name = payload.system_name
    record.role_name = payload.role_name
    record.access_level = payload.access_level
    record.effective_from = payload.effective_from
    record.effective_to = payload.effective_to
    record.approval_status = "pending" if payload.access_level in {"admin", "privileged", "super_admin"} else "approved"
    _audit(db, user, employee, "EMP-086_SYSTEM_ROLE_UPDATED", "System role updated.", before, _row(record), "restricted")
    _event(db, employee, user, "EmployeeSystemRoleUpdated", "IAM", _row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/access/request")
def request_additional_access(employee_id: UUID, payload: AccessRequestPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    payload.request_type = "additional_access"
    return create_account_request(employee_id, payload, db, user)


def _access_action(db: Session, employee: HRMEmployee, user: UserResponse, action: str, payload: AccessActionPayload):
    account = db.query(HRMEmployeeAccountStatus).filter(HRMEmployeeAccountStatus.employee_id == employee.id).first()
    if not account:
        account = HRMEmployeeAccountStatus(employee_id=employee.id)
        db.add(account)
    before = _row(account)
    if action == "revoke":
        account.account_status = "revoked"
        employee.iam_request_status = "revocation_queued"
    elif action == "lock":
        account.account_status = "locked"
        account.lock_reason = payload.reason
        account.locked_at = datetime.utcnow()
    elif action == "unlock":
        if account.account_status != "locked":
            raise HTTPException(status_code=422, detail="Employee account must be locked before unlock")
        account.account_status = "active"
        account.unlocked_at = datetime.utcnow()
    elif action == "reset":
        account.last_reset_type = payload.reset_type or "password"
    account.updated_by = user.full_name
    log = HRMEmployeeAccessLog(employee_id=employee.id, action=action, system_name=payload.system_name, details={"reason": payload.reason, "reset_type": payload.reset_type}, performed_by=user.full_name)
    db.add(log)
    _audit(db, user, employee, f"EMP-{ {'revoke':'088','lock':'089','unlock':'090','reset':'091'}[action] }_ACCESS_{action.upper()}", f"Employee access {action} recorded.", before, _row(account), "restricted")
    _event(db, employee, user, f"EmployeeAccess{action.title()}Requested", "IAM", _row(log))
    db.commit()
    return _row(account)


@router.post("/employees/{employee_id:uuid}/access/revoke")
def revoke_access(employee_id: UUID, payload: AccessActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    return _access_action(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, "revoke", payload)


@router.post("/employees/{employee_id:uuid}/access/lock")
def lock_account(employee_id: UUID, payload: AccessActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    return _access_action(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, "lock", payload)


@router.post("/employees/{employee_id:uuid}/access/unlock")
def unlock_account(employee_id: UUID, payload: AccessActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    return _access_action(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, "unlock", payload)


@router.post("/employees/{employee_id:uuid}/access/reset")
def reset_access(employee_id: UUID, payload: AccessActionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    return _access_action(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, "reset", payload)


@router.get("/employees/{employee_id:uuid}/compensation")
def get_compensation(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return {
        "current": {"base_salary": _jsonable(employee.base_salary), "currency": "KES", "salary_band": employee.salary_band, "pay_frequency": employee.pay_frequency},
        "salary_history": [_row(row) for row in db.query(HRMEmployeeSalaryHistory).filter(HRMEmployeeSalaryHistory.employee_id == employee.id).order_by(HRMEmployeeSalaryHistory.effective_date.desc()).all()],
        "compensation_records": [_row(row) for row in db.query(HRMCompensation).filter(HRMCompensation.employee_id == employee.id).order_by(HRMCompensation.effective_date.desc()).all()],
        "allowances": [_row(row) for row in db.query(HRMEmployeeAllowance).filter(HRMEmployeeAllowance.employee_id == employee.id).all()],
        "benefits": [_row(row) for row in db.query(HRMEmployeeBenefitAssignment).filter(HRMEmployeeBenefitAssignment.employee_id == employee.id).all()],
        "insurance_plans": [_row(row) for row in db.query(HRMEmployeeInsurancePlan).filter(HRMEmployeeInsurancePlan.employee_id == employee.id).all()],
    }


def _record_salary(db: Session, employee: HRMEmployee, user: UserResponse, payload: SalaryPayload, change_type: str):
    before = {"base_salary": _jsonable(employee.base_salary), "salary_band": employee.salary_band}
    record = HRMEmployeeSalaryHistory(employee_id=employee.id, previous_salary=employee.base_salary, new_salary=payload.base_salary, currency=payload.currency, salary_band=payload.salary_band, pay_frequency=payload.pay_frequency, effective_date=payload.effective_date, change_type=change_type, reason=payload.reason, created_by=user.full_name)
    db.add(record)
    db.add(HRMCompensation(employee_id=employee.id, effective_date=payload.effective_date, compensation_type=change_type, base_salary=payload.base_salary, currency=payload.currency, pay_frequency=payload.pay_frequency, approval_status="approved", notes=payload.reason))
    employee.base_salary = payload.base_salary
    employee.salary_band = payload.salary_band or employee.salary_band
    employee.pay_frequency = payload.pay_frequency
    employee.payroll_profile_status = "payroll_update_queued"
    _audit(db, user, employee, f"EMP-{ {'capture':'092','update':'093','increment':'094','reduction':'095'}[change_type] }_SALARY_{change_type.upper()}", "Salary information updated.", before, _row(record), "confidential")
    _event(db, employee, user, "EmployeeCompensationChanged", "Payroll", _row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/compensation/salary")
def capture_salary(employee_id: UUID, payload: SalaryPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    return _record_salary(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, payload, "capture")


@router.put("/employees/{employee_id:uuid}/compensation/salary")
def update_salary(employee_id: UUID, payload: SalaryPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    return _record_salary(db, get_or_404(db, HRMEmployee, employee_id, "Employee"), user, payload, "update")


@router.post("/employees/{employee_id:uuid}/compensation/increment")
def salary_increment(employee_id: UUID, payload: SalaryAdjustmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    current = Decimal(str(employee.base_salary or 0))
    new_salary = current + (payload.amount or Decimal("0"))
    if payload.percentage:
        new_salary = current + (current * Decimal(str(payload.percentage)) / Decimal("100"))
    return _record_salary(db, employee, user, SalaryPayload(base_salary=new_salary, effective_date=payload.effective_date, reason=payload.reason, salary_band=employee.salary_band, pay_frequency=employee.pay_frequency or "monthly"), "increment")


@router.post("/employees/{employee_id:uuid}/compensation/reduction")
def salary_reduction(employee_id: UUID, payload: SalaryAdjustmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    current = Decimal(str(employee.base_salary or 0))
    new_salary = current - (payload.amount or Decimal("0"))
    if payload.percentage:
        new_salary = current - (current * Decimal(str(payload.percentage)) / Decimal("100"))
    if new_salary < 0:
        raise HTTPException(status_code=422, detail="Salary reduction cannot make salary negative")
    return _record_salary(db, employee, user, SalaryPayload(base_salary=new_salary, effective_date=payload.effective_date, reason=payload.reason, salary_band=employee.salary_band, pay_frequency=employee.pay_frequency or "monthly"), "reduction")


@router.post("/employees/{employee_id:uuid}/allowances")
def assign_allowance(employee_id: UUID, payload: AllowancePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = HRMEmployeeAllowance(employee_id=employee.id, allowance_type=payload.allowance_type, amount=payload.amount, currency=payload.currency, recurring=payload.recurring, taxable=payload.taxable, effective_from=payload.effective_from, effective_to=payload.effective_to, reason=payload.reason, created_by=user.full_name)
    db.add(record)
    _audit(db, user, employee, "EMP-096_ALLOWANCE_ASSIGNED", "Allowance assigned.", after=_row(record), sensitivity="confidential")
    _event(db, employee, user, "EmployeeAllowanceChanged", "Payroll", _row(record))
    db.commit()
    return _row(record)


@router.delete("/employees/{employee_id:uuid}/allowances/{allowance_id:uuid}")
def remove_allowance(employee_id: UUID, allowance_id: UUID, payload: RemovePayload = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = get_or_404(db, HRMEmployeeAllowance, allowance_id, "Allowance")
    record.status = "removed"
    record.effective_to = payload.end_date
    record.reason = payload.reason
    _audit(db, user, employee, "EMP-097_ALLOWANCE_REMOVED", "Allowance removed.", after=_row(record), sensitivity="confidential")
    _event(db, employee, user, "EmployeeAllowanceRemoved", "Payroll", _row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/benefits")
def assign_benefit(employee_id: UUID, payload: BenefitPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = HRMEmployeeBenefitAssignment(employee_id=employee.id, benefit_type=payload.benefit_type, benefit_name=payload.benefit_name, provider=payload.provider, effective_from=payload.effective_from, effective_to=payload.effective_to, dependant_ids=[str(item) for item in payload.dependant_ids], created_by=user.full_name)
    db.add(record)
    db.add(HRMBenefit(employee_id=employee.id, benefit_type=payload.benefit_type, benefit_name=payload.benefit_name, provider=payload.provider, start_date=payload.effective_from, end_date=payload.effective_to, status="active"))
    _audit(db, user, employee, "EMP-098_BENEFIT_ASSIGNED", "Benefit assigned.", after=_row(record), sensitivity="confidential")
    db.commit()
    return _row(record)


@router.delete("/employees/{employee_id:uuid}/benefits/{benefit_id:uuid}")
def remove_benefit(employee_id: UUID, benefit_id: UUID, payload: RemovePayload = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = get_or_404(db, HRMEmployeeBenefitAssignment, benefit_id, "Benefit")
    record.status = "removed"
    record.effective_to = payload.end_date
    _audit(db, user, employee, "EMP-099_BENEFIT_REMOVED", "Benefit removed.", after=_row(record), sensitivity="confidential")
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/insurance-plans")
def assign_insurance(employee_id: UUID, payload: InsurancePlanPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = HRMEmployeeInsurancePlan(employee_id=employee.id, plan_name=payload.plan_name, provider=payload.provider, policy_number=payload.policy_number, coverage_start=payload.coverage_start, coverage_end=payload.coverage_end, dependant_ids=[str(item) for item in payload.dependant_ids], created_by=user.full_name)
    db.add(record)
    _audit(db, user, employee, "EMP-100_INSURANCE_PLAN_ASSIGNED", "Insurance plan assigned.", after=_row(record), sensitivity="confidential")
    db.commit()
    return _row(record)


def _employee_for_self_service(db: Session, user: UserResponse) -> HRMEmployee:
    employee = db.query(HRMEmployee).filter(HRMEmployee.email == user.email).first()
    if not employee:
        raise HTTPException(status_code=404, detail="No employee profile is linked to this user")
    return employee


@router.get("/self-service/profile")
def self_profile(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    data = _row(employee)
    data.pop("base_salary", None)
    return data


@router.put("/self-service/profile")
def update_self_profile(payload: dict[str, Any], db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    allowed = {"personal_email", "phone", "alternative_phone", "physical_address", "postal_address", "city", "county", "country", "preferred_name"}
    sensitive = set(payload) - allowed
    before = _row(employee)
    for key, value in payload.items():
        if key in allowed:
            setattr(employee, key, value)
    if sensitive:
        db.add(HRMEmployeeChangeRequest(employee_id=employee.id, section="self_service_profile", requested_changes=_jsonable({key: payload[key] for key in sensitive}), reason="Sensitive self-service profile update", requested_by=user.full_name, approval_status="submitted"))
    _audit(db, user, employee, "EMP-102_SELF_PROFILE_UPDATED", "Self-service profile update submitted.", before, payload)
    db.commit()
    return {"updated_fields": sorted(set(payload) & allowed), "approval_required_fields": sorted(sensitive)}


@router.get("/self-service/documents")
def self_documents(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    return [_row(row) for row in db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id).order_by(HRMDocument.created_at.desc()).all()]


@router.post("/self-service/documents")
def self_document_upload_placeholder(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    _audit(db, user, employee, "EMP-103_SELF_DOCUMENT_UPLOAD_REQUESTED", "Self-service document upload requested.")
    db.commit()
    return {"message": "Use the employee document upload endpoint with self-service token; uploaded documents enter Pending Verification."}


@router.get("/self-service/reporting-structure")
def self_reporting_structure(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    manager = db.query(HRMEmployee).filter(HRMEmployee.id == employee.supervisor_id).first() if employee.supervisor_id else None
    return {"employee": _row(employee), "reporting_manager": _row(manager) if manager else None, "department": employee.department, "branch": employee.branch, "business_unit": employee.business_unit}


@router.get("/self-service/employment-history")
def self_employment_history(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    return {
        "movements": [_row(row) for row in db.query(HRMEmployeeMovement).filter(HRMEmployeeMovement.employee_id == employee.id).order_by(HRMEmployeeMovement.created_at.desc()).all()],
        "status_history": [_row(row) for row in db.query(HRMEmployeeStatusHistory).filter(HRMEmployeeStatusHistory.employee_id == employee.id).order_by(HRMEmployeeStatusHistory.created_at.desc()).all()],
    }


@router.get("/self-service/compensation-history")
def self_compensation_history(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    return {"benefits": [_row(row) for row in db.query(HRMEmployeeBenefitAssignment).filter(HRMEmployeeBenefitAssignment.employee_id == employee.id).all()], "allowances": [_row(row) for row in db.query(HRMEmployeeAllowance).filter(HRMEmployeeAllowance.employee_id == employee.id).all()]}


@router.post("/self-service/profile-change-requests")
def self_change_request(payload: SelfServiceChangeRequestPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = _employee_for_self_service(db, user)
    record = HRMEmployeeChangeRequest(employee_id=employee.id, section=payload.section, requested_changes=_jsonable(payload.requested_changes), reason=payload.reason, requested_by=user.full_name, approval_status="submitted")
    db.add(record)
    _audit(db, user, employee, "EMP-108_PROFILE_CHANGE_REQUEST_SUBMITTED", "Profile change request submitted.", after=_row(record))
    db.commit()
    return _row(record)


@router.get("/analytics/employees/dashboard")
def employee_dashboard(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    total = db.query(HRMEmployee).count()
    active = db.query(HRMEmployee).filter(HRMEmployee.employment_status == "active").count()
    probation = db.query(HRMEmployee).filter(HRMEmployee.probation_status.in_(["Pending", "In Progress", "Due for Review", "Extended"])).count()
    exits = db.query(HRMEmployee).filter(HRMEmployee.employment_status.in_(["terminated", "retired", "deceased", "exited"])).count()
    expiring_contracts = db.query(HRMEmployee).filter(HRMEmployee.employment_end_date.isnot(None), HRMEmployee.employment_end_date <= date.today() + timedelta(days=90)).count()
    pending_docs = db.query(HRMDocument).filter(HRMDocument.verification_status == "Pending Verification").count()
    return {"total_employees": total, "active_employees": active, "new_hires": db.query(HRMEmployee).filter(HRMEmployee.hire_date >= date.today() - timedelta(days=30)).count(), "exits": exits, "on_probation": probation, "expiring_contracts": expiring_contracts, "pending_document_verification": pending_docs}


@router.get("/analytics/headcount")
def headcount_analysis(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    def group(field):
        col = getattr(HRMEmployee, field)
        return [{"label": row[0] or "Unassigned", "count": row[1]} for row in db.query(col, func.count(HRMEmployee.id)).group_by(col).all()]
    return {field: group(field) for field in ["department", "branch", "business_unit", "employment_type", "gender", "salary_grade"]}


@router.get("/analytics/demographics")
def demographics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    def group(field):
        col = getattr(HRMEmployee, field)
        return [{"label": row[0] or "Unknown", "count": row[1]} for row in db.query(col, func.count(HRMEmployee.id)).group_by(col).all()]
    return {field: group(field) for field in ["gender", "nationality", "marital_status", "employment_type"]}


@router.get("/reports/employees")
def employee_report(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    return [_row(row) for row in db.query(HRMEmployee).order_by(HRMEmployee.created_at.desc()).limit(500).all()]


@router.post("/reports/employees/export")
def export_employee_report(payload: ExportPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    rows = employee_report(db, user)
    columns = payload.columns or ["employee_code", "first_name", "last_name", "email", "department", "job_title", "employment_status"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    record = HRMEmployeeReportExport(report_type="employees", export_format=payload.export_format, filters=payload.filters, columns=columns, exported_by=user.full_name, row_count=len(rows))
    db.add(record)
    db.commit()
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=employees.csv"})


@router.get("/reports/movements")
def movement_report(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    return [_row(row) for row in db.query(HRMEmployeeMovement).order_by(HRMEmployeeMovement.created_at.desc()).limit(500).all()]


@router.get("/reports/compliance")
def compliance_report(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return non_compliant_employees(db, user)


@router.get("/reports/organization")
def organization_report(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employees = db.query(HRMEmployee).all()
    return [{"employee": _full_name(emp), "manager_id": str(emp.supervisor_id) if emp.supervisor_id else None, "department": emp.department, "branch": emp.branch, "business_unit": emp.business_unit} for emp in employees]


def _active_offboarding(db: Session, employee: HRMEmployee) -> HRMEmployeeOffboardingCase:
    case = db.query(HRMEmployeeOffboardingCase).filter(HRMEmployeeOffboardingCase.employee_id == employee.id, HRMEmployeeOffboardingCase.status == "active").order_by(HRMEmployeeOffboardingCase.created_at.desc()).first()
    if not case:
        raise HTTPException(status_code=404, detail="No active offboarding case found")
    return case


@router.post("/employees/{employee_id:uuid}/offboarding/separation")
def initiate_separation(employee_id: UUID, payload: OffboardingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    if not payload.separation_type or not payload.separation_reason or not payload.effective_date:
        raise HTTPException(status_code=422, detail="Separation type, reason, and effective date are required")
    case = HRMEmployeeOffboardingCase(employee_id=employee.id, separation_type=payload.separation_type, separation_reason=payload.separation_reason, effective_date=payload.effective_date, notice_period_days=payload.notice_period_days, created_by=user.full_name)
    employee.employment_status = "pending_exit"
    db.add(case)
    _audit(db, user, employee, "EMP-117_SEPARATION_INITIATED", "Employee separation initiated.", after=_row(case), sensitivity="restricted")
    _event(db, employee, user, "EmployeeSeparationInitiated", "Enterprise", _row(case))
    db.commit()
    return _row(case)


@router.post("/employees/{employee_id:uuid}/offboarding/clearance")
def initiate_clearance(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = _active_offboarding(db, employee)
    for department in ["HR", "IT/IAM", "Finance", "Assets", "Manager", "Legal", "Projects", "Payroll"]:
        db.add(HRMClearanceChecklist(employee_id=employee.id, checklist_item=f"{department} clearance", owner_department=department, status="pending"))
    case.clearance_status = "in_progress"
    _audit(db, user, employee, "EMP-118_CLEARANCE_STARTED", "Clearance workflow generated.", after=_row(case))
    db.commit()
    return _row(case)


@router.post("/employees/{employee_id:uuid}/offboarding/assets/recover")
def recover_assets(employee_id: UUID, payload: OffboardingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = _active_offboarding(db, employee)
    record = HRMEmployeeAssetRecovery(offboarding_case_id=case.id, employee_id=employee.id, asset_name=payload.asset_name or "Assigned asset", asset_status=payload.asset_status or "returned", settlement_impact=payload.asset_deductions, notes=payload.reason, created_by=user.full_name)
    case.asset_recovery_status = "in_progress"
    db.add(record)
    _audit(db, user, employee, "EMP-119_ASSET_RECOVERY_RECORDED", "Asset recovery recorded.", after=_row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/offboarding/access/revoke")
def offboarding_revoke_access(employee_id: UUID, payload: OffboardingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = _active_offboarding(db, employee)
    case.access_revocation_status = "queued"
    employee.iam_request_status = "revocation_queued"
    _event(db, employee, user, "EmployeeOffboardingAccessRevocationRequested", "IAM", _row(case))
    _audit(db, user, employee, "EMP-120_OFFBOARDING_ACCESS_REVOKED", "Offboarding access revocation queued.", after=_row(case), sensitivity="restricted")
    db.commit()
    return _row(case)


@router.post("/employees/{employee_id:uuid}/offboarding/documents/generate")
def generate_exit_documents(employee_id: UUID, payload: OffboardingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = _active_offboarding(db, employee)
    doc_types = payload.document_types or ["Clearance Form", "Exit Letter", "Certificate of Service", "Final Settlement Summary", "NDA Reminder", "Handover Checklist", "Exit Interview Form"]
    rows = []
    for doc_type in doc_types:
        row = HRMEmployeeExitDocument(offboarding_case_id=case.id, employee_id=employee.id, document_type=doc_type, generated_by=user.full_name)
        db.add(row)
        rows.append(row)
    case.exit_document_status = "generated"
    _audit(db, user, employee, "EMP-121_EXIT_DOCUMENTS_GENERATED", "Exit documentation generated.", after={"documents": doc_types})
    db.commit()
    return [_row(row) for row in rows]


@router.post("/employees/{employee_id:uuid}/offboarding/archive")
def archive_employee_record(employee_id: UUID, payload: OffboardingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = _active_offboarding(db, employee)
    employee.employment_status = "archived"
    case.archived_at = datetime.utcnow()
    case.workflow_status = "archived"
    _audit(db, user, employee, "EMP-122_EMPLOYEE_ARCHIVED", "Employee record archived.", after=_row(case), sensitivity="restricted")
    db.commit()
    return _row(case)


@router.post("/employees/{employee_id:uuid}/offboarding/final-settlement")
def final_settlement(employee_id: UUID, payload: OffboardingPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = _active_offboarding(db, employee)
    net = payload.final_salary + payload.leave_payout + payload.allowances + payload.benefits - payload.deductions - payload.asset_deductions - payload.tax_deductions
    record = HRMEmployeeFinalSettlement(offboarding_case_id=case.id, employee_id=employee.id, final_salary=payload.final_salary, leave_payout=payload.leave_payout, deductions=payload.deductions, asset_deductions=payload.asset_deductions, allowances=payload.allowances, benefits=payload.benefits, tax_deductions=payload.tax_deductions, net_settlement=net, payroll_approval_status="approved", finance_approval_status="approved", status="approved", created_by=user.full_name)
    case.final_settlement_status = "approved"
    db.add(record)
    _audit(db, user, employee, "EMP-123_FINAL_SETTLEMENT_PROCESSED", "Final settlement processed.", after=_row(record), sensitivity="confidential")
    _event(db, employee, user, "EmployeeFinalSettlementProcessed", "Finance", _row(record))
    db.commit()
    return _row(record)


@router.post("/employees/{employee_id:uuid}/offboarding/complete")
def complete_offboarding(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = _active_offboarding(db, employee)
    case.workflow_status = "completed"
    case.completed_at = datetime.utcnow()
    employee.employment_status = {"Retirement": "retired", "Death in Service": "deceased", "Contract Expiry": "contract_ended"}.get(case.separation_type, "exited")
    _audit(db, user, employee, "EMP-124_OFFBOARDING_COMPLETED", "Employee offboarding completed.", after=_row(case), sensitivity="restricted")
    _event(db, employee, user, "EmployeeOffboardingCompleted", "Enterprise", _row(case))
    db.commit()
    return _row(case)


@router.get("/employees/{employee_id:uuid}/offboarding/status")
def offboarding_status(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    case = db.query(HRMEmployeeOffboardingCase).filter(HRMEmployeeOffboardingCase.employee_id == employee.id).order_by(HRMEmployeeOffboardingCase.created_at.desc()).first()
    if not case:
        return {"employee_id": str(employee.id), "offboarding_status": "not_started"}
    return {"case": _row(case), "clearance": [_row(row) for row in db.query(HRMClearanceChecklist).filter(HRMClearanceChecklist.employee_id == employee.id).all()], "asset_recovery": [_row(row) for row in db.query(HRMEmployeeAssetRecovery).filter(HRMEmployeeAssetRecovery.employee_id == employee.id).all()], "exit_documents": [_row(row) for row in db.query(HRMEmployeeExitDocument).filter(HRMEmployeeExitDocument.employee_id == employee.id).all()], "final_settlements": [_row(row) for row in db.query(HRMEmployeeFinalSettlement).filter(HRMEmployeeFinalSettlement.employee_id == employee.id).all()]}
