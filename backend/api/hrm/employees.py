import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.crud import delete_record, get_or_404
from backend.core.database import get_db
from backend.core.storage import get_upload_root, resolve_upload_url
from backend.models.automation import AuditLog, EnterpriseEvent, UserAccessProfile
from backend.models.enterprise import EntitySequence, NotificationEvent, StaffRoleAssignment
from backend.models.finance import FinanceCostCenter
from backend.models.hrm import (
    HRMAssetAssignment,
    HRMCandidate,
    HRMCompensation,
    HRMCostCenter,
    HRMDepartment,
    HRMDocument,
    HRMContractExtension,
    HRMEmployee,
    HRMConfirmationRecord,
    HRMEmployeeEmploymentDetail,
    HRMEmployeeImportBatch,
    HRMEmployeeImportRow,
    HRMEmployeeLeaveOfAbsenceRecord,
    HRMEmployeeMovement,
    HRMEmployeeMovementApproval,
    HRMEmploymentTypeHistory,
    HRMAuditLog,
    HRMBranch,
    HRMEmployeeBiography,
    HRMEmployeeChangeRequest,
    HRMEmployeeContactInformation,
    HRMEmployeeDependant,
    HRMEmployeeDependantHistory,
    HRMEmployeeAssignmentHistory,
    HRMEmployeeBranchAssignment,
    HRMEmployeeBusinessUnitAssignment,
    HRMLeaveBalance,
    HRMEmployeeDepartmentAssignment,
    HRMEmployeeDocumentArchive,
    HRMEmployeeDocumentAccessLog,
    HRMEmployeeDocumentExpiryTracking,
    HRMEmployeeDocumentRejection,
    HRMEmployeeDocumentReview,
    HRMEmployeeDocumentTypeConfig,
    HRMEmployeeDocumentVersion,
    HRMEmployeeProjectAssignment,
    HRMEmployeeTeamAssignment,
    HRMEmployeeTransferRequest,
    HRMLifecycleEvent,
    HRMOnboardingTask,
    HRMPolicyAcknowledgement,
    HRMPosition,
    HRMEmployeeEmergencyContactHistory,
    HRMEmployeeProfile,
    HRMEmployeeProfileHistory,
    HRMEmployeeProfilePhoto,
    HRMEmergencyContact,
    HRMEmployeeDeathRecord,
    HRMEmployeeReinstatementRecord,
    HRMEmployeeRetirementRecord,
    HRMEmployeeStatusHistory,
    HRMEmployeeSuspensionRecord,
    HRMProbationRecord,
    HRMProbationReview,
    HRMRecruitment,
    HRMSalaryStructure,
    HRMTerminationRecord,
)
from backend.models.projects import Project
from backend.schemas.hrm.assignments_documents import (
    DocumentArchivePayload,
    DocumentRejectPayload,
    DocumentReplacePayload,
    DocumentReviewPayload,
    OrgAssignmentPayload,
    ProjectAssignmentPayload,
    TeamAssignmentPayload,
)
from backend.schemas.hrm.employees import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from backend.schemas.hrm.movements import EmployeeMovementPayload, EmployeeStatusPayload
from backend.schemas.hrm.profile import (
    BiographyPayload,
    ContactInformationPayload,
    DependantPayload,
    DependantUpdate,
    EmergencyContactPayload,
    EmergencyContactUpdate,
    EmployeeProfilePayload,
    EmployeeProfileUpdate,
)
from backend.schemas.auth import UserResponse


router = APIRouter(prefix="/hrm/employees", tags=["HRM Employees"])


def _require_hr_write(user: UserResponse):
    if user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="HRM write access requires admin or manager rights")


def _require_hr_admin(user: UserResponse):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Deleting employee master data requires admin rights")


DOCUMENT_TYPE_CONFIGS: dict[str, dict[str, Any]] = {
    "NATIONAL_ID": {"display_name": "National ID", "is_mandatory": True, "requires_verification": True, "allows_expiry_date": False, "requires_issue_date": False, "is_confidential": True, "allowed_file_types": ["pdf", "jpg", "jpeg", "png", "doc", "docx"], "max_file_size_mb": 15, "retention_policy": "employee_lifecycle_plus_7_years", "access_level_required": "hr"},
    "PASSPORT": {"display_name": "Passport", "is_mandatory": False, "requires_verification": True, "allows_expiry_date": True, "requires_issue_date": True, "is_confidential": True, "allowed_file_types": ["pdf", "jpg", "jpeg", "png"], "max_file_size_mb": 15, "retention_policy": "employee_lifecycle_plus_7_years", "access_level_required": "hr"},
    "ACADEMIC_CERTIFICATE": {"display_name": "Academic Certificate", "is_mandatory": False, "requires_verification": True, "allows_expiry_date": False, "requires_issue_date": True, "is_confidential": False, "allowed_file_types": ["pdf", "jpg", "jpeg", "png", "doc", "docx"], "max_file_size_mb": 15, "retention_policy": "employee_lifecycle_plus_7_years", "access_level_required": "manager"},
    "PROFESSIONAL_CERTIFICATION": {"display_name": "Professional Certification", "is_mandatory": False, "requires_verification": True, "allows_expiry_date": True, "requires_issue_date": True, "is_confidential": False, "allowed_file_types": ["pdf", "jpg", "jpeg", "png", "doc", "docx"], "max_file_size_mb": 15, "retention_policy": "employee_lifecycle_plus_7_years", "access_level_required": "manager"},
    "EMPLOYMENT_CONTRACT": {"display_name": "Employment Contract", "is_mandatory": True, "requires_verification": True, "allows_expiry_date": True, "requires_issue_date": True, "is_confidential": True, "allowed_file_types": ["pdf", "jpg", "jpeg", "png", "doc", "docx"], "max_file_size_mb": 20, "retention_policy": "employee_lifecycle_plus_7_years", "access_level_required": "hr"},
    "NDA": {"display_name": "NDA", "is_mandatory": False, "requires_verification": True, "allows_expiry_date": True, "requires_issue_date": True, "is_confidential": True, "allowed_file_types": ["pdf", "jpg", "jpeg", "png", "doc", "docx"], "max_file_size_mb": 15, "retention_policy": "employee_lifecycle_plus_7_years", "access_level_required": "hr"},
    "CV": {"display_name": "CV", "is_mandatory": False, "requires_verification": False, "allows_expiry_date": False, "requires_issue_date": False, "is_confidential": False, "allowed_file_types": ["pdf", "doc", "docx"], "max_file_size_mb": 10, "retention_policy": "employee_lifecycle_plus_3_years", "access_level_required": "manager"},
    "MEDICAL_DOCUMENT": {"display_name": "Medical Document", "is_mandatory": False, "requires_verification": True, "allows_expiry_date": True, "requires_issue_date": True, "is_confidential": True, "allowed_file_types": ["pdf", "jpg", "jpeg", "png"], "max_file_size_mb": 15, "retention_policy": "medical_confidential", "access_level_required": "medical"},
    "TAX_DOCUMENT": {"display_name": "Tax Document", "is_mandatory": True, "requires_verification": True, "allows_expiry_date": True, "requires_issue_date": False, "is_confidential": True, "allowed_file_types": ["pdf", "jpg", "jpeg", "png", "doc", "docx"], "max_file_size_mb": 15, "retention_policy": "statutory_plus_7_years", "access_level_required": "payroll"},
    "WORK_PERMIT": {"display_name": "Work Permit", "is_mandatory": False, "requires_verification": True, "allows_expiry_date": True, "requires_issue_date": True, "is_confidential": True, "allowed_file_types": ["pdf", "jpg", "jpeg", "png"], "max_file_size_mb": 15, "retention_policy": "statutory_plus_7_years", "access_level_required": "hr"},
}

ALLOWED_MIME_BY_EXTENSION = {
    "pdf": {"application/pdf"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "doc": {"application/msword", "application/octet-stream"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip", "application/octet-stream"},
    "xls": {"application/vnd.ms-excel", "application/octet-stream"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/zip", "application/octet-stream"},
    "webp": {"image/webp"},
}

BLOCKED_DOCUMENT_EXTENSIONS = {"exe", "bat", "cmd", "com", "dll", "js", "msi", "ps1", "sh", "vbs"}


def _document_type_key(document_type: str) -> str:
    clean = (document_type or "").strip().upper().replace("-", "_").replace("/", "_").replace(" ", "_")
    aliases = {config["display_name"].upper().replace(" ", "_"): key for key, config in DOCUMENT_TYPE_CONFIGS.items()}
    return aliases.get(clean, clean)


def _document_config(document_type: str) -> dict[str, Any]:
    key = _document_type_key(document_type)
    config = DOCUMENT_TYPE_CONFIGS.get(key)
    if not config:
        raise HTTPException(status_code=422, detail=f"Unsupported employee document type: {document_type}")
    return {"document_type": key, **config}


def _document_runtime_status(document: HRMDocument) -> str:
    if document.status == "archived" or document.is_archived:
        return "Archived"
    if document.expiry_date and document.expiry_date < date.today():
        return "Expired"
    if document.expiry_date and document.expiry_date <= date.today() + timedelta(days=30):
        return "Expiring Soon"
    if document.verification_status == "Rejected":
        return "Rejected"
    if document.verification_status == "Verified":
        return "Verified"
    return document.verification_status or "Uploaded"


def _can_access_document(user: UserResponse, document: HRMDocument) -> bool:
    if user.role == "admin":
        return True
    if document.document_type == "MEDICAL_DOCUMENT" or document.visibility_level == "medical" or document.confidentiality_level == "medical":
        return False
    if document.is_confidential or document.visibility_level in {"hr", "payroll", "restricted"}:
        return user.role == "manager"
    return user.role in {"manager", "user"}


def _secure_document_path(document: HRMDocument) -> Path:
    if not document.file_url:
        raise HTTPException(status_code=404, detail="Document file is not available")
    path = resolve_upload_url(document.file_url)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document file is missing from secure storage")
    return path


def _validate_employee_payload(db: Session, data: dict, employee_id: UUID | None = None, enforce_readiness: bool = True):
    email = (data.get("email") or "").strip().lower()
    employee_code = (data.get("employee_code") or "").strip()
    national_id = (data.get("national_id") or "").strip()
    tax_pin = (data.get("tax_pin") or "").strip()
    supervisor_id = data.get("supervisor_id")
    department_name = (data.get("department") or "").strip()
    job_title = (data.get("job_title") or "").strip()
    employment_type = _canonical_employment_type(data.get("employment_type"))

    if not data.get("first_name") or not data.get("last_name"):
        raise HTTPException(status_code=422, detail="Employee first name and last name are required")
    if enforce_readiness and not national_id:
        raise HTTPException(status_code=422, detail="National ID is required")
    if enforce_readiness and not tax_pin:
        raise HTTPException(status_code=422, detail="Tax PIN is required")
    if not email:
        raise HTTPException(status_code=422, detail="Employee email is required and must be unique")
    if enforce_readiness and not department_name:
        raise HTTPException(status_code=422, detail="Department is required")
    if enforce_readiness and not job_title:
        raise HTTPException(status_code=422, detail="Job title is required")
    if enforce_readiness and not data.get("hire_date"):
        raise HTTPException(status_code=422, detail="Employment start date is required")
    if enforce_readiness and not data.get("contract_signed"):
        raise HTTPException(status_code=422, detail="Employment contract must be signed before employee creation")
    if enforce_readiness and not data.get("budget_approved"):
        raise HTTPException(status_code=422, detail="Recruitment budget must be approved before employee creation")
    if enforce_readiness:
        type_errors = _validate_employment_type_rules(
            {
                "employment_type": employment_type,
                "start_date": data.get("employment_start_date") or data.get("hire_date"),
                "end_date": data.get("employment_end_date"),
                "institution": data.get("institution"),
                "internship_supervisor": data.get("internship_supervisor"),
                "consultancy_agreement_ref": data.get("consultancy_agreement_ref"),
                "consultancy_project": data.get("consultancy_project"),
            }
        )
        if type_errors:
            raise HTTPException(status_code=422, detail={"message": "Employment type validation failed", "errors": type_errors})
    if supervisor_id and employee_id and str(supervisor_id) == str(employee_id):
        raise HTTPException(status_code=422, detail="An employee cannot be their own line manager")

    email_query = db.query(HRMEmployee).filter(HRMEmployee.email.ilike(email))
    if employee_id:
        email_query = email_query.filter(HRMEmployee.id != employee_id)
    if email_query.first():
        raise HTTPException(status_code=409, detail="Another employee already uses this email")

    if national_id:
        national_query = db.query(HRMEmployee).filter(HRMEmployee.national_id == national_id)
        if employee_id:
            national_query = national_query.filter(HRMEmployee.id != employee_id)
        if national_query.first():
            raise HTTPException(status_code=409, detail="National ID already exists")

    if tax_pin:
        tax_query = db.query(HRMEmployee).filter(HRMEmployee.tax_pin == tax_pin)
        if employee_id:
            tax_query = tax_query.filter(HRMEmployee.id != employee_id)
        if tax_query.first():
            raise HTTPException(status_code=409, detail="Tax PIN already exists")

    if employee_code:
        code_query = db.query(HRMEmployee).filter(HRMEmployee.employee_code == employee_code)
        if employee_id:
            code_query = code_query.filter(HRMEmployee.id != employee_id)
        if code_query.first():
            raise HTTPException(status_code=409, detail="Another employee already uses this employee code")

    if supervisor_id:
        supervisor = db.query(HRMEmployee).filter(HRMEmployee.id == supervisor_id).first()
        if not supervisor:
            raise HTTPException(status_code=422, detail="Selected line manager does not exist in HRM")
        if supervisor.employment_status not in {"active", "probation", "on_leave"}:
            raise HTTPException(status_code=422, detail="Line manager must be an active internal employee")

    data["email"] = email
    data["national_id"] = national_id
    data["tax_pin"] = tax_pin
    data["employment_type"] = employment_type
    data["employment_start_date"] = data.get("employment_start_date") or data.get("hire_date")
    data["employment_type_status"] = "active"
    if employee_code:
        data["employee_code"] = employee_code
    if not enforce_readiness:
        return

    department = db.query(HRMDepartment).filter(HRMDepartment.name.ilike(department_name)).first()
    if not department or department.status != "active":
        raise HTTPException(status_code=422, detail="Department does not exist or is not active")

    position = (
        db.query(HRMPosition)
        .filter(
            HRMPosition.position_title.ilike(job_title),
            HRMPosition.department.ilike(department_name),
            HRMPosition.status == "active",
        )
        .first()
    )
    if not position:
        raise HTTPException(status_code=422, detail="Position does not exist or is not active in this department")
    occupied_query = db.query(HRMEmployee).filter(
        HRMEmployee.department.ilike(department_name),
        HRMEmployee.job_title.ilike(job_title),
    )
    if employee_id:
        occupied_query = occupied_query.filter(HRMEmployee.id != employee_id)
    occupied_count = occupied_query.count()
    approved_budget = data.get("budget_approved")
    if occupied_count >= (position.headcount_budget or 0):
        if not approved_budget:
            raise HTTPException(status_code=422, detail="Approved headcount is not available for this position")
        position.headcount_budget = occupied_count + 1
        position.description = (
            f"{position.description or ''}\nEMP-001 reserved additional approved headcount from budget approval."
        ).strip()


def _full_name(employee: HRMEmployee) -> str:
    return f"{employee.first_name} {employee.last_name}".strip()


def _employee_number_sequence(db: Session) -> EntitySequence:
    year = date.today().year
    sequence = (
        db.query(EntitySequence)
        .filter(EntitySequence.entity_key == "hrm.employees.employee_code")
        .with_for_update()
        .first()
    )
    if not sequence:
        sequence = EntitySequence(
            entity_key="hrm.employees.employee_code",
            prefix=f"EMP-{year}",
            next_number=1,
            padding=6,
        )
        db.add(sequence)
        db.flush()
    elif sequence.prefix != f"EMP-{year}":
        sequence.prefix = f"EMP-{year}"
        sequence.next_number = 1
        sequence.padding = 6

    return sequence


def _next_employee_code(db: Session) -> str:
    sequence = _employee_number_sequence(db)
    for _attempt in range(100):
        code = f"{sequence.prefix}-{str(sequence.next_number or 1).zfill(sequence.padding or 6)}"
        last_sequence = sequence.next_number or 1
        sequence.next_number = (sequence.next_number or 1) + 1
        if not db.query(HRMEmployee).filter(HRMEmployee.employee_code == code).first():
            _mirror_employee_number_sequence(db, sequence.prefix, last_sequence)
            return code
    raise HTTPException(status_code=409, detail="Could not generate a unique employee number")


def _mirror_employee_number_sequence(db: Session, prefix: str, last_sequence: int):
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS employee_number_sequences (
                id UUID PRIMARY KEY,
                year INTEGER NOT NULL,
                prefix VARCHAR(80) NOT NULL,
                last_sequence INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                UNIQUE(year, prefix)
            )
            """
        )
    )
    db.execute(
        text(
            """
            INSERT INTO employee_number_sequences (id, year, prefix, last_sequence, created_at, updated_at)
            VALUES (:id, :year, :prefix, :last_sequence, now(), now())
            ON CONFLICT (year, prefix)
            DO UPDATE SET last_sequence = GREATEST(employee_number_sequences.last_sequence, :last_sequence), updated_at = now()
            """
        ),
        {"id": str(uuid4()), "year": date.today().year, "prefix": prefix, "last_sequence": int(last_sequence)},
    )


def _employee_number_policy(db: Session) -> dict:
    sequence = _employee_number_sequence(db)
    return {
        "entity_key": sequence.entity_key,
        "pattern": f"{sequence.prefix}-{'0' * (sequence.padding or 6)}",
        "prefix": sequence.prefix,
        "next_sequence": sequence.next_number,
        "padding": sequence.padding,
        "immutable": True,
        "reuse_policy": "never_reuse",
    }


def _audit_employee_number_generation(db: Session, employee: HRMEmployee, user: UserResponse, before: str | None):
    after = employee.employee_code
    payload = {
        "employee_id": str(employee.id),
        "old_value": before,
        "new_value": after,
        "immutable": True,
        "policy": _employee_number_policy(db),
    }
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action="EMP-002_GENERATE_EMPLOYEE_NUMBER",
            entity_type="HRMEmployee",
            entity_id=str(employee.id),
            sensitivity="confidential",
            summary=f"Employee number generated and locked: {after}.",
            before_json={"employee_code": before},
            after_json=payload,
        )
    )
    db.add(
        AuditLog(
            user_email=user.email,
            module="HRM",
            action="EMP-002_GENERATE_EMPLOYEE_NUMBER",
            entity_type="HRMEmployee",
            entity_id=employee.id,
            old_value={"employee_code": before},
            new_value=payload,
            result="success",
            created_by=user.full_name,
        )
    )
    db.add(
        NotificationEvent(
            module="HRM",
            related_entity="Employee",
            related_id=employee.id,
            recipient_name="HR Officer",
            subject=f"Employee number generated: {after}",
            body=f"{_full_name(employee)} is now linked by immutable employee number {after}. Payroll, IAM, Leave, Assets, Finance, Projects, and Analytics can consume this identifier.",
            status="queued",
            created_by=user.full_name,
        )
    )


def _validate_recruitment_readiness(recruitment: HRMRecruitment | None):
    if not recruitment:
        raise HTTPException(status_code=422, detail="A recruitment readiness record is required before employee creation")
    state = f"{recruitment.recruitment_stage or ''} {recruitment.application_status or ''}".lower()
    errors = []
    if "hired" not in state:
        errors.append("Candidate status must be HIRED before employee creation")
    if not recruitment.headcount_approved:
        errors.append("Approved headcount is required before employee creation")
    if not recruitment.budget_approved:
        errors.append("Recruitment budget approval is required before employee creation")
    if not recruitment.offer_accepted:
        errors.append("Accepted offer is required before employee creation")
    if not recruitment.contract_signed:
        errors.append("Signed employment contract is required before employee creation")
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Recruitment readiness failed", "errors": errors})


def _candidate_is_hired(db: Session, candidate_id: UUID | None) -> bool:
    if not candidate_id:
        raise HTTPException(status_code=422, detail="Employee creation requires a hired recruitment candidate")
    recruitment = db.query(HRMRecruitment).filter(HRMRecruitment.id == candidate_id).first()
    if recruitment:
        _validate_recruitment_readiness(recruitment)
        return True
    candidate = db.query(HRMCandidate).filter(HRMCandidate.id == candidate_id).first()
    if candidate:
        candidate_state = f"{candidate.current_stage or ''} {candidate.status or ''}".lower()
        if "hired" not in candidate_state:
            raise HTTPException(status_code=422, detail="Candidate must be HIRED before employee creation")
        readiness = (
            db.query(HRMRecruitment)
            .filter(
                or_(
                    HRMRecruitment.candidate_email.ilike(candidate.email or "___no_email___"),
                    HRMRecruitment.candidate_name.ilike(candidate.candidate_name),
                )
            )
            .order_by(HRMRecruitment.created_at.desc())
            .first()
        )
        _validate_recruitment_readiness(readiness)
        return True
    raise HTTPException(status_code=422, detail="Candidate profile does not exist")


def _apply_recruitment_readiness(db: Session, data: dict):
    candidate_id = data.get("candidate_id")
    if not candidate_id:
        return
    recruitment = db.query(HRMRecruitment).filter(HRMRecruitment.id == candidate_id).first()
    if not recruitment:
        return
    data["contract_signed"] = bool(data.get("contract_signed") or recruitment.contract_signed)
    data["budget_approved"] = bool(data.get("budget_approved") or recruitment.budget_approved)
    data["hire_date"] = data.get("hire_date") or recruitment.target_start_date
    data["employment_start_date"] = data.get("employment_start_date") or data.get("hire_date")


def _position_code(department: str, job_title: str) -> str:
    raw = f"{department}-{job_title}".upper()
    cleaned = "".join(character if character.isalnum() else "-" for character in raw)
    parts = [part for part in cleaned.split("-") if part]
    return "POS-" + "-".join(parts[:4])[:40]


def _manager_name(db: Session, employee: HRMEmployee) -> str | None:
    if not employee.supervisor_id:
        return None
    supervisor = db.query(HRMEmployee).filter(HRMEmployee.id == employee.supervisor_id).first()
    return _full_name(supervisor) if supervisor else None


def _ensure_department(db: Session, employee: HRMEmployee):
    if not employee.department:
        return
    department = db.query(HRMDepartment).filter(HRMDepartment.name.ilike(employee.department)).first()
    if not department:
        db.add(HRMDepartment(name=employee.department, status="active", description="Created from employee master data."))


def _ensure_position(db: Session, employee: HRMEmployee):
    if not employee.department or not employee.job_title:
        return

    code = _position_code(employee.department, employee.job_title)
    position = db.query(HRMPosition).filter(HRMPosition.position_code == code).first()
    if not position:
        position = HRMPosition(
            position_code=code,
            position_title=employee.job_title,
            department=employee.department,
            job_group=employee.job_group,
            salary_grade=employee.salary_grade,
            reports_to_position=None,
            headcount_budget=1,
            current_headcount=0,
            status="active",
            description="Created from employee master data.",
        )
        db.add(position)
        db.flush()

    position.job_group = employee.job_group or position.job_group
    position.salary_grade = employee.salary_grade or position.salary_grade
    position.current_headcount = (
        db.query(HRMEmployee)
        .filter(HRMEmployee.department == employee.department, HRMEmployee.job_title == employee.job_title)
        .count()
    )


def _ensure_payroll_profile(db: Session, employee: HRMEmployee):
    if _validate_employment_type_rules(
        {
            "employment_type": employee.employment_type,
            "start_date": employee.employment_start_date or employee.hire_date,
            "end_date": employee.employment_end_date,
            "institution": employee.institution,
            "internship_supervisor": employee.internship_supervisor,
            "consultancy_agreement_ref": employee.consultancy_agreement_ref,
            "consultancy_project": employee.consultancy_project,
        },
        for_activation=True,
    ):
        employee.payroll_profile_status = "blocked"
        return
    existing = db.query(HRMSalaryStructure).filter(HRMSalaryStructure.employee_id == employee.id).first()
    if existing:
        existing.base_salary = Decimal(str(employee.base_salary or existing.base_salary or 0))
        existing.pay_frequency = employee.pay_frequency or existing.pay_frequency
        existing.effective_from = employee.hire_date or existing.effective_from
        employee.payroll_profile_status = "created"
        compensation = db.query(HRMCompensation).filter(HRMCompensation.employee_id == employee.id).first()
        if compensation:
            compensation.base_salary = Decimal(str(employee.base_salary or compensation.base_salary or 0))
            compensation.pay_frequency = employee.pay_frequency or compensation.pay_frequency
            compensation.effective_date = employee.hire_date or compensation.effective_date
        return
    db.add(
        HRMSalaryStructure(
            employee_id=employee.id,
            structure_name=f"{employee.employee_code} payroll profile",
            base_salary=Decimal(str(employee.base_salary or 0)),
            currency="KES",
            pay_frequency=employee.pay_frequency or "monthly",
            effective_from=employee.hire_date or date.today(),
            status="draft",
        )
    )
    db.add(
        HRMCompensation(
            employee_id=employee.id,
            effective_date=employee.hire_date or date.today(),
            compensation_type="salary",
            base_salary=Decimal(str(employee.base_salary or 0)),
            currency="KES",
            pay_frequency=employee.pay_frequency or "monthly",
            approval_status="pending",
            notes="Created automatically by EMP-001 employee creation workflow.",
        )
    )
    employee.payroll_profile_status = "created"


def _ensure_iam_request(db: Session, employee: HRMEmployee):
    existing = db.query(UserAccessProfile).filter(UserAccessProfile.employee_id == employee.id).first()
    if existing:
        existing.user_email = employee.email
        existing.department = employee.department
        existing.role_name = employee.role_category or employee.job_title
        existing.provisioning_status = existing.provisioning_status or "requested"
        employee.iam_request_status = existing.provisioning_status or "requested"
        return
    db.add(
        UserAccessProfile(
            user_email=employee.email,
            employee_id=employee.id,
            department=employee.department,
            role_name=employee.role_category or employee.job_title,
            access_level="standard",
            privileged=False,
            provisioning_status="requested",
            status="pending",
            created_by="EMP-001",
        )
    )
    db.add(
        EnterpriseEvent(
            event_type="AccountProvisioningRequested",
            source_module="HRM",
            target_module="IAM",
            payload={
                "employee_id": str(employee.id),
                "employee_code": employee.employee_code,
                "email": employee.email,
                "department": employee.department,
            },
            status="pending",
            created_by="EMP-001",
        )
    )
    employee.iam_request_status = "requested"


def _ensure_finance_mapping(db: Session, employee: HRMEmployee):
    if not employee.department:
        return
    code = "CC-" + "".join(character for character in employee.department.upper() if character.isalnum())[:24]
    cost_center = db.query(HRMCostCenter).filter(HRMCostCenter.cost_center_code == code).first()
    if not cost_center:
        cost_center = HRMCostCenter(
            cost_center_code=code,
            cost_center_name=f"{employee.department} Cost Center",
            department=employee.department,
            budget_owner=_manager_name(db, employee),
            status="active",
        )
        db.add(cost_center)
    else:
        cost_center.department = employee.department
        cost_center.budget_owner = _manager_name(db, employee) or cost_center.budget_owner

    finance_cost_center = db.query(FinanceCostCenter).filter(FinanceCostCenter.cost_center_code == code).first()
    if not finance_cost_center:
        db.add(
            FinanceCostCenter(
                cost_center_code=code,
                cost_center_name=f"{employee.department} Cost Center",
                department=employee.department,
                owner_employee_id=employee.supervisor_id,
                status="active",
            )
        )
    else:
        finance_cost_center.department = employee.department
        finance_cost_center.owner_employee_id = employee.supervisor_id or finance_cost_center.owner_employee_id
    employee.finance_mapping_status = "mapped"


def _ensure_asset_request(db: Session, employee: HRMEmployee):
    existing = (
        db.query(HRMAssetAssignment)
        .filter(HRMAssetAssignment.employee_id == employee.id, HRMAssetAssignment.asset_name == "Onboarding asset request")
        .first()
    )
    if existing:
        existing.assigned_date = employee.hire_date or existing.assigned_date
        existing.status = existing.status or "requested"
        employee.asset_request_status = existing.status or "requested"
        return
    db.add(
        HRMAssetAssignment(
            employee_id=employee.id,
            asset_name="Onboarding asset request",
            asset_tag=f"REQ-{employee.employee_code}",
            assigned_date=employee.hire_date or date.today(),
            condition_on_issue="pending allocation",
            status="requested",
            notes="Created automatically by EMP-001 for Operations/IT asset allocation.",
        )
    )
    employee.asset_request_status = "requested"


def _queue_employee_notifications(db: Session, employee: HRMEmployee, user: UserResponse):
    recipients = [
        ("Employee", _full_name(employee), employee.email),
        ("Hiring Manager", _manager_name(db, employee), None),
        ("HR", "HR Team", None),
        ("IT Support", "IT Support", None),
        ("Payroll Officer", "Payroll Officer", None),
        ("Finance Officer", "Finance Officer", None),
    ]
    for role, name, email in recipients:
        db.add(
            NotificationEvent(
                module="HRM",
                related_entity="Employee",
                related_id=employee.id,
                recipient_name=name or role,
                recipient_email=email,
                subject=f"EMP-001 employee record created: {_full_name(employee)}",
                body=f"{_full_name(employee)} has been created with status Pending Activation. Required follow-up: {role}.",
                status="queued",
                created_by=user.full_name,
            )
        )


def _audit_employee_creation(db: Session, employee: HRMEmployee, user: UserResponse):
    after = {
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "email": employee.email,
        "department": employee.department,
        "job_title": employee.job_title,
        "status": employee.employment_status,
        "payroll_profile_status": employee.payroll_profile_status,
        "iam_request_status": employee.iam_request_status,
        "finance_mapping_status": employee.finance_mapping_status,
        "asset_request_status": employee.asset_request_status,
    }
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action="EMP-001_CREATE_EMPLOYEE",
            entity_type="HRMEmployee",
            entity_id=str(employee.id),
            sensitivity="confidential",
            summary=f"Employee master record created by {user.full_name}.",
            before_json=None,
            after_json=after,
        )
    )
    db.add(
        AuditLog(
            user_email=user.email,
            module="HRM",
            action="EMP-001_CREATE_EMPLOYEE",
            entity_type="HRMEmployee",
            entity_id=employee.id,
            new_value=after,
            result="success",
            created_by=user.full_name,
        )
    )


def _ensure_staff_role(db: Session, employee: HRMEmployee):
    if not employee.role_category:
        return

    existing = (
        db.query(StaffRoleAssignment)
        .filter(
            StaffRoleAssignment.employee_id == employee.id,
            StaffRoleAssignment.role_name == employee.role_category,
            StaffRoleAssignment.status == "active",
        )
        .first()
    )
    if existing:
        existing.staff_name = _full_name(employee)
        existing.department = employee.department
        existing.line_manager = _manager_name(db, employee)
        return

    db.add(
        StaffRoleAssignment(
            employee_id=employee.id,
            staff_name=_full_name(employee),
            role_name=employee.role_category,
            department=employee.department,
            role_scope=employee.branch,
            line_manager=_manager_name(db, employee),
            effective_from=employee.hire_date or date.today(),
            status="active",
            notes="Created from HRM employee source-of-truth record.",
        )
    )


def _ensure_leave_balances(db: Session, employee: HRMEmployee):
    fiscal_year = str((employee.hire_date or date.today()).year)
    defaults = {"Annual Leave": 21, "Sick Leave": 14, "Compassionate Leave": 5}
    for leave_type, days in defaults.items():
        existing = (
            db.query(HRMLeaveBalance)
            .filter(
                HRMLeaveBalance.employee_id == employee.id,
                HRMLeaveBalance.leave_type == leave_type,
                HRMLeaveBalance.fiscal_year == fiscal_year,
            )
            .first()
        )
        if not existing:
            db.add(
                HRMLeaveBalance(
                    employee_id=employee.id,
                    leave_type=leave_type,
                    fiscal_year=fiscal_year,
                    opening_balance=0,
                    accrued_days=days,
                    used_days=0,
                    adjusted_days=0,
                    available_days=days,
                    status="active",
                    notes="Created automatically from HRM employee onboarding.",
                )
            )


def _ensure_onboarding(db: Session, employee: HRMEmployee):
    start_date = employee.hire_date or date.today()
    tasks = [
        ("Employee master data verification", "HR", "HR"),
        ("Policy acknowledgement", "Compliance", "HR"),
        ("Payroll and benefits setup", "Finance", "Finance"),
        ("Equipment and access provisioning", "IT", "Technical"),
        ("Line manager onboarding plan", "Manager", _manager_name(db, employee)),
    ]
    for task_name, category, owner in tasks:
        existing = (
            db.query(HRMOnboardingTask)
            .filter(HRMOnboardingTask.employee_id == employee.id, HRMOnboardingTask.task_name == task_name)
            .first()
        )
        if not existing:
            db.add(
                HRMOnboardingTask(
                    employee_id=employee.id,
                    task_name=task_name,
                    task_category=category,
                    owner=owner,
                    due_date=start_date + timedelta(days=14),
                    status="pending",
                    notes="Created automatically from HRM employee onboarding.",
                )
            )


def _ensure_policy_acknowledgements(db: Session, employee: HRMEmployee):
    due_date = (employee.hire_date or date.today()) + timedelta(days=14)
    for policy_name in ["Employee Handbook", "Code of Conduct", "Information Security Policy"]:
        existing = (
            db.query(HRMPolicyAcknowledgement)
            .filter(
                HRMPolicyAcknowledgement.employee_id == employee.id,
                HRMPolicyAcknowledgement.policy_name == policy_name,
            )
            .first()
        )
        if not existing:
            db.add(
                HRMPolicyAcknowledgement(
                    employee_id=employee.id,
                    policy_name=policy_name,
                    policy_version="1.0",
                    due_date=due_date,
                    status="pending",
                    notes="Created automatically from HRM employee onboarding.",
                )
            )


def _add_lifecycle_event(db: Session, employee: HRMEmployee, event_type: str, from_value: str | None, to_value: str | None):
    effective_date = employee.hire_date or date.today()
    db.add(
        HRMLifecycleEvent(
            employee_id=employee.id,
            event_type=event_type,
            effective_date=effective_date,
            from_value=from_value,
            to_value=to_value,
            reason="System-generated HRM source-of-truth event.",
            status="approved",
        )
    )


def _sync_employee_foundation(db: Session, employee: HRMEmployee, include_leave_balances: bool = False):
    _ensure_department(db, employee)
    _ensure_position(db, employee)
    _ensure_staff_role(db, employee)
    if include_leave_balances:
        _ensure_leave_balances(db, employee)
    _ensure_onboarding(db, employee)
    _ensure_policy_acknowledgements(db, employee)
    _ensure_payroll_profile(db, employee)
    _ensure_iam_request(db, employee)
    _ensure_finance_mapping(db, employee)
    _ensure_asset_request(db, employee)
    employee.onboarding_status = "created"


ACTIVE_EMPLOYEE_STATUSES = {"active", "probation", "confirmed", "on_leave"}
EMPLOYEE_MOVEMENT_RULES = {
    "promote": ("EMP-055", "promotion", "Promote Employee"),
    "demote": ("EMP-056", "demotion", "Demote Employee"),
    "transfer": ("EMP-057", "transfer", "Transfer Employee"),
    "change-role": ("EMP-058", "role_change", "Change Job Role"),
    "acting-appointment": ("EMP-059", "acting_appointment", "Acting Appointment"),
    "secondment": ("EMP-060", "secondment", "Secondment"),
    "internal-transfer": ("EMP-061", "internal_transfer", "Internal Transfer"),
    "temporary-assignment": ("EMP-062", "temporary_assignment", "Temporary Assignment"),
    "return-from-assignment": ("EMP-063", "return_from_assignment", "Return From Assignment"),
}

EMPLOYEE_STATUS_RULES = {
    "suspend": ("EMP-067", "suspended", "Suspend Employee"),
    "reinstate": ("EMP-068", "active", "Reinstate Employee"),
    "leave-of-absence": ("EMP-069", "leave_of_absence", "Leave Of Absence"),
    "return-from-leave-of-absence": ("EMP-070", "active", "Return From Leave Of Absence"),
    "mark-inactive": ("EMP-071", "inactive", "Mark Employee Inactive"),
    "terminate": ("EMP-072", "terminated", "Terminate Employee"),
    "retire": ("EMP-073", "retired", "Process Retirement"),
    "death-in-service": ("EMP-074", "deceased", "Record Death In Service"),
}


def _employee_current_job(employee: HRMEmployee) -> dict[str, Any]:
    return _jsonable(
        {
            "job_title": employee.job_title,
            "job_group": employee.job_group,
            "salary_grade": employee.salary_grade,
            "salary_band": employee.salary_band,
            "department": employee.department,
            "branch": employee.branch,
            "business_unit": employee.business_unit,
            "cost_center_code": employee.cost_center_code,
            "role_category": employee.role_category,
            "supervisor_id": employee.supervisor_id,
        }
    )


def _movement_new_job(payload: EmployeeMovementPayload) -> dict[str, Any]:
    return _jsonable(
        {
            "job_title": payload.new_job_title,
            "job_grade": payload.new_job_grade,
            "salary_band": payload.new_salary_band,
            "department": payload.new_department,
            "branch": payload.new_branch,
            "business_unit": payload.new_business_unit,
            "cost_center": payload.new_cost_center,
            "manager_id": payload.new_manager_id,
            "role": payload.new_role,
            "assignment_owner": payload.assignment_owner,
            "host_unit": payload.host_unit,
            "host_organization": payload.host_organization,
            "allocation_percentage": payload.allocation_percentage,
            "cost_allocation_rule": payload.cost_allocation_rule,
            **(payload.metadata or {}),
        }
    )


def _queue_employee_workflow_integrations(db: Session, employee: HRMEmployee, user: UserResponse, buc_code: str, action: str, payload: dict[str, Any]):
    integration_events = [
        {"target": "Payroll", "status": "queued", "reason": "Eligibility, pay, allowance, final settlement, or payroll-impact review"},
        {"target": "IAM", "status": "queued", "reason": "Access review, elevation, revocation, or reactivation"},
        {"target": "Finance", "status": "queued", "reason": "Cost center, benefit, settlement, or budget impact review"},
        {"target": "Leave", "status": "queued", "reason": "Leave eligibility and balance impact review"},
        {"target": "Attendance", "status": "queued", "reason": "Attendance rule and schedule eligibility review"},
        {"target": "Projects", "status": "queued", "reason": "Resource assignment and project allocation review"},
        {"target": "Assets", "status": "queued", "reason": "Asset assignment, recovery, or clearance review"},
        {"target": "Reporting", "status": "queued", "reason": "Headcount and workforce analytics update"},
    ]
    db.add(
        EnterpriseEvent(
            event_type=f"{buc_code}.{action}",
            source_module="HRM",
            target_module="Enterprise",
            payload=_jsonable({"employee_id": employee.id, "employee_code": employee.employee_code, "action": action, **payload, "integrations": integration_events}),
            event_status="pending",
            created_by=user.full_name,
        )
    )
    return integration_events


def _movement_notify(db: Session, employee: HRMEmployee, user: UserResponse, subject: str, body: str):
    for recipient in ["Employee", "Manager", "HR", "Payroll", "IAM", "Finance"]:
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


def _record_status_history(db: Session, employee: HRMEmployee, user: UserResponse, buc_code: str, old_status: str | None, new_status: str, payload: EmployeeStatusPayload, metadata: dict[str, Any]):
    record = HRMEmployeeStatusHistory(
        employee_id=employee.id,
        status_code=buc_code,
        old_status=old_status,
        new_status=new_status,
        effective_date=payload.effective_date or payload.return_date or payload.date_of_death or date.today(),
        end_date=payload.end_date or payload.expected_return_date,
        reason=payload.reason,
        initiated_by=user.full_name,
        approved_by=user.full_name,
        approval_status="approved",
        workflow_status="completed",
        supporting_document_url=payload.supporting_document_url,
        metadata_json=_jsonable(metadata),
    )
    db.add(record)
    _add_lifecycle_event(db, employee, buc_code, old_status, new_status)
    return record


def _execute_employee_movement(db: Session, employee: HRMEmployee, user: UserResponse, action_key: str, payload: EmployeeMovementPayload):
    buc_code, movement_type, label = EMPLOYEE_MOVEMENT_RULES[action_key]
    if employee.employment_status not in ACTIVE_EMPLOYEE_STATUSES:
        raise HTTPException(status_code=422, detail=f"{label} requires an active employee")
    if action_key in {"acting-appointment", "secondment", "temporary-assignment"} and not (payload.start_date and payload.end_date):
        raise HTTPException(status_code=422, detail=f"{label} requires start and end dates")
    if action_key == "secondment" and not (payload.host_unit or payload.host_organization):
        raise HTTPException(status_code=422, detail="Secondment requires a host unit or host organization")
    if action_key in {"return-from-assignment"} and not payload.return_date:
        raise HTTPException(status_code=422, detail="Return date is required")
    if action_key in {"transfer", "internal-transfer"} and not (payload.new_department or payload.new_branch or payload.new_business_unit or payload.new_manager_id or payload.new_cost_center):
        raise HTTPException(status_code=422, detail="Transfer requires at least one new organization assignment")
    before = _employee_current_job(employee)
    after = _movement_new_job(payload)
    integrations = _queue_employee_workflow_integrations(db, employee, user, buc_code, movement_type, {"effective_date": payload.effective_date, "reason": payload.reason, "new_job_details": after})
    movement = HRMEmployeeMovement(
        employee_id=employee.id,
        movement_code=buc_code,
        movement_type=movement_type,
        current_status=employee.employment_status,
        new_status=employee.employment_status,
        current_job_details=before,
        new_job_details=after,
        effective_date=payload.effective_date,
        end_date=payload.end_date,
        reason=payload.reason,
        supporting_document_url=payload.supporting_document_url,
        initiated_by=user.full_name,
        approved_by=user.full_name,
        approval_status="approved",
        workflow_status="completed",
        integration_events=integrations,
    )
    db.add(movement)
    db.flush()
    db.add(HRMEmployeeMovementApproval(movement_id=movement.id, employee_id=employee.id, approver_role="HR_ADMIN", approver_name=user.full_name, decision="approved", comments="Auto-approved by HR admin prototype workflow."))
    if action_key in {"promote", "demote", "change-role", "transfer", "internal-transfer"}:
        if payload.new_job_title:
            employee.job_title = payload.new_job_title
        if payload.new_job_grade:
            employee.salary_grade = payload.new_job_grade
        if payload.new_salary_band:
            employee.salary_band = payload.new_salary_band
        if payload.new_department:
            employee.department = payload.new_department
        if payload.new_branch:
            employee.branch = payload.new_branch
        if payload.new_business_unit:
            employee.business_unit = payload.new_business_unit
        if payload.new_cost_center:
            employee.cost_center_code = payload.new_cost_center
        if payload.new_manager_id:
            employee.supervisor_id = payload.new_manager_id
        if payload.new_role:
            employee.role_category = payload.new_role
    elif action_key in {"acting-appointment", "secondment", "temporary-assignment"}:
        employee.employment_status = "on_assignment"
    elif action_key == "return-from-assignment":
        employee.employment_status = "active"
    db.add(HRMEmployeeAssignmentHistory(employee_id=employee.id, buc_code=buc_code, assignment_type=movement_type, previous_value=str(before), new_value=str(after), effective_from=payload.effective_date, effective_to=payload.end_date, reason=payload.reason, status="active", initiated_by=user.full_name, audit_reference=str(movement.id)))
    _audit_profile_event(db, employee, user, f"{buc_code}_{movement_type.upper()}", f"{label} recorded for {_full_name(employee)}.", before=before, after=_serialize_model(movement))
    _movement_notify(db, employee, user, f"{label}: {employee.employee_code}", f"{label} was recorded effective {payload.effective_date}.")
    _sync_employee_foundation(db, employee)
    db.commit()
    return _serialize_model(movement)


def _execute_employee_status(db: Session, employee: HRMEmployee, user: UserResponse, action_key: str, payload: EmployeeStatusPayload):
    buc_code, new_status, label = EMPLOYEE_STATUS_RULES[action_key]
    old_status = employee.employment_status
    effective = payload.effective_date or payload.return_date or payload.date_of_death or date.today()
    if action_key in {"suspend", "leave-of-absence", "mark-inactive"} and old_status not in ACTIVE_EMPLOYEE_STATUSES:
        raise HTTPException(status_code=422, detail=f"{label} requires an active employee")
    if action_key == "reinstate" and old_status not in {"suspended", "inactive"}:
        raise HTTPException(status_code=422, detail="Reinstatement requires suspended or inactive employee")
    if action_key == "return-from-leave-of-absence" and old_status != "leave_of_absence":
        raise HTTPException(status_code=422, detail="Employee must currently be on leave of absence")
    if action_key == "death-in-service" and not (payload.date_of_death and payload.supporting_document_url):
        raise HTTPException(status_code=422, detail="Date of death and supporting documentation are required")
    if action_key == "retire" and not payload.retirement_type:
        raise HTTPException(status_code=422, detail="Retirement type is required")
    if action_key == "terminate" and not payload.termination_type:
        raise HTTPException(status_code=422, detail="Termination type is required")
    if action_key == "leave-of-absence" and not (payload.leave_type and payload.expected_return_date):
        raise HTTPException(status_code=422, detail="Leave of absence type and expected return date are required")
    employee.employment_status = new_status
    if new_status in {"terminated", "retired", "deceased", "inactive", "suspended"}:
        employee.iam_request_status = "deactivation_queued"
        employee.payroll_profile_status = "review_required"
    elif new_status == "active":
        employee.iam_request_status = "reactivation_review"
        employee.payroll_profile_status = "review_required"
    integrations = _queue_employee_workflow_integrations(db, employee, user, buc_code, action_key, {"old_status": old_status, "new_status": new_status, "effective_date": effective, "reason": payload.reason})
    status_row = _record_status_history(db, employee, user, buc_code, old_status, new_status, payload, {"integrations": integrations, **(payload.metadata or {})})
    if action_key == "suspend":
        db.add(HRMEmployeeSuspensionRecord(employee_id=employee.id, suspension_type=payload.suspension_type or "administrative", start_date=effective, expected_end_date=payload.end_date, reason=payload.reason, paid=True if payload.paid is None else payload.paid, created_by=user.full_name))
    elif action_key == "reinstate":
        db.add(HRMEmployeeReinstatementRecord(employee_id=employee.id, reinstatement_date=effective, previous_status=old_status, reason=payload.reason, created_by=user.full_name))
    elif action_key == "leave-of-absence":
        db.add(HRMEmployeeLeaveOfAbsenceRecord(employee_id=employee.id, leave_type=payload.leave_type or "Leave of Absence", start_date=effective, expected_return_date=payload.expected_return_date or effective, reason=payload.reason, payroll_impact=payload.payroll_impact or "review_required", iam_access_impact=payload.iam_access_impact or "review_required", created_by=user.full_name))
    elif action_key == "return-from-leave-of-absence":
        loa = db.query(HRMEmployeeLeaveOfAbsenceRecord).filter(HRMEmployeeLeaveOfAbsenceRecord.employee_id == employee.id, HRMEmployeeLeaveOfAbsenceRecord.status == "active").order_by(HRMEmployeeLeaveOfAbsenceRecord.created_at.desc()).first()
        if loa:
            loa.actual_return_date = effective
            loa.status = "returned"
    elif action_key == "terminate":
        db.add(HRMTerminationRecord(employee_id=employee.id, termination_type=payload.termination_type or "termination", termination_date=effective, reason=payload.reason, status="approved"))
    elif action_key == "retire":
        db.add(HRMEmployeeRetirementRecord(employee_id=employee.id, retirement_type=payload.retirement_type or "normal", retirement_date=effective, reason=payload.reason, created_by=user.full_name))
    elif action_key == "death-in-service":
        db.add(HRMEmployeeDeathRecord(employee_id=employee.id, date_of_death=payload.date_of_death or effective, supporting_document_url=payload.supporting_document_url or "", notes=payload.reason, created_by=user.full_name))
    _audit_profile_event(db, employee, user, f"{buc_code}_{action_key.upper().replace('-', '_')}", f"{label} recorded for {_full_name(employee)}.", before={"employment_status": old_status}, after=_serialize_model(status_row))
    _movement_notify(db, employee, user, f"{label}: {employee.employee_code}", f"{label} was recorded effective {effective}.")
    db.commit()
    return _serialize_model(status_row)


ACTIVATABLE_STATUSES = {"draft", "pending_activation", "onboarding", "employee_number_assigned"}


def _is_top_level_employee(employee: HRMEmployee) -> bool:
    title = f"{employee.job_title or ''} {employee.role_category or ''}".lower()
    return any(term in title for term in ["ceo", "chief executive", "executive director", "managing director", "founder"])


def _has_required_document(db: Session, employee: HRMEmployee, labels: set[str]) -> bool:
    documents = (
        db.query(HRMDocument)
        .filter(HRMDocument.employee_id == employee.id, HRMDocument.status == "active")
        .all()
    )
    for document in documents:
        haystack = f"{document.document_title or ''} {document.document_type or ''} {document.file_name or ''}".lower()
        if any(label in haystack for label in labels):
            return True
    return False


def _activation_readiness(db: Session, employee: HRMEmployee, allow_early_activation: bool = False) -> dict[str, Any]:
    department = db.query(HRMDepartment).filter(HRMDepartment.name.ilike(employee.department or "")).first()
    manager = db.query(HRMEmployee).filter(HRMEmployee.id == employee.supervisor_id).first() if employee.supervisor_id else None
    position = (
        db.query(HRMPosition)
        .filter(
            HRMPosition.position_title.ilike(employee.job_title or ""),
            HRMPosition.department.ilike(employee.department or ""),
            HRMPosition.status == "active",
        )
        .first()
    )
    checks = [
        {"key": "employee_number", "label": "Employee Number Exists", "met": bool(employee.employee_code), "blocking": True, "error": "Employee Number Required"},
        {"key": "status", "label": "Status Allows Activation", "met": employee.employment_status in ACTIVATABLE_STATUSES, "blocking": True, "error": "Employee status does not allow activation"},
        {"key": "department", "label": "Active Department Assigned", "met": bool(department and department.status == "active"), "blocking": True, "error": "Department Assignment Required"},
        {"key": "position", "label": "Active Job Title Assigned", "met": bool(position), "blocking": True, "error": "Active position required"},
        {
            "key": "manager",
            "label": "Reporting Manager Assigned",
            "met": bool(_is_top_level_employee(employee) or (manager and manager.employment_status in {"active", "probation", "on_leave"})),
            "blocking": True,
            "error": "Reporting Manager Required",
        },
        {"key": "start_date", "label": "Employment Start Date Exists", "met": bool(employee.hire_date), "blocking": True, "error": "Employment start date required"},
        {
            "key": "start_date_reached",
            "label": "Start Date Reached",
            "met": bool(allow_early_activation or not employee.hire_date or employee.hire_date <= date.today()),
            "blocking": True,
            "error": "Employee Cannot Be Activated Before Start Date",
        },
        {
            "key": "contract",
            "label": "Signed Employment Contract",
            "met": bool(employee.contract_signed or _has_required_document(db, employee, {"contract", "employment contract"})),
            "blocking": True,
            "error": "Signed Employment Contract Missing",
        },
        {"key": "national_id", "label": "National ID or Passport", "met": bool(employee.national_id), "blocking": True, "error": "National ID or Passport Missing"},
        {"key": "tax_pin", "label": "KRA PIN or Tax PIN", "met": bool(employee.tax_pin), "blocking": True, "error": "KRA PIN Missing"},
        {
            "key": "employment_type_rules",
            "label": "Employment Type Rules Complete",
            "met": not _validate_employment_type_rules(
                {
                    "employment_type": employee.employment_type,
                    "start_date": employee.employment_start_date or employee.hire_date,
                    "end_date": employee.employment_end_date,
                    "institution": employee.institution,
                    "internship_supervisor": employee.internship_supervisor,
                    "consultancy_agreement_ref": employee.consultancy_agreement_ref,
                    "consultancy_project": employee.consultancy_project,
                },
                for_activation=True,
            ),
            "blocking": True,
            "error": "Employment type rules incomplete",
        },
        {"key": "payroll_profile", "label": "Payroll Profile Ready", "met": employee.payroll_profile_status in {"created", "active"}, "blocking": False, "error": None},
        {"key": "iam_request", "label": "IAM Request Ready", "met": employee.iam_request_status in {"requested", "provisioned", "active"}, "blocking": False, "error": None},
        {"key": "asset_request", "label": "Asset Request Ready", "met": employee.asset_request_status in {"requested", "assigned"}, "blocking": False, "error": None},
    ]
    blocking_failures = [check["error"] for check in checks if check["blocking"] and not check["met"]]
    readiness_score = round((sum(1 for check in checks if check["met"]) / len(checks)) * 100)
    return {
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "employee_name": _full_name(employee),
        "current_status": employee.employment_status,
        "activation_date": employee.activation_date.isoformat() if employee.activation_date else None,
        "activated_by": employee.activated_by,
        "readiness_score": readiness_score,
        "ready": not blocking_failures,
        "blocking_errors": blocking_failures,
        "checks": checks,
        "downstream": {
            "payroll_profile_status": employee.payroll_profile_status,
            "iam_request_status": employee.iam_request_status,
            "onboarding_status": employee.onboarding_status,
            "finance_mapping_status": employee.finance_mapping_status,
            "asset_request_status": employee.asset_request_status,
        },
    }


def _queue_activation_notifications(db: Session, employee: HRMEmployee, user: UserResponse):
    recipients = [
        ("Employee", _full_name(employee), employee.email, "Welcome to the Organization"),
        ("Manager", _manager_name(db, employee), None, "New Team Member Activated"),
        ("Payroll Team", "Payroll Team", None, "Employee Ready For Payroll Processing"),
        ("IT Team", "IT Team", None, "Provision User Access"),
        ("HR Team", "HR Team", None, "Employee Successfully Activated"),
    ]
    for role, name, email, subject in recipients:
        db.add(
            NotificationEvent(
                module="HRM",
                related_entity="Employee",
                related_id=employee.id,
                recipient_name=name or role,
                recipient_email=email,
                subject=subject,
                body=f"{_full_name(employee)} ({employee.employee_code}) was activated by {user.full_name}.",
                status="queued",
                created_by=user.full_name,
            )
        )


def _activate_employee_record(db: Session, employee: HRMEmployee, user: UserResponse, allow_early_activation: bool = False) -> dict[str, Any]:
    if employee.employment_status == "active":
        raise HTTPException(status_code=409, detail="Employee is already active")
    readiness = _activation_readiness(db, employee, allow_early_activation)
    if not readiness["ready"]:
        raise HTTPException(status_code=422, detail={"message": "Employee activation readiness failed", "errors": readiness["blocking_errors"], "readiness": readiness})

    previous_status = employee.employment_status
    _sync_employee_foundation(db, employee, include_leave_balances=True)
    employee.employment_status = "active"
    employee.activation_date = datetime.utcnow()
    employee.activated_by = user.full_name
    employee.payroll_profile_status = "active"
    employee.iam_request_status = "requested"
    employee.onboarding_status = "completed"
    employee.finance_mapping_status = "mapped"
    employee.asset_request_status = employee.asset_request_status or "requested"

    _add_lifecycle_event(db, employee, "activation", previous_status, "active")
    _queue_activation_notifications(db, employee, user)
    for event_type, target_module in [
        ("EmployeeActivated", "HRM"),
        ("PayrollEnrollmentRequested", "Payroll"),
        ("LeaveEntitlementsAllocated", "Leave"),
        ("AttendanceEnrollmentRequested", "Attendance"),
        ("AccountProvisioningRequested", "IAM"),
        ("AssetAllocationRequested", "Operations"),
        ("EmployeeCostCenterMapped", "Finance"),
        ("ProjectAssignmentEligibilityEnabled", "Projects"),
    ]:
        db.add(
            EnterpriseEvent(
                event_type=event_type,
                source_module="HRM",
                target_module=target_module,
                payload={
                    "employee_id": str(employee.id),
                    "employee_code": employee.employee_code,
                    "employee_name": _full_name(employee),
                    "department": employee.department,
                    "manager": _manager_name(db, employee),
                    "activation_date": employee.activation_date.isoformat(),
                },
                status="pending" if event_type != "EmployeeActivated" else "processed",
                processed_by=user.full_name if event_type == "EmployeeActivated" else None,
                created_by=user.full_name,
            )
        )

    audit_payload = {
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "activation_date": employee.activation_date.isoformat(),
        "activated_by": user.full_name,
        "previous_status": previous_status,
        "new_status": "active",
        "readiness_score": 100,
        "downstream": readiness["downstream"],
    }
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action="EMP-004_ACTIVATE_EMPLOYEE",
            entity_type="HRMEmployee",
            entity_id=str(employee.id),
            sensitivity="confidential",
            summary=f"Employee activated by {user.full_name}.",
            before_json={"employment_status": previous_status, "activation_date": None},
            after_json=audit_payload,
        )
    )
    db.add(
        AuditLog(
            user_email=user.email,
            module="HRM",
            action="EMP-004_ACTIVATE_EMPLOYEE",
            entity_type="HRMEmployee",
            entity_id=employee.id,
            old_value={"employment_status": previous_status},
            new_value=audit_payload,
            result="success",
            created_by=user.full_name,
        )
    )
    return {
        **readiness,
        "current_status": "active",
        "activation_date": employee.activation_date.isoformat(),
        "activated_by": employee.activated_by,
        "readiness_score": 100,
        "ready": True,
        "blocking_errors": [],
        "downstream": {
            "payroll_profile_status": employee.payroll_profile_status,
            "iam_request_status": employee.iam_request_status,
            "onboarding_status": employee.onboarding_status,
            "finance_mapping_status": employee.finance_mapping_status,
            "asset_request_status": employee.asset_request_status,
        },
    }


def process_expired_employment_engagements(db: Session, user_label: str = "EMP-005 scheduler") -> dict[str, int]:
    today = date.today()
    employees = db.query(HRMEmployee).filter(HRMEmployee.employment_status == "active").all()
    checked = deactivated = reminders = 0
    for employee in employees:
        checked += 1
        employee.employment_type = _canonical_employment_type(employee.employment_type)
        end_date = employee.extension_approved_until or employee.employment_end_date
        if employee.employment_type not in EXPIRING_EMPLOYMENT_TYPES or not end_date:
            continue
        days = (end_date - today).days
        if days in {90, 60, 30, 7}:
            reminders += 1
            db.add(
                NotificationEvent(
                    module="HRM",
                    related_entity="Employee",
                    related_id=employee.id,
                    recipient_name="HR Team",
                    subject=f"{employee.employment_type} engagement expires in {days} days",
                    body=f"{_full_name(employee)} ({employee.employee_code}) ends on {end_date}. Extend or prepare offboarding.",
                    status="queued",
                    created_by=user_label,
                )
            )
        if days < 0:
            previous_status = employee.employment_status
            employee.employment_status = "inactive"
            employee.employment_type_status = "expired"
            employee.payroll_profile_status = "blocked"
            employee.iam_request_status = "deactivation_requested"
            _add_lifecycle_event(db, employee, "employment_expired", previous_status, "inactive")
            db.add(
                EnterpriseEvent(
                    event_type="AccessDeactivationRequested",
                    source_module="HRM",
                    target_module="IAM",
                    payload={"employee_id": str(employee.id), "employee_code": employee.employee_code, "reason": "employment_expired"},
                    event_status="pending",
                    created_by=user_label,
                )
            )
            db.add(
                EnterpriseEvent(
                    event_type="OffboardingWorkflowRequested",
                    source_module="HRM",
                    target_module="HRM",
                    payload={"employee_id": str(employee.id), "employee_code": employee.employee_code, "employment_type": employee.employment_type},
                    event_status="pending",
                    created_by=user_label,
                )
            )
            db.add(
                HRMAuditLog(
                    actor_email="system",
                    action="EMP-005_AUTO_DEACTIVATION",
                    entity_type="HRMEmployee",
                    entity_id=str(employee.id),
                    sensitivity="confidential",
                    summary=f"Employee automatically deactivated after {employee.employment_type} expiry.",
                    before_json={"employment_status": previous_status, "employment_end_date": str(end_date)},
                    after_json={"employment_status": "inactive", "employment_type_status": "expired", "iam_request_status": employee.iam_request_status},
                )
            )
            deactivated += 1
    db.commit()
    return {"checked": checked, "deactivated": deactivated, "reminders": reminders}


PROBATION_STATUSES = {"Not Applicable", "Pending", "In Progress", "Due for Review", "Extended", "Confirmed", "Failed", "Closed"}
PROBATION_APPLICABLE_TYPES = {"Permanent", "Contract", "Internship"}


def _add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    month_days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(start.day, month_days[month - 1]))


def _default_probation_required(employment_type: str) -> bool:
    return _canonical_employment_type(employment_type) in PROBATION_APPLICABLE_TYPES


def _probation_status(start_date: date | None, end_date: date | None, current: str | None = None, today: date | None = None) -> str:
    if current in {"Confirmed", "Failed", "Closed"}:
        return current
    if not start_date or not end_date:
        return "Not Applicable"
    today = today or date.today()
    if today < start_date:
        return "Pending"
    if today >= end_date - timedelta(days=30):
        return "Due for Review"
    return "In Progress"


def _probation_payload(payload: dict[str, Any], employee: HRMEmployee) -> dict[str, Any]:
    employment_type = _canonical_employment_type(employee.employment_type)
    probation_required = bool(payload.get("probation_required", _default_probation_required(employment_type)))
    duration = int(payload.get("probation_duration_months") or employee.probation_duration_months or 6)
    start_date = _parse_import_date(payload.get("probation_start_date") or payload.get("start_date")) or employee.probation_start_date or employee.employment_start_date or employee.hire_date
    end_date = _parse_import_date(payload.get("probation_end_date") or payload.get("end_date")) or employee.probation_end_date
    if probation_required and start_date and not end_date:
        end_date = _add_months(start_date, duration)
    return {
        "probation_required": probation_required,
        "probation_start_date": start_date,
        "probation_end_date": end_date,
        "probation_duration_months": duration,
        "probation_status": payload.get("probation_status") or _probation_status(start_date, end_date),
        "probation_extension_reason": _string(payload.get("probation_extension_reason") or payload.get("extension_reason")),
        "max_extension_count": int(payload.get("max_extension_count") or 2),
    }


def _validate_probation(employee: HRMEmployee, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if employee.employment_status in {"inactive", "terminated", "suspended"}:
        errors.append("Probation cannot be assigned to inactive, suspended, or exited employees")
    if _canonical_employment_type(employee.employment_type) in {"Consultant", "Casual"} and payload.get("probation_required"):
        errors.append("Probation does not apply to consultants or casual employees unless explicitly enabled by policy")
    if payload.get("probation_required"):
        if not payload.get("probation_start_date"):
            errors.append("Probation start date is required")
        if not payload.get("probation_end_date"):
            errors.append("Probation end date is required")
        if payload.get("probation_duration_months", 0) <= 0:
            errors.append("Probation duration must be positive")
        if payload.get("probation_start_date") and payload.get("probation_end_date") and payload["probation_end_date"] < payload["probation_start_date"]:
            errors.append("Probation end date cannot be before probation start date")
    return errors


def _probation_record(db: Session, employee: HRMEmployee) -> HRMProbationRecord | None:
    return db.query(HRMProbationRecord).filter(HRMProbationRecord.employee_id == employee.id).order_by(HRMProbationRecord.created_at.desc()).first()


def _serialize_probation(record: HRMProbationRecord | None, employee: HRMEmployee) -> dict[str, Any]:
    if not record:
        return _jsonable({
            "employee_id": str(employee.id),
            "probation_required": bool(employee.probation_required),
            "start_date": employee.probation_start_date,
            "end_date": employee.probation_end_date,
            "duration_months": employee.probation_duration_months,
            "status": employee.probation_status or "Not Applicable",
            "extended": bool(employee.probation_extended),
            "extension_count": employee.probation_extension_count or 0,
            "confirmed_date": employee.probation_confirmed_date,
            "confirmed_by": employee.probation_confirmed_by,
        })
    return {column.name: _jsonable(getattr(record, column.name)) for column in record.__table__.columns}


def _audit_probation(db: Session, employee: HRMEmployee, user: UserResponse | None, action: str, before: dict[str, Any] | None, after: dict[str, Any]):
    actor_email = user.email if user else "system"
    actor_name = user.full_name if user else "EMP-006 scheduler"
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if user and isinstance(user.id, UUID) else None,
            actor_email=actor_email,
            action=action,
            entity_type="HRMEmployee",
            entity_id=str(employee.id),
            sensitivity="confidential",
            summary=f"EMP-006 probation event for {_full_name(employee)}.",
            before_json=_jsonable(before),
            after_json=_jsonable(after),
        )
    )
    db.add(
        AuditLog(
            user_email=actor_email,
            module="HRM",
            action=action,
            entity_type="HRMEmployee",
            entity_id=employee.id,
            old_value=_jsonable(before),
            new_value=_jsonable(after),
            result="success",
            created_by=actor_name,
        )
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    return value


def _serialize_model(record) -> dict[str, Any] | None:
    if not record:
        return None
    return {column.name: _jsonable(getattr(record, column.name)) for column in record.__table__.columns}


def _profile_completion(employee: HRMEmployee) -> float:
    fields = [
        employee.first_name,
        employee.last_name,
        employee.gender,
        employee.date_of_birth,
        employee.national_id or employee.passport_number,
        employee.marital_status,
        employee.personal_email or employee.email,
        employee.phone,
        employee.physical_address or employee.address,
        employee.city,
        employee.country,
        employee.biography or employee.professional_summary,
        employee.photo_url,
    ]
    return round((sum(1 for value in fields if value not in (None, "")) / len(fields)) * 100, 2)


def _audit_profile_event(
    db: Session,
    employee: HRMEmployee,
    user: UserResponse,
    action: str,
    summary: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
):
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action=action,
            entity_type="HRMEmployeeProfile",
            entity_id=str(employee.id),
            sensitivity="confidential",
            summary=summary,
            before_json=_jsonable(before),
            after_json=_jsonable(after),
        )
    )
    db.add(
        AuditLog(
            user_email=user.email,
            module="HRM",
            action=action,
            entity_type="HRMEmployeeProfile",
            entity_id=employee.id,
            old_value=_jsonable(before),
            new_value=_jsonable(after),
            result="success",
            created_by=user.full_name,
        )
    )


def _profile_history(
    db: Session,
    employee: HRMEmployee,
    user: UserResponse,
    section: str,
    before: dict[str, Any] | None,
    after: dict[str, Any],
    reason: str | None = None,
    approval_status: str = "applied",
):
    for key, new_value in after.items():
        old_value = before.get(key) if before else None
        if _jsonable(old_value) == _jsonable(new_value):
            continue
        db.add(
            HRMEmployeeProfileHistory(
                employee_id=employee.id,
                section=section,
                field_name=key,
                old_value=str(_jsonable(old_value)) if old_value is not None else None,
                new_value=str(_jsonable(new_value)) if new_value is not None else None,
                change_reason=reason,
                changed_by=user.full_name,
                approval_status=approval_status,
            )
        )


def _sync_profile_completion(db: Session, employee: HRMEmployee):
    employee.profile_completion_percentage = Decimal(str(_profile_completion(employee)))
    profile = db.query(HRMEmployeeProfile).filter(HRMEmployeeProfile.employee_id == employee.id).first()
    if profile:
        profile.profile_completion_percentage = employee.profile_completion_percentage


def _validate_unique_profile_values(db: Session, employee: HRMEmployee, data: dict[str, Any]):
    national_id = _string(data.get("national_id"))
    passport_number = _string(data.get("passport_number"))
    personal_email = _string(data.get("personal_email")).lower()
    if national_id:
        existing = db.query(HRMEmployee).filter(HRMEmployee.national_id == national_id, HRMEmployee.id != employee.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="National ID already exists")
    if passport_number:
        existing = db.query(HRMEmployee).filter(HRMEmployee.passport_number == passport_number, HRMEmployee.id != employee.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Passport number already exists")
    if personal_email:
        existing = db.query(HRMEmployee).filter(HRMEmployee.personal_email.ilike(personal_email), HRMEmployee.id != employee.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Personal email already exists")


def _sensitive_profile_changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    sensitive_fields = {"first_name", "middle_name", "last_name", "date_of_birth", "national_id", "passport_number", "marital_status"}
    return {key: after[key] for key in sensitive_fields if key in after and _jsonable(before.get(key)) != _jsonable(after.get(key))}


def _queue_profile_change_request(db: Session, employee: HRMEmployee, user: UserResponse, section: str, changes: dict[str, Any], reason: str | None):
    request = HRMEmployeeChangeRequest(
        employee_id=employee.id,
        section=section,
        requested_changes={key: _jsonable(value) for key, value in changes.items()},
        reason=reason,
        approval_status="pending_hr_approval",
        requested_by=user.full_name,
    )
    db.add(request)
    db.add(
        NotificationEvent(
            module="HRM",
            related_entity="Employee",
            related_id=employee.id,
            recipient_name="HR Approver",
            subject=f"Profile change approval required: {_full_name(employee)}",
            body=f"{user.full_name} requested sensitive {section} changes for {_full_name(employee)}.",
            status="queued",
            created_by=user.full_name,
        )
    )
    return request


def _profile_payload(employee: HRMEmployee) -> dict[str, Any]:
    return {
        "first_name": employee.first_name,
        "middle_name": employee.middle_name,
        "last_name": employee.last_name,
        "preferred_name": employee.preferred_name,
        "gender": employee.gender,
        "date_of_birth": employee.date_of_birth,
        "nationality": employee.nationality,
        "national_id": employee.national_id,
        "passport_number": employee.passport_number,
        "place_of_birth": employee.place_of_birth,
        "religion": employee.religion,
        "marital_status": employee.marital_status,
        "employee_status": employee.employment_status,
        "profile_completion_percentage": float(employee.profile_completion_percentage or 0),
    }


def _contact_payload(employee: HRMEmployee) -> dict[str, Any]:
    return {
        "personal_email": employee.personal_email,
        "corporate_email": employee.corporate_email or employee.email,
        "mobile_number": employee.phone,
        "alternative_phone": employee.alternative_phone,
        "physical_address": employee.physical_address or employee.address,
        "postal_address": employee.postal_address,
        "city": employee.city,
        "county": employee.county,
        "country": employee.country,
    }


def _audit_assignment_event(db: Session, employee: HRMEmployee, user: UserResponse, buc_code: str, action: str, previous: Any, new: Any, reason: str | None):
    payload = {"buc_code": buc_code, "previous": _jsonable(previous), "new": _jsonable(new), "reason": reason}
    db.add(HRMAuditLog(actor_user_id=user.id if isinstance(user.id, UUID) else None, actor_email=user.email, action=f"{buc_code}_{action}", entity_type="HRMOrganizationalAssignment", entity_id=str(employee.id), sensitivity="internal", summary=f"{buc_code} {action} for {_full_name(employee)}.", before_json={"value": _jsonable(previous)}, after_json={"value": _jsonable(new), "reason": reason}))
    db.add(AuditLog(user_email=user.email, module="HRM", action=f"{buc_code}_{action}", entity_type="HRMOrganizationalAssignment", entity_id=employee.id, old_value={"value": _jsonable(previous)}, new_value=payload, result="success", created_by=user.full_name))


def _assignment_history(db: Session, employee: HRMEmployee, user: UserResponse, buc_code: str, assignment_type: str, previous: Any, new: Any, effective_date: date | None, reason: str | None, status_value: str = "active"):
    db.add(HRMEmployeeAssignmentHistory(employee_id=employee.id, buc_code=buc_code, assignment_type=assignment_type, previous_value=str(previous) if previous else None, new_value=str(new) if new else None, effective_from=effective_date, reason=reason, status=status_value, initiated_by=user.full_name))
    db.add(EnterpriseEvent(event_type=f"{buc_code}_{assignment_type}_changed", source_module="HRM", target_module="Enterprise", payload={"employee_id": str(employee.id), "assignment_type": assignment_type, "new_value": str(new) if new else None}, status="pending", created_by=user.full_name))
    for target in ["IAM", "Payroll", "Finance", "Projects", "Analytics"]:
        db.add(EnterpriseEvent(event_type=f"Employee{assignment_type.title().replace('_', '')}SyncRequested", source_module="HRM", target_module=target, payload={"employee_id": str(employee.id), "new_value": str(new) if new else None}, status="pending", created_by=user.full_name))


def _close_assignment_rows(db: Session, model, employee_id: UUID, field: str | None = None):
    query = db.query(model).filter(model.employee_id == employee_id, model.status == "active")
    if field and hasattr(model, "manager_type"):
        query = query.filter(model.manager_type == field)
    for row in query.all():
        row.status = "closed"
        if hasattr(row, "effective_to"):
            row.effective_to = date.today()


def _validate_department(db: Session, value: str) -> HRMDepartment:
    department = db.query(HRMDepartment).filter(HRMDepartment.name.ilike(value), HRMDepartment.status == "active").first()
    if not department:
        raise HTTPException(status_code=422, detail="Department must exist and be active")
    return department


def _validate_branch(db: Session, value: str) -> HRMBranch:
    branch = db.query(HRMBranch).filter(or_(HRMBranch.branch_name.ilike(value), HRMBranch.branch_code.ilike(value)), HRMBranch.status == "active").first()
    if not branch:
        raise HTTPException(status_code=422, detail="Branch must exist and be active")
    return branch


def _save_org_assignment(db: Session, employee_id: UUID, payload: OrgAssignmentPayload, user: UserResponse, assignment_type: str, buc_code: str, transfer: bool):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    previous = getattr(employee, assignment_type)
    if transfer and not previous:
        raise HTTPException(status_code=422, detail=f"Current {assignment_type.replace('_', ' ')} must exist before transfer")
    if previous and str(previous).lower() == payload.value.lower():
        raise HTTPException(status_code=409, detail="New assignment must be different from current assignment")
    if assignment_type == "department":
        _validate_department(db, payload.value)
        _close_assignment_rows(db, HRMEmployeeDepartmentAssignment, employee.id)
        db.add(HRMEmployeeDepartmentAssignment(employee_id=employee.id, department=payload.value, effective_from=payload.effective_date, reason=payload.reason, initiated_by=user.full_name, approved_by=user.full_name))
    elif assignment_type == "branch":
        _validate_branch(db, payload.value)
        _close_assignment_rows(db, HRMEmployeeBranchAssignment, employee.id)
        db.add(HRMEmployeeBranchAssignment(employee_id=employee.id, branch=payload.value, effective_from=payload.effective_date, reason=payload.reason, initiated_by=user.full_name, approved_by=user.full_name))
    elif assignment_type == "business_unit":
        _close_assignment_rows(db, HRMEmployeeBusinessUnitAssignment, employee.id)
        db.add(HRMEmployeeBusinessUnitAssignment(employee_id=employee.id, business_unit=payload.value, effective_from=payload.effective_date, reason=payload.reason, initiated_by=user.full_name, approved_by=user.full_name))
    setattr(employee, assignment_type, payload.value)
    _assignment_history(db, employee, user, buc_code, assignment_type, previous, payload.value, payload.effective_date, payload.reason)
    _audit_assignment_event(db, employee, user, buc_code, "TRANSFER" if transfer else "ASSIGN", previous, payload.value, payload.reason)
    db.commit()
    return {"status": "active", "employee_id": employee.id, "assignment_type": assignment_type, "new_value": payload.value}


def _document_required_types() -> set[str]:
    return {"National ID", "Employment Contract", "Tax Document"}


CONFIRMATION_STATUSES = {"Not Applicable", "Pending Confirmation", "Confirmed", "Confirmation Deferred", "Rejected"}


def _latest_confirmation_record(db: Session, employee: HRMEmployee) -> HRMConfirmationRecord | None:
    return (
        db.query(HRMConfirmationRecord)
        .filter(HRMConfirmationRecord.employee_id == employee.id)
        .order_by(HRMConfirmationRecord.created_at.desc())
        .first()
    )


def _latest_probation_review(db: Session, employee: HRMEmployee, outcomes: set[str] | None = None) -> HRMProbationReview | None:
    query = db.query(HRMProbationReview).filter(HRMProbationReview.employee_id == employee.id)
    if outcomes:
        query = query.filter(HRMProbationReview.outcome.in_(list(outcomes)))
    return query.order_by(HRMProbationReview.created_at.desc()).first()


def _serialize_confirmation(record: HRMConfirmationRecord | None, employee: HRMEmployee) -> dict[str, Any]:
    return {
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "employee_name": _full_name(employee),
        "confirmation_status": employee.confirmation_status or "Not Applicable",
        "confirmation_date": employee.confirmation_date,
        "confirmed_by": employee.confirmed_by,
        "confirmation_notes": employee.confirmation_notes,
        "probation_review_id": str(employee.probation_review_id) if employee.probation_review_id else None,
        "next_review_date": employee.next_confirmation_review_date,
        "record": {column.name: getattr(record, column.name) for column in record.__table__.columns} if record else None,
    }


def _confirmation_jsonable(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, (date, datetime, UUID)):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = _confirmation_jsonable(value)
        else:
            result[key] = value
    return result


def _audit_confirmation(db: Session, employee: HRMEmployee, user: UserResponse, action: str, before: dict[str, Any] | None, after: dict[str, Any]):
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action=action,
            entity_type="HRMEmployee",
            entity_id=str(employee.id),
            sensitivity="confidential",
            summary=f"EMP-007 confirmation event for {_full_name(employee)}.",
            before_json=_confirmation_jsonable(before),
            after_json=_confirmation_jsonable(after),
        )
    )
    db.add(
        AuditLog(
            user_email=user.email,
            module="HRM",
            action=action,
            entity_type="HRMEmployee",
            entity_id=employee.id,
            old_value=_confirmation_jsonable(before),
            new_value=_confirmation_jsonable(after),
            result="success",
            created_by=user.full_name,
        )
    )


def _confirmation_record(
    db: Session,
    employee: HRMEmployee,
    decision: str,
    status_value: str,
    user: UserResponse,
    payload: dict[str, Any],
    probation_record: HRMProbationRecord | None,
    review: HRMProbationReview | None,
) -> HRMConfirmationRecord:
    record = HRMConfirmationRecord(
        employee_id=employee.id,
        probation_record_id=probation_record.id if probation_record else None,
        probation_review_id=review.id if review else None,
        decision=decision,
        status=status_value,
        confirmation_date=_parse_import_date(payload.get("confirmation_date")),
        confirmed_by=user.full_name if status_value == "Confirmed" else None,
        notes=_string(payload.get("confirmation_notes") or payload.get("notes")),
        reason=_string(payload.get("reason") or payload.get("deferment_reason") or payload.get("rejection_reason")),
        next_review_date=_parse_import_date(payload.get("next_review_date")),
        created_by=user.full_name,
    )
    db.add(record)
    db.flush()
    return record


def _confirmation_precheck(
    db: Session,
    employee: HRMEmployee,
    decision: str,
    payload: dict[str, Any],
    allow_override: bool = False,
) -> tuple[HRMProbationRecord | None, HRMProbationReview | None]:
    if employee.employment_status not in {"active", "probation"}:
        raise HTTPException(status_code=422, detail="Only active or on-probation employees can enter confirmation workflow")
    if employee.employment_status in {"inactive", "suspended", "terminated", "retired", "exited"}:
        raise HTTPException(status_code=422, detail="Inactive, suspended, terminated, retired, or exited employees cannot be confirmed")
    if employee.confirmation_status == "Confirmed" or employee.confirmation_date:
        raise HTTPException(status_code=409, detail="Employee has already been confirmed")

    probation_record = _probation_record(db, employee)
    review = _latest_probation_review(db, employee, {"Confirmed", "Extended", "Failed", "Closed"})
    if not allow_override and (not probation_record or not review):
        raise HTTPException(status_code=422, detail="Probation review must be completed before employee confirmation")

    if decision == "defer":
        if not _string(payload.get("reason") or payload.get("deferment_reason")):
            raise HTTPException(status_code=422, detail="Deferment reason is required")
        if not _parse_import_date(payload.get("next_review_date")):
            raise HTTPException(status_code=422, detail="Next review date is required")
    if decision == "reject" and not _string(payload.get("reason") or payload.get("rejection_reason")):
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    if decision == "confirm":
        confirmation_date = _parse_import_date(payload.get("confirmation_date")) or date.today()
        start_date = employee.employment_start_date or employee.hire_date
        if start_date and confirmation_date < start_date:
            raise HTTPException(status_code=422, detail="Confirmation date cannot be before employment start date")
        if probation_record and probation_record.end_date and confirmation_date < probation_record.end_date and not allow_override:
            raise HTTPException(status_code=422, detail="Confirmation date should be on or after probation end date")
    return probation_record, review


def _queue_confirmation_notifications(db: Session, employee: HRMEmployee, user: UserResponse, subject: str, body: str):
    for recipient in ["Employee", "Manager", "HR"]:
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


def _upsert_probation(db: Session, employee: HRMEmployee, payload: dict[str, Any], user: UserResponse, action: str) -> HRMProbationRecord:
    normalized = _probation_payload(payload, employee)
    errors = _validate_probation(employee, normalized)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Probation validation failed", "errors": errors})
    before = {
        "probation_required": employee.probation_required,
        "probation_status": employee.probation_status,
        "probation_start_date": str(employee.probation_start_date) if employee.probation_start_date else None,
        "probation_end_date": str(employee.probation_end_date) if employee.probation_end_date else None,
    }
    employee.probation_required = normalized["probation_required"]
    employee.probation_start_date = normalized["probation_start_date"]
    employee.probation_end_date = normalized["probation_end_date"]
    employee.probation_duration_months = normalized["probation_duration_months"]
    employee.probation_status = normalized["probation_status"] if employee.probation_required else "Not Applicable"
    detail = db.query(HRMEmployeeEmploymentDetail).filter(HRMEmployeeEmploymentDetail.employee_id == employee.id, HRMEmployeeEmploymentDetail.status == "active").first()
    record = _probation_record(db, employee)
    if not record:
        record = HRMProbationRecord(employee_id=employee.id, employment_detail_id=detail.id if detail else None, created_by=user.full_name)
        db.add(record)
    record.probation_required = employee.probation_required
    record.start_date = employee.probation_start_date
    record.end_date = employee.probation_end_date
    record.duration_months = employee.probation_duration_months
    record.status = employee.probation_status
    record.updated_by = user.full_name
    if detail:
        detail.probation_required = employee.probation_required
        detail.probation_start_date = employee.probation_start_date
        detail.probation_end_date = employee.probation_end_date
        detail.probation_duration_months = employee.probation_duration_months
        detail.probation_status = employee.probation_status
    after = _serialize_probation(record, employee)
    _audit_probation(db, employee, user, action, before, after)
    return record


def process_probation_reviews(db: Session, user_label: str = "EMP-006 scheduler") -> dict[str, int]:
    today = date.today()
    records = db.query(HRMProbationRecord).filter(HRMProbationRecord.probation_required == True).all()  # noqa: E712
    checked = updated = reminders = 0
    for record in records:
        employee = db.query(HRMEmployee).filter(HRMEmployee.id == record.employee_id).first()
        if not employee or record.status in {"Confirmed", "Failed", "Closed"}:
            continue
        checked += 1
        new_status = _probation_status(record.start_date, record.end_date, record.status, today)
        if new_status != record.status:
            before = {"probation_status": record.status}
            record.status = new_status
            employee.probation_status = new_status
            _audit_probation(db, employee, None, "EMP-006_PROBATION_STATUS_UPDATED", before, {"probation_status": new_status})
            updated += 1
        if record.end_date:
            days = (record.end_date - today).days
            if days in {30, 14, 7, 0}:
                reminders += 1
                db.add(
                    NotificationEvent(
                        module="HRM",
                        related_entity="Employee",
                        related_id=employee.id,
                        recipient_name="HR Team",
                        subject=f"Probation review due for {_full_name(employee)}",
                        body=f"Probation review is due in {days} day(s), ending {record.end_date}.",
                        status="queued",
                        created_by=user_label,
                    )
                )
    db.commit()
    return {"checked": checked, "updated": updated, "reminders": reminders}


EMPLOYEE_IMPORT_MANDATORY = {
    "first_name",
    "last_name",
    "email",
    "phone",
    "national_id",
    "employment_type",
    "job_title",
    "department",
    "branch",
    "supervisor_id",
    "hire_date",
    "employment_status",
}

EMPLOYEE_IMPORT_MODES = {"create", "update", "upsert", "validate_only", "draft"}
EMPLOYMENT_TYPES = {"Permanent", "Contract", "Casual", "Internship", "Consultant"}
EMPLOYMENT_TYPE_ALIASES = {
    "permanent": "Permanent",
    "full time": "Permanent",
    "full-time": "Permanent",
    "fulltime": "Permanent",
    "part time": "Casual",
    "part-time": "Casual",
    "parttime": "Casual",
    "casual": "Casual",
    "contract": "Contract",
    "contractor": "Contract",
    "intern": "Internship",
    "internship": "Internship",
    "consultant": "Consultant",
    "consultancy": "Consultant",
}
EXPIRING_EMPLOYMENT_TYPES = {"Contract", "Casual", "Internship", "Consultant"}
EMPLOYEE_STATUSES = {"draft", "pending_activation", "active", "on_leave", "probation", "inactive", "suspended", "terminated"}
EMPLOYEE_STATUS_ALIASES = {
    "draft": "draft",
    "pending activation": "pending_activation",
    "pending_activation": "pending_activation",
    "active": "active",
    "on leave": "on_leave",
    "on_leave": "on_leave",
    "probation": "probation",
    "inactive": "inactive",
    "suspended": "suspended",
    "terminated": "terminated",
}


def _string(value: Any) -> str:
    return str(value or "").strip()


def _parse_import_decimal(value: Any) -> Decimal:
    raw = _string(value)
    if not raw:
        return Decimal("0")
    cleaned = raw.replace(",", "").replace("$", "").replace("KES", "").replace("KSh", "").strip()
    try:
        return Decimal(cleaned or "0")
    except Exception:
        return Decimal("0")


def _import_batch_number(db: Session) -> str:
    sequence = db.query(EntitySequence).filter(EntitySequence.entity_key == "hrm.employee_import_batches").with_for_update().first()
    if not sequence:
        sequence = EntitySequence(entity_key="hrm.employee_import_batches", prefix="EMP-IMP", next_number=1, padding=5)
        db.add(sequence)
        db.flush()
    batch_number = f"{sequence.prefix}-{str(sequence.next_number or 1).zfill(sequence.padding or 5)}"
    sequence.next_number = (sequence.next_number or 1) + 1
    return batch_number


def _parse_import_date(value: Any) -> date | None:
    raw = _string(value)
    if not raw:
        return None
    if raw.replace(".", "", 1).isdigit():
        try:
            return date(1899, 12, 30) + timedelta(days=int(float(raw)))
        except ValueError:
            return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _canonical_employment_type(value: Any) -> str:
    raw = _string(value) or "Permanent"
    return EMPLOYMENT_TYPE_ALIASES.get(raw.lower().replace("_", " "), raw)


def _canonical_employee_status(value: Any, import_as_draft: bool) -> str:
    raw = _string(value) or ("draft" if import_as_draft else "pending_activation")
    return EMPLOYEE_STATUS_ALIASES.get(raw.lower().replace("_", " "), raw.lower().replace(" ", "_"))


def _employment_type_payload(payload: dict[str, Any]) -> dict[str, Any]:
    employment_type = _canonical_employment_type(payload.get("employment_type"))
    return {
        "employment_type": employment_type,
        "start_date": _parse_import_date(payload.get("start_date") or payload.get("employment_start_date") or payload.get("contract_start_date") or payload.get("engagement_start_date") or payload.get("internship_start_date") or payload.get("hire_date")),
        "end_date": _parse_import_date(payload.get("end_date") or payload.get("employment_end_date") or payload.get("contract_end_date") or payload.get("engagement_end_date") or payload.get("internship_end_date")),
        "institution": _string(payload.get("institution")),
        "internship_supervisor": _string(payload.get("internship_supervisor") or payload.get("supervisor")),
        "consultancy_agreement_ref": _string(payload.get("consultancy_agreement_ref") or payload.get("agreement_reference")),
        "consultancy_project": _string(payload.get("consultancy_project") or payload.get("project")),
        "change_reason": _string(payload.get("change_reason") or payload.get("reason")),
    }


def _validate_employment_type_rules(payload: dict[str, Any], for_activation: bool = False) -> list[str]:
    employment_type = _canonical_employment_type(payload.get("employment_type"))
    start_date = payload.get("start_date") or payload.get("employment_start_date")
    end_date = payload.get("end_date") or payload.get("employment_end_date")
    errors: list[str] = []
    if employment_type not in EMPLOYMENT_TYPES:
        errors.append("Invalid employment type")
    if employment_type == "Contract":
        if not start_date:
            errors.append("Contract start date is required")
        if not end_date:
            errors.append("Contract end date is required")
    if employment_type == "Casual":
        if not start_date:
            errors.append("Engagement start date is required")
        if not end_date:
            errors.append("Engagement end date is required")
    if employment_type == "Internship":
        if not payload.get("institution"):
            errors.append("Institution is required for internship employees")
        if not payload.get("internship_supervisor"):
            errors.append("Internship supervisor is required")
        if not start_date:
            errors.append("Internship start date is required")
        if not end_date:
            errors.append("Internship end date is required")
    if employment_type == "Consultant":
        if not payload.get("consultancy_agreement_ref"):
            errors.append("Consultancy agreement reference is required")
        if not payload.get("consultancy_project"):
            errors.append("Consultancy project is required")
        if not start_date:
            errors.append("Consultancy start date is required")
        if not end_date:
            errors.append("Consultancy end date is required")
    if for_activation and employment_type in EXPIRING_EMPLOYMENT_TYPES and not end_date:
        errors.append("Employment end date is required before activation")
    if start_date and end_date and end_date < start_date:
        errors.append("Employment end date cannot be before start date")
    return errors


def _employment_expiry_status(employee: HRMEmployee, today: date | None = None) -> str:
    today = today or date.today()
    employment_type = _canonical_employment_type(employee.employment_type)
    end_date = employee.extension_approved_until or employee.employment_end_date
    if employment_type not in EXPIRING_EMPLOYMENT_TYPES:
        return "active"
    if not end_date:
        return "incomplete"
    days = (end_date - today).days
    if days < 0:
        return "expired"
    if days <= 90:
        return "expiring_soon"
    return "active"


def _audit_employment_type(db: Session, employee: HRMEmployee, user: UserResponse, action: str, before: dict[str, Any] | None, after: dict[str, Any]):
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action=action,
            entity_type="HRMEmployee",
            entity_id=str(employee.id),
            sensitivity="confidential",
            summary=f"EMP-005 employment type event for {_full_name(employee)}.",
            before_json=_jsonable(before),
            after_json=_jsonable(after),
        )
    )
    db.add(
        AuditLog(
            user_email=user.email,
            module="HRM",
            action=action,
            entity_type="HRMEmployee",
            entity_id=employee.id,
            old_value=_jsonable(before),
            new_value=_jsonable(after),
            result="success",
            created_by=user.full_name,
        )
    )


def _upsert_employment_detail(db: Session, employee: HRMEmployee, payload: dict[str, Any], user: UserResponse, action: str) -> HRMEmployeeEmploymentDetail:
    errors = _validate_employment_type_rules(payload)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Employment type validation failed", "errors": errors})
    previous = {
        "employment_type": employee.employment_type,
        "employment_start_date": str(employee.employment_start_date) if employee.employment_start_date else None,
        "employment_end_date": str(employee.employment_end_date) if employee.employment_end_date else None,
    }
    employee.employment_type = payload["employment_type"]
    employee.employment_start_date = payload.get("start_date")
    employee.employment_end_date = payload.get("end_date")
    employee.institution = payload.get("institution")
    employee.internship_supervisor = payload.get("internship_supervisor")
    employee.consultancy_agreement_ref = payload.get("consultancy_agreement_ref")
    employee.consultancy_project = payload.get("consultancy_project")
    employee.employment_type_status = _employment_expiry_status(employee)
    if employee.employment_type_status == "incomplete":
        employee.payroll_profile_status = "blocked"

    detail = db.query(HRMEmployeeEmploymentDetail).filter(HRMEmployeeEmploymentDetail.employee_id == employee.id, HRMEmployeeEmploymentDetail.status == "active").first()
    if not detail:
        detail = HRMEmployeeEmploymentDetail(employee_id=employee.id, created_by=user.full_name)
        db.add(detail)
    detail.employment_type = employee.employment_type
    detail.start_date = employee.employment_start_date
    detail.end_date = employee.employment_end_date
    detail.institution = employee.institution
    detail.internship_supervisor = employee.internship_supervisor
    detail.consultancy_agreement_ref = employee.consultancy_agreement_ref
    detail.consultancy_project = employee.consultancy_project
    detail.extension_approved_until = employee.extension_approved_until
    detail.expiry_status = employee.employment_type_status
    detail.updated_by = user.full_name
    db.add(
        HRMEmploymentTypeHistory(
            employee_id=employee.id,
            previous_type=previous["employment_type"],
            new_type=employee.employment_type,
            previous_end_date=_parse_import_date(previous["employment_end_date"]),
            new_end_date=employee.employment_end_date,
            change_reason=payload.get("change_reason") or action,
            changed_by=user.full_name,
        )
    )
    after = {
        "employment_type": employee.employment_type,
        "employment_start_date": str(employee.employment_start_date) if employee.employment_start_date else None,
        "employment_end_date": str(employee.employment_end_date) if employee.employment_end_date else None,
        "employment_type_status": employee.employment_type_status,
    }
    _audit_employment_type(db, employee, user, action, previous, after)
    return detail


def _employee_import_template(db: Session) -> str:
    position = db.query(HRMPosition).filter(HRMPosition.status == "active").order_by(HRMPosition.created_at.asc()).first()
    department = None
    if position:
        department = db.query(HRMDepartment).filter(HRMDepartment.name.ilike(position.department), HRMDepartment.status == "active").first()
    if not department:
        department = db.query(HRMDepartment).filter(HRMDepartment.status == "active").order_by(HRMDepartment.created_at.asc()).first()
    branch = db.query(HRMBranch).filter(HRMBranch.status == "active").order_by(HRMBranch.created_at.asc()).first()
    manager = (
        db.query(HRMEmployee)
        .filter(HRMEmployee.employment_status.in_(["active", "probation", "on_leave"]))
        .order_by(HRMEmployee.created_at.asc())
        .first()
    )
    headers = [
        "First Name",
        "Last Name",
        "Email",
        "Phone Number",
        "National ID / Passport",
        "Employment Type",
        "Job Title",
        "Department",
        "Branch",
        "Reporting Manager",
        "Start Date",
        "Status",
        "Tax PIN",
        "Date of Birth",
        "Gender",
        "Address",
        "Salary Band",
        "Base Salary",
        "Cost Center",
        "Contract End Date",
        "Emergency Contact",
    ]
    example = [
        "Jane",
        "Doe",
        "jane.doe@example.com",
        "+254700000000",
        "12345678",
        "Permanent",
        position.position_title if position else "Create an active position first",
        department.name if department else "Create an active department first",
        branch.branch_name if branch else "",
        manager.email if manager else "",
        "2026-06-01",
        "Draft",
        "A123456789B",
        "1995-01-01",
        "Female",
        "Nairobi",
        "JG-5",
        "120000",
        "CC-HR",
        "",
        "John Doe +254711111111",
    ]
    return ",".join(headers) + "\n" + ",".join(example) + "\n"


def _header_value(row: dict[str, Any], names: list[str]) -> Any:
    lookup = {key.lower().replace("_", " ").replace("/", " ").strip(): value for key, value in row.items()}
    for name in names:
        normalized = name.lower().replace("_", " ").replace("/", " ").strip()
        if normalized in lookup:
            return lookup[normalized]
    return None


def _split_import_full_name(value: Any) -> tuple[str, str]:
    raw = _string(value)
    if not raw:
        return "", ""
    parts = raw.split()
    if len(parts) == 1:
        return parts[0], "Unknown"
    return parts[0], " ".join(parts[1:])


def _manager_id_for_value(db: Session, value: Any) -> UUID | None:
    raw = _string(value)
    if not raw:
        return None
    manager = (
        db.query(HRMEmployee)
        .filter(
            (HRMEmployee.email.ilike(raw))
            | (HRMEmployee.employee_code.ilike(raw))
            | ((HRMEmployee.first_name + " " + HRMEmployee.last_name).ilike(raw))
        )
        .first()
    )
    return manager.id if manager else None


def _normalize_employee_import_row(db: Session, row: dict[str, Any], import_as_draft: bool) -> dict[str, Any]:
    manager_id = _manager_id_for_value(db, _header_value(row, ["Reporting Manager", "Manager", "Line Manager", "Supervisor"]))
    status_value = _canonical_employee_status(_header_value(row, ["Status", "Employment Status"]), import_as_draft)
    row_is_draft = import_as_draft or status_value == "draft"
    first_name = _string(_header_value(row, ["First Name", "FirstName", "Given Name"]))
    last_name = _string(_header_value(row, ["Last Name", "LastName", "Surname", "Family Name"]))
    if not first_name or not last_name:
        derived_first, derived_last = _split_import_full_name(_header_value(row, ["Full Name", "Name", "Employee Name", "Staff Name"]))
        first_name = first_name or derived_first
        last_name = last_name or derived_last
    import_warnings: list[str] = []
    if not _string(_header_value(row, ["Department", "Dept"])):
        import_warnings.append("Department was not supplied; assigned to Unassigned for HR review.")
    if not _string(_header_value(row, ["Job Title", "Position", "Role"])):
        import_warnings.append("Job title was not supplied; assigned to Unassigned Role for HR review.")
    normalized = {
        "first_name": first_name,
        "last_name": last_name,
        "email": _string(_header_value(row, ["Email", "Work Email", "Email Address"])).lower(),
        "phone": _string(_header_value(row, ["Phone Number", "Phone", "Mobile"])),
        "national_id": _string(_header_value(row, ["National ID / Passport", "National ID", "Passport", "ID Number"])),
        "tax_pin": _string(_header_value(row, ["Tax PIN", "PIN", "KRA PIN"])),
        "employment_type": _canonical_employment_type(_header_value(row, ["Employment Type", "Employee Type"])),
        "job_title": _string(_header_value(row, ["Job Title", "Position", "Role"])) or "Unassigned Role",
        "department": _string(_header_value(row, ["Department", "Dept"])) or "Unassigned",
        "branch": _string(_header_value(row, ["Branch", "Office", "Location"])) or "Unassigned",
        "supervisor_id": manager_id,
        "hire_date": _parse_import_date(_header_value(row, ["Start Date", "Hire Date", "Employment Start Date"])),
        "employment_start_date": _parse_import_date(_header_value(row, ["Employment Start Date", "Contract Start Date", "Engagement Start Date", "Internship Start Date", "Start Date", "Hire Date"])),
        "employment_end_date": _parse_import_date(_header_value(row, ["Employment End Date", "Contract End Date", "Engagement End Date", "Internship End Date", "End Date"])),
        "institution": _string(_header_value(row, ["Institution", "School", "University"])),
        "internship_supervisor": _string(_header_value(row, ["Internship Supervisor", "Intern Supervisor"])),
        "consultancy_agreement_ref": _string(_header_value(row, ["Consultancy Agreement Reference", "Agreement Reference", "Agreement Ref"])),
        "consultancy_project": _string(_header_value(row, ["Consultancy Project", "Project"])),
        "employment_status": status_value,
        "date_of_birth": _parse_import_date(_header_value(row, ["Date of Birth", "DOB"])),
        "gender": _string(_header_value(row, ["Gender"])),
        "address": _string(_header_value(row, ["Address"])),
        "salary_grade": _string(_header_value(row, ["Salary Band", "Salary Grade", "Job Grade"])),
        "base_salary": _parse_import_decimal(_header_value(row, ["Base Salary", "Salary"])),
        "pay_frequency": _string(_header_value(row, ["Pay Frequency"])) or "monthly",
        "contract_signed": False if row_is_draft else True,
        "budget_approved": False if row_is_draft else True,
        "internal_only": True,
        "import_warnings": import_warnings,
    }
    return normalized


def _existing_employee_for_import(db: Session, payload: dict[str, Any]) -> HRMEmployee | None:
    filters = []
    if payload.get("email"):
        filters.append(HRMEmployee.email.ilike(payload["email"]))
    if payload.get("national_id"):
        filters.append(HRMEmployee.national_id == payload["national_id"])
    if payload.get("tax_pin"):
        filters.append(HRMEmployee.tax_pin == payload["tax_pin"])
    if payload.get("phone"):
        filters.append(HRMEmployee.phone == payload["phone"])
    if not filters:
        return None
    return db.query(HRMEmployee).filter(or_(*filters)).first()


def _validate_import_row(db: Session, payload: dict[str, Any], row_seen: dict[str, set[str]], import_as_draft: bool, mode: str) -> list[str]:
    errors: list[str] = []
    row_is_draft = import_as_draft or payload.get("employment_status") == "draft"
    mandatory = {"first_name", "last_name", "email"}
    for field in mandatory:
        if not payload.get(field):
            errors.append(f"Missing mandatory field: {field}")
    for field in ["email", "national_id", "tax_pin", "phone"]:
        value = _string(payload.get(field))
        if value and value in row_seen.setdefault(field, set()):
            errors.append(f"Duplicate {field} inside import file")
        if value:
            row_seen[field].add(value)
    if payload.get("employment_type") not in EMPLOYMENT_TYPES:
        errors.append("Invalid employment type")
    if not row_is_draft:
        errors.extend(
            _validate_employment_type_rules(
                {
                    "employment_type": payload.get("employment_type"),
                    "start_date": payload.get("employment_start_date") or payload.get("hire_date"),
                    "end_date": payload.get("employment_end_date"),
                    "institution": payload.get("institution"),
                    "internship_supervisor": payload.get("internship_supervisor"),
                    "consultancy_agreement_ref": payload.get("consultancy_agreement_ref"),
                    "consultancy_project": payload.get("consultancy_project"),
                }
            )
        )
    if payload.get("employment_status") not in EMPLOYEE_STATUSES:
        errors.append("Invalid employee status")
    if not payload.get("hire_date") and not row_is_draft:
        errors.append("Invalid or missing start date")
    if "@" not in payload.get("email", ""):
        errors.append("Invalid employee email")
    if payload.get("supervisor_id"):
        manager = db.query(HRMEmployee).filter(HRMEmployee.id == payload["supervisor_id"]).first()
        if not manager or manager.employment_status not in {"active", "probation", "on_leave"}:
            errors.append("Invalid or inactive reporting manager")
    existing = _existing_employee_for_import(db, payload)
    if existing and mode == "create":
        errors.append("Duplicate employee found; use update or create_and_update mode")
    if not existing and mode == "update":
        errors.append("No existing employee found for update mode")
    return errors


def _serialize_import_batch(batch: HRMEmployeeImportBatch) -> dict[str, Any]:
    return {column.name: _jsonable(getattr(batch, column.name)) for column in batch.__table__.columns}


def _serialize_import_row(row: HRMEmployeeImportRow) -> dict[str, Any]:
    return {column.name: _jsonable(getattr(row, column.name)) for column in row.__table__.columns}


async def _read_employee_import_file(file: UploadFile) -> tuple[bytes, list[dict[str, Any]], str, str]:
    filename = file.filename or "employee-import"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in {"csv", "xlsx", "xls"}:
        raise HTTPException(status_code=422, detail="Invalid file format. Upload .xlsx, .xls, or .csv.")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds the 10MB employee import limit.")
    try:
        from backend.api.enterprise import _extract_textish_summary

        rows, summary = _extract_textish_summary(content, filename)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse employee import file: {exc}") from exc
    rows = [
        {str(key).strip(): value for key, value in row.items() if str(key).strip()}
        for row in rows
        if any(_string(value) for value in row.values())
    ]
    if suffix == "xls" and not rows:
        raise HTTPException(status_code=422, detail="Legacy .xls files must contain readable worksheet rows. Save as .xlsx or .csv and retry.")
    if not rows:
        raise HTTPException(status_code=422, detail="No employee rows were found. Use the approved employee import template.")
    return content, rows, summary, suffix


def _create_employee_import_batch(db: Session, file: UploadFile, content: bytes, suffix: str, rows: list[dict[str, Any]], summary: str, user: UserResponse, mode: str) -> HRMEmployeeImportBatch:
    salary_columns = {"base salary", "salary", "salary band", "salary grade", "job grade"}
    has_salary_data = any(any(str(key).strip().lower() in salary_columns for key in row.keys()) for row in rows)
    batch = HRMEmployeeImportBatch(
        id=uuid4(),
        batch_number=_import_batch_number(db),
        file_name=file.filename,
        file_hash=hashlib.sha256(content).hexdigest(),
        source_format=suffix,
        import_mode=mode,
        uploaded_by=user.full_name,
        approval_status="pending" if has_salary_data or mode in {"update", "upsert"} else "not_required",
        processing_status="uploaded",
        total_rows=len(rows),
        parse_summary=summary,
    )
    db.add(batch)
    db.flush()
    return batch


def _validate_employee_import(db: Session, batch: HRMEmployeeImportBatch, rows: list[dict[str, Any]], import_as_draft: bool, mode: str) -> tuple[int, int]:
    row_seen: dict[str, set[str]] = {}
    valid = rejected = 0
    missing_headers: list[str] = []
    batch.validation_errors = []
    for index, row in enumerate(rows, start=2):
        payload = _normalize_employee_import_row(db, row, import_as_draft)
        errors = _validate_import_row(db, payload, row_seen, import_as_draft, mode)
        if missing_headers:
            errors.extend([f"Missing mandatory column: {header}" for header in missing_headers])
        status_value = "valid" if not errors else "rejected"
        valid += 1 if not errors else 0
        rejected += 1 if errors else 0
        db.add(
            HRMEmployeeImportRow(
                id=uuid4(),
                batch_id=batch.id,
                row_number=index,
                row_payload=row,
                normalized_payload={key: str(value) if isinstance(value, (date, Decimal, UUID)) else value for key, value in payload.items()},
                row_status=status_value,
                error_messages=errors,
            )
        )
    batch.valid_rows = valid
    batch.rejected_rows = rejected
    batch.processing_status = "validated" if not rejected else "validation_failed" if not valid else "partially_valid"
    return valid, rejected


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    data = employee.model_dump()
    data["employee_code"] = _next_employee_code(db)
    data["internal_only"] = True
    data["employment_status"] = "pending_activation"
    if not _candidate_is_hired(db, data.get("candidate_id")):
        raise HTTPException(status_code=422, detail="Candidate must be HIRED before employee creation")
    _apply_recruitment_readiness(db, data)
    _validate_employee_payload(db, data)

    record = HRMEmployee(**data)
    db.add(record)
    db.flush()
    _upsert_employment_detail(
        db,
        record,
        {
            "employment_type": record.employment_type,
            "start_date": record.employment_start_date or record.hire_date,
            "end_date": record.employment_end_date,
            "institution": record.institution,
            "internship_supervisor": record.internship_supervisor,
            "consultancy_agreement_ref": record.consultancy_agreement_ref,
            "consultancy_project": record.consultancy_project,
            "change_reason": "EMP-001 initial employee creation",
        },
        user,
        "EMP-005_ASSIGN_EMPLOYMENT_TYPE",
    )
    if data.get("probation_required"):
        _upsert_probation(
            db,
            record,
            {
                "probation_required": data.get("probation_required"),
                "probation_start_date": data.get("probation_start_date") or record.hire_date,
                "probation_end_date": data.get("probation_end_date"),
                "probation_duration_months": data.get("probation_duration_months") or 6,
            },
            user,
            "EMP-006_ASSIGN_PROBATION",
        )
    _audit_employee_number_generation(db, record, user, None)
    _add_lifecycle_event(db, record, "hire", None, record.employment_status)
    _sync_employee_foundation(db, record)
    _queue_employee_notifications(db, record, user)
    _audit_employee_creation(db, record, user)
    db.commit()
    db.refresh(record)
    return record


@router.post("/from-candidate/{candidate_id}", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee_from_candidate(
    candidate_id: UUID,
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    data = employee.model_dump()
    data["candidate_id"] = candidate_id
    return create_employee(EmployeeCreate(**data), db, user)


@router.get("")
def get_employees(
    summary: bool = Query(default=True),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    query = db.query(HRMEmployee).order_by(HRMEmployee.created_at.desc()).limit(limit)
    if not summary:
        return query.all()
    return [
        {
            "id": row.id,
            "created_at": row.created_at,
            "employee_code": row.employee_code,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "department": row.department,
            "job_title": row.job_title,
            "role_category": row.role_category,
            "supervisor_id": row.supervisor_id,
            "employment_type": row.employment_type,
            "employment_type_status": row.employment_type_status,
            "employment_end_date": row.employment_end_date,
            "extension_approved_until": row.extension_approved_until,
            "probation_required": row.probation_required,
            "probation_status": row.probation_status,
            "probation_start_date": row.probation_start_date,
            "probation_end_date": row.probation_end_date,
            "probation_duration_months": row.probation_duration_months,
            "confirmation_status": row.confirmation_status,
            "confirmation_date": row.confirmation_date,
            "confirmed_by": row.confirmed_by,
            "confirmation_notes": row.confirmation_notes,
            "probation_review_id": row.probation_review_id,
            "next_confirmation_review_date": row.next_confirmation_review_date,
            "employment_status": row.employment_status,
            "activation_date": row.activation_date,
            "activated_by": row.activated_by,
        }
        for row in query.all()
    ]


@router.get("/employment-types")
def get_employment_types():
    return {
        "types": [
            {"value": "Permanent", "requires_end_date": False, "required_fields": []},
            {"value": "Contract", "requires_end_date": True, "required_fields": ["start_date", "end_date"]},
            {"value": "Casual", "requires_end_date": True, "required_fields": ["start_date", "end_date"]},
            {"value": "Internship", "requires_end_date": True, "required_fields": ["institution", "internship_supervisor", "start_date", "end_date"]},
            {"value": "Consultant", "requires_end_date": True, "required_fields": ["consultancy_agreement_ref", "consultancy_project", "start_date", "end_date"]},
        ],
        "expiry_reminder_days": [90, 60, 30, 7],
    }


@router.post("/employment-expiry/check")
def run_employment_expiry_check(
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    return process_expired_employment_engagements(db, user.full_name)


@router.post("/bulk-activate")
def bulk_activate_employees(
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee_ids = payload.get("employee_ids") or []
    if not isinstance(employee_ids, list) or not employee_ids:
        raise HTTPException(status_code=422, detail="employee_ids must be a non-empty list")
    allow_early_activation = bool(payload.get("allow_early_activation", False))
    continue_on_error = bool(payload.get("continue_on_error", True))
    results = []
    for raw_id in employee_ids:
        try:
            employee_id = UUID(str(raw_id))
            employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
            result = _activate_employee_record(db, employee, user, allow_early_activation)
            db.commit()
            results.append({"employee_id": str(employee.id), "status": "activated", "result": result})
        except HTTPException as exc:
            detail = exc.detail
            results.append({"employee_id": str(raw_id), "status": "failed", "error": detail})
            db.rollback()
            if not continue_on_error:
                raise
        except Exception as exc:
            results.append({"employee_id": str(raw_id), "status": "failed", "error": str(exc)})
            db.rollback()
            if not continue_on_error:
                raise
    return {
        "total": len(results),
        "activated": sum(1 for result in results if result["status"] == "activated"),
        "failed": sum(1 for result in results if result["status"] == "failed"),
        "results": results,
    }


@router.get("/{employee_id:uuid}/employment-type")
def get_employee_employment_type(
    employee_id: UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    detail = db.query(HRMEmployeeEmploymentDetail).filter(HRMEmployeeEmploymentDetail.employee_id == employee.id, HRMEmployeeEmploymentDetail.status == "active").first()
    history = db.query(HRMEmploymentTypeHistory).filter(HRMEmploymentTypeHistory.employee_id == employee.id).order_by(HRMEmploymentTypeHistory.changed_at.desc()).all()
    return {
        "employee_id": str(employee.id),
        "employment_type": _canonical_employment_type(employee.employment_type),
        "employment_type_status": _employment_expiry_status(employee),
        "start_date": employee.employment_start_date,
        "end_date": employee.employment_end_date,
        "extension_approved_until": employee.extension_approved_until,
        "institution": employee.institution,
        "internship_supervisor": employee.internship_supervisor,
        "consultancy_agreement_ref": employee.consultancy_agreement_ref,
        "consultancy_project": employee.consultancy_project,
        "detail": {column.name: getattr(detail, column.name) for column in detail.__table__.columns} if detail else None,
        "history": [{column.name: getattr(row, column.name) for column in row.__table__.columns} for row in history],
    }


@router.post("/{employee_id:uuid}/employment-type")
def assign_employee_employment_type(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    normalized = _employment_type_payload(payload)
    _upsert_employment_detail(db, employee, normalized, user, "EMP-005_ASSIGN_EMPLOYMENT_TYPE")
    db.commit()
    db.refresh(employee)
    return {"employee_id": str(employee.id), "employment_type": employee.employment_type, "employment_type_status": employee.employment_type_status}


@router.put("/{employee_id:uuid}/employment-type")
def update_employee_employment_type(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    normalized = _employment_type_payload(payload)
    _upsert_employment_detail(db, employee, normalized, user, "EMP-005_CHANGE_EMPLOYMENT_TYPE")
    db.commit()
    db.refresh(employee)
    return {"employee_id": str(employee.id), "employment_type": employee.employment_type, "employment_type_status": employee.employment_type_status}


@router.post("/{employee_id:uuid}/employment-extension")
def extend_employee_employment(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    new_end_date = _parse_import_date(payload.get("new_end_date") or payload.get("end_date"))
    if not new_end_date:
        raise HTTPException(status_code=422, detail="Extension end date is required")
    if employee.employment_type not in EXPIRING_EMPLOYMENT_TYPES:
        raise HTTPException(status_code=422, detail="Permanent employees do not require employment extensions")
    previous_end_date = employee.extension_approved_until or employee.employment_end_date
    if previous_end_date and new_end_date <= previous_end_date:
        raise HTTPException(status_code=422, detail="Extension date must be after the current end date")
    detail = db.query(HRMEmployeeEmploymentDetail).filter(HRMEmployeeEmploymentDetail.employee_id == employee.id, HRMEmployeeEmploymentDetail.status == "active").first()
    extension = HRMContractExtension(
        employee_id=employee.id,
        employment_detail_id=detail.id if detail else None,
        previous_end_date=previous_end_date,
        new_end_date=new_end_date,
        reason=_string(payload.get("reason")),
        approval_status="approved",
        approved_by=user.full_name,
        created_by=user.full_name,
    )
    db.add(extension)
    employee.extension_approved_until = new_end_date
    employee.employment_type_status = _employment_expiry_status(employee)
    if detail:
        detail.extension_approved_until = new_end_date
        detail.expiry_status = employee.employment_type_status
    _audit_employment_type(
        db,
        employee,
        user,
        "EMP-005_EXTENSION_APPROVAL",
        {"employment_end_date": str(previous_end_date) if previous_end_date else None},
        {"extension_approved_until": str(new_end_date), "employment_type_status": employee.employment_type_status},
    )
    db.commit()
    return {"employee_id": str(employee.id), "extension_approved_until": str(new_end_date), "employment_type_status": employee.employment_type_status}


@router.get("/{employee_id:uuid}/probation")
def get_employee_probation(
    employee_id: UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = _probation_record(db, employee)
    reviews = db.query(HRMProbationReview).filter(HRMProbationReview.employee_id == employee.id).order_by(HRMProbationReview.created_at.desc()).all()
    return {
        "probation": _serialize_probation(record, employee),
        "reviews": [{column.name: getattr(review, column.name) for column in review.__table__.columns} for review in reviews],
    }


@router.post("/{employee_id:uuid}/probation")
def assign_employee_probation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = _upsert_probation(db, employee, payload, user, "EMP-006_ASSIGN_PROBATION")
    db.commit()
    return _serialize_probation(record, employee)


@router.put("/{employee_id:uuid}/probation")
def update_employee_probation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = _upsert_probation(db, employee, payload, user, "EMP-006_UPDATE_PROBATION")
    db.commit()
    return _serialize_probation(record, employee)


@router.post("/{employee_id:uuid}/probation/extend")
def extend_employee_probation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = _probation_record(db, employee)
    if not record or not record.probation_required:
        raise HTTPException(status_code=422, detail="No active probation record found")
    if record.extension_count >= (record.max_extension_count or 2):
        raise HTTPException(status_code=422, detail="Maximum probation extension count exceeded")
    new_end_date = _parse_import_date(payload.get("new_end_date") or payload.get("probation_end_date") or payload.get("end_date"))
    reason = _string(payload.get("reason") or payload.get("extension_reason"))
    if not new_end_date:
        raise HTTPException(status_code=422, detail="New probation end date is required")
    if not reason:
        raise HTTPException(status_code=422, detail="Probation extension reason is required")
    if record.end_date and new_end_date <= record.end_date:
        raise HTTPException(status_code=422, detail="New probation end date must be after current end date")
    before = _serialize_probation(record, employee)
    record.end_date = new_end_date
    record.extended = True
    record.extension_count = (record.extension_count or 0) + 1
    record.extension_reason = reason
    record.status = "Extended"
    record.updated_by = user.full_name
    employee.probation_end_date = new_end_date
    employee.probation_extended = True
    employee.probation_extension_count = record.extension_count
    employee.probation_extension_reason = reason
    employee.probation_status = "Extended"
    db.add(HRMProbationReview(employee_id=employee.id, probation_record_id=record.id, review_type="extension", outcome="Extended", comments=reason, reviewer=user.full_name))
    _audit_probation(db, employee, user, "EMP-006_PROBATION_EXTENDED", before, _serialize_probation(record, employee))
    for recipient in ["Employee", "Manager", "HR Team"]:
        db.add(NotificationEvent(module="HRM", related_entity="Employee", related_id=employee.id, recipient_name=recipient, subject="Probation extended", body=f"{_full_name(employee)} probation was extended to {new_end_date}.", status="queued", created_by=user.full_name))
    db.commit()
    return _serialize_probation(record, employee)


@router.post("/{employee_id:uuid}/probation/confirm")
def confirm_employee_probation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = _probation_record(db, employee)
    if not record:
        raise HTTPException(status_code=422, detail="No probation record found")
    before = _serialize_probation(record, employee)
    today = date.today()
    record.status = "Confirmed"
    record.confirmed_date = today
    record.confirmed_by = user.full_name
    employee.probation_status = "Confirmed"
    employee.probation_confirmed_date = today
    employee.probation_confirmed_by = user.full_name
    db.add(HRMProbationReview(employee_id=employee.id, probation_record_id=record.id, review_type="confirmation", outcome="Confirmed", comments=_string(payload.get("comments")), reviewer=user.full_name))
    db.add(EnterpriseEvent(event_type="EmployeeConfirmationRequested", source_module="HRM", target_module="HRM", payload={"employee_id": str(employee.id), "employee_code": employee.employee_code}, event_status="pending", created_by=user.full_name))
    _audit_probation(db, employee, user, "EMP-006_PROBATION_CONFIRMED", before, _serialize_probation(record, employee))
    db.commit()
    return _serialize_probation(record, employee)


@router.post("/{employee_id:uuid}/probation/fail")
def fail_employee_probation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = _probation_record(db, employee)
    if not record:
        raise HTTPException(status_code=422, detail="No probation record found")
    reason = _string(payload.get("reason") or payload.get("failed_reason"))
    if not reason:
        raise HTTPException(status_code=422, detail="Probation failure reason is required")
    before = _serialize_probation(record, employee)
    record.status = "Failed"
    record.failed_date = date.today()
    record.failed_reason = reason
    employee.probation_status = "Failed"
    db.add(HRMProbationReview(employee_id=employee.id, probation_record_id=record.id, review_type="failure", outcome="Failed", comments=reason, reviewer=user.full_name))
    db.add(EnterpriseEvent(event_type="ProbationFailureEscalationRequested", source_module="HRM", target_module="HRM", payload={"employee_id": str(employee.id), "employee_code": employee.employee_code, "reason": reason}, event_status="pending", created_by=user.full_name))
    _audit_probation(db, employee, user, "EMP-006_PROBATION_FAILED", before, _serialize_probation(record, employee))
    db.commit()
    return _serialize_probation(record, employee)


@router.post("/{employee_id:uuid}/probation/close")
def close_employee_probation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = _probation_record(db, employee)
    if not record:
        raise HTTPException(status_code=422, detail="No probation record found")
    before = _serialize_probation(record, employee)
    record.status = "Closed"
    employee.probation_status = "Closed"
    db.add(HRMProbationReview(employee_id=employee.id, probation_record_id=record.id, review_type="closure", outcome="Closed", comments=_string(payload.get("comments")), reviewer=user.full_name))
    _audit_probation(db, employee, user, "EMP-006_PROBATION_CLOSED", before, _serialize_probation(record, employee))
    db.commit()
    return _serialize_probation(record, employee)


@router.get("/confirmations/pending")
def get_pending_confirmations(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    rows = (
        db.query(HRMEmployee)
        .filter(
            HRMEmployee.employment_status.in_(["active", "probation"]),
            HRMEmployee.probation_status.in_(["Due for Review", "Extended", "Confirmed", "Closed"]),
            or_(
                HRMEmployee.confirmation_status.is_(None),
                HRMEmployee.confirmation_status.in_(["Pending Confirmation", "Confirmation Deferred"]),
            ),
        )
        .order_by(HRMEmployee.probation_end_date.asc().nullslast(), HRMEmployee.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(employee.id),
            "employee_code": employee.employee_code,
            "employee_name": _full_name(employee),
            "department": employee.department,
            "job_title": employee.job_title,
            "probation_status": employee.probation_status,
            "probation_end_date": employee.probation_end_date,
            "confirmation_status": employee.confirmation_status or "Pending Confirmation",
            "next_review_date": employee.next_confirmation_review_date,
        }
        for employee in rows
    ]


@router.get("/{employee_id:uuid}/confirmation")
def get_employee_confirmation(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return _serialize_confirmation(_latest_confirmation_record(db, employee), employee)


@router.post("/{employee_id:uuid}/confirm")
def confirm_employee(
    employee_id: UUID,
    payload: dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    allow_override = bool(payload.get("override"))
    probation_record, review = _confirmation_precheck(db, employee, "confirm", payload, allow_override)
    before = _serialize_confirmation(_latest_confirmation_record(db, employee), employee)
    confirmation_date = _parse_import_date(payload.get("confirmation_date")) or date.today()
    record = _confirmation_record(db, employee, "confirm", "Confirmed", user, {**payload, "confirmation_date": confirmation_date}, probation_record, review)
    employee.probation_status = "Confirmed"
    employee.probation_confirmed_date = confirmation_date
    employee.probation_confirmed_by = user.full_name
    employee.confirmation_status = "Confirmed"
    employee.confirmation_date = confirmation_date
    employee.confirmed_by = user.full_name
    employee.confirmation_notes = _string(payload.get("confirmation_notes") or payload.get("notes"))
    employee.probation_review_id = review.id if review else None
    employee.employment_status = "active"
    if probation_record:
        probation_record.status = "Confirmed"
        probation_record.confirmed_date = confirmation_date
        probation_record.confirmed_by = user.full_name
    if probation_record:
        db.add(HRMProbationReview(employee_id=employee.id, probation_record_id=probation_record.id, review_type="confirmation", outcome="Confirmed", comments=employee.confirmation_notes, reviewer=user.full_name))
    _add_lifecycle_event(db, employee, "confirmation_status", before.get("confirmation_status"), "Confirmed")
    after = _serialize_confirmation(record, employee)
    _audit_confirmation(db, employee, user, "EMP-007_CONFIRM_EMPLOYEE", before, after)
    _queue_confirmation_notifications(db, employee, user, "Employee confirmed", f"{_full_name(employee)} has been confirmed effective {confirmation_date}.")
    db.commit()
    return after


@router.post("/{employee_id:uuid}/confirmation/defer")
def defer_employee_confirmation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    probation_record, review = _confirmation_precheck(db, employee, "defer", payload, bool(payload.get("override")))
    before = _serialize_confirmation(_latest_confirmation_record(db, employee), employee)
    record = _confirmation_record(db, employee, "defer", "Confirmation Deferred", user, payload, probation_record, review)
    employee.confirmation_status = "Confirmation Deferred"
    employee.confirmation_notes = _string(payload.get("reason") or payload.get("deferment_reason"))
    employee.next_confirmation_review_date = record.next_review_date
    employee.probation_review_id = review.id if review else None
    _add_lifecycle_event(db, employee, "confirmation_status", before.get("confirmation_status"), "Confirmation Deferred")
    after = _serialize_confirmation(record, employee)
    _audit_confirmation(db, employee, user, "EMP-007_DEFER_CONFIRMATION", before, after)
    _queue_confirmation_notifications(db, employee, user, "Employee confirmation deferred", f"{_full_name(employee)} confirmation was deferred to {record.next_review_date}.")
    db.commit()
    return after


@router.post("/{employee_id:uuid}/confirmation/reject")
def reject_employee_confirmation(
    employee_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    probation_record, review = _confirmation_precheck(db, employee, "reject", payload, bool(payload.get("override")))
    before = _serialize_confirmation(_latest_confirmation_record(db, employee), employee)
    record = _confirmation_record(db, employee, "reject", "Rejected", user, payload, probation_record, review)
    employee.confirmation_status = "Rejected"
    employee.confirmation_notes = _string(payload.get("reason") or payload.get("rejection_reason"))
    employee.probation_review_id = review.id if review else None
    if probation_record:
        probation_record.status = "Failed"
        probation_record.failed_date = date.today()
        probation_record.failed_reason = employee.confirmation_notes
    if probation_record:
        db.add(HRMProbationReview(employee_id=employee.id, probation_record_id=probation_record.id, review_type="confirmation_rejection", outcome="Rejected", comments=employee.confirmation_notes, reviewer=user.full_name))
    _add_lifecycle_event(db, employee, "confirmation_status", before.get("confirmation_status"), "Rejected")
    after = _serialize_confirmation(record, employee)
    _audit_confirmation(db, employee, user, "EMP-007_REJECT_CONFIRMATION", before, after)
    _queue_confirmation_notifications(db, employee, user, "Employee confirmation rejected", f"{_full_name(employee)} confirmation was rejected and requires HR escalation.")
    db.commit()
    return after


@router.get("/import/template", response_class=PlainTextResponse)
def download_employee_import_template(db: Session = Depends(get_db)):
    return PlainTextResponse(
        _employee_import_template(db),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employee-import-template.csv"},
    )


@router.post("/import/validate", status_code=status.HTTP_201_CREATED)
async def validate_employee_import(
    file: UploadFile = File(...),
    mode: str = Query(default="validate_only"),
    import_as_draft: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    mode = "draft" if import_as_draft else mode
    if mode not in EMPLOYEE_IMPORT_MODES:
        raise HTTPException(status_code=422, detail="Invalid import mode")
    content, rows, summary, suffix = await _read_employee_import_file(file)
    batch = _create_employee_import_batch(db, file, content, suffix, rows, summary, user, mode)
    _validate_employee_import(db, batch, rows, import_as_draft or mode == "draft", mode if mode != "validate_only" else "create")
    batch.processing_status = "validated" if not batch.rejected_rows else batch.processing_status
    batch.parse_summary = f"{summary} Valid rows: {batch.valid_rows}. Rejected rows: {batch.rejected_rows}."
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action="EMP-003_VALIDATE_IMPORT",
            entity_type="HRMEmployeeImportBatch",
            entity_id=str(batch.id),
            sensitivity="internal",
            summary=f"Validated employee import batch {batch.batch_number}: {batch.valid_rows} valid, {batch.rejected_rows} rejected.",
            after_json={"batch_number": batch.batch_number, "file_hash": batch.file_hash, "mode": mode},
        )
    )
    db.commit()
    db.refresh(batch)
    return _serialize_import_batch(batch)


def _process_import_batch(db: Session, batch: HRMEmployeeImportBatch, mode: str, import_as_draft: bool, user: UserResponse):
    created = updated = 0
    rows = db.query(HRMEmployeeImportRow).filter(HRMEmployeeImportRow.batch_id == batch.id).order_by(HRMEmployeeImportRow.row_number.asc()).all()
    for row in rows:
        if row.row_status != "valid":
            continue
        payload = _normalize_employee_import_row(db, row.row_payload or {}, import_as_draft)
        payload.pop("import_warnings", None)
        existing = _existing_employee_for_import(db, payload)
        try:
            if existing and mode in {"update", "upsert"}:
                before = {key: getattr(existing, key, None) for key in ["email", "phone", "department", "job_title", "supervisor_id", "employment_status"]}
                payload.pop("employee_code", None)
                for key, value in payload.items():
                    if key in {"employee_code"}:
                        continue
                    if hasattr(existing, key) and value not in [None, ""]:
                        setattr(existing, key, value)
                _sync_employee_foundation(db, existing)
                row.employee_id = existing.id
                row.employee_code = existing.employee_code
                row.action_taken = "updated"
                row.row_status = "updated"
                updated += 1
                db.add(
                    HRMAuditLog(
                        actor_user_id=user.id if isinstance(user.id, UUID) else None,
                        actor_email=user.email,
                        action="EMP-003_IMPORT_UPDATE_ROW",
                        entity_type="HRMEmployee",
                        entity_id=str(existing.id),
                        sensitivity="confidential",
                        summary=f"Employee updated from import batch {batch.batch_number}.",
                        before_json=before,
                        after_json={key: str(value) if isinstance(value, (date, Decimal, UUID)) else value for key, value in payload.items()},
                    )
                )
            elif not existing and mode in {"create", "upsert", "draft"}:
                payload["employee_code"] = _next_employee_code(db)
                if import_as_draft or mode == "draft":
                    payload["employment_status"] = "draft"
                record = HRMEmployee(**payload)
                db.add(record)
                db.flush()
                _audit_employee_number_generation(db, record, user, None)
                _add_lifecycle_event(db, record, "hire", None, record.employment_status)
                _sync_employee_foundation(db, record)
                _queue_employee_notifications(db, record, user)
                _audit_employee_creation(db, record, user)
                row.employee_id = record.id
                row.employee_code = record.employee_code
                row.action_taken = "created"
                row.row_status = "created"
                created += 1
            else:
                row.row_status = "rejected"
                row.error_messages = ["Import mode does not allow this row action"]
                batch.rejected_rows = (batch.rejected_rows or 0) + 1
        except Exception as exc:
            row.row_status = "rejected"
            row.error_messages = [str(exc)]
            batch.rejected_rows = (batch.rejected_rows or 0) + 1
    batch.created_rows = created
    batch.updated_rows = updated
    batch.processing_status = "completed" if not batch.rejected_rows else "completed_with_errors" if created or updated else "failed"
    batch.parse_summary = f"{batch.parse_summary or ''} Created {created}. Updated {updated}. Rejected {batch.rejected_rows}.".strip()


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_employee_records(
    file: UploadFile = File(...),
    mode: str = Query(default="create"),
    import_as_draft: bool = Query(default=False),
    rollback_on_error: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    mode = "draft" if import_as_draft else mode
    if mode not in EMPLOYEE_IMPORT_MODES - {"validate_only"}:
        raise HTTPException(status_code=422, detail="Invalid import mode")
    content, rows, summary, suffix = await _read_employee_import_file(file)
    batch = _create_employee_import_batch(db, file, content, suffix, rows, summary, user, mode)
    _validate_employee_import(db, batch, rows, import_as_draft or mode == "draft", mode)
    if rollback_on_error and batch.rejected_rows:
        batch.processing_status = "rejected"
        batch.parse_summary = f"{summary} Full rollback policy selected: no rows imported because {batch.rejected_rows} row(s) failed validation."
        db.commit()
        db.refresh(batch)
        return _serialize_import_batch(batch)
    _process_import_batch(db, batch, mode, import_as_draft or mode == "draft", user)
    db.add(
        NotificationEvent(
            module="HRM",
            related_entity="HRMEmployeeImportBatch",
            related_id=batch.id,
            recipient_name=user.full_name,
            recipient_email=user.email,
            subject=f"EMP-003 employee import completed: {batch.batch_number}",
            body=f"Created {batch.created_rows}, updated {batch.updated_rows}, rejected {batch.rejected_rows}.",
            status="queued",
            created_by=user.full_name,
        )
    )
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action="EMP-003_PROCESS_IMPORT",
            entity_type="HRMEmployeeImportBatch",
            entity_id=str(batch.id),
            sensitivity="confidential",
            summary=f"Processed employee import batch {batch.batch_number}.",
            after_json=_serialize_import_batch(batch),
        )
    )
    db.commit()
    db.refresh(batch)
    return _serialize_import_batch(batch)


@router.get("/import/{batch_id}")
def get_employee_import_batch(batch_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    batch = get_or_404(db, HRMEmployeeImportBatch, batch_id, "Employee import batch")
    return _serialize_import_batch(batch)


@router.get("/import/{batch_id}/errors")
def get_employee_import_errors(batch_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    get_or_404(db, HRMEmployeeImportBatch, batch_id, "Employee import batch")
    rows = (
        db.query(HRMEmployeeImportRow)
        .filter(HRMEmployeeImportRow.batch_id == batch_id, HRMEmployeeImportRow.row_status.in_(["rejected", "failed"]))
        .order_by(HRMEmployeeImportRow.row_number.asc())
        .all()
    )
    return [_serialize_import_row(row) for row in rows]


@router.post("/import/{batch_id}/approve")
def approve_employee_import(batch_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_admin(user)
    batch = get_or_404(db, HRMEmployeeImportBatch, batch_id, "Employee import batch")
    batch.approval_status = "approved"
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action="EMP-003_APPROVE_IMPORT",
            entity_type="HRMEmployeeImportBatch",
            entity_id=str(batch.id),
            sensitivity="confidential",
            summary=f"Approved employee import batch {batch.batch_number}.",
        )
    )
    db.commit()
    db.refresh(batch)
    return _serialize_import_batch(batch)


@router.post("/import/{batch_id}/rollback")
def rollback_employee_import(batch_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_admin(user)
    batch = get_or_404(db, HRMEmployeeImportBatch, batch_id, "Employee import batch")
    rows = db.query(HRMEmployeeImportRow).filter(HRMEmployeeImportRow.batch_id == batch.id, HRMEmployeeImportRow.action_taken == "created").all()
    rolled_back = 0
    for row in rows:
        if row.employee_id:
            employee = db.query(HRMEmployee).filter(HRMEmployee.id == row.employee_id).first()
            if employee:
                db.delete(employee)
                rolled_back += 1
        row.row_status = "rolled_back"
    batch.rollback_status = "completed"
    batch.processing_status = "rolled_back"
    db.add(
        HRMAuditLog(
            actor_user_id=user.id if isinstance(user.id, UUID) else None,
            actor_email=user.email,
            action="EMP-003_ROLLBACK_IMPORT",
            entity_type="HRMEmployeeImportBatch",
            entity_id=str(batch.id),
            sensitivity="confidential",
            summary=f"Rolled back {rolled_back} employees from import batch {batch.batch_number}.",
        )
    )
    db.commit()
    db.refresh(batch)
    return {**_serialize_import_batch(batch), "rolled_back_rows": rolled_back}


@router.get("/profile/analytics")
def get_profile_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employees = db.query(HRMEmployee).all()
    total = len(employees)
    completion_values = [float(employee.profile_completion_percentage or _profile_completion(employee)) for employee in employees]
    missing = {
        "date_of_birth": sum(1 for employee in employees if not employee.date_of_birth),
        "gender": sum(1 for employee in employees if not employee.gender),
        "contact": sum(1 for employee in employees if not (employee.phone or employee.personal_email or employee.email)),
        "address": sum(1 for employee in employees if not (employee.physical_address or employee.address)),
        "emergency_contact": max(total - db.query(HRMEmergencyContact.employee_id).filter(HRMEmergencyContact.status == "active").distinct().count(), 0),
    }
    demographics: dict[str, int] = {}
    for employee in employees:
        key = employee.nationality or "Unspecified"
        demographics[key] = demographics.get(key, 0) + 1
    return {
        "total_employees": total,
        "average_profile_completion": round(sum(completion_values) / total, 2) if total else 0,
        "complete_profiles": sum(1 for value in completion_values if value >= 90),
        "missing_employee_data": missing,
        "dependants": {
            "active": db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.status == "active").count(),
            "medical_cover_eligible": db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.medical_cover_eligible == True, HRMEmployeeDependant.status == "active").count(),  # noqa: E712
        },
        "nationality_distribution": demographics,
    }


@router.get("/profile/reports/{report_name}")
def get_profile_report(report_name: str, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employees = db.query(HRMEmployee).order_by(HRMEmployee.department.asc().nullslast(), HRMEmployee.last_name.asc()).all()
    if report_name == "employee-directory":
        return [
            {
                "employee_code": employee.employee_code,
                "name": _full_name(employee),
                "department": employee.department,
                "job_title": employee.job_title,
                "corporate_email": employee.corporate_email or employee.email,
                "mobile_number": employee.phone,
                "city": employee.city,
                "country": employee.country,
            }
            for employee in employees
        ]
    if report_name == "missing-information":
        return [
            {
                "employee_code": employee.employee_code,
                "name": _full_name(employee),
                "missing": [
                    label
                    for label, value in {
                        "date_of_birth": employee.date_of_birth,
                        "gender": employee.gender,
                        "national_id_or_passport": employee.national_id or employee.passport_number,
                        "phone": employee.phone,
                        "address": employee.physical_address or employee.address,
                        "marital_status": employee.marital_status,
                    }.items()
                    if not value
                ],
                "profile_completion": float(employee.profile_completion_percentage or _profile_completion(employee)),
            }
            for employee in employees
        ]
    if report_name == "dependants":
        return [_serialize_model(row) for row in db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.status == "active").all()]
    if report_name == "emergency-contacts":
        return [_serialize_model(row) for row in db.query(HRMEmergencyContact).filter(HRMEmergencyContact.status == "active").all()]
    if report_name == "profile-completion":
        return [{"employee_code": employee.employee_code, "name": _full_name(employee), "completion": float(employee.profile_completion_percentage or _profile_completion(employee))} for employee in employees]
    if report_name == "demographics":
        return [{"employee_code": employee.employee_code, "name": _full_name(employee), "gender": employee.gender, "date_of_birth": employee.date_of_birth, "nationality": employee.nationality, "marital_status": employee.marital_status} for employee in employees]
    raise HTTPException(status_code=404, detail="Employee profile report not found")


@router.post("/{employee_id:uuid}/profile", status_code=status.HTTP_201_CREATED)
def create_employee_profile(employee_id: UUID, payload: EmployeeProfilePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    if db.query(HRMEmployeeProfile).filter(HRMEmployeeProfile.employee_id == employee.id).first():
        raise HTTPException(status_code=409, detail="Employee personal profile already exists")
    data = payload.model_dump(exclude={"change_reason"})
    _validate_unique_profile_values(db, employee, data)
    for key, value in data.items():
        setattr(employee, key, value)
    _sync_profile_completion(db, employee)
    profile = HRMEmployeeProfile(employee_id=employee.id, employee_status=employee.employment_status, profile_completion_percentage=employee.profile_completion_percentage, created_by=user.full_name, **data)
    db.add(profile)
    _profile_history(db, employee, user, "personal_information", None, data, payload.change_reason)
    _audit_profile_event(db, employee, user, "EMP-009_PROFILE_CREATED", "Employee personal profile created.", after=data)
    db.commit()
    db.refresh(employee)
    return get_employee_profile(employee_id, db, user)


@router.get("/{employee_id:uuid}/profile")
def get_employee_profile(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    _sync_profile_completion(db, employee)
    profile = db.query(HRMEmployeeProfile).filter(HRMEmployeeProfile.employee_id == employee.id).first()
    contact = db.query(HRMEmployeeContactInformation).filter(HRMEmployeeContactInformation.employee_id == employee.id).first()
    biography = db.query(HRMEmployeeBiography).filter(HRMEmployeeBiography.employee_id == employee.id).first()
    photo = db.query(HRMEmployeeProfilePhoto).filter(HRMEmployeeProfilePhoto.employee_id == employee.id, HRMEmployeeProfilePhoto.active == True).order_by(HRMEmployeeProfilePhoto.created_at.desc()).first()  # noqa: E712
    change_requests = db.query(HRMEmployeeChangeRequest).filter(HRMEmployeeChangeRequest.employee_id == employee.id).order_by(HRMEmployeeChangeRequest.created_at.desc()).limit(20).all()
    audit_rows = db.query(HRMAuditLog).filter(HRMAuditLog.entity_id == str(employee.id)).order_by(HRMAuditLog.created_at.desc()).limit(30).all()
    return {
        "employee_id": employee.id,
        "profile_completion_percentage": float(employee.profile_completion_percentage or _profile_completion(employee)),
        "personal_information": _serialize_model(profile) or _profile_payload(employee),
        "contact_information": _serialize_model(contact) or _contact_payload(employee),
        "dependants": [_serialize_model(row) for row in db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.employee_id == employee.id, HRMEmployeeDependant.status == "active").order_by(HRMEmployeeDependant.created_at.desc()).all()],
        "emergency_contacts": [_serialize_model(row) for row in db.query(HRMEmergencyContact).filter(HRMEmergencyContact.employee_id == employee.id, HRMEmergencyContact.status == "active").order_by(HRMEmergencyContact.created_at.desc()).all()],
        "biography": _serialize_model(biography) or {
            "employee_bio": employee.biography,
            "professional_summary": employee.professional_summary,
            "skills": employee.skills,
            "languages": employee.languages,
            "certifications_summary": employee.certifications_summary,
        },
        "active_photo": _serialize_model(photo),
        "change_requests": [_serialize_model(row) for row in change_requests],
        "audit_history": [_serialize_model(row) for row in audit_rows],
    }


@router.put("/{employee_id:uuid}/profile")
def update_employee_profile(employee_id: UUID, payload: EmployeeProfileUpdate, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    data = payload.model_dump(exclude_unset=True, exclude={"change_reason"})
    if not data:
        return get_employee_profile(employee_id, db, user)
    _validate_unique_profile_values(db, employee, data)
    before = _profile_payload(employee)
    changes_requiring_approval = _sensitive_profile_changes(before, data)
    approval_status = "applied"
    if changes_requiring_approval and user.role != "admin":
        request = _queue_profile_change_request(db, employee, user, "personal_information", changes_requiring_approval, payload.change_reason)
        _profile_history(db, employee, user, "personal_information", before, changes_requiring_approval, payload.change_reason, "pending_hr_approval")
        _audit_profile_event(db, employee, user, "PROFILE_CHANGE_REQUESTED", "Sensitive profile change request created.", before=before, after=_serialize_model(request))
        db.commit()
        return get_employee_profile(employee_id, db, user)
    for key, value in data.items():
        setattr(employee, key, value)
    profile = db.query(HRMEmployeeProfile).filter(HRMEmployeeProfile.employee_id == employee.id).first()
    profile_data = {**_profile_payload(employee), "employee_status": employee.employment_status}
    if not profile and employee.first_name and employee.last_name and employee.gender and employee.date_of_birth:
        profile = HRMEmployeeProfile(employee_id=employee.id, created_by=user.full_name, **profile_data)
        db.add(profile)
    elif profile:
        for key, value in profile_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_by = user.full_name
    _sync_profile_completion(db, employee)
    after = _profile_payload(employee)
    _profile_history(db, employee, user, "personal_information", before, after, payload.change_reason, approval_status)
    action = "EMP-012_MARITAL_STATUS_CHANGED" if "marital_status" in data else "EMP-010_PERSONAL_DETAILS_UPDATED"
    _audit_profile_event(db, employee, user, action, "Employee personal details updated.", before=before, after=after)
    if "marital_status" in data:
        db.add(EnterpriseEvent(event_type="EmployeeMaritalStatusChanged", source_module="HRM", target_module="Benefits", payload={"employee_id": str(employee.id), "marital_status": employee.marital_status}, status="pending", created_by=user.full_name))
    db.commit()
    db.refresh(employee)
    return get_employee_profile(employee_id, db, user)


@router.get("/{employee_id:uuid}/contacts")
def get_employee_contacts(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    contact = db.query(HRMEmployeeContactInformation).filter(HRMEmployeeContactInformation.employee_id == employee.id).first()
    return _serialize_model(contact) or _contact_payload(employee)


@router.put("/{employee_id:uuid}/contacts")
def update_employee_contacts(employee_id: UUID, payload: ContactInformationPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    data = payload.model_dump(exclude_unset=True, exclude={"change_reason"})
    _validate_unique_profile_values(db, employee, data)
    before = _contact_payload(employee)
    employee.personal_email = _string(data.get("personal_email") or employee.personal_email).lower() or None
    employee.corporate_email = data.get("corporate_email", employee.corporate_email)
    employee.phone = data.get("mobile_number", employee.phone)
    employee.alternative_phone = data.get("alternative_phone", employee.alternative_phone)
    employee.physical_address = data.get("physical_address", employee.physical_address)
    employee.postal_address = data.get("postal_address", employee.postal_address)
    employee.city = data.get("city", employee.city)
    employee.county = data.get("county", employee.county)
    employee.country = data.get("country", employee.country)
    contact = db.query(HRMEmployeeContactInformation).filter(HRMEmployeeContactInformation.employee_id == employee.id).first()
    if not contact:
        contact = HRMEmployeeContactInformation(employee_id=employee.id, created_by=user.full_name)
        db.add(contact)
    for key, value in _contact_payload(employee).items():
        if hasattr(contact, key):
            setattr(contact, key, value)
    contact.updated_by = user.full_name
    _sync_profile_completion(db, employee)
    after = _contact_payload(employee)
    _profile_history(db, employee, user, "contact_information", before, after, payload.change_reason)
    _audit_profile_event(db, employee, user, "EMP-011_CONTACT_INFORMATION_UPDATED", "Employee contact information updated.", before=before, after=after)
    db.commit()
    return get_employee_contacts(employee_id, db, user)


@router.post("/{employee_id:uuid}/dependants", status_code=status.HTTP_201_CREATED)
def add_employee_dependant(employee_id: UUID, payload: DependantPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    duplicate = db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.employee_id == employee.id, HRMEmployeeDependant.full_name.ilike(payload.full_name), HRMEmployeeDependant.relationship.ilike(payload.relationship), HRMEmployeeDependant.status == "active").first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Duplicate active dependant found")
    active_count = db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.employee_id == employee.id, HRMEmployeeDependant.status == "active").count()
    if active_count >= 10:
        raise HTTPException(status_code=422, detail="Maximum dependant limit reached")
    current_percentage = sum(float(row.beneficiary_percentage or 0) for row in db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.employee_id == employee.id, HRMEmployeeDependant.status == "active").all())
    if current_percentage + payload.beneficiary_percentage > 100:
        raise HTTPException(status_code=422, detail="Total beneficiary percentage cannot exceed 100")
    record = HRMEmployeeDependant(employee_id=employee.id, created_by=user.full_name, **payload.model_dump())
    db.add(record)
    db.flush()
    after = _serialize_model(record)
    db.add(HRMEmployeeDependantHistory(dependant_id=record.id, employee_id=employee.id, action="EMP-013_DEPENDANT_ADDED", after_json=after, changed_by=user.full_name))
    _audit_profile_event(db, employee, user, "EMP-013_DEPENDANT_ADDED", "Employee dependant added.", after=after)
    db.commit()
    return after


@router.get("/{employee_id:uuid}/dependants")
def get_employee_dependants(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return [_serialize_model(row) for row in db.query(HRMEmployeeDependant).filter(HRMEmployeeDependant.employee_id == employee.id, HRMEmployeeDependant.status == "active").order_by(HRMEmployeeDependant.created_at.desc()).all()]


@router.put("/{employee_id:uuid}/dependants/{dependant_id:uuid}")
def update_employee_dependant(employee_id: UUID, dependant_id: UUID, payload: DependantUpdate, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = get_or_404(db, HRMEmployeeDependant, dependant_id, "Dependant")
    if record.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Dependant not found for this employee")
    before = _serialize_model(record)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    record.updated_by = user.full_name
    db.flush()
    after = _serialize_model(record)
    db.add(HRMEmployeeDependantHistory(dependant_id=record.id, employee_id=employee.id, action="DEPENDANT_UPDATED", before_json=before, after_json=after, changed_by=user.full_name))
    _audit_profile_event(db, employee, user, "DEPENDANT_UPDATED", "Employee dependant updated.", before=before, after=after)
    db.commit()
    return after


@router.delete("/{employee_id:uuid}/dependants/{dependant_id:uuid}", status_code=status.HTTP_200_OK)
def remove_employee_dependant(employee_id: UUID, dependant_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = get_or_404(db, HRMEmployeeDependant, dependant_id, "Dependant")
    if record.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Dependant not found for this employee")
    before = _serialize_model(record)
    record.status = "archived"
    record.soft_deleted = True
    record.archived_at = datetime.utcnow()
    record.archive_reason = "Archived from employee profile"
    db.add(HRMEmployeeDependantHistory(dependant_id=record.id, employee_id=employee.id, action="EMP-014_DEPENDANT_REMOVED", before_json=before, changed_by=user.full_name))
    _audit_profile_event(db, employee, user, "EMP-014_DEPENDANT_REMOVED", "Employee dependant archived.", before=before)
    db.commit()
    return {"status": "archived", "dependant_id": dependant_id}


@router.post("/{employee_id:uuid}/emergency-contacts", status_code=status.HTTP_201_CREATED)
def add_employee_emergency_contact(employee_id: UUID, payload: EmergencyContactPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = HRMEmergencyContact(employee_id=employee.id, contact_name=payload.full_name, relationship=payload.relationship, phone=payload.phone_number, email=payload.email, address=payload.address, is_primary=payload.is_primary, status="active")
    if hasattr(record, "alternative_phone"):
        record.alternative_phone = payload.alternative_phone
    if hasattr(record, "created_by"):
        record.created_by = user.full_name
    db.add(record)
    db.flush()
    after = _serialize_model(record)
    db.add(HRMEmployeeEmergencyContactHistory(contact_id=record.id, employee_id=employee.id, action="EMP-015_EMERGENCY_CONTACT_ADDED", after_json=after, changed_by=user.full_name))
    _audit_profile_event(db, employee, user, "EMP-015_EMERGENCY_CONTACT_ADDED", "Employee emergency contact added.", after=after)
    db.commit()
    return after


@router.get("/{employee_id:uuid}/emergency-contacts")
def get_employee_emergency_contacts(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return [_serialize_model(row) for row in db.query(HRMEmergencyContact).filter(HRMEmergencyContact.employee_id == employee.id, HRMEmergencyContact.status == "active").order_by(HRMEmergencyContact.created_at.desc()).all()]


@router.put("/{employee_id:uuid}/emergency-contacts/{contact_id:uuid}")
def update_employee_emergency_contact(employee_id: UUID, contact_id: UUID, payload: EmergencyContactUpdate, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = get_or_404(db, HRMEmergencyContact, contact_id, "Emergency contact")
    if record.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Emergency contact not found for this employee")
    before = _serialize_model(record)
    mapping = {"full_name": "contact_name", "phone_number": "phone"}
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, mapping.get(key, key), value)
    if hasattr(record, "updated_by"):
        record.updated_by = user.full_name
    db.flush()
    after = _serialize_model(record)
    db.add(HRMEmployeeEmergencyContactHistory(contact_id=record.id, employee_id=employee.id, action="EMP-016_EMERGENCY_CONTACT_UPDATED", before_json=before, after_json=after, changed_by=user.full_name))
    _audit_profile_event(db, employee, user, "EMP-016_EMERGENCY_CONTACT_UPDATED", "Employee emergency contact updated.", before=before, after=after)
    db.commit()
    return after


@router.get("/{employee_id:uuid}/biography")
def get_employee_biography(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    biography = db.query(HRMEmployeeBiography).filter(HRMEmployeeBiography.employee_id == employee.id).first()
    return _serialize_model(biography) or {"employee_bio": employee.biography, "professional_summary": employee.professional_summary, "skills": employee.skills, "languages": employee.languages, "certifications_summary": employee.certifications_summary}


@router.put("/{employee_id:uuid}/biography")
def update_employee_biography(employee_id: UUID, payload: BiographyPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    data = payload.model_dump(exclude_unset=True)
    if any(value and len(value) > 5000 for value in data.values()):
        raise HTTPException(status_code=422, detail="Biography fields are limited to 5000 characters")
    before = {"employee_bio": employee.biography, "professional_summary": employee.professional_summary, "skills": employee.skills, "languages": employee.languages, "certifications_summary": employee.certifications_summary}
    employee.biography = data.get("employee_bio", employee.biography)
    employee.professional_summary = data.get("professional_summary", employee.professional_summary)
    employee.skills = data.get("skills", employee.skills)
    employee.languages = data.get("languages", employee.languages)
    employee.certifications_summary = data.get("certifications_summary", employee.certifications_summary)
    biography = db.query(HRMEmployeeBiography).filter(HRMEmployeeBiography.employee_id == employee.id).first()
    if not biography:
        biography = HRMEmployeeBiography(employee_id=employee.id, created_by=user.full_name)
        db.add(biography)
    for key, value in {"employee_bio": employee.biography, "professional_summary": employee.professional_summary, "skills": employee.skills, "languages": employee.languages, "certifications_summary": employee.certifications_summary}.items():
        setattr(biography, key, value)
    biography.updated_by = user.full_name
    _sync_profile_completion(db, employee)
    after = {"employee_bio": employee.biography, "professional_summary": employee.professional_summary, "skills": employee.skills, "languages": employee.languages, "certifications_summary": employee.certifications_summary}
    _profile_history(db, employee, user, "biography", before, after)
    _audit_profile_event(db, employee, user, "EMP-018_BIOGRAPHY_UPDATED", "Employee biography updated.", before=before, after=after)
    db.commit()
    return get_employee_biography(employee_id, db, user)


@router.post("/{employee_id:uuid}/photo", status_code=status.HTTP_201_CREATED)
async def upload_employee_photo(employee_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()
    if suffix not in {"jpg", "jpeg", "png", "webp"}:
        raise HTTPException(status_code=422, detail="Employee photo must be JPG, JPEG, PNG, or WEBP")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Employee photo exceeds the 5MB limit")
    if not content.startswith((b"\xff\xd8", b"\x89PNG", b"RIFF")):
        raise HTTPException(status_code=422, detail="Uploaded file is not a supported image")
    photo_dir = get_upload_root() / "hrm" / "employees" / str(employee.id)
    photo_dir.mkdir(parents=True, exist_ok=True)
    file_hash = hashlib.sha256(content).hexdigest()
    file_name = f"profile-{file_hash[:12]}.{suffix}"
    path = photo_dir / file_name
    path.write_bytes(content)
    db.query(HRMEmployeeProfilePhoto).filter(HRMEmployeeProfilePhoto.employee_id == employee.id).update({"active": False})
    url = f"/uploads/hrm/employees/{employee.id}/{file_name}"
    photo = HRMEmployeeProfilePhoto(employee_id=employee.id, file_name=file.filename or file_name, file_url=url, thumbnail_url=url, content_type=file.content_type, file_size=len(content), file_hash=file_hash, active=True, created_by=user.full_name)
    employee.photo_url = url
    _sync_profile_completion(db, employee)
    db.add(photo)
    db.flush()
    _audit_profile_event(db, employee, user, "EMP-017_PHOTO_UPLOADED", "Employee profile photo uploaded.", after=_serialize_model(photo))
    db.commit()
    return _serialize_model(photo)


@router.delete("/{employee_id:uuid}/photo")
def delete_employee_photo(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    photos = db.query(HRMEmployeeProfilePhoto).filter(HRMEmployeeProfilePhoto.employee_id == employee.id, HRMEmployeeProfilePhoto.active == True).all()  # noqa: E712
    before = [_serialize_model(photo) for photo in photos]
    for photo in photos:
        photo.active = False
    employee.photo_url = None
    _sync_profile_completion(db, employee)
    _audit_profile_event(db, employee, user, "EMP-017_PHOTO_REMOVED", "Employee profile photo removed.", before={"photos": before})
    db.commit()
    return {"status": "removed"}


@router.get("/{employee_id:uuid}/assignments")
def get_employee_assignments(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    projects = db.query(HRMEmployeeProjectAssignment).filter(HRMEmployeeProjectAssignment.employee_id == employee.id, HRMEmployeeProjectAssignment.status == "active").all()
    documents = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.status != "archived").all()
    required = _document_required_types()
    present = {doc.document_type for doc in documents if doc.status == "active" and doc.verification_status == "Verified"}
    return {
        "current": {"department": employee.department, "branch": employee.branch, "business_unit": employee.business_unit},
        "departments": [_serialize_model(row) for row in db.query(HRMEmployeeDepartmentAssignment).filter(HRMEmployeeDepartmentAssignment.employee_id == employee.id).order_by(HRMEmployeeDepartmentAssignment.created_at.desc()).all()],
        "branches": [_serialize_model(row) for row in db.query(HRMEmployeeBranchAssignment).filter(HRMEmployeeBranchAssignment.employee_id == employee.id).order_by(HRMEmployeeBranchAssignment.created_at.desc()).all()],
        "business_units": [_serialize_model(row) for row in db.query(HRMEmployeeBusinessUnitAssignment).filter(HRMEmployeeBusinessUnitAssignment.employee_id == employee.id).order_by(HRMEmployeeBusinessUnitAssignment.created_at.desc()).all()],
        "projects": [_serialize_model(row) for row in projects],
        "teams": [_serialize_model(row) for row in db.query(HRMEmployeeTeamAssignment).filter(HRMEmployeeTeamAssignment.employee_id == employee.id, HRMEmployeeTeamAssignment.status == "active").order_by(HRMEmployeeTeamAssignment.created_at.desc()).all()],
        "history": [_serialize_model(row) for row in db.query(HRMEmployeeAssignmentHistory).filter(HRMEmployeeAssignmentHistory.employee_id == employee.id).order_by(HRMEmployeeAssignmentHistory.created_at.desc()).limit(50).all()],
        "analytics": {"project_allocation": sum(float(row.allocation_percentage or 0) for row in projects), "missing_documents": sorted(required - present)},
    }


@router.post("/{employee_id:uuid}/department")
def assign_department(employee_id: UUID, payload: OrgAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _save_org_assignment(db, employee_id, payload, user, "department", "EMP-031", False)


@router.put("/{employee_id:uuid}/department-transfer")
def transfer_department(employee_id: UUID, payload: OrgAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _save_org_assignment(db, employee_id, payload, user, "department", "EMP-032", True)


@router.post("/{employee_id:uuid}/branch")
def assign_branch(employee_id: UUID, payload: OrgAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _save_org_assignment(db, employee_id, payload, user, "branch", "EMP-033", False)


@router.put("/{employee_id:uuid}/branch-transfer")
def transfer_branch(employee_id: UUID, payload: OrgAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _save_org_assignment(db, employee_id, payload, user, "branch", "EMP-034", True)


@router.post("/{employee_id:uuid}/business-unit")
def assign_business_unit(employee_id: UUID, payload: OrgAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _save_org_assignment(db, employee_id, payload, user, "business_unit", "EMP-035", False)


@router.put("/{employee_id:uuid}/business-unit-transfer")
def transfer_business_unit(employee_id: UUID, payload: OrgAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _save_org_assignment(db, employee_id, payload, user, "business_unit", "EMP-036", True)


@router.post("/{employee_id:uuid}/projects")
def assign_employee_project(employee_id: UUID, payload: ProjectAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    project = db.query(Project).filter(Project.id == payload.project_id, Project.soft_deleted == False).first()  # noqa: E712
    project_name = payload.project_name or (project.project_name if project else None)
    active = db.query(HRMEmployeeProjectAssignment).filter(HRMEmployeeProjectAssignment.employee_id == employee.id, HRMEmployeeProjectAssignment.status == "active").all()
    total = sum(float(row.allocation_percentage or 0) for row in active)
    if total + payload.allocation_percentage > 100:
        raise HTTPException(status_code=422, detail="Total active project allocation cannot exceed 100%")
    record = HRMEmployeeProjectAssignment(employee_id=employee.id, project_id=payload.project_id, project_name=project_name, project_role=payload.role, allocation_percentage=Decimal(str(payload.allocation_percentage)), start_date=payload.start_date, end_date=payload.end_date, reason=payload.reason, initiated_by=user.full_name)
    db.add(record)
    _assignment_history(db, employee, user, "EMP-037", "project", None, project_name or payload.project_id, payload.start_date, payload.reason)
    _audit_assignment_event(db, employee, user, "EMP-037", "ASSIGN_PROJECT", None, project_name or payload.project_id, payload.reason)
    db.commit()
    return _serialize_model(record)


@router.delete("/{employee_id:uuid}/projects/{project_id:uuid}")
def remove_employee_project(employee_id: UUID, project_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = db.query(HRMEmployeeProjectAssignment).filter(HRMEmployeeProjectAssignment.employee_id == employee.id, HRMEmployeeProjectAssignment.project_id == project_id, HRMEmployeeProjectAssignment.status == "active").first()
    if not record:
        raise HTTPException(status_code=404, detail="Active project assignment not found")
    record.status = "removed"
    record.removed_at = datetime.utcnow()
    _assignment_history(db, employee, user, "EMP-038", "project", record.project_name or project_id, None, date.today(), "Project assignment removed", "removed")
    _audit_assignment_event(db, employee, user, "EMP-038", "REMOVE_PROJECT", record.project_name or project_id, None, "Project assignment removed")
    db.commit()
    return {"status": "removed"}


@router.post("/{employee_id:uuid}/teams")
def assign_employee_team(employee_id: UUID, payload: TeamAssignmentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    if employee.department and payload.department.lower() != employee.department.lower():
        raise HTTPException(status_code=422, detail="Team must belong to the employee department")
    if payload.primary_team:
        db.query(HRMEmployeeTeamAssignment).filter(HRMEmployeeTeamAssignment.employee_id == employee.id, HRMEmployeeTeamAssignment.status == "active").update({"primary_team": False})
    elif not db.query(HRMEmployeeTeamAssignment).filter(HRMEmployeeTeamAssignment.employee_id == employee.id, HRMEmployeeTeamAssignment.status == "active", HRMEmployeeTeamAssignment.primary_team == True).first():  # noqa: E712
        payload.primary_team = True
    record = HRMEmployeeTeamAssignment(employee_id=employee.id, team_name=payload.team_name, department=payload.department, primary_team=payload.primary_team, effective_from=payload.effective_date, reason=payload.reason, initiated_by=user.full_name)
    db.add(record)
    _assignment_history(db, employee, user, "EMP-039", "team", None, payload.team_name, payload.effective_date, payload.reason)
    _audit_assignment_event(db, employee, user, "EMP-039", "ASSIGN_TEAM", None, payload.team_name, payload.reason)
    db.commit()
    return _serialize_model(record)


@router.delete("/{employee_id:uuid}/teams/{team_id:uuid}")
def remove_employee_team(employee_id: UUID, team_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    record = get_or_404(db, HRMEmployeeTeamAssignment, team_id, "Team assignment")
    if record.employee_id != employee.id or record.status != "active":
        raise HTTPException(status_code=404, detail="Active team assignment not found")
    if record.primary_team:
        replacement = db.query(HRMEmployeeTeamAssignment).filter(HRMEmployeeTeamAssignment.employee_id == employee.id, HRMEmployeeTeamAssignment.id != record.id, HRMEmployeeTeamAssignment.status == "active").first()
        if not replacement:
            raise HTTPException(status_code=422, detail="Primary team replacement is required before removal")
        replacement.primary_team = True
    record.status = "removed"
    record.removed_at = datetime.utcnow()
    _assignment_history(db, employee, user, "EMP-040", "team", record.team_name, None, date.today(), "Team assignment removed", "removed")
    _audit_assignment_event(db, employee, user, "EMP-040", "REMOVE_TEAM", record.team_name, None, "Team assignment removed")
    db.commit()
    return {"status": "removed"}


@router.post("/{employee_id:uuid}/documents", status_code=status.HTTP_201_CREATED)
async def upload_employee_document(
    employee_id: UUID,
    document_type: str = Query(...),
    expiry_date: date | None = Query(default=None),
    issue_date: date | None = Query(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    config = _document_config(document_type)
    document_type_key = config["document_type"]
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()
    if suffix in BLOCKED_DOCUMENT_EXTENSIONS or suffix not in set(config["allowed_file_types"]) | {"xls", "xlsx", "webp"}:
        raise HTTPException(status_code=422, detail="Unsupported employee document format")
    if file.content_type and file.content_type not in (ALLOWED_MIME_BY_EXTENSION.get(suffix, set()) | {"application/octet-stream"}):
        raise HTTPException(status_code=422, detail="Employee document MIME type does not match the uploaded file extension")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Employee document file is empty")
    max_size = int(config["max_file_size_mb"]) * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"Employee document exceeds {config['max_file_size_mb']}MB")
    if config["requires_issue_date"] and not issue_date:
        raise HTTPException(status_code=422, detail=f"{config['display_name']} requires an issue date")
    if config["allows_expiry_date"] and document_type_key in {"PASSPORT", "WORK_PERMIT"} and not expiry_date:
        raise HTTPException(status_code=422, detail=f"{config['display_name']} requires an expiry date")
    file_hash = hashlib.sha256(content).hexdigest()
    duplicate = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.file_hash == file_hash, HRMDocument.status != "archived").first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Duplicate employee document detected")
    previous = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.document_type == document_type_key, HRMDocument.current_version == True, HRMDocument.status != "archived").order_by(HRMDocument.version_number.desc()).first()  # noqa: E712
    version = (previous.version_number + 1) if previous else 1
    if previous:
        previous.status = "superseded"
        previous.current_version = False
    doc_dir = get_upload_root() / "hrm" / "documents" / str(employee.id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    safe_type = "".join(ch if ch.isalnum() else "_" for ch in document_type_key).strip("_") or "Document"
    file_name = f"{safe_type}_v{version}.{suffix}"
    path = doc_dir / file_name
    path.write_bytes(content)
    url = f"/uploads/hrm/documents/{employee.id}/{file_name}"
    verification_status = "Pending Verification" if config["requires_verification"] else "Verified"
    doc = HRMDocument(
        employee_id=employee.id,
        document_title=f"{config['display_name']} v{version}",
        document_type=document_type_key,
        file_name=file_name,
        file_url=url,
        file_key=url,
        file_extension=suffix,
        file_hash=file_hash,
        file_size=len(content),
        mime_type=file.content_type,
        content_type=file.content_type,
        issue_date=issue_date,
        expiry_date=expiry_date,
        uploaded_by_name=user.full_name,
        uploaded_at=datetime.utcnow(),
        version_number=version,
        current_version=True,
        is_mandatory=bool(config["is_mandatory"]),
        is_confidential=bool(config["is_confidential"]),
        confidentiality_level="medical" if document_type_key == "MEDICAL_DOCUMENT" else ("confidential" if config["is_confidential"] else "internal"),
        visibility_level=str(config["access_level_required"]),
        verification_status=verification_status,
        verified_by=user.full_name if verification_status == "Verified" else None,
        verified_at=datetime.utcnow() if verification_status == "Verified" else None,
        status="active",
        ocr_summary=f"Parsed metadata from {file.filename}. OCR extraction queued.",
    )
    db.add(doc)
    db.flush()
    db.add(HRMEmployeeDocumentVersion(document_id=doc.id, employee_id=employee.id, version_number=version, file_name=file_name, file_url=url, file_key=url, file_hash=file_hash, file_size=len(content), uploaded_by_name=user.full_name, uploaded_at=datetime.utcnow(), status="current"))
    if expiry_date:
        for days in [90, 60, 30, 7]:
            db.add(HRMEmployeeDocumentExpiryTracking(document_id=doc.id, employee_id=employee.id, expiry_date=expiry_date, reminder_stage=f"{days}_days", escalation_level="employee"))
    _audit_profile_event(db, employee, user, f"EMPLOYEE_DOCUMENT_UPLOADED_{document_type_key}", "Employee document uploaded.", after=_serialize_model(doc))
    db.commit()
    payload = _serialize_model(doc)
    payload["runtime_status"] = _document_runtime_status(doc)
    payload["display_name"] = config["display_name"]
    return payload


@router.get("/{employee_id:uuid}/documents")
def get_employee_documents(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    docs = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id).order_by(HRMDocument.created_at.desc()).all()
    visible = []
    for row in docs:
        if not _can_access_document(user, row):
            continue
        payload = _serialize_model(row)
        payload["runtime_status"] = _document_runtime_status(row)
        payload["display_name"] = DOCUMENT_TYPE_CONFIGS.get(row.document_type, {}).get("display_name", row.document_type)
        visible.append(payload)
    return visible


@router.get("/documents/expiring")
def get_all_expiring_employee_documents(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    threshold = date.today() + timedelta(days=90)
    docs = db.query(HRMDocument).filter(HRMDocument.expiry_date.isnot(None), HRMDocument.expiry_date <= threshold, HRMDocument.status == "active").order_by(HRMDocument.expiry_date.asc()).all()
    return [_serialize_model(row) | {"runtime_status": _document_runtime_status(row)} for row in docs]


@router.get("/documents/types")
def get_employee_document_types(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    configured = db.query(HRMEmployeeDocumentTypeConfig).filter(HRMEmployeeDocumentTypeConfig.status == "active").order_by(HRMEmployeeDocumentTypeConfig.display_name.asc()).all()
    if configured:
        return [_serialize_model(row) for row in configured]
    return [{"document_type": key, **config} for key, config in DOCUMENT_TYPE_CONFIGS.items()]


@router.get("/{employee_id:uuid}/documents/missing")
def get_missing_employee_documents(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    docs = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.status == "active", HRMDocument.current_version == True).all()  # noqa: E712
    compliant = {doc.document_type for doc in docs if doc.verification_status == "Verified" and _document_runtime_status(doc) not in {"Expired", "Archived"}}
    missing = [config | {"document_type": key} for key, config in DOCUMENT_TYPE_CONFIGS.items() if config["is_mandatory"] and key not in compliant]
    return {"employee_id": str(employee.id), "missing": missing, "count": len(missing)}


@router.get("/{employee_id:uuid}/documents/compliance")
def get_employee_document_compliance(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    docs = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.status == "active", HRMDocument.current_version == True).all()  # noqa: E712
    mandatory_keys = {key for key, config in DOCUMENT_TYPE_CONFIGS.items() if config["is_mandatory"]}
    verified = {doc.document_type for doc in docs if doc.verification_status == "Verified" and _document_runtime_status(doc) not in {"Expired", "Archived"}}
    missing = sorted(mandatory_keys - verified)
    expiring = [doc for doc in docs if _document_runtime_status(doc) == "Expiring Soon"]
    expired = [doc for doc in docs if _document_runtime_status(doc) == "Expired"]
    score = round(((len(mandatory_keys) - len(missing)) / len(mandatory_keys)) * 100, 2) if mandatory_keys else 100
    return {
        "employee_id": str(employee.id),
        "score": score,
        "mandatory_count": len(mandatory_keys),
        "missing_count": len(missing),
        "pending_verification": sum(1 for doc in docs if doc.verification_status == "Pending Verification"),
        "rejected": sum(1 for doc in docs if doc.verification_status == "Rejected"),
        "expiring_soon": len(expiring),
        "expired": len(expired),
        "missing": missing,
    }


@router.get("/{employee_id:uuid}/documents/{document_id:uuid}")
def get_employee_document(employee_id: UUID, document_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    doc = get_or_404(db, HRMDocument, document_id, "Employee document")
    if doc.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    if not _can_access_document(user, doc):
        raise HTTPException(status_code=403, detail="You do not have access to this employee document")
    payload = _serialize_model(doc)
    payload["runtime_status"] = _document_runtime_status(doc)
    return payload


@router.get("/{employee_id:uuid}/documents/{document_id:uuid}/download")
def download_employee_document(employee_id: UUID, document_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    doc = get_or_404(db, HRMDocument, document_id, "Employee document")
    if doc.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    if not _can_access_document(user, doc):
        raise HTTPException(status_code=403, detail="You do not have access to this employee document")
    db.add(HRMEmployeeDocumentAccessLog(document_id=doc.id, employee_id=employee.id, accessed_by=user.full_name, access_type="download"))
    _audit_profile_event(db, employee, user, "EMPLOYEE_DOCUMENT_DOWNLOADED", "Controlled employee document download.", after={"document_id": str(doc.id), "document_type": doc.document_type})
    db.commit()
    path = _secure_document_path(doc)
    return FileResponse(path, filename=doc.file_name, media_type=doc.mime_type or doc.content_type or "application/octet-stream")


@router.put("/{employee_id:uuid}/documents/{document_id:uuid}")
def update_employee_document(employee_id: UUID, document_id: UUID, payload: dict[str, Any] = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    doc = get_or_404(db, HRMDocument, document_id, "Employee document")
    if doc.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    before = _serialize_model(doc)
    for key in ["document_title", "description", "issue_date", "expiry_date", "remarks", "confidentiality_level", "visibility_level"]:
        if key in payload:
            setattr(doc, key, payload[key])
    _audit_profile_event(db, employee, user, "EMPLOYEE_DOCUMENT_UPDATED", "Employee document metadata updated.", before=before, after=_serialize_model(doc))
    db.commit()
    return _serialize_model(doc)


@router.post("/{employee_id:uuid}/documents/{document_id:uuid}/replace")
async def replace_employee_document(
    employee_id: UUID,
    document_id: UUID,
    replacement_reason: str = Query(..., min_length=3),
    expiry_date: date | None = Query(default=None),
    issue_date: date | None = Query(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    existing = get_or_404(db, HRMDocument, document_id, "Employee document")
    if existing.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    result = await upload_employee_document(employee_id=employee.id, document_type=existing.document_type, expiry_date=expiry_date or existing.expiry_date, issue_date=issue_date or existing.issue_date, file=file, db=db, user=user)
    replacement = get_or_404(db, HRMDocument, UUID(str(result["id"])), "Employee document")
    version = db.query(HRMEmployeeDocumentVersion).filter(HRMEmployeeDocumentVersion.document_id == replacement.id).first()
    if version:
        version.replacement_reason = replacement_reason
    existing.status = "superseded"
    existing.current_version = False
    _audit_profile_event(db, employee, user, "EMP-051_DOCUMENT_REPLACED", "Employee document replaced with preserved version history.", before=_serialize_model(existing), after=_serialize_model(replacement))
    db.commit()
    return _serialize_model(replacement) | {"runtime_status": _document_runtime_status(replacement)}


@router.get("/{employee_id:uuid}/documents/{document_id:uuid}/versions")
def get_employee_document_versions(employee_id: UUID, document_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    doc = get_or_404(db, HRMDocument, document_id, "Employee document")
    if doc.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    if not _can_access_document(user, doc):
        raise HTTPException(status_code=403, detail="You do not have access to this employee document")
    document_ids = [row.id for row in db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.document_type == doc.document_type).all()]
    rows = db.query(HRMEmployeeDocumentVersion).filter(HRMEmployeeDocumentVersion.document_id.in_(document_ids)).order_by(HRMEmployeeDocumentVersion.version_number.desc(), HRMEmployeeDocumentVersion.created_at.desc()).all()
    return [_serialize_model(row) for row in rows]


@router.post("/{employee_id:uuid}/documents/{document_id:uuid}/verify")
def verify_employee_document(employee_id: UUID, document_id: UUID, payload: DocumentReviewPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    doc = get_or_404(db, HRMDocument, document_id, "Employee document")
    if doc.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    if doc.verification_status != "Pending Verification":
        raise HTTPException(status_code=422, detail="Only pending documents can be verified")
    doc.verification_status = "Verified"
    doc.verified_by = user.full_name
    doc.verified_at = datetime.utcnow()
    db.add(HRMEmployeeDocumentReview(document_id=doc.id, employee_id=employee.id, decision="Verified", review_action="verify", reviewer=user.full_name, comments=payload.comments, review_notes=payload.comments, reviewed_at=datetime.utcnow()))
    _audit_profile_event(db, employee, user, "EMP-052_DOCUMENT_VERIFIED", "Employee document verified.", after=_serialize_model(doc))
    db.commit()
    return _serialize_model(doc)


@router.post("/{employee_id:uuid}/documents/{document_id:uuid}/reject")
def reject_employee_document(employee_id: UUID, document_id: UUID, payload: DocumentRejectPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    doc = get_or_404(db, HRMDocument, document_id, "Employee document")
    if doc.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    doc.verification_status = "Rejected"
    doc.rejection_reason = payload.reason
    doc.rejected_by = user.full_name
    doc.rejected_at = datetime.utcnow()
    db.add(HRMEmployeeDocumentReview(document_id=doc.id, employee_id=employee.id, decision="Rejected", review_action="reject", reviewer=user.full_name, comments=payload.reason, review_notes=payload.reason, reviewed_at=datetime.utcnow()))
    db.add(HRMEmployeeDocumentRejection(document_id=doc.id, employee_id=employee.id, rejection_reason=payload.reason, rejected_by=user.full_name))
    db.add(NotificationEvent(module="HRM", related_entity="EmployeeDocument", related_id=doc.id, recipient_name=_full_name(employee), recipient_email=employee.email, subject=f"Document rejected: {doc.document_type}", body=payload.reason, status="queued", created_by=user.full_name))
    _audit_profile_event(db, employee, user, "EMP-053_DOCUMENT_REJECTED", "Employee document rejected.", after=_serialize_model(doc))
    db.commit()
    return _serialize_model(doc)


@router.post("/{employee_id:uuid}/documents/{document_id:uuid}/archive")
def archive_employee_document(employee_id: UUID, document_id: UUID, payload: DocumentArchivePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    doc = get_or_404(db, HRMDocument, document_id, "Employee document")
    if doc.employee_id != employee.id:
        raise HTTPException(status_code=404, detail="Document not found for this employee")
    doc.status = "archived"
    doc.is_archived = True
    doc.current_version = False
    doc.archived_at = datetime.utcnow()
    doc.archived_by = user.full_name
    doc.archive_reason = payload.reason
    db.add(HRMEmployeeDocumentArchive(document_id=doc.id, employee_id=employee.id, archived_by=user.full_name, archive_reason=payload.reason))
    _audit_profile_event(db, employee, user, "EMP-054_DOCUMENT_ARCHIVED", "Employee document archived.", after=_serialize_model(doc))
    db.commit()
    return _serialize_model(doc)


@router.get("/{employee_id:uuid}/documents/expiring")
def get_expiring_employee_documents(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    threshold = date.today() + timedelta(days=90)
    docs = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.expiry_date.isnot(None), HRMDocument.expiry_date <= threshold, HRMDocument.status == "active").order_by(HRMDocument.expiry_date.asc()).all()
    return [_serialize_model(row) | {"runtime_status": _document_runtime_status(row)} for row in docs]


def _movement_endpoint(employee_id: UUID, action_key: str, payload: EmployeeMovementPayload, db: Session, user: UserResponse):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return _execute_employee_movement(db, employee, user, action_key, payload)


@router.post("/{employee_id:uuid}/promote")
def promote_employee(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "promote", payload, db, user)


@router.post("/{employee_id:uuid}/demote")
def demote_employee(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "demote", payload, db, user)


@router.post("/{employee_id:uuid}/transfer")
def transfer_employee(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "transfer", payload, db, user)


@router.post("/{employee_id:uuid}/change-role")
def change_employee_role(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "change-role", payload, db, user)


@router.post("/{employee_id:uuid}/acting-appointment")
def acting_appointment(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "acting-appointment", payload, db, user)


@router.post("/{employee_id:uuid}/secondment")
def second_employee(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "secondment", payload, db, user)


@router.post("/{employee_id:uuid}/internal-transfer")
def internal_transfer_employee(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "internal-transfer", payload, db, user)


@router.post("/{employee_id:uuid}/temporary-assignment")
def temporary_assignment(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "temporary-assignment", payload, db, user)


@router.post("/{employee_id:uuid}/return-from-assignment")
def return_from_assignment(employee_id: UUID, payload: EmployeeMovementPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _movement_endpoint(employee_id, "return-from-assignment", payload, db, user)


@router.post("/{employee_id:uuid}/probation/place")
def place_employee_on_probation(employee_id: UUID, payload: dict[str, Any] = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    payload["probation_required"] = True
    record = _upsert_probation(db, employee, payload, user, "EMP-064_PLACE_ON_PROBATION")
    employee.employment_status = "probation"
    _record_status_history(db, employee, user, "EMP-064", "active", "probation", EmployeeStatusPayload(effective_date=_parse_import_date(payload.get("probation_start_date")) or date.today(), reason=_string(payload.get("reason") or "Placed on probation")), {"probation": _serialize_probation(record, employee)})
    db.commit()
    return _serialize_probation(record, employee)


@router.post("/{employee_id:uuid}/probation/confirm")
def confirm_probation_status(employee_id: UUID, payload: dict[str, Any] = Body(default_factory=dict), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return confirm_employee_probation(employee_id, payload, db, user)


@router.post("/{employee_id:uuid}/probation/extend")
def extend_probation_status(employee_id: UUID, payload: dict[str, Any] = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return extend_employee_probation(employee_id, payload, db, user)


def _status_endpoint(employee_id: UUID, action_key: str, payload: EmployeeStatusPayload, db: Session, user: UserResponse):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return _execute_employee_status(db, employee, user, action_key, payload)


@router.post("/{employee_id:uuid}/suspend")
def suspend_employee(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _status_endpoint(employee_id, "suspend", payload, db, user)


@router.post("/{employee_id:uuid}/reinstate")
def reinstate_employee(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _status_endpoint(employee_id, "reinstate", payload, db, user)


@router.post("/{employee_id:uuid}/leave-of-absence")
def place_employee_on_leave_of_absence(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _status_endpoint(employee_id, "leave-of-absence", payload, db, user)


@router.post("/{employee_id:uuid}/return-from-leave-of-absence")
def return_employee_from_leave_of_absence(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _status_endpoint(employee_id, "return-from-leave-of-absence", payload, db, user)


@router.post("/{employee_id:uuid}/mark-inactive")
def mark_employee_inactive(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _status_endpoint(employee_id, "mark-inactive", payload, db, user)


@router.post("/{employee_id:uuid}/terminate")
def terminate_employee_lifecycle(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _status_endpoint(employee_id, "terminate", payload, db, user)


@router.post("/{employee_id:uuid}/retire")
def retire_employee(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _status_endpoint(employee_id, "retire", payload, db, user)


@router.post("/{employee_id:uuid}/death-in-service")
def record_death_in_service(employee_id: UUID, payload: EmployeeStatusPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr_admin(user)
    return _status_endpoint(employee_id, "death-in-service", payload, db, user)


@router.get("/{employee_id:uuid}/movements")
def get_employee_movements(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    get_or_404(db, HRMEmployee, employee_id, "Employee")
    rows = db.query(HRMEmployeeMovement).filter(HRMEmployeeMovement.employee_id == employee_id).order_by(HRMEmployeeMovement.created_at.desc()).all()
    return [_serialize_model(row) for row in rows]


@router.get("/{employee_id:uuid}/status-history")
def get_employee_status_history(employee_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    get_or_404(db, HRMEmployee, employee_id, "Employee")
    rows = db.query(HRMEmployeeStatusHistory).filter(HRMEmployeeStatusHistory.employee_id == employee_id).order_by(HRMEmployeeStatusHistory.created_at.desc()).all()
    return [_serialize_model(row) for row in rows]


@router.get("/validate-number")
def validate_employee_number(
    employee_code: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    code = employee_code.strip()
    exists = db.query(HRMEmployee).filter(HRMEmployee.employee_code == code).first()
    return {
        "employee_code": code,
        "available": exists is None,
        "locked": exists is not None,
        "policy": _employee_number_policy(db),
    }


@router.get("/{employee_id:uuid}", response_model=EmployeeResponse)
def get_employee(employee_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, HRMEmployee, employee_id, "Employee")


@router.get("/{employee_id:uuid}/employee-number")
def get_employee_number(
    employee_id: UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return {
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "locked": bool(employee.employee_code),
        "status": employee.employment_status,
        "policy": _employee_number_policy(db),
    }


@router.get("/{employee_id:uuid}/activation-status")
def get_employee_activation_status(
    employee_id: UUID,
    allow_early_activation: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return _activation_readiness(db, employee, allow_early_activation)


@router.post("/{employee_id:uuid}/activate")
def activate_employee(
    employee_id: UUID,
    allow_early_activation: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    result = _activate_employee_record(db, employee, user, allow_early_activation)
    db.commit()
    db.refresh(employee)
    return result


@router.post("/{employee_id:uuid}/generate-number")
def generate_employee_number(
    employee_id: UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    if employee.employee_code:
        raise HTTPException(status_code=409, detail="Employee number is already assigned and locked")
    if employee.employment_status not in {"draft", "pending_activation", "employee_number_assigned"}:
        raise HTTPException(status_code=422, detail="Employee status does not allow employee number generation")
    before = employee.employee_code
    employee.employee_code = _next_employee_code(db)
    _audit_employee_number_generation(db, employee, user, before)
    _sync_employee_foundation(db, employee)
    db.commit()
    db.refresh(employee)
    return {
        "employee_id": str(employee.id),
        "employee_code": employee.employee_code,
        "locked": True,
        "status": employee.employment_status,
        "policy": _employee_number_policy(db),
    }


@router.put("/{employee_id:uuid}", response_model=EmployeeResponse)
def update_employee(
    employee_id: UUID,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_write(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    before = {
        "department": employee.department,
        "job_title": employee.job_title,
        "job_group": employee.job_group,
        "salary_grade": employee.salary_grade,
        "role_category": employee.role_category,
        "employment_status": employee.employment_status,
        "supervisor_id": str(employee.supervisor_id) if employee.supervisor_id else None,
    }

    data = employee_update.model_dump(exclude_unset=True)
    data.pop("employee_code", None)
    merged = {
        "first_name": data.get("first_name", employee.first_name),
        "last_name": data.get("last_name", employee.last_name),
        "email": data.get("email", employee.email),
        "employee_code": employee.employee_code,
        "national_id": data.get("national_id", employee.national_id),
        "tax_pin": data.get("tax_pin", employee.tax_pin),
        "department": data.get("department", employee.department),
        "job_title": data.get("job_title", employee.job_title),
        "hire_date": data.get("hire_date", employee.hire_date),
        "employment_type": data.get("employment_type", employee.employment_type),
        "employment_start_date": data.get("employment_start_date", employee.employment_start_date),
        "employment_end_date": data.get("employment_end_date", employee.employment_end_date),
        "institution": data.get("institution", employee.institution),
        "internship_supervisor": data.get("internship_supervisor", employee.internship_supervisor),
        "consultancy_agreement_ref": data.get("consultancy_agreement_ref", employee.consultancy_agreement_ref),
        "consultancy_project": data.get("consultancy_project", employee.consultancy_project),
        "contract_signed": data.get("contract_signed", employee.contract_signed),
        "budget_approved": data.get("budget_approved", employee.budget_approved),
        "supervisor_id": data.get("supervisor_id", employee.supervisor_id),
    }
    _validate_employee_payload(db, merged, employee.id, enforce_readiness=False)
    if any(key in data for key in ["probation_required", "probation_start_date", "probation_end_date", "probation_duration_months", "probation_status"]):
        _upsert_probation(
            db,
            employee,
            {
                "probation_required": data.get("probation_required", employee.probation_required),
                "probation_start_date": data.get("probation_start_date", employee.probation_start_date),
                "probation_end_date": data.get("probation_end_date", employee.probation_end_date),
                "probation_duration_months": data.get("probation_duration_months", employee.probation_duration_months or 6),
                "probation_status": data.get("probation_status", employee.probation_status),
            },
            user,
            "EMP-006_UPDATE_PROBATION",
        )
    data["internal_only"] = True

    for field, value in data.items():
        setattr(employee, field, value)

    db.flush()
    after = {
        "department": employee.department,
        "job_title": employee.job_title,
        "job_group": employee.job_group,
        "salary_grade": employee.salary_grade,
        "role_category": employee.role_category,
        "employment_status": employee.employment_status,
        "supervisor_id": str(employee.supervisor_id) if employee.supervisor_id else None,
    }
    for field, previous in before.items():
        current = after[field]
        if previous != current:
            _add_lifecycle_event(db, employee, field, previous, current)

    _sync_employee_foundation(db, employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id:uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_hr_admin(user)
    employee = get_or_404(db, HRMEmployee, employee_id, "Employee")
    return delete_record(db, employee)
