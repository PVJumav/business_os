from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.crm import (
    CRMAccount,
    CRMDeal,
    CRMInvoice,
    CRMOpportunity,
    CRMPMOProject,
    CRMSLAAssignment,
    CRMSalesTarget,
    CRMTender,
    CRMTicket,
)
from backend.models.automation import UserAccessProfile
from backend.models.enterprise import NotificationEvent
from backend.models.finance import FinanceCostCenter
from backend.models.hrm import (
    HRMAssetAssignment,
    HRMAttendance,
    HRMBenefit,
    HRMCompensation,
    HRMDocument,
    HRMEmployee,
    HRMEmployeeRelationCase,
    HRMLeave,
    HRMLeaveBalance,
    HRMLifecycleEvent,
    HRMOnboardingTask,
    HRMPayroll,
    HRMPerformance,
    HRMPolicyAcknowledgement,
    HRMProbationRecord,
    HRMProbationReview,
    HRMTraining,
    HRMAuditLog,
    HRMSalaryStructure,
)
from backend.schemas.auth import UserResponse


router = APIRouter(prefix="/staff", tags=["Staff Intelligence"])


def row_to_dict(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def full_name(employee: HRMEmployee) -> str:
    return f"{employee.first_name} {employee.last_name}".strip()


def person_filters(*columns, employee: HRMEmployee):
    names = {full_name(employee), employee.email, employee.employee_code}
    return [column.ilike(f"%{name}%") for column in columns for name in names if name]


def sensitive_hr_visible(current_user: UserResponse, db: Session) -> bool:
    if current_user.role == "admin":
        return True
    employee = db.query(HRMEmployee).filter(HRMEmployee.email == current_user.email).first()
    return bool(employee and (employee.department or "").strip().lower() == "hr")


@router.get("/search")
def search_staff(
    query: str = Query(default="", min_length=0),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    term = query.strip()
    if not term:
        return []

    pattern = f"%{term}%"
    employees = (
        db.query(HRMEmployee)
        .filter(
            or_(
                HRMEmployee.first_name.ilike(pattern),
                HRMEmployee.last_name.ilike(pattern),
                HRMEmployee.email.ilike(pattern),
                HRMEmployee.employee_code.ilike(pattern),
                HRMEmployee.job_title.ilike(pattern),
                HRMEmployee.department.ilike(pattern),
            )
        )
        .order_by(HRMEmployee.first_name.asc(), HRMEmployee.last_name.asc())
        .limit(12)
        .all()
    )

    return [
        {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "full_name": full_name(employee),
            "email": employee.email,
            "department": employee.department,
            "job_title": employee.job_title,
            "job_group": employee.job_group,
            "salary_grade": employee.salary_grade if sensitive_hr_visible(current_user, db) else None,
            "employment_status": employee.employment_status,
        }
        for employee in employees
    ]


@router.get("/{employee_id}/profile")
def get_staff_profile(
    employee_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    visible_sensitive = sensitive_hr_visible(current_user, db)
    person_match = person_filters(
        CRMAccount.account_manager,
        CRMAccount.relationship_owner,
        employee=employee,
    )
    opportunity_match = person_filters(CRMOpportunity.owner, employee=employee)
    deal_match = person_filters(CRMDeal.owner, employee=employee)
    project_match = person_filters(
        CRMPMOProject.project_manager,
        CRMPMOProject.account_manager,
        CRMPMOProject.technical_lead,
        CRMPMOProject.pit_team,
        employee=employee,
    )
    sla_match = person_filters(CRMSLAAssignment.assigned_engineer, CRMSLAAssignment.technical_lead, employee=employee)
    tender_match = person_filters(CRMTender.bid_manager, CRMTender.account_manager, CRMTender.technical_lead, employee=employee)
    ticket_match = person_filters(CRMTicket.assigned_engineer, CRMTicket.technical_lead, employee=employee)

    supervisor = (
        db.query(HRMEmployee).filter(HRMEmployee.id == employee.supervisor_id).first()
        if employee.supervisor_id
        else None
    )
    direct_reports = db.query(HRMEmployee).filter(HRMEmployee.supervisor_id == employee.id).all()

    accounts = db.query(CRMAccount).filter(or_(*person_match)).order_by(CRMAccount.company_name.asc()).all() if person_match else []
    opportunities = db.query(CRMOpportunity).filter(or_(*opportunity_match)).order_by(CRMOpportunity.created_at.desc()).all() if opportunity_match else []
    deals = db.query(CRMDeal).filter(or_(*deal_match)).order_by(CRMDeal.created_at.desc()).all() if deal_match else []
    projects = db.query(CRMPMOProject).filter(or_(*project_match)).order_by(CRMPMOProject.created_at.desc()).all() if project_match else []
    slas = db.query(CRMSLAAssignment).filter(or_(*sla_match)).order_by(CRMSLAAssignment.created_at.desc()).all() if sla_match else []
    tenders = db.query(CRMTender).filter(or_(*tender_match)).order_by(CRMTender.created_at.desc()).all() if tender_match else []
    tickets = db.query(CRMTicket).filter(or_(*ticket_match)).order_by(CRMTicket.created_at.desc()).all() if ticket_match else []
    targets = (
        db.query(CRMSalesTarget)
        .filter(CRMSalesTarget.target_owner.ilike(f"%{full_name(employee)}%"))
        .order_by(CRMSalesTarget.created_at.desc())
        .all()
    )
    invoices = (
        db.query(CRMInvoice)
        .filter(CRMInvoice.debt_owner.ilike(f"%{full_name(employee)}%"))
        .order_by(CRMInvoice.created_at.desc())
        .all()
    )
    performance = (
        db.query(HRMPerformance)
        .filter(or_(HRMPerformance.employee_id == employee.id, HRMPerformance.reviewer_id == employee.id))
        .order_by(HRMPerformance.created_at.desc())
        .all()
    )
    attendance = (
        db.query(HRMAttendance)
        .filter(HRMAttendance.employee_id == employee.id)
        .order_by(HRMAttendance.attendance_date.desc())
        .limit(60)
        .all()
    )
    leave = (
        db.query(HRMLeave)
        .filter(HRMLeave.employee_id == employee.id)
        .order_by(HRMLeave.created_at.desc())
        .all()
    )
    leave_balances = (
        db.query(HRMLeaveBalance)
        .filter(HRMLeaveBalance.employee_id == employee.id)
        .order_by(HRMLeaveBalance.fiscal_year.desc(), HRMLeaveBalance.leave_type.asc())
        .all()
    )
    training = (
        db.query(HRMTraining)
        .filter(HRMTraining.employee_id == employee.id)
        .order_by(HRMTraining.created_at.desc())
        .all()
    )
    benefits = (
        db.query(HRMBenefit)
        .filter(HRMBenefit.employee_id == employee.id)
        .order_by(HRMBenefit.created_at.desc())
        .all()
    )
    documents = (
        db.query(HRMDocument)
        .filter(HRMDocument.employee_id == employee.id)
        .order_by(HRMDocument.created_at.desc())
        .all()
    )
    onboarding = (
        db.query(HRMOnboardingTask)
        .filter(HRMOnboardingTask.employee_id == employee.id)
        .order_by(HRMOnboardingTask.created_at.desc())
        .all()
    )
    lifecycle = (
        db.query(HRMLifecycleEvent)
        .filter(HRMLifecycleEvent.employee_id == employee.id)
        .order_by(HRMLifecycleEvent.effective_date.desc(), HRMLifecycleEvent.created_at.desc())
        .all()
    )
    policy_acknowledgements = (
        db.query(HRMPolicyAcknowledgement)
        .filter(HRMPolicyAcknowledgement.employee_id == employee.id)
        .order_by(HRMPolicyAcknowledgement.created_at.desc())
        .all()
    )
    asset_assignments = (
        db.query(HRMAssetAssignment)
        .filter(HRMAssetAssignment.employee_id == employee.id)
        .order_by(HRMAssetAssignment.created_at.desc())
        .all()
    )
    compensation = (
        db.query(HRMCompensation)
        .filter(HRMCompensation.employee_id == employee.id)
        .order_by(HRMCompensation.effective_date.desc())
        .all()
        if visible_sensitive
        else []
    )
    salary_structures = (
        db.query(HRMSalaryStructure)
        .filter(HRMSalaryStructure.employee_id == employee.id)
        .order_by(HRMSalaryStructure.effective_from.desc())
        .all()
        if visible_sensitive
        else []
    )
    iam_access = (
        db.query(UserAccessProfile)
        .filter(UserAccessProfile.employee_id == employee.id)
        .order_by(UserAccessProfile.created_at.desc())
        .all()
        if visible_sensitive
        else []
    )
    finance_cost_centers = (
        db.query(FinanceCostCenter)
        .filter(or_(FinanceCostCenter.owner_employee_id == employee.id, FinanceCostCenter.department == employee.department))
        .order_by(FinanceCostCenter.created_at.desc())
        .all()
        if visible_sensitive
        else []
    )
    notifications = (
        db.query(NotificationEvent)
        .filter(NotificationEvent.related_id == employee.id)
        .order_by(NotificationEvent.created_at.desc())
        .all()
    )
    audit_logs = (
        db.query(HRMAuditLog)
        .filter(HRMAuditLog.entity_id == str(employee.id))
        .order_by(HRMAuditLog.created_at.desc())
        .all()
        if visible_sensitive
        else []
    )
    employee_relations = (
        db.query(HRMEmployeeRelationCase)
        .filter(HRMEmployeeRelationCase.employee_id == employee.id)
        .order_by(HRMEmployeeRelationCase.created_at.desc())
        .all()
        if visible_sensitive
        else []
    )
    payroll = (
        db.query(HRMPayroll).filter(HRMPayroll.employee_id == employee.id).order_by(HRMPayroll.created_at.desc()).all()
        if visible_sensitive
        else []
    )
    probation_records = (
        db.query(HRMProbationRecord)
        .filter(HRMProbationRecord.employee_id == employee.id)
        .order_by(HRMProbationRecord.created_at.desc())
        .all()
    )
    probation_reviews = (
        db.query(HRMProbationReview)
        .filter(HRMProbationReview.employee_id == employee.id)
        .order_by(HRMProbationReview.created_at.desc())
        .all()
    )

    return {
        "employee": {
            **row_to_dict(employee),
            "full_name": full_name(employee),
            "salary_grade": employee.salary_grade if visible_sensitive else None,
        },
        "line_manager": {
            "id": supervisor.id,
            "full_name": full_name(supervisor),
            "department": supervisor.department,
            "job_title": supervisor.job_title,
        }
        if supervisor
        else None,
        "direct_reports": [
            {
                "id": report.id,
                "full_name": full_name(report),
                "department": report.department,
                "job_title": report.job_title,
            }
            for report in direct_reports
        ],
        "crm": {
            "accounts": [row_to_dict(item) for item in accounts],
            "opportunities": [row_to_dict(item) for item in opportunities],
            "deals": [row_to_dict(item) for item in deals],
            "targets": [row_to_dict(item) for item in targets],
            "projects": [row_to_dict(item) for item in projects],
            "slas": [row_to_dict(item) for item in slas],
            "tenders": [row_to_dict(item) for item in tenders],
            "tickets": [row_to_dict(item) for item in tickets],
            "invoices": [row_to_dict(item) for item in invoices],
        },
        "hr": {
            "attendance": [row_to_dict(item) for item in attendance],
            "leave": [row_to_dict(item) for item in leave],
            "leave_balances": [row_to_dict(item) for item in leave_balances],
            "training": [row_to_dict(item) for item in training],
            "benefits": [row_to_dict(item) for item in benefits],
            "documents": [row_to_dict(item) for item in documents],
            "onboarding": [row_to_dict(item) for item in onboarding],
            "lifecycle": [row_to_dict(item) for item in lifecycle],
            "policy_acknowledgements": [row_to_dict(item) for item in policy_acknowledgements],
            "asset_assignments": [row_to_dict(item) for item in asset_assignments],
            "performance": [row_to_dict(item) for item in performance],
            "compensation": [row_to_dict(item) for item in compensation],
            "salary_structures": [row_to_dict(item) for item in salary_structures],
            "iam_access": [row_to_dict(item) for item in iam_access],
            "finance_cost_centers": [row_to_dict(item) for item in finance_cost_centers],
            "notifications": [row_to_dict(item) for item in notifications],
            "audit_logs": [row_to_dict(item) for item in audit_logs],
            "employee_relations": [row_to_dict(item) for item in employee_relations],
            "payroll": [row_to_dict(item) for item in payroll],
            "probation_records": [row_to_dict(item) for item in probation_records],
            "probation_reviews": [row_to_dict(item) for item in probation_reviews],
            "sensitive_visible": visible_sensitive,
        },
    }
