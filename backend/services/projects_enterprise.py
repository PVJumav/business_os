from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.hrm import HRMEmployee
from backend.models.auth import AuthUser
from backend.models.projects import (
    BusinessInvoiceLifecycle,
    BusinessInvoiceSchedule,
    BusinessInvoiceTemplate,
    LicenseTracking,
    LicenseAllocation,
    LicenseComplianceCheck,
    LicenseSubscription,
    MarketingInitiative,
    Project,
    ProjectApproval,
    ProjectAuditLog,
    ProjectBudget,
    ProjectChangeRequest,
    ProjectCharter,
    ProjectDependency,
    ProjectDeliverable,
    ProjectDocument,
    ProjectExpense,
    ProjectIssue,
    ProjectLessonLearned,
    ProjectMilestone,
    ProjectPhase,
    ProjectResourceForecast,
    ProjectRisk,
    ProjectRole,
    ProjectSignoff,
    ProjectScope,
    ProjectStatusUpdate,
    ProjectSubtask,
    ProjectTask,
    ProjectTeamMember,
    ProjectTimesheet,
    ProjectWBSItem,
    SLA,
    SLAEscalation,
    SLAExceptionApproval,
    SLAHealthCheck,
    SLARenewal,
    SLAServiceHour,
    SLASupportCoverage,
    SLATarget,
    SLATicket,
    SLATier,
    VendorEngagement,
)
from backend.policies.projects import deny_locked_project, require_project_access
from backend.schemas.auth import UserResponse


RESOURCE_MAP = {
    "projects": Project,
    "phases": ProjectPhase,
    "milestones": ProjectMilestone,
    "tasks": ProjectTask,
    "subtasks": ProjectSubtask,
    "team": ProjectTeamMember,
    "team-members": ProjectTeamMember,
    "roles": ProjectRole,
    "documents": ProjectDocument,
    "charters": ProjectCharter,
    "scopes": ProjectScope,
    "deliverables": ProjectDeliverable,
    "wbs": ProjectWBSItem,
    "wbs-items": ProjectWBSItem,
    "budget": ProjectBudget,
    "budgets": ProjectBudget,
    "expenses": ProjectExpense,
    "risks": ProjectRisk,
    "issues": ProjectIssue,
    "dependencies": ProjectDependency,
    "status-updates": ProjectStatusUpdate,
    "timesheets": ProjectTimesheet,
    "resource-forecasts": ProjectResourceForecast,
    "lessons-learned": ProjectLessonLearned,
    "approvals": ProjectApproval,
    "signoff": ProjectSignoff,
    "signoffs": ProjectSignoff,
    "slas": SLA,
    "sla-tiers": SLATier,
    "sla-targets": SLATarget,
    "sla-service-hours": SLAServiceHour,
    "sla-support-coverage": SLASupportCoverage,
    "sla-health-checks": SLAHealthCheck,
    "sla-tickets": SLATicket,
    "sla-escalations": SLAEscalation,
    "sla-exceptions": SLAExceptionApproval,
    "sla-renewals": SLARenewal,
    "licenses": LicenseTracking,
    "license-allocations": LicenseAllocation,
    "license-subscriptions": LicenseSubscription,
    "license-compliance": LicenseComplianceCheck,
    "invoice-templates": BusinessInvoiceTemplate,
    "invoice-lifecycle": BusinessInvoiceLifecycle,
    "invoice-schedules": BusinessInvoiceSchedule,
    "vendor-engagements": VendorEngagement,
    "marketing-initiatives": MarketingInitiative,
    "change-requests": ProjectChangeRequest,
    "audit-logs": ProjectAuditLog,
}

WORKFLOW_TRANSITIONS = {
    "submit": "pending_approval",
    "approve": "approved",
    "reject": "rejected",
    "start": "in_progress",
    "pause": "on_hold",
    "resume": "in_progress",
    "complete": "completed",
    "signoff": "signed_off",
    "close": "closed",
    "cancel": "cancelled",
    "reopen": "in_progress",
}


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Project resource not found")
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
    blocked = {"id", "created_at", "updated_at", "deleted_at"}
    columns = {column.name for column in model.__table__.columns}
    return {key: value for key, value in data.items() if key in columns and key not in blocked and value not in ("", None)}


def audit(db: Session, user: UserResponse | None, action: str, entity_type: str, entity_id: str | None, before=None, after=None):
    actor_id = getattr(user, "id", None)
    if actor_id and not db.query(AuthUser).filter(AuthUser.id == actor_id).first():
        actor_id = None
    db.add(
        ProjectAuditLog(
            actor_user_id=actor_id,
            actor_email=getattr(user, "email", None),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=f"{action} project {entity_type}",
            before_json=before,
            after_json=after,
        )
    )


def active_employee(db: Session, employee_id: UUID | str | None) -> HRMEmployee | None:
    if not employee_id:
        return None
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=422, detail="Referenced employee does not exist in HRM")
    if employee.employment_status in {"inactive", "terminated", "suspended"}:
        raise HTTPException(status_code=422, detail="Inactive, suspended, or terminated employees cannot receive project work")
    return employee


def get_record(db: Session, resource: str, record_id: UUID):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Project record not found")
    return record


def project_for_child(db: Session, resource: str, data_or_record: dict[str, Any] | Any) -> Project | None:
    project_id = data_or_record.get("project_id") if isinstance(data_or_record, dict) else getattr(data_or_record, "project_id", None)
    if not project_id:
        return data_or_record if isinstance(data_or_record, Project) else None
    return db.query(Project).filter(Project.id == project_id).first()


def list_records(db: Session, resource: str, user: UserResponse, project_id: UUID | None = None) -> list[dict[str, Any]]:
    model = model_for(resource)
    require_project_access(db, user, "read", resource)
    query = db.query(model)
    if project_id and hasattr(model, "project_id"):
        query = query.filter(model.project_id == project_id)
    if hasattr(model, "soft_deleted"):
        query = query.filter(model.soft_deleted.is_(False))
    if hasattr(model, "created_at"):
        query = query.order_by(model.created_at.desc())
    rows = query.limit(500).all()
    return [serialize(row) for row in rows]


def validate(db: Session, resource: str, data: dict[str, Any], record: Any | None = None) -> None:
    if resource == "projects":
        if not data.get("owner_user_id") and not (record and getattr(record, "owner_user_id", None)):
            raise HTTPException(status_code=422, detail="A project must have an owner")
        if data.get("project_type") in {"customer_implementation", "sla_service"} and not data.get("crm_account_id"):
            raise HTTPException(status_code=422, detail="Customer projects must link to a CRM account")
        active_employee(db, data.get("project_manager_employee_id"))
    if resource in {"team", "team-members"}:
        active_employee(db, data.get("employee_id"))
    if resource in {"tasks", "subtasks", "issues", "sla-tickets"}:
        active_employee(db, data.get("assigned_employee_id") or data.get("escalated_to_employee_id"))
    if resource in {"charters"}:
        active_employee(db, data.get("sponsor_employee_id"))
    if resource in {"deliverables", "wbs", "wbs-items", "resource-forecasts", "license-allocations"}:
        active_employee(db, data.get("owner_employee_id") or data.get("employee_id"))
    if resource == "timesheets":
        active_employee(db, data.get("employee_id"))
        if (Decimal(str(data.get("billable_hours") or 0)) + Decimal(str(data.get("non_billable_hours") or 0))) <= 0:
            raise HTTPException(status_code=422, detail="Timesheet hours must be greater than zero")
    if resource in {"sla-targets"} and not data.get("target_type"):
        raise HTTPException(status_code=422, detail="SLA target type is required")
    if resource in {"sla-support-coverage"}:
        active_employee(db, data.get("primary_owner_employee_id"))
    if resource == "license-compliance":
        used = Decimal(str(data.get("used_licenses") or 0))
        purchased = Decimal(str(data.get("purchased_licenses") or 0))
        if purchased and used > purchased:
            data["compliance_status"] = "non_compliant"
    if resource == "invoice-lifecycle" and not data.get("account_id"):
        raise HTTPException(status_code=422, detail="Invoice lifecycle records must link to a CRM account")
    if resource in {"expenses"} and not data.get("expense_category"):
        raise HTTPException(status_code=422, detail="Project expenses require an expense category")


def calculate_sla_ticket(db: Session, ticket: SLATicket) -> None:
    response_hours = {"critical": 1, "high": 4, "medium": 8, "low": 24}.get(str(ticket.priority).lower(), 8)
    resolution_hours = {"critical": 8, "high": 24, "medium": 48, "low": 96}.get(str(ticket.priority).lower(), 48)
    if ticket.sla_id:
        sla = db.query(SLA).filter(SLA.id == ticket.sla_id).first()
        if sla:
            response_hours = sla.response_hours or response_hours
            resolution_hours = sla.resolution_hours or resolution_hours
    opened = ticket.opened_at or datetime.now(timezone.utc)
    ticket.response_due_at = opened + timedelta(hours=response_hours)
    ticket.resolution_due_at = opened + timedelta(hours=resolution_hours)
    now = datetime.now(timezone.utc)
    if ticket.status not in {"resolved", "closed"} and ticket.resolution_due_at and now > ticket.resolution_due_at:
        ticket.sla_status = "breached"
    elif not ticket.first_response_at and ticket.response_due_at and now > ticket.response_due_at:
        ticket.sla_status = "response_breached"
    else:
        ticket.sla_status = "within_sla"


def create_record(db: Session, resource: str, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    data = clean_payload(model, data)
    if resource == "projects" and not data.get("owner_user_id"):
        data["owner_user_id"] = getattr(user, "id", None)
    project = project_for_child(db, resource, data)
    require_project_access(db, user, "create", resource, project)
    if project:
        deny_locked_project(project)
    validate(db, resource, data)
    record = model(**data)
    if resource == "sla-tickets":
        calculate_sla_ticket(db, record)
    if resource == "licenses":
        purchased = Decimal(str(getattr(record, "purchased_licenses", 0) or 0))
        used = Decimal(str(getattr(record, "used_licenses", 0) or 0))
        record.consumption_percent = (used / purchased * Decimal("100")) if purchased else Decimal("0")
    if resource == "invoice-lifecycle":
        record.total_amount = Decimal(str(record.amount or 0)) + Decimal(str(record.tax_amount or 0))
    db.add(record)
    db.flush()
    if resource in {"team", "team-members"} and project:
        project.team_assignment_status = "assigned"
    after = serialize(record)
    audit(db, user, "create", resource, str(record.id), after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def update_record(db: Session, resource: str, record_id: UUID, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    record = get_record(db, resource, record_id)
    project = record if isinstance(record, Project) else project_for_child(db, resource, record)
    require_project_access(db, user, "update", resource, project)
    if project:
        deny_locked_project(project)
    before = serialize(record)
    data = clean_payload(model, data)
    validate(db, resource, data, record)
    if isinstance(record, Project) and any(key in data for key in ["approved_budget", "start_date", "target_end_date"]):
        db.add(ProjectChangeRequest(project_id=record.id, change_type="approved_field_update", reason=data.get("notes") or "Sensitive project field changed", requested_by=user.email))
    for key, value in data.items():
        setattr(record, key, value)
    if resource == "sla-tickets":
        calculate_sla_ticket(db, record)
    if resource == "licenses":
        purchased = Decimal(str(getattr(record, "purchased_licenses", 0) or 0))
        used = Decimal(str(getattr(record, "used_licenses", 0) or 0))
        record.consumption_percent = (used / purchased * Decimal("100")) if purchased else Decimal("0")
    if resource == "invoice-lifecycle":
        record.total_amount = Decimal(str(record.amount or 0)) + Decimal(str(record.tax_amount or 0))
    db.flush()
    audit(db, user, "update", resource, str(record_id), before=before, after=serialize(record))
    db.commit()
    db.refresh(record)
    return serialize(record)


def delete_record(db: Session, resource: str, record_id: UUID, user: UserResponse) -> None:
    record = get_record(db, resource, record_id)
    project = record if isinstance(record, Project) else project_for_child(db, resource, record)
    require_project_access(db, user, "delete", resource, project)
    if project:
        deny_locked_project(project)
    before = serialize(record)
    if hasattr(record, "soft_deleted"):
        record.soft_deleted = True
        record.deleted_at = datetime.now(timezone.utc)
        if hasattr(record, "lifecycle_status"):
            record.lifecycle_status = "deleted"
    else:
        db.delete(record)
    audit(db, user, "delete", resource, str(record_id), before=before)
    db.commit()


def assert_can_start(project: Project, db: Session) -> None:
    if project.budget_approval_status not in {"approved", "active"}:
        raise HTTPException(status_code=422, detail="Project cannot start implementation before budget approval")
    if project.team_assignment_status != "assigned":
        raise HTTPException(status_code=422, detail="Project cannot start implementation before team assignment")


def assert_can_close(project: Project, db: Session) -> None:
    incomplete = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.project_id == project.id, ProjectMilestone.required_for_close.is_(True), ProjectMilestone.status.notin_(["completed", "closed"]))
        .count()
    )
    if incomplete:
        raise HTTPException(status_code=422, detail="Project cannot close before required milestones are completed")


def assert_can_signoff(project: Project, db: Session) -> None:
    approved = db.query(ProjectApproval).filter(ProjectApproval.project_id == project.id, ProjectApproval.status == "approved").count()
    if not approved:
        raise HTTPException(status_code=422, detail="Project requires approval records before signoff")


def workflow(db: Session, resource: str, record_id: UUID, action: str, user: UserResponse, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    record = get_record(db, resource, record_id)
    project = record if isinstance(record, Project) else project_for_child(db, resource, record)
    require_project_access(db, user, "update", resource, project)
    before = serialize(record)
    payload = payload or {}
    now = datetime.now(timezone.utc)
    if isinstance(record, Project):
        if action == "start":
            assert_can_start(record, db)
        if action == "signoff":
            assert_can_signoff(record, db)
            record.signoff_status = "signed_off"
            record.locked = True
        if action == "close":
            assert_can_close(record, db)
            record.locked = True
            record.actual_end_date = now.date()
        if action == "reopen" and not payload.get("reason"):
            raise HTTPException(status_code=422, detail="Reopening a project requires a reason")
        if action not in WORKFLOW_TRANSITIONS:
            raise HTTPException(status_code=422, detail="Unsupported project workflow action")
        record.lifecycle_status = WORKFLOW_TRANSITIONS[action]
    elif isinstance(record, (ProjectApproval, ProjectBudget, ProjectExpense, ProjectSignoff)):
        if action == "approve":
            if hasattr(record, "approval_status"):
                record.approval_status = "approved"
            record.status = "approved"
            if hasattr(record, "approved_by"):
                record.approved_by = user.email
            if hasattr(record, "approved_at"):
                record.approved_at = now
        elif action == "reject":
            if hasattr(record, "approval_status"):
                record.approval_status = "rejected"
            record.status = "rejected"
        elif action == "submit":
            if hasattr(record, "approval_status"):
                record.approval_status = "submitted"
            record.status = "submitted"
        else:
            raise HTTPException(status_code=422, detail="Unsupported approval workflow action")
    elif isinstance(record, SLATicket):
        if action == "resolve":
            record.status = "resolved"
            record.resolved_at = now
            record.resolution_notes = payload.get("comments")
        elif action == "close":
            record.status = "closed"
        elif action == "escalate":
            record.escalation_level = (record.escalation_level or 0) + 1
            db.add(SLAEscalation(sla_ticket_id=record.id, escalation_level=record.escalation_level, reason=payload.get("reason")))
        elif action == "reopen":
            record.status = "open"
        else:
            raise HTTPException(status_code=422, detail="Unsupported SLA ticket workflow action")
        calculate_sla_ticket(db, record)
    elif isinstance(record, ProjectTimesheet):
        if action == "approve":
            record.approval_status = "approved"
            record.approved_by = user.email
            record.approved_at = now
        elif action == "reject":
            record.approval_status = "rejected"
        else:
            raise HTTPException(status_code=422, detail="Unsupported timesheet workflow action")
    elif isinstance(record, BusinessInvoiceLifecycle):
        if action == "approve":
            record.approval_status = "approved"
            record.status = "approved"
        elif action == "dispatch":
            if record.approval_status != "approved":
                raise HTTPException(status_code=422, detail="Only approved invoices can be dispatched")
            record.dispatch_status = "sent"
            record.status = "sent"
        elif action == "accept":
            record.acceptance_status = "accepted"
            record.status = "accepted"
        elif action == "cancel":
            record.status = "cancelled"
        else:
            raise HTTPException(status_code=422, detail="Unsupported invoice workflow action")
    else:
        if not hasattr(record, "status") or action not in WORKFLOW_TRANSITIONS:
            raise HTTPException(status_code=422, detail="Unsupported workflow action")
        record.status = WORKFLOW_TRANSITIONS[action]
    db.flush()
    audit(db, user, action, resource, str(record_id), before=before, after=serialize(record))
    db.commit()
    db.refresh(record)
    return serialize(record)


def analytics_summary(db: Session) -> dict[str, Any]:
    total_budget = db.query(func.coalesce(func.sum(Project.approved_budget), 0)).scalar() or 0
    total_cost = db.query(func.coalesce(func.sum(Project.actual_cost), 0)).scalar() or 0
    billable = db.query(func.coalesce(func.sum(ProjectTimesheet.billable_hours), 0)).filter(ProjectTimesheet.approval_status == "approved").scalar() or 0
    available = db.query(func.coalesce(func.sum(ProjectTimesheet.available_hours), 0)).filter(ProjectTimesheet.approval_status == "approved").scalar() or 0
    breached_sla = db.query(SLATicket).filter(SLATicket.sla_status.in_(["breached", "response_breached"])).count()
    total_tickets = db.query(SLATicket).count()
    within_sla = db.query(SLATicket).filter(SLATicket.sla_status == "within_sla").count()
    license_purchased = db.query(func.coalesce(func.sum(LicenseTracking.purchased_licenses), 0)).scalar() or 0
    license_used = db.query(func.coalesce(func.sum(LicenseTracking.used_licenses), 0)).scalar() or 0
    return {
        "projects": db.query(Project).filter(Project.soft_deleted.is_(False)).count(),
        "active_projects": db.query(Project).filter(Project.lifecycle_status.in_(["approved", "planning", "in_progress", "on_hold"])).count(),
        "completed_projects": db.query(Project).filter(Project.lifecycle_status.in_(["completed", "signed_off", "closed"])).count(),
        "total_budget": float(total_budget),
        "total_cost": float(total_cost),
        "profitability_proxy": float((total_budget or 0) - (total_cost or 0)),
        "resource_utilization_percent": float((Decimal(str(billable)) / Decimal(str(available)) * Decimal("100")) if available else 0),
        "open_sla_tickets": db.query(SLATicket).filter(SLATicket.status.notin_(["resolved", "closed"])).count(),
        "breached_sla_tickets": breached_sla,
        "sla_compliance_percent": float((Decimal(str(within_sla)) / Decimal(str(total_tickets)) * Decimal("100")) if total_tickets else 0),
        "licenses_expiring": db.query(LicenseTracking).filter(LicenseTracking.status == "active").count(),
        "license_consumption_percent": float((Decimal(str(license_used)) / Decimal(str(license_purchased)) * Decimal("100")) if license_purchased else 0),
        "invoice_lifecycle_total": db.query(BusinessInvoiceLifecycle).count(),
    }
