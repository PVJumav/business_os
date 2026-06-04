from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.crud import assign_business_id
from backend.core.database import get_db
from backend.models.automation import EnterpriseEvent
from backend.models.crm import (
    CRMAccount,
    CRMAuditLog,
    CRMContact,
    CRMCustomerLPO,
    CRMLead,
    CRMOpportunity,
    CRMQuotation,
    CRMTask,
)
from backend.models.enterprise import NotificationEvent
from backend.models.hrm import HRMEmployee
from backend.schemas.auth import UserResponse
from backend.services.crm_enterprise import convert_lead, serialize, workflow


router = APIRouter(tags=["CRM v6 HRMS-linked workflows"])

ACTIVE_EMPLOYEE_STATUSES = {"active", "confirmed", "on_probation", "probation", "pending_activation"}
BLOCKED_EMPLOYEE_STATUSES = {"inactive", "suspended", "terminated", "retired", "exited", "deceased", "archived", "blacklisted"}
SALES_DEPARTMENTS = {"sales", "presales", "business development", "business_development", "marketing"}
TECHNICAL_DEPARTMENTS = {"presales", "technical", "cybersecurity", "data", "infrastructure", "engineering", "solutions"}
CRM_ACCESS_ROLES = {"crm", "sales", "presales", "business development", "account manager", "sales manager", "customer success"}
CRM_STAGES = {
    "Prospecting",
    "Qualification",
    "Needs Analysis",
    "Solution Design",
    "Proposal",
    "Negotiation",
    "Awaiting LPO",
    "Won",
    "Lost",
    "Stage 1.a Discovery",
    "Stage 1.b Presentation/Demo/POC",
    "Stage 1.c RFP/Tender",
    "Stage 1.d Commit/Award",
    "Stage 6.a Closed as Won",
    "Stage 6.b Closed as Lost",
}
CRM_STAGE_ALIASES = {
    "Closed Won": "Stage 6.a Closed as Won",
    "closed_won": "Stage 6.a Closed as Won",
    "Stage 6.a Closed as Won": "Stage 6.a Closed as Won",
    "Closed Lost": "Stage 6.b Closed as Lost",
    "closed_lost": "Stage 6.b Closed as Lost",
    "Stage 6.b Closed as Lost": "Stage 6.b Closed as Lost",
}


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


def _audit(db: Session, user: UserResponse, action: str, entity_type: str, entity_id: UUID | str | None, before: Any = None, after: Any = None, summary: str | None = None) -> None:
    db.add(
        CRMAuditLog(
            actor_user_id=user.id,
            actor_email=user.email,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            summary=summary or f"{action} {entity_type}",
            before_json=_jsonable(before),
            after_json=_jsonable(after),
        )
    )


def _event(db: Session, user: UserResponse, event_type: str, payload: dict[str, Any], target_module: str = "Enterprise") -> None:
    db.add(
        EnterpriseEvent(
            event_type=event_type,
            source_module="CRM",
            target_module=target_module,
            payload=_jsonable(payload),
            event_status="pending",
            created_by=user.full_name,
        )
    )


def _notify(db: Session, user: UserResponse, subject: str, body: str, related_id: UUID | None = None, recipient_name: str = "CRM Owner") -> None:
    db.add(
        NotificationEvent(
            module="CRM",
            related_entity="CRM",
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


def _employee_name(employee: HRMEmployee) -> str:
    return f"{employee.first_name} {employee.last_name}".strip() or employee.email or str(employee.id)


def _active_employee(db: Session, employee_id: UUID, label: str = "Employee", allowed_departments: set[str] | None = None, require_crm_role: bool = True) -> HRMEmployee:
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=f"{label} not found in HRMS")
    status_value = (employee.employment_status or "").strip().lower()
    if status_value in BLOCKED_EMPLOYEE_STATUSES or status_value not in ACTIVE_EMPLOYEE_STATUSES:
        raise HTTPException(status_code=422, detail=f"{label} must be an active HRMS employee")
    department = (employee.department or "").strip().lower()
    role = (employee.role_category or employee.job_title or "").strip().lower()
    if allowed_departments and department not in allowed_departments and role not in allowed_departments:
        raise HTTPException(status_code=422, detail=f"{label} is not in an authorized CRM department")
    if require_crm_role and not any(token in f"{department} {role}" for token in CRM_ACCESS_ROLES):
        raise HTTPException(status_code=422, detail=f"{label} does not have a CRM access role mapping")
    return employee


def _manager_id(employee: HRMEmployee) -> UUID | None:
    return employee.supervisor_id


def _duplicate_lead_reason(db: Session, payload: dict[str, Any], exclude_id: UUID | None = None) -> str | None:
    filters = []
    if payload.get("email"):
        filters.append(CRMLead.email.ilike(str(payload["email"])))
    if payload.get("phone"):
        filters.append(CRMLead.phone == str(payload["phone"]))
    if payload.get("company_name"):
        filters.append(CRMLead.company_name.ilike(str(payload["company_name"])))
    website = str(payload.get("account_website") or "").replace("https://", "").replace("http://", "").strip("/").lower()
    if website:
        filters.append(func.lower(CRMLead.account_website).contains(website))
    if not filters:
        return None
    query = db.query(CRMLead).filter(or_(*filters), CRMLead.soft_deleted.is_(False))
    if exclude_id:
        query = query.filter(CRMLead.id != exclude_id)
    return "Possible duplicate lead detected" if query.first() else None


@router.get("/crm/active-employees")
def list_active_crm_employees(
    role_group: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    query = db.query(HRMEmployee).filter(HRMEmployee.employment_status.in_(["active", "confirmed", "on_probation", "probation", "pending_activation"]))
    rows = query.order_by(HRMEmployee.first_name, HRMEmployee.last_name).all()
    if role_group == "sales":
        rows = [row for row in rows if (row.department or "").lower() in SALES_DEPARTMENTS or (row.role_category or "").lower() in SALES_DEPARTMENTS]
    elif role_group == "technical":
        rows = [row for row in rows if (row.department or "").lower() in TECHNICAL_DEPARTMENTS or (row.role_category or "").lower() in TECHNICAL_DEPARTMENTS]
    return [
        {
            "id": str(row.id),
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "department": row.department,
            "job_title": row.job_title,
            "role_category": row.role_category,
            "employment_status": row.employment_status,
        }
        for row in rows
    ]


@router.post("/crm/leads/{lead_id}/assign-owner")
def assign_lead_owner(
    lead_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    owner_id = payload.get("owner_employee_id") or payload.get("employee_id")
    if not owner_id:
        raise HTTPException(status_code=422, detail="owner_employee_id is required")
    owner = _active_employee(db, UUID(str(owner_id)), "Lead owner", SALES_DEPARTMENTS)
    lead = _get_or_404(db, CRMLead, lead_id, "Lead")
    before = serialize(lead)
    lead.owner_employee_id = owner.id
    lead.assigned_employee_id = owner.id
    lead.assigned_to = _employee_name(owner)
    lead.manager_employee_id = _manager_id(owner)
    lead.status = "Assigned"
    db.flush()
    after = serialize(lead)
    _audit(db, user, "crm.lead.assigned", "CRMLead", lead.id, before, after)
    _event(db, user, "crm.lead.assigned", {"lead_id": lead.id, "owner_employee_id": owner.id}, "HRMS Employees")
    _notify(db, user, "Lead assigned", f"{lead.contact_name} has been assigned to {_employee_name(owner)}.", lead.id, _employee_name(owner))
    db.commit()
    return after


@router.post("/crm/leads/{lead_id}/qualify")
def qualify_lead(
    lead_id: UUID,
    payload: dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    lead = _get_or_404(db, CRMLead, lead_id, "Lead")
    if not lead.owner_employee_id and not lead.assigned_to:
        raise HTTPException(status_code=422, detail="Lead must have an active owner before qualification")
    before = serialize(lead)
    disqualified = bool(payload.get("disqualified"))
    if disqualified:
        reason = payload.get("reason") or payload.get("disqualification_reason")
        if not reason:
            raise HTTPException(status_code=422, detail="Disqualification reason is required")
        lead.status = "Lost"
        lead.qualification_status = "disqualified"
        lead.disqualification_reason = str(reason)
    else:
        score = sum(int(bool(payload.get(field))) * weight for field, weight in {
            "need": 25,
            "budget": 25,
            "authority": 25,
            "timeline": 15,
            "solution_interest": 10,
        }.items())
        explicit_score = payload.get("lead_score")
        lead.lead_score = int(explicit_score if explicit_score is not None else score)
        lead.status = "Qualified"
        lead.qualification_status = "qualified"
    db.flush()
    after = serialize(lead)
    _audit(db, user, "crm.lead.qualified" if not disqualified else "crm.lead.disqualified", "CRMLead", lead.id, before, after)
    _event(db, user, "crm.lead.qualified" if not disqualified else "crm.lead.disqualified", {"lead_id": lead.id, "score": lead.lead_score})
    db.commit()
    return after


@router.post("/crm/leads/{lead_id}/convert")
def convert_qualified_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    lead = _get_or_404(db, CRMLead, lead_id, "Lead")
    if (lead.qualification_status or "").lower() != "qualified" and (lead.status or "").lower() != "qualified":
        raise HTTPException(status_code=422, detail="Only qualified leads can be converted")
    result = convert_lead(db, lead, user)
    _event(db, user, "crm.lead.converted", {"lead_id": lead.id, "result": result}, "Projects")
    return result


@router.post("/crm/accounts/{account_id}/team-members", status_code=status.HTTP_201_CREATED)
def add_account_team_member(
    account_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    account = _get_or_404(db, CRMAccount, account_id, "Account")
    employee_id = payload.get("employee_id") or payload.get("owner_employee_id")
    if not employee_id:
        raise HTTPException(status_code=422, detail="employee_id is required")
    employee = _active_employee(db, UUID(str(employee_id)), "Account team member", require_crm_role=False)
    before = serialize(account)
    role = str(payload.get("team_role") or "Account Team Member")
    if role.lower() in {"account manager", "account_manager"}:
        account.owner_employee_id = employee.id
        account.account_manager = _employee_name(employee)
    account.notes = f"{account.notes or ''}\nTeam: {role} - {_employee_name(employee)}".strip()
    db.flush()
    after = serialize(account)
    _audit(db, user, "crm.account.team_member_added", "CRMAccount", account.id, before, after)
    _event(db, user, "crm.account.team_member_added", {"account_id": account.id, "employee_id": employee.id, "role": role}, "HRMS Employees")
    db.commit()
    return {"account": after, "team_member": {"employee_id": str(employee.id), "name": _employee_name(employee), "role": role}}


@router.post("/crm/opportunities/{opportunity_id}/assign-presales")
def assign_presales(
    opportunity_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    employee_id = payload.get("presales_employee_id") or payload.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=422, detail="presales_employee_id is required")
    engineer = _active_employee(db, UUID(str(employee_id)), "Presales engineer", TECHNICAL_DEPARTMENTS)
    opportunity = _get_or_404(db, CRMOpportunity, opportunity_id, "Opportunity")
    before = serialize(opportunity)
    opportunity.presales_employee_id = engineer.id
    task = CRMTask(
        title=f"Presales support: {opportunity.title}",
        description=payload.get("scope") or "Review opportunity and provide presales support.",
        related_type="opportunity",
        related_id=opportunity.id,
        assigned_to=_employee_name(engineer),
        assigned_employee_id=engineer.id,
        priority="high",
        status="pending",
        due_date=payload.get("due_date"),
    )
    db.add(task)
    db.flush()
    after = serialize(opportunity)
    _audit(db, user, "crm.presales.assigned", "CRMOpportunity", opportunity.id, before, after)
    _event(db, user, "crm.presales.assigned", {"opportunity_id": opportunity.id, "employee_id": engineer.id, "task_id": task.id}, "HRMS Employees")
    db.commit()
    return {"opportunity": after, "task": serialize(task)}


@router.post("/crm/opportunities/{opportunity_id}/stage")
def update_opportunity_stage(
    opportunity_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    stage = CRM_STAGE_ALIASES.get(str(payload.get("stage") or ""), payload.get("stage"))
    if stage not in CRM_STAGES:
        raise HTTPException(status_code=422, detail="Invalid CRM opportunity stage")
    opportunity = _get_or_404(db, CRMOpportunity, opportunity_id, "Opportunity")
    if stage == "Proposal":
        has_quote = db.query(CRMQuotation).filter(CRMQuotation.opportunity_id == opportunity.id, CRMQuotation.soft_deleted.is_(False)).first()
        if not has_quote:
            raise HTTPException(status_code=422, detail="Moving to Proposal requires a quotation")
    if stage in {"Won", "Stage 6.a Closed as Won"} and not (payload.get("lpo_document_url") or opportunity.lpo_document_url):
        raise HTTPException(status_code=422, detail="LPO or contract confirmation is required before marking won")
    if stage in {"Lost", "Stage 6.b Closed as Lost"} and not (payload.get("loss_reason") or payload.get("reason")):
        raise HTTPException(status_code=422, detail="Lost opportunity requires a loss reason")
    before = serialize(opportunity)
    opportunity.stage = str(stage)
    if stage in {"Lost", "Stage 6.b Closed as Lost"}:
        opportunity.status = "closed_lost"
        opportunity.stage = "Stage 6.b Closed as Lost"
        opportunity.win_loss_reason = str(payload.get("loss_reason") or payload.get("reason"))
        opportunity.actual_close_date = date.today()
        opportunity.closed_at = datetime.now(timezone.utc)
    elif stage in {"Won", "Stage 6.a Closed as Won"}:
        opportunity.status = "closed_won"
        opportunity.stage = "Stage 6.a Closed as Won"
        opportunity.lpo_document_url = payload.get("lpo_document_url") or opportunity.lpo_document_url
        opportunity.actual_close_date = date.today()
        opportunity.closed_at = datetime.now(timezone.utc)
    db.flush()
    after = serialize(opportunity)
    _audit(db, user, "crm.opportunity.stage_changed", "CRMOpportunity", opportunity.id, before, after)
    _event(db, user, "crm.opportunity.stage_changed", {"opportunity_id": opportunity.id, "stage": stage})
    db.commit()
    return after


@router.post("/crm/opportunities/{opportunity_id}/mark-won")
def mark_opportunity_won(
    opportunity_id: UUID,
    payload: dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    opportunity = _get_or_404(db, CRMOpportunity, opportunity_id, "Opportunity")
    if not (payload.get("lpo_document_url") or opportunity.lpo_document_url):
        raise HTTPException(status_code=422, detail="LPO or contract confirmation is required before marking won")
    before = serialize(opportunity)
    opportunity.status = "closed_won"
    opportunity.stage = "Stage 6.a Closed as Won"
    opportunity.lpo_document_url = payload.get("lpo_document_url") or opportunity.lpo_document_url
    opportunity.actual_close_date = date.today()
    opportunity.closed_at = datetime.now(timezone.utc)
    db.flush()
    after = serialize(opportunity)
    _audit(db, user, "crm.opportunity.won", "CRMOpportunity", opportunity.id, before, after)
    _event(db, user, "crm.opportunity.won", {"opportunity_id": opportunity.id}, "Projects")
    db.commit()
    return after


@router.post("/crm/opportunities/{opportunity_id}/mark-lost")
def mark_opportunity_lost(
    opportunity_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    reason = payload.get("loss_reason") or payload.get("reason")
    if not reason:
        raise HTTPException(status_code=422, detail="Loss reason is required")
    return workflow(db, "opportunities", opportunity_id, "close-lost", user, {"loss_reason": reason})


@router.post("/crm/quotations/{quotation_id}/approve")
def approve_quotation(quotation_id: UUID, payload: dict[str, Any] = Body(default={}), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    result = workflow(db, "quotations", quotation_id, "approve", user, payload)
    _event(db, user, "crm.quotation.approved", {"quotation_id": quotation_id}, "Finance")
    return result


@router.post("/crm/quotations/{quotation_id}/reject")
def reject_quotation(quotation_id: UUID, payload: dict[str, Any] = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    if not (payload.get("reason") or payload.get("rejection_reason")):
        raise HTTPException(status_code=422, detail="Rejection reason is required")
    return workflow(db, "quotations", quotation_id, "reject", user, payload)


@router.post("/crm/quotations/{quotation_id}/send")
def send_quotation(quotation_id: UUID, payload: dict[str, Any] = Body(default={}), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    quote = _get_or_404(db, CRMQuotation, quotation_id, "Quotation")
    if quote.approval_status not in {"approved", "not_required"} and quote.status != "approved":
        raise HTTPException(status_code=422, detail="Only approved quotations can be sent")
    before = serialize(quote)
    quote.status = "sent"
    db.flush()
    after = serialize(quote)
    _audit(db, user, "crm.quotation.sent", "CRMQuotation", quote.id, before, after)
    _event(db, user, "crm.quotation.sent", {"quotation_id": quote.id}, "Documents")
    db.commit()
    return after


@router.post("/crm/quotations/{quotation_id}/revise")
def revise_quotation(quotation_id: UUID, payload: dict[str, Any] = Body(...), db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Revision reason is required")
    return workflow(db, "quotations", quotation_id, "revise", user, payload)


@router.post("/crm/opportunities/{opportunity_id}/upload-lpo")
def upload_lpo_reference(
    opportunity_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    opportunity = _get_or_404(db, CRMOpportunity, opportunity_id, "Opportunity")
    account_id = payload.get("account_id") or opportunity.account_id
    if not account_id:
        raise HTTPException(status_code=422, detail="LPO requires an account")
    document_url = payload.get("document_url") or payload.get("lpo_document_url")
    if not document_url:
        raise HTTPException(status_code=422, detail="LPO document reference is required")
    before = serialize(opportunity)
    lpo = CRMCustomerLPO(
        lpo_number=str(payload.get("lpo_number") or f"LPO-{str(opportunity.id)[:8]}"),
        account_id=UUID(str(account_id)),
        opportunity_id=opportunity.id,
        quotation_id=UUID(str(payload["quotation_id"])) if payload.get("quotation_id") else None,
        lpo_date=payload.get("lpo_date") or date.today(),
        total_amount=payload.get("total_amount") or opportunity.opportunity_value or 0,
        document_url=str(document_url),
        uploaded_by=user.full_name,
        validation_status="received",
        status="received",
    )
    db.add(lpo)
    opportunity.lpo_document_url = str(document_url)
    opportunity.stage = "Awaiting LPO"
    db.flush()
    after = serialize(opportunity)
    _audit(db, user, "crm.lpo.received", "CRMOpportunity", opportunity.id, before, after)
    _event(db, user, "crm.lpo.received", {"opportunity_id": opportunity.id, "lpo_id": lpo.id}, "Finance")
    db.commit()
    return {"opportunity": after, "lpo": serialize(lpo)}


@router.post("/crm/opportunities/{opportunity_id}/handover-to-project")
def handover_to_project(
    opportunity_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    manager_id = payload.get("project_manager_employee_id")
    if not manager_id:
        raise HTTPException(status_code=422, detail="project_manager_employee_id is required")
    manager = _active_employee(db, UUID(str(manager_id)), "Project manager", require_crm_role=False)
    opportunity = _get_or_404(db, CRMOpportunity, opportunity_id, "Opportunity")
    if opportunity.status != "closed_won":
        raise HTTPException(status_code=422, detail="Only won opportunities can be handed over to Projects")
    if not opportunity.lpo_document_url:
        raise HTTPException(status_code=422, detail="Project handover requires LPO or contract document")
    before = serialize(opportunity)
    opportunity.project_manager_employee_id = manager.id
    opportunity.handover_status = "project_handover_requested"
    db.flush()
    after = serialize(opportunity)
    _audit(db, user, "crm.project_handover.requested", "CRMOpportunity", opportunity.id, before, after)
    _event(db, user, "crm.project_handover.requested", {"opportunity_id": opportunity.id, "project_manager_employee_id": manager.id}, "Projects")
    db.commit()
    return after


@router.post("/crm/opportunities/{opportunity_id}/customer-success-handover")
def customer_success_handover(
    opportunity_id: UUID,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    notes = payload.get("handover_notes")
    if not notes:
        raise HTTPException(status_code=422, detail="Handover notes are required")
    cs_owner = _active_employee(db, UUID(str(payload["customer_success_owner_employee_id"])), "Customer success owner", require_crm_role=False)
    tech_owner = _active_employee(db, UUID(str(payload["technical_owner_employee_id"])), "Technical owner", require_crm_role=False)
    opportunity = _get_or_404(db, CRMOpportunity, opportunity_id, "Opportunity")
    before = serialize(opportunity)
    opportunity.customer_success_owner_employee_id = cs_owner.id
    opportunity.technical_owner_employee_id = tech_owner.id
    opportunity.handover_status = "customer_success_handover_created"
    opportunity.description = f"{opportunity.description or ''}\nCustomer Success Handover: {notes}".strip()
    db.flush()
    after = serialize(opportunity)
    _audit(db, user, "crm.customer_success_handover.created", "CRMOpportunity", opportunity.id, before, after)
    _event(db, user, "crm.customer_success_handover.created", {"opportunity_id": opportunity.id, "customer_success_owner_employee_id": cs_owner.id}, "Projects")
    db.commit()
    return after


@router.get("/crm/analytics/dashboard")
def crm_dashboard(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    leads_by_status = dict(db.query(CRMLead.status, func.count(CRMLead.id)).group_by(CRMLead.status).all())
    opportunities_by_stage = dict(db.query(CRMOpportunity.stage, func.count(CRMOpportunity.id)).group_by(CRMOpportunity.stage).all())
    pipeline_value = sum(Decimal(str(row.opportunity_value or 0)) for row in db.query(CRMOpportunity).filter(CRMOpportunity.status == "open").all())
    won_value = sum(Decimal(str(row.opportunity_value or 0)) for row in db.query(CRMOpportunity).filter(CRMOpportunity.status == "closed_won").all())
    lost_value = sum(Decimal(str(row.opportunity_value or 0)) for row in db.query(CRMOpportunity).filter(CRMOpportunity.status == "closed_lost").all())
    pending_quotes = db.query(CRMQuotation).filter(CRMQuotation.approval_status.in_(["pending", "draft"])).count()
    overdue_tasks = db.query(CRMTask).filter(CRMTask.status != "completed", CRMTask.due_date < datetime.now(timezone.utc)).count()
    sales_by_employee = [
        {"employee": owner or "Unassigned", "opportunities": count, "value": float(value or 0)}
        for owner, count, value in db.query(CRMOpportunity.owner, func.count(CRMOpportunity.id), func.coalesce(func.sum(CRMOpportunity.opportunity_value), 0)).group_by(CRMOpportunity.owner).all()
    ]
    total_leads = db.query(CRMLead).count()
    converted = db.query(CRMLead).filter(CRMLead.converted.is_(True)).count()
    return {
        "leads_by_status": leads_by_status,
        "opportunities_by_stage": opportunities_by_stage,
        "pipeline_value": float(pipeline_value),
        "won_value": float(won_value),
        "lost_value": float(lost_value),
        "quotations_pending_approval": pending_quotes,
        "tasks_overdue": overdue_tasks,
        "sales_by_employee": sales_by_employee,
        "conversion_rate": round((converted / total_leads) * 100, 2) if total_leads else 0,
        "forecast_revenue": float(pipeline_value),
    }


@router.get("/crm/audit-logs")
def list_crm_audit_logs(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    rows = db.query(CRMAuditLog).order_by(CRMAuditLog.created_at.desc()).limit(300).all()
    return [serialize(row) for row in rows]
