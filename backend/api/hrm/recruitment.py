from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.hrm.employees import (
    _add_lifecycle_event,
    _audit_employee_creation,
    _audit_employee_number_generation,
    _next_employee_code,
    _queue_employee_notifications,
    _sync_employee_foundation,
    _upsert_employment_detail,
    _upsert_probation,
    _validate_employee_payload,
)
from backend.core.database import get_db
from backend.models.automation import EnterpriseEvent
from backend.models.enterprise import NotificationEvent
from backend.models.hrm import (
    HRMDepartment,
    HRMDocument,
    HRMEmployee,
    HRMInterview,
    HRMInterviewFeedback,
    HRMJobOpening,
    HRMJobRequisition,
    HRMCandidateDocument,
    HRMCandidateEmployeeConversion,
    HRMOfferLetter,
    HRMRecruitment,
    HRMRecruitmentAuditLog,
)
from backend.schemas.auth import UserResponse
from backend.schemas.hrm.recruitment import (
    ApplicationPayload,
    ApprovalPayload,
    BulkConvertPayload,
    CandidateDocumentPayload,
    CandidatePayload,
    ConvertApplicantPayload,
    InterviewFeedbackPayload,
    InterviewPayload,
    JobOpeningPayload,
    JobRequisitionPayload,
    OfferDecisionPayload,
    OfferPayload,
    RecruitmentCreate,
    RecruitmentResponse,
    RecruitmentUpdate,
    ScreeningPayload,
)


router = APIRouter(prefix="/hrm/recruitment", tags=["HRM Recruitment"])


def _jsonable(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (date, datetime)):
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
    if str(user.role).lower() not in {"admin", "manager", "hr", "hr_admin", "hr_manager", "recruiter", "recruitment_admin"}:
        raise HTTPException(status_code=403, detail="Recruitment action requires HR or manager permission")


def _audit(db: Session, user: UserResponse, action: str, summary: str, recruitment_id: UUID | None = None, before: Any = None, after: Any = None) -> None:
    db.add(
        HRMRecruitmentAuditLog(
            recruitment_id=recruitment_id,
            action=action,
            actor_email=user.email,
            summary=summary,
            before_json=_jsonable(before),
            after_json=_jsonable(after),
        )
    )


def _event(db: Session, user: UserResponse, event_type: str, payload: dict[str, Any]) -> None:
    db.add(
        EnterpriseEvent(
            event_type=event_type,
            source_module="Recruitment",
            target_module="Enterprise",
            payload=_jsonable(payload),
            event_status="pending",
            created_by=user.full_name,
        )
    )


def _notify(db: Session, user: UserResponse, related_id: UUID | None, subject: str, body: str, recipient_name: str = "HR") -> None:
    db.add(
        NotificationEvent(
            module="HRM",
            related_entity="Recruitment",
            related_id=related_id,
            recipient_name=recipient_name,
            subject=subject,
            body=body,
            status="queued",
            created_by=user.full_name,
        )
    )


def _get_or_404(db: Session, model: Any, record_id: UUID, label: str) -> Any:
    row = db.query(model).filter(model.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return row


def _candidate_names(candidate_name: str) -> tuple[str, str]:
    parts = [part for part in (candidate_name or "").strip().split(" ") if part]
    if not parts:
        return "Candidate", "Unknown"
    if len(parts) == 1:
        return parts[0], "Unknown"
    return parts[0], " ".join(parts[1:])


def _score_candidate(record: HRMRecruitment) -> Decimal:
    total = (
        Decimal(str(record.screening_score or 0)) * Decimal("0.30")
        + Decimal(str(record.interview_score or 0)) * Decimal("0.45")
        + Decimal(str(record.assessment_score or 0)) * Decimal("0.15")
        + Decimal(str(record.background_score or 0)) * Decimal("0.10")
    )
    record.total_score = total
    return total


def _ready_for_successful_applicant(record: HRMRecruitment) -> list[str]:
    errors: list[str] = []
    if not record.offer_accepted:
        errors.append("Offer must be accepted")
    if record.approval_status != "approved":
        errors.append("Recruitment approvals must be complete")
    if record.background_check_status not in {"passed", "complete", "cleared"}:
        errors.append("Background/compliance checks must be complete")
    if not record.headcount_approved:
        errors.append("Headcount must be approved")
    if not record.budget_approved:
        errors.append("Budget must be approved")
    return errors


def _mark_successful_if_ready(db: Session, user: UserResponse, record: HRMRecruitment) -> None:
    errors = _ready_for_successful_applicant(record)
    if errors:
        record.successful_applicant_status = "pending"
        record.compliance_readiness = "attention_required"
        return
    record.successful_applicant_status = "ready"
    record.recruitment_stage = "successful_applicant"
    record.application_status = "hired"
    record.compliance_readiness = "ready"
    record.document_readiness = "ready" if record.contract_signed else "pending_contract"
    _event(db, user, "recruitment.successful_applicant.ready", {"recruitment_id": record.id, "candidate_email": record.candidate_email})
    _notify(db, user, record.id, "Successful applicant ready for conversion", f"{record.candidate_name} is ready to convert to employee.", "HR Officer")


def _duplicate_employee(db: Session, record: HRMRecruitment) -> HRMEmployee | None:
    filters = []
    if record.candidate_email:
        filters.append(HRMEmployee.email.ilike(record.candidate_email))
    if record.candidate_phone:
        filters.append(HRMEmployee.phone == record.candidate_phone)
    if record.national_id:
        filters.append(HRMEmployee.national_id == record.national_id)
    if record.passport_number:
        filters.append(HRMEmployee.passport_number == record.passport_number)
    if not filters:
        return None
    return db.query(HRMEmployee).filter(or_(*filters)).first()


def _employee_payload_from_candidate(record: HRMRecruitment, overrides: dict[str, Any]) -> dict[str, Any]:
    first_name, last_name = _candidate_names(record.candidate_name)
    start_date = record.target_start_date or date.today()
    employment_type = record.employment_type or "Permanent"
    payload = {
        "employee_code": None,
        "candidate_id": record.id,
        "first_name": first_name,
        "last_name": last_name,
        "email": record.candidate_email,
        "phone": record.candidate_phone,
        "national_id": record.national_id,
        "passport_number": record.passport_number,
        "date_of_birth": record.date_of_birth,
        "gender": record.gender,
        "physical_address": record.address,
        "address": record.address,
        "department": record.department,
        "business_unit": record.business_unit,
        "branch": record.branch,
        "job_title": record.job_title,
        "salary_band": record.salary_band,
        "base_salary": record.base_salary or 0,
        "pay_frequency": record.pay_frequency or "monthly",
        "employment_type": employment_type,
        "employment_start_date": start_date,
        "employment_end_date": record.contract_end_date if employment_type in {"Contract", "Casual", "Internship", "Consultant"} else None,
        "hire_date": start_date,
        "supervisor_id": record.reporting_manager_id or record.hiring_manager_id,
        "contract_signed": record.contract_signed,
        "budget_approved": record.budget_approved,
        "probation_required": record.probation_required,
        "probation_start_date": start_date if record.probation_required else None,
        "probation_duration_months": record.probation_duration_months or (6 if record.probation_required else None),
        "probation_end_date": record.probation_end_date or (start_date + timedelta(days=180) if record.probation_required else None),
        "employment_status": "pending_activation",
        "internal_only": True,
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})
    payload["employee_code"] = payload.get("employee_code")
    return payload


def _migrate_candidate_documents(db: Session, record: HRMRecruitment, employee: HRMEmployee, user: UserResponse) -> int:
    migrated = 0
    docs = db.query(HRMCandidateDocument).filter(HRMCandidateDocument.recruitment_id == record.id).all()
    type_map = {
        "CV": "CV",
        "COVER_LETTER": "CV",
        "CERTIFICATE": "ACADEMIC_CERTIFICATE",
        "CERTIFICATES": "ACADEMIC_CERTIFICATE",
        "OFFER_LETTER": "EMPLOYMENT_CONTRACT",
        "CONTRACT": "EMPLOYMENT_CONTRACT",
        "NATIONAL_ID": "NATIONAL_ID",
        "PASSPORT": "PASSPORT",
        "WORK_PERMIT": "WORK_PERMIT",
        "TAX_DOCUMENT": "TAX_DOCUMENT",
    }
    for doc in docs:
        document_type = type_map.get((doc.document_type or "").upper(), doc.document_type)
        existing = db.query(HRMDocument).filter(HRMDocument.employee_id == employee.id, HRMDocument.file_hash == doc.file_hash, HRMDocument.file_hash.isnot(None)).first()
        if existing:
            continue
        db.add(
            HRMDocument(
                employee_id=employee.id,
                document_title=doc.title,
                description=f"Migrated from recruitment candidate record {record.id}.",
                document_type=document_type,
                file_name=doc.file_name,
                file_url=doc.file_url,
                file_key=doc.file_key,
                file_hash=doc.file_hash,
                version_number=doc.version_number,
                current_version=doc.is_current_version,
                is_confidential=doc.is_confidential,
                visibility_level="hr" if doc.is_confidential else "manager",
                expiry_date=doc.expiry_date,
                uploaded_by_name=user.full_name,
                uploaded_at=datetime.utcnow(),
                verification_status=doc.verification_status,
                status="active",
                remarks="Migrated automatically by REC-023 candidate conversion.",
            )
        )
        migrated += 1
    return migrated


def _convert_record(db: Session, user: UserResponse, record: HRMRecruitment, payload: ConvertApplicantPayload) -> dict[str, Any]:
    _require_hr(user)
    if record.converted_employee_id:
        employee = _get_or_404(db, HRMEmployee, record.converted_employee_id, "Converted employee")
        return {"status": "already_converted", "employee": _row(employee), "recruitment": _row(record)}
    duplicate = _duplicate_employee(db, record)
    if duplicate:
        raise HTTPException(status_code=409, detail={"message": "Candidate matches an existing employee", "employee_id": str(duplicate.id)})
    readiness_errors = _ready_for_successful_applicant(record)
    if readiness_errors:
        raise HTTPException(status_code=422, detail={"message": "Candidate is not ready for employee conversion", "errors": readiness_errors})
    if not record.candidate_email:
        raise HTTPException(status_code=422, detail="Candidate email is required before conversion")

    data = _employee_payload_from_candidate(record, payload.employee_overrides)
    data["employee_code"] = _next_employee_code(db)
    _validate_employee_payload(db, data, enforce_readiness=False)
    employee = HRMEmployee(**data)
    db.add(employee)
    db.flush()

    _upsert_employment_detail(
        db,
        employee,
        {
            "employment_type": employee.employment_type or "Permanent",
            "start_date": employee.employment_start_date or employee.hire_date,
            "end_date": employee.employment_end_date,
            "institution": employee.institution,
            "internship_supervisor": employee.internship_supervisor,
            "consultancy_agreement_ref": employee.consultancy_agreement_ref,
            "consultancy_project": employee.consultancy_project,
            "change_reason": "REC-023 successful applicant conversion",
        },
        user,
        "REC-023_ASSIGN_EMPLOYMENT_TYPE",
    )
    if employee.probation_required:
        _upsert_probation(
            db,
            employee,
            {
                "probation_required": True,
                "probation_start_date": employee.probation_start_date or employee.hire_date,
                "probation_end_date": employee.probation_end_date,
                "probation_duration_months": employee.probation_duration_months or 6,
            },
            user,
            "REC-023_ASSIGN_PROBATION",
        )
    _audit_employee_number_generation(db, employee, user, None)
    _add_lifecycle_event(db, employee, "hire", None, employee.employment_status)
    _sync_employee_foundation(db, employee, include_leave_balances=True)
    _queue_employee_notifications(db, employee, user)
    _audit_employee_creation(db, employee, user)
    migrated_docs = _migrate_candidate_documents(db, record, employee, user)

    record.converted_employee_id = employee.id
    record.converted_at = datetime.utcnow()
    record.conversion_status = "converted"
    record.successful_applicant_status = "converted"
    record.application_status = "hired"
    conversion_events = [
        "recruitment.candidate.converted_to_employee",
        "recruitment.onboarding.triggered",
        "iam.account_request.created",
        "payroll.profile.created",
        "assets.onboarding_request.created",
        "leave.policy.assignment.ready",
        "training.onboarding_plan.ready",
    ]
    db.add(
        HRMCandidateEmployeeConversion(
            recruitment_id=record.id,
            employee_id=employee.id,
            conversion_status="completed",
            readiness_snapshot={
                "headcount_approved": record.headcount_approved,
                "budget_approved": record.budget_approved,
                "offer_accepted": record.offer_accepted,
                "contract_signed": record.contract_signed,
                "documents_migrated": migrated_docs,
            },
            integration_events=conversion_events,
            converted_by=user.full_name,
        )
    )
    for event_type in conversion_events:
        _event(db, user, event_type, {"recruitment_id": record.id, "employee_id": employee.id, "employee_code": employee.employee_code})
    _audit(db, user, "REC-023_CONVERT_TO_EMPLOYEE", f"Converted {record.candidate_name} to employee {employee.employee_code}.", record.id, None, {"employee_id": employee.id, "employee_code": employee.employee_code})
    _notify(db, user, record.id, "Candidate converted to employee", f"{record.candidate_name} is now employee {employee.employee_code}.", "HR Officer")
    db.commit()
    db.refresh(employee)
    return {"status": "converted", "employee": _row(employee), "recruitment": _row(record), "documents_migrated": migrated_docs}


@router.post("", response_model=RecruitmentResponse, status_code=status.HTTP_201_CREATED)
def create_recruitment(recruitment: RecruitmentCreate, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    record = HRMRecruitment(**recruitment.model_dump())
    record.application_date = record.application_date or date.today()
    db.add(record)
    _audit(db, user, "REC-005_APPLICATION_RECEIVED", f"Recruitment record created for {record.candidate_name}.", record.id, None, recruitment.model_dump())
    _event(db, user, "recruitment.application.received", {"candidate_email": record.candidate_email, "job_title": record.job_title})
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=List[RecruitmentResponse])
def get_recruitment_records(db: Session = Depends(get_db)):
    return db.query(HRMRecruitment).order_by(HRMRecruitment.created_at.desc()).all()


@router.post("/requisitions", status_code=status.HTTP_201_CREATED)
def create_requisition(payload: JobRequisitionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    if not db.query(HRMDepartment).filter(HRMDepartment.name.ilike(payload.department), HRMDepartment.status == "active").first():
        raise HTTPException(status_code=422, detail="Department must exist and be active")
    row = HRMJobRequisition(
        **payload.model_dump(),
        requisition_number=f"REQ-{date.today().year}-{uuid4().hex[:8].upper()}",
        position_title=payload.job_title,
        requested_by=payload.hiring_manager_id,
        openings=payload.vacancies,
        justification=payload.reason_for_hire,
        created_by=user.full_name,
    )
    db.add(row)
    db.flush()
    _audit(db, user, "REC-001_CREATE_JOB_REQUISITION", f"Created requisition for {row.job_title}.", None, None, _row(row))
    _event(db, user, "recruitment.requisition.created", {"requisition_id": row.id, "job_title": row.job_title, "department": row.department})
    db.commit()
    db.refresh(row)
    return _row(row)


@router.get("/requisitions")
def list_requisitions(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMJobRequisition).order_by(HRMJobRequisition.created_at.desc()).all()]


@router.get("/requisitions/__analytics")
def requisitions_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _simple_analytics(db, HRMJobRequisition, "approval_status")


@router.post("/requisitions/{requisition_id}/approve")
def approve_requisition(requisition_id: UUID, payload: ApprovalPayload = Body(default_factory=ApprovalPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    row = _get_or_404(db, HRMJobRequisition, requisition_id, "Job requisition")
    row.approval_status = "approved"
    row.status = "approved"
    row.approved_by = user.full_name
    row.approved_at = datetime.utcnow()
    _audit(db, user, "REC-002_APPROVE_JOB_REQUISITION", f"Approved requisition {row.job_title}.", None, None, _row(row))
    _event(db, user, "recruitment.requisition.approved", {"requisition_id": row.id, "job_title": row.job_title})
    db.commit()
    return _row(row)


@router.post("/requisitions/{requisition_id}/reject")
def reject_requisition(requisition_id: UUID, payload: ApprovalPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    row = _get_or_404(db, HRMJobRequisition, requisition_id, "Job requisition")
    row.approval_status = "rejected"
    row.status = "rejected"
    row.rejection_reason = payload.reason or payload.comments or "Rejected"
    _audit(db, user, "REC-002_REJECT_JOB_REQUISITION", f"Rejected requisition {row.job_title}.", None, None, _row(row))
    db.commit()
    return _row(row)


@router.post("/openings", status_code=status.HTTP_201_CREATED)
def create_opening(payload: JobOpeningPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    req = _get_or_404(db, HRMJobRequisition, payload.requisition_id, "Approved requisition")
    if req.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Job opening must link to an approved requisition")
    row = HRMJobOpening(
        requisition_id=req.id,
        opening_title=req.job_title or req.position_title,
        job_title=req.job_title,
        department=req.department,
        branch=req.branch,
        business_unit=req.business_unit,
        employment_type=req.employment_type,
        salary_band=req.salary_band,
        description=payload.description or req.job_description,
        posting_date=date.today(),
        closing_date=payload.closing_date,
        publishing_channels=payload.publishing_channels,
        created_by=user.full_name,
    )
    db.add(row)
    db.flush()
    _audit(db, user, "REC-003_CREATE_JOB_OPENING", f"Created opening for {row.job_title}.", None, None, _row(row))
    db.commit()
    db.refresh(row)
    return _row(row)


@router.get("/openings")
def list_openings(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMJobOpening).order_by(HRMJobOpening.created_at.desc()).all()]


@router.get("/openings/__analytics")
def openings_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _simple_analytics(db, HRMJobOpening, "status")


@router.post("/openings/{opening_id}/publish")
def publish_opening(opening_id: UUID, payload: ApprovalPayload = Body(default_factory=ApprovalPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    row = _get_or_404(db, HRMJobOpening, opening_id, "Job opening")
    if not row.closing_date:
        raise HTTPException(status_code=422, detail="Closing date is required before publishing")
    row.status = "published"
    row.published_at = datetime.utcnow()
    _audit(db, user, "REC-004_PUBLISH_JOB_OPENING", f"Published opening {row.job_title}.", None, None, _row(row))
    _event(db, user, "recruitment.opening.published", {"opening_id": row.id, "job_title": row.job_title})
    db.commit()
    return _row(row)


@router.post("/openings/{opening_id}/close")
def close_opening(opening_id: UUID, payload: ApprovalPayload = Body(default_factory=ApprovalPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    row = _get_or_404(db, HRMJobOpening, opening_id, "Job opening")
    row.status = "closed"
    _audit(db, user, "REC_CLOSE_JOB_OPENING", f"Closed opening {row.job_title}.", None, None, _row(row))
    db.commit()
    return _row(row)


@router.post("/candidates", status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidatePayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    record = HRMRecruitment(job_title="Talent Pool", candidate_name=payload.candidate_name, candidate_email=payload.candidate_email, candidate_phone=payload.candidate_phone, national_id=payload.national_id, passport_number=payload.passport_number, date_of_birth=payload.date_of_birth, gender=payload.gender, address=payload.address, source_channel=payload.source_channel, recruitment_stage="candidate_profile", application_status="talent_pool", application_date=date.today(), notes=payload.notes)
    db.add(record)
    db.flush()
    _audit(db, user, "REC-007_CANDIDATE_PROFILE_CREATED", f"Created candidate profile for {record.candidate_name}.", record.id, None, _row(record))
    db.commit()
    db.refresh(record)
    return _row(record)


@router.get("/candidates")
def list_candidates(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMRecruitment).filter(HRMRecruitment.recruitment_stage.in_(["candidate_profile", "applied", "screening", "shortlisted", "interview", "offer", "successful_applicant"])).order_by(HRMRecruitment.created_at.desc()).all()]


def _simple_analytics(db: Session, model, status_field: str | None = None, value_field: str | None = None) -> dict[str, Any]:
    total = db.query(model).count()
    status_breakdown = []
    if status_field:
        column = getattr(model, status_field)
        status_breakdown = [{"name": row[0] or "Unspecified", "count": row[1]} for row in db.query(column, func.count(model.id)).group_by(column).all()]
    total_value = 0
    if value_field:
        total_value = float(db.query(func.coalesce(func.sum(getattr(model, value_field)), 0)).scalar() or 0)
    return {"total": total, "status_breakdown": status_breakdown, "total_value": total_value}


@router.get("/candidates/__analytics")
def candidates_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _simple_analytics(db, HRMRecruitment, "application_status", "expected_salary")


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _row(_get_or_404(db, HRMRecruitment, candidate_id, "Candidate"))


@router.post("/applications", status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    opening = _get_or_404(db, HRMJobOpening, payload.opening_id, "Published opening")
    if opening.status != "published":
        raise HTTPException(status_code=422, detail="Applications can only be received for published openings")
    if opening.closing_date and opening.closing_date < date.today():
        raise HTTPException(status_code=422, detail="Opening is closed and no longer accepts applications")
    parsed = {"raw_text_available": bool(payload.cv_text), "confidence": 0.7 if payload.cv_text else 0, "skills": []}
    record = HRMRecruitment(job_title=opening.job_title, department=opening.department, branch=opening.branch, business_unit=opening.business_unit, employment_type=opening.employment_type, salary_band=opening.salary_band, candidate_name=payload.candidate_name, candidate_email=payload.candidate_email, candidate_phone=payload.candidate_phone, national_id=payload.national_id, passport_number=payload.passport_number, date_of_birth=payload.date_of_birth, gender=payload.gender, address=payload.address, opening_id=opening.id, requisition_id=opening.requisition_id, expected_salary=payload.expected_salary, source_channel=payload.source_channel, target_start_date=payload.availability_date, application_date=date.today(), parsed_cv_json=parsed, recruitment_stage="applied", application_status="pending")
    db.add(record)
    db.flush()
    _audit(db, user, "REC-005_RECEIVE_APPLICATION", f"Application received from {record.candidate_name}.", record.id, None, _row(record))
    _event(db, user, "recruitment.application.received", {"recruitment_id": record.id, "opening_id": opening.id, "candidate_email": record.candidate_email})
    db.commit()
    db.refresh(record)
    return _row(record)


@router.get("/applications")
def list_applications(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMRecruitment).filter(HRMRecruitment.opening_id.isnot(None)).order_by(HRMRecruitment.created_at.desc()).all()]


@router.get("/applications/__analytics")
def applications_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _simple_analytics(db, HRMRecruitment, "application_status", "total_score")


@router.post("/applications/{application_id}/screen")
def screen_application(application_id: UUID, payload: ScreeningPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    record = _get_or_404(db, HRMRecruitment, application_id, "Candidate application")
    record.screening_score = payload.screening_score
    record.assessment_score = payload.assessment_score
    if payload.disqualified_reason:
        record.application_status = "disqualified"
        record.notes = f"{record.notes or ''}\nDisqualified: {payload.disqualified_reason}".strip()
    else:
        record.application_status = "screened"
        record.recruitment_stage = "screening"
    _score_candidate(record)
    _audit(db, user, "REC-008_APPLICATION_SCREENING", f"Screened application for {record.candidate_name}.", record.id, None, _row(record))
    db.commit()
    return _row(record)


@router.post("/applications/{application_id}/shortlist")
def shortlist_application(application_id: UUID, payload: ApprovalPayload = Body(default_factory=ApprovalPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    record = _get_or_404(db, HRMRecruitment, application_id, "Candidate application")
    if record.application_status not in {"screened", "shortlisted"}:
        raise HTTPException(status_code=422, detail="Only screened candidates can be shortlisted")
    record.application_status = "shortlisted"
    record.recruitment_stage = "shortlisted"
    _audit(db, user, "REC-009_CANDIDATE_SHORTLISTED", f"Shortlisted {record.candidate_name}.", record.id, None, _row(record))
    _event(db, user, "recruitment.candidate.shortlisted", {"recruitment_id": record.id})
    db.commit()
    return _row(record)


@router.post("/interviews", status_code=status.HTTP_201_CREATED)
def schedule_interview(payload: InterviewPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    record = _get_or_404(db, HRMRecruitment, payload.recruitment_id, "Candidate")
    for panel_member_id in payload.panel_member_ids:
        panel_member = _get_or_404(db, HRMEmployee, panel_member_id, "Panel member")
        if panel_member.employment_status not in {"active", "probation", "confirmed", "on_leave"}:
            raise HTTPException(status_code=422, detail="Interview panel members must be active employees")
    interview = HRMInterview(**payload.model_dump(), created_by=user.full_name)
    db.add(interview)
    record.interview_date = payload.scheduled_at
    record.recruitment_stage = "interview"
    record.application_status = "interview_scheduled"
    _audit(db, user, "REC-010_SCHEDULE_INTERVIEW", f"Scheduled interview for {record.candidate_name}.", record.id, None, payload.model_dump())
    _event(db, user, "recruitment.interview.scheduled", {"recruitment_id": record.id, "scheduled_at": payload.scheduled_at})
    db.commit()
    db.refresh(interview)
    return _row(interview)


@router.get("/interviews")
def list_interviews(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMInterview).order_by(HRMInterview.created_at.desc()).all()]


@router.get("/interviews/__analytics")
def interviews_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _simple_analytics(db, HRMInterview, "status")


@router.post("/interviews/{interview_id}/feedback")
def submit_feedback(interview_id: UUID, payload: InterviewFeedbackPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    interview = _get_or_404(db, HRMInterview, interview_id, "Interview")
    record = _get_or_404(db, HRMRecruitment, interview.recruitment_id, "Candidate")
    feedback = HRMInterviewFeedback(interview_id=interview.id, recruitment_id=record.id, **payload.model_dump(), submitted_by=user.full_name, submitted_at=datetime.utcnow())
    db.add(feedback)
    interview.status = "completed"
    scores = [payload.technical_score, payload.culture_score, payload.communication_score, payload.experience_score]
    record.interview_score = sum(Decimal(str(score)) for score in scores) / Decimal(len(scores))
    record.application_status = "interview_completed"
    _score_candidate(record)
    _audit(db, user, "REC-013_FEEDBACK_SUBMITTED", f"Interview feedback submitted for {record.candidate_name}.", record.id, None, payload.model_dump())
    _event(db, user, "recruitment.feedback.submitted", {"recruitment_id": record.id, "interview_id": interview.id})
    db.commit()
    return _row(feedback)


@router.get("/interview-feedback")
def list_interview_feedback(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMInterviewFeedback).order_by(HRMInterviewFeedback.created_at.desc()).all()]


@router.get("/interview-feedback/__analytics")
def interview_feedback_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _simple_analytics(db, HRMInterviewFeedback, "recommendation", "technical_score")


@router.post("/interview-feedback", status_code=status.HTTP_201_CREATED)
def create_interview_feedback(payload: dict[str, Any] = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    interview_id = payload.get("interview_id")
    if not interview_id:
        raise HTTPException(status_code=422, detail="interview_id is required")
    feedback_payload = InterviewFeedbackPayload(**{key: value for key, value in payload.items() if key != "interview_id"})
    return submit_feedback(UUID(str(interview_id)), feedback_payload, db, user)


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def add_candidate_document(payload: CandidateDocumentPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _get_or_404(db, HRMRecruitment, payload.recruitment_id, "Candidate")
    doc = HRMCandidateDocument(**payload.model_dump(), uploaded_by=user.full_name)
    db.add(doc)
    _audit(db, user, "REC-026_DOCUMENT_UPLOADED", f"Candidate document uploaded: {doc.title}.", payload.recruitment_id, None, payload.model_dump())
    db.commit()
    db.refresh(doc)
    return _row(doc)


@router.post("/offers", status_code=status.HTTP_201_CREATED)
def generate_offer(payload: OfferPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    record = _get_or_404(db, HRMRecruitment, payload.recruitment_id, "Candidate")
    if record.background_check_status not in {"passed", "complete", "cleared", "pending"}:
        raise HTTPException(status_code=422, detail="Failed background checks block offer generation")
    offer_reference = f"OFFER-{date.today().year}-{uuid4().hex[:8].upper()}"
    offer = HRMOfferLetter(offer_reference=offer_reference, offer_number=offer_reference, recruitment_id=record.id, job_title=record.job_title, department=record.department, employment_type=record.employment_type, start_date=payload.start_date or record.target_start_date, salary_band=payload.salary_band or record.salary_band, base_salary=payload.base_salary or record.base_salary, salary_offer=payload.base_salary or record.base_salary, benefits_summary=payload.benefits_summary, contract_end_date=payload.contract_end_date or record.contract_end_date, probation_months=payload.probation_months or record.probation_duration_months, offer_expiry_date=payload.offer_expiry_date, created_by=user.full_name)
    db.add(offer)
    record.offer_status = "generated"
    record.recruitment_stage = "offer"
    _audit(db, user, "REC-016_GENERATE_OFFER", f"Generated offer for {record.candidate_name}.", record.id, None, _row(offer))
    _event(db, user, "recruitment.offer.generated", {"recruitment_id": record.id})
    db.commit()
    db.refresh(offer)
    return _row(offer)


@router.get("/offers")
def list_offers(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return [_row(row) for row in db.query(HRMOfferLetter).order_by(HRMOfferLetter.created_at.desc()).all()]


@router.get("/offers/__analytics")
def offers_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return _simple_analytics(db, HRMOfferLetter, "offer_status", "base_salary")


@router.post("/offers/{offer_id}/approve")
def approve_offer(offer_id: UUID, payload: ApprovalPayload = Body(default_factory=ApprovalPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    offer = _get_or_404(db, HRMOfferLetter, offer_id, "Offer")
    record = _get_or_404(db, HRMRecruitment, offer.recruitment_id, "Candidate")
    offer.approval_status = "approved"
    offer.approved_by = user.full_name
    offer.approved_at = datetime.utcnow()
    record.offer_status = "approved"
    record.approval_status = "approved"
    record.headcount_approved = True
    record.budget_approved = True
    _audit(db, user, "REC-017_APPROVE_OFFER", f"Approved offer for {record.candidate_name}.", record.id, None, _row(offer))
    _event(db, user, "recruitment.offer.approved", {"recruitment_id": record.id, "offer_id": offer.id})
    db.commit()
    return _row(offer)


@router.post("/offers/{offer_id}/send")
def send_offer(offer_id: UUID, payload: ApprovalPayload = Body(default_factory=ApprovalPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    offer = _get_or_404(db, HRMOfferLetter, offer_id, "Offer")
    if offer.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Offer cannot be sent before approval")
    record = _get_or_404(db, HRMRecruitment, offer.recruitment_id, "Candidate")
    offer.offer_status = "sent"
    record.offer_status = "sent"
    _audit(db, user, "REC-018_SEND_OFFER", f"Sent offer to {record.candidate_name}.", record.id, None, _row(offer))
    db.commit()
    return _row(offer)


@router.post("/offers/{offer_id}/accept")
def accept_offer(offer_id: UUID, payload: OfferDecisionPayload = Body(default_factory=OfferDecisionPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    offer = _get_or_404(db, HRMOfferLetter, offer_id, "Offer")
    record = _get_or_404(db, HRMRecruitment, offer.recruitment_id, "Candidate")
    offer.offer_status = "accepted"
    record.offer_status = "accepted"
    record.offer_accepted = True
    record.contract_signed = bool(record.contract_signed or record.employment_contract_reference)
    record.target_start_date = record.target_start_date or offer.start_date
    record.contract_end_date = record.contract_end_date or offer.contract_end_date
    record.base_salary = record.base_salary or offer.base_salary
    record.salary_band = record.salary_band or offer.salary_band
    record.probation_duration_months = record.probation_duration_months or offer.probation_months
    record.background_check_status = "passed" if record.background_check_status == "pending" else record.background_check_status
    _mark_successful_if_ready(db, user, record)
    _audit(db, user, "REC-019_ACCEPT_OFFER", f"Offer accepted by {record.candidate_name}.", record.id, None, _row(record))
    _event(db, user, "recruitment.offer.accepted", {"recruitment_id": record.id, "offer_id": offer.id})
    db.commit()
    return _row(record)


@router.post("/offers/{offer_id}/reject")
def reject_offer(offer_id: UUID, payload: OfferDecisionPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    offer = _get_or_404(db, HRMOfferLetter, offer_id, "Offer")
    record = _get_or_404(db, HRMRecruitment, offer.recruitment_id, "Candidate")
    offer.offer_status = "rejected"
    record.offer_status = "rejected"
    record.offer_accepted = False
    record.application_status = "offer_rejected"
    record.notes = f"{record.notes or ''}\nOffer rejected: {payload.reason or 'No reason supplied'}".strip()
    _audit(db, user, "REC-020_REJECT_OFFER", f"Offer rejected by {record.candidate_name}.", record.id, None, {"reason": payload.reason})
    db.commit()
    return _row(record)


@router.get("/successful-applicants")
def successful_applicants(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    rows = db.query(HRMRecruitment).filter(HRMRecruitment.offer_accepted == True, HRMRecruitment.conversion_status != "converted").order_by(HRMRecruitment.created_at.desc()).all()  # noqa: E712
    for row in rows:
        _mark_successful_if_ready(db, user, row)
    db.commit()
    return [
        {
            **_row(row),
            "readiness_errors": _ready_for_successful_applicant(row),
            "can_convert": not _ready_for_successful_applicant(row) and row.conversion_status != "converted",
        }
        for row in rows
    ]


@router.get("/successful-applicants/__analytics")
def successful_applicants_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    return {
        "total": db.query(HRMRecruitment).filter(HRMRecruitment.offer_accepted == True, HRMRecruitment.conversion_status != "converted").count(),  # noqa: E712
        "status_breakdown": [{"name": "ready", "count": db.query(HRMRecruitment).filter(HRMRecruitment.successful_applicant_status == "ready").count()}],
        "total_value": 0,
    }


@router.post("/successful-applicants/{applicant_id}/convert-to-employee")
def convert_successful_applicant(applicant_id: UUID, payload: ConvertApplicantPayload = Body(default_factory=ConvertApplicantPayload), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    record = _get_or_404(db, HRMRecruitment, applicant_id, "Successful applicant")
    return _convert_record(db, user, record, payload)


@router.post("/successful-applicants/bulk-convert")
def bulk_convert_successful_applicants(payload: BulkConvertPayload, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    results = []
    for applicant_id in payload.applicant_ids:
        record = _get_or_404(db, HRMRecruitment, applicant_id, "Successful applicant")
        try:
            results.append(_convert_record(db, user, record, ConvertApplicantPayload(confirm_missing_data=payload.confirm_missing_data)))
        except HTTPException as exc:
            db.rollback()
            results.append({"applicant_id": str(applicant_id), "status": "failed", "detail": exc.detail})
    return {"results": results}


@router.get("/analytics")
def recruitment_analytics(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    rows = db.query(HRMRecruitment).all()
    requisitions = db.query(HRMJobRequisition).all()
    openings = db.query(HRMJobOpening).all()
    offers = db.query(HRMOfferLetter).all()
    accepted = [row for row in rows if row.offer_accepted]
    converted = [row for row in rows if row.converted_employee_id]
    return {
        "requisitions_created": len(requisitions),
        "open_vacancies": sum(row.vacancies or 1 for row in requisitions if row.status in {"approved", "draft"}),
        "job_openings": len(openings),
        "published_openings": sum(1 for row in openings if row.status == "published"),
        "applications_received": len([row for row in rows if row.opening_id]),
        "shortlisted_candidates": sum(1 for row in rows if row.application_status == "shortlisted"),
        "interviews_scheduled": sum(1 for row in rows if row.interview_date),
        "offers_sent": sum(1 for row in offers if row.offer_status in {"sent", "accepted", "rejected"}),
        "offers_accepted": len(accepted),
        "offers_rejected": sum(1 for row in rows if row.offer_status == "rejected"),
        "successful_applicants": sum(1 for row in rows if row.successful_applicant_status in {"ready", "converted"}),
        "candidates_converted_to_employees": len(converted),
        "average_score": float(sum(Decimal(str(row.total_score or 0)) for row in rows) / Decimal(len(rows))) if rows else 0,
        "source_effectiveness": {},
    }


@router.get("/{recruitment_id}", response_model=RecruitmentResponse)
def get_recruitment(recruitment_id: UUID, db: Session = Depends(get_db)):
    return _get_or_404(db, HRMRecruitment, recruitment_id, "Recruitment record")


@router.put("/{recruitment_id}", response_model=RecruitmentResponse)
def update_recruitment(recruitment_id: UUID, recruitment_update: RecruitmentUpdate, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    record = _get_or_404(db, HRMRecruitment, recruitment_id, "Recruitment record")
    before = _row(record)
    for field, value in recruitment_update.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    _score_candidate(record)
    _audit(db, user, "REC_UPDATE_RECRUITMENT", f"Updated recruitment record for {record.candidate_name}.", record.id, before, _row(record))
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{recruitment_id}")
def delete_recruitment(recruitment_id: UUID, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_hr(user)
    record = _get_or_404(db, HRMRecruitment, recruitment_id, "Recruitment record")
    record.application_status = "archived"
    record.recruitment_stage = "archived"
    _audit(db, user, "REC_ARCHIVE_RECRUITMENT", f"Archived recruitment record for {record.candidate_name}.", record.id, None, _row(record))
    db.commit()
    return {"status": "success", "message": "Recruitment record archived successfully"}
