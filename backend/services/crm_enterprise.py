from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.api.crud import assign_business_id
from backend.models.crm import (
    CRMAccount,
    CRMActivity,
    CRMAuditLog,
    CRMCampaign,
    CRMCampaignResponse,
    CRMContact,
    CRMContract,
    CRMLead,
    CRMOpportunity,
    CRMPriceBook,
    CRMProductService,
    CRMCustomerLPO,
    CRMQuotation,
    CRMQuoteLineItem,
    CRMTask,
    CRMTicket,
    CRMApprovalRule,
    CRMPipelineStageRule,
)
from backend.models.hrm import HRMEmployee
from backend.policies.crm import require_crm_access
from backend.policies.crm import is_admin, is_manager, owner_matches, is_shared
from backend.schemas.auth import UserResponse


RESOURCE_MAP = {
    "accounts": CRMAccount,
    "contacts": CRMContact,
    "leads": CRMLead,
    "opportunities": CRMOpportunity,
    "activities": CRMActivity,
    "tasks": CRMTask,
    "quotations": CRMQuotation,
    "quote-line-items": CRMQuoteLineItem,
    "lpos": CRMCustomerLPO,
    "customer-lpos": CRMCustomerLPO,
    "products": CRMProductService,
    "price-books": CRMPriceBook,
    "contracts": CRMContract,
    "tickets": CRMTicket,
    "campaigns": CRMCampaign,
    "campaign-responses": CRMCampaignResponse,
    "approval-rules": CRMApprovalRule,
    "pipeline-stage-rules": CRMPipelineStageRule,
    "audit-logs": CRMAuditLog,
}

DEFAULT_STAGES = [
    "Stage 1.a Discovery",
    "Stage 1.b Presentation/Demo/POC",
    "Stage 1.c RFP/Tender",
    "Stage 1.d Commit/Award",
    "Stage 2 Contracting & Legal Finalization",
    "Stage 3 Project Management Delivery & Implementation",
    "Stage 4 SLA Management & Support",
    "Stage 5 Renewal or Exit",
    "Stage 6.a Closed as Won",
    "Stage 6.b Closed as Lost",
]

LOCKED_STATUSES = {"closed_won", "accepted", "approved", "active", "locked"}
ACTIVE_EMPLOYEE_STATUSES = {"active", "confirmed", "on_probation", "probation", "pending_activation"}
BLOCKED_EMPLOYEE_STATUSES = {"inactive", "suspended", "terminated", "retired", "exited", "deceased", "archived", "blacklisted"}
SALES_DEPARTMENTS = {"sales", "presales", "business development", "business_development", "marketing"}
TECHNICAL_DEPARTMENTS = {"presales", "technical", "cybersecurity", "data", "infrastructure", "engineering", "solutions"}


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="CRM resource not found")
    return model


def serialize(row) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, UUID):
            value = str(value)
        result[column.name] = value
    return result


def clean_payload(model, data: dict[str, Any]) -> dict[str, Any]:
    columns = {column.name for column in model.__table__.columns}
    return {key: value for key, value in data.items() if key in columns and value not in ("", None)}


def employee_name(employee: HRMEmployee) -> str:
    return " ".join(part for part in [employee.first_name, employee.last_name] if part).strip() or employee.email or str(employee.id)


def active_employee(
    db: Session,
    employee_id: UUID | str,
    *,
    allowed_departments: set[str] | None = None,
) -> HRMEmployee:
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=422, detail="CRM employee reference must exist in HRMS")
    status_value = (employee.employment_status or employee.status or "").strip().lower()
    if status_value in BLOCKED_EMPLOYEE_STATUSES or status_value not in ACTIVE_EMPLOYEE_STATUSES:
        raise HTTPException(status_code=422, detail=f"{employee_name(employee)} is not an active employee and cannot own CRM work")
    if allowed_departments:
        tokens = {
            str(getattr(employee, field, "") or "").strip().lower()
            for field in ("department", "business_unit", "job_title", "role_category")
        }
        if not tokens & allowed_departments:
            raise HTTPException(status_code=422, detail=f"{employee_name(employee)} is not in an authorized CRM department or role")
    return employee


def duplicate_lead_reason(db: Session, data: dict[str, Any], exclude_id: UUID | str | None = None) -> str | None:
    query = db.query(CRMLead)
    if exclude_id:
        query = query.filter(CRMLead.id != exclude_id)
    if data.get("email") and query.filter(CRMLead.email == data["email"]).first():
        return "Email already exists in another lead"
    if data.get("phone") and query.filter(CRMLead.phone == data["phone"]).first():
        return "Phone already exists in another lead"
    if data.get("company_name") and query.filter(CRMLead.company_name.ilike(data["company_name"])).first():
        return "Company already exists in another lead"
    return None


def apply_hrms_links(db: Session, resource: str, data: dict[str, Any], record_id: UUID | str | None = None) -> dict[str, Any]:
    if resource in {"accounts", "leads"} and data.get("owner_employee_id"):
        owner = active_employee(db, data["owner_employee_id"], allowed_departments=SALES_DEPARTMENTS)
        if resource == "accounts":
            data["account_manager"] = employee_name(owner)
            data["relationship_owner"] = data.get("relationship_owner") or employee_name(owner)
            data["manager_employee_id"] = getattr(owner, "supervisor_id", None)
        else:
            data["assigned_to"] = employee_name(owner)
            data["assigned_employee_id"] = data.get("assigned_employee_id") or data["owner_employee_id"]
            data["manager_employee_id"] = getattr(owner, "supervisor_id", None)
    if resource == "contacts" and data.get("owner_employee_id"):
        active_employee(db, data["owner_employee_id"], allowed_departments=SALES_DEPARTMENTS)
    if resource == "opportunities":
        if data.get("owner_employee_id"):
            owner = active_employee(db, data["owner_employee_id"], allowed_departments=SALES_DEPARTMENTS)
            data["owner"] = employee_name(owner)
            data["manager_employee_id"] = getattr(owner, "supervisor_id", None)
        if data.get("presales_employee_id"):
            active_employee(db, data["presales_employee_id"], allowed_departments=TECHNICAL_DEPARTMENTS)
        if data.get("project_manager_employee_id"):
            active_employee(db, data["project_manager_employee_id"])
        if data.get("customer_success_owner_employee_id"):
            active_employee(db, data["customer_success_owner_employee_id"])
        if data.get("technical_owner_employee_id"):
            active_employee(db, data["technical_owner_employee_id"], allowed_departments=TECHNICAL_DEPARTMENTS)
    if resource == "tasks":
        if data.get("assigned_employee_id"):
            assignee = active_employee(db, data["assigned_employee_id"])
            data["assigned_to"] = employee_name(assignee)
        if data.get("owner_employee_id"):
            active_employee(db, data["owner_employee_id"])
    if resource == "quotations":
        if data.get("owner_employee_id"):
            owner = active_employee(db, data["owner_employee_id"], allowed_departments=SALES_DEPARTMENTS)
            data["created_by"] = data.get("created_by") or employee_name(owner)
        if data.get("approved_by_employee_id"):
            approver = active_employee(db, data["approved_by_employee_id"])
            data["approved_by"] = employee_name(approver)
    if resource == "leads":
        reason = duplicate_lead_reason(db, data, exclude_id=record_id)
        data["duplicate_flag"] = bool(reason)
        data["duplicate_reason"] = reason
    return data


def derived_hrms_fields(resource: str) -> set[str]:
    return {
        "accounts": {"account_manager", "relationship_owner", "manager_employee_id"},
        "leads": {"assigned_to", "assigned_employee_id", "manager_employee_id", "duplicate_flag", "duplicate_reason"},
        "opportunities": {"owner", "manager_employee_id"},
        "tasks": {"assigned_to"},
        "quotations": {"created_by", "approved_by"},
    }.get(resource, set())


def audit(db: Session, user: UserResponse | None, action: str, entity_type: str, entity_id: str | None, before=None, after=None) -> None:
    db.add(
        CRMAuditLog(
            actor_user_id=getattr(user, "id", None),
            actor_email=getattr(user, "email", None),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=f"{action} CRM {entity_type}",
            before_json=before,
            after_json=after,
        )
    )


def get_record(db: Session, resource: str, record_id: UUID):
    model = model_for(resource)
    row = db.query(model).filter(model.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="CRM record not found")
    return row


def list_records(db: Session, resource: str, user: UserResponse) -> list[dict[str, Any]]:
    model = model_for(resource)
    require_crm_access(db, user, "read", resource)
    query = db.query(model)
    if hasattr(model, "soft_deleted"):
        query = query.filter(model.soft_deleted.is_(False))
    if hasattr(model, "created_at"):
        query = query.order_by(model.created_at.desc())
    rows = query.all()
    if not is_admin(user) and not is_manager(user):
        rows = [
            row for row in rows
            if owner_matches(user, getattr(row, "owner", None) or getattr(row, "assigned_to", None) or getattr(row, "account_manager", None) or getattr(row, "created_by", None))
            or is_shared(db, user, resource, row.id)
        ]
    return [serialize(row) for row in rows]


def validate_required_relationships(db: Session, resource: str, data: dict[str, Any]) -> None:
    if resource == "opportunities" and not data.get("account_id"):
        raise HTTPException(status_code=422, detail="Every opportunity must belong to an account")
    if resource == "contacts" and not data.get("account_id") and not (data.get("unlinked_prospect") or data.get("tags") == "unlinked_prospect"):
        raise HTTPException(status_code=422, detail="Every contact must belong to an account unless marked as an unlinked prospect")
    if resource == "leads":
        missing = [field for field in ["lead_source", "assigned_to", "status"] if not data.get(field)]
        if missing:
            raise HTTPException(status_code=422, detail=f"Lead requires: {', '.join(missing)}")
    if resource == "quote-line-items":
        if not db.query(CRMProductService).filter(CRMProductService.id == data.get("product_service_id")).first():
            raise HTTPException(status_code=422, detail="Quote line item must reference a valid product or service")
    if resource == "contracts" and not data.get("account_id"):
        raise HTTPException(status_code=422, detail="Contract must be linked to an account")
    if resource in {"lpos", "customer-lpos"}:
        missing = [field for field in ["account_id", "lpo_number", "lpo_date", "total_amount"] if not data.get(field)]
        if missing:
            raise HTTPException(status_code=422, detail=f"Customer LPO requires: {', '.join(missing)}")
    if resource == "contracts" and data.get("opportunity_id"):
        opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == data.get("opportunity_id")).first()
        if opportunity and opportunity.status != "closed_won":
            raise HTTPException(status_code=422, detail="Contracts can only link to a won opportunity")
    if resource == "opportunities" and data.get("status") == "closed_lost" and not (data.get("win_loss_reason") or data.get("description")):
        raise HTTPException(status_code=422, detail="Closed-lost opportunities require a loss reason")


def create_record(db: Session, resource: str, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    require_crm_access(db, user, "create", resource)
    data = clean_payload(model, data)
    data = apply_hrms_links(db, resource, data)
    validate_required_relationships(db, resource, data)
    record = model(**data)
    if hasattr(record, "business_id"):
        assign_business_id(db, model, record)
    if resource == "quote-line-items":
        calculate_quote_line(record)
    if resource == "tickets":
        calculate_ticket_sla(record)
    db.add(record)
    db.flush()
    if resource == "quote-line-items":
        recalculate_quote(db, record.quotation_id)
    after = serialize(record)
    audit(db, user, "create", resource, str(record.id), after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def update_record(db: Session, resource: str, record_id: UUID, data: dict[str, Any], user: UserResponse) -> dict[str, Any]:
    model = model_for(resource)
    record = get_record(db, resource, record_id)
    require_crm_access(db, user, "update", resource, record)
    if resource == "opportunities" and getattr(record, "status", "") == "closed_won":
        raise HTTPException(status_code=423, detail="Closed-won opportunities are locked from normal editing")
    if resource == "quotations" and getattr(record, "status", "") in {"approved", "accepted"}:
        raise HTTPException(status_code=423, detail="Approved quotes require a new version")
    before = serialize(record)
    data = clean_payload(model, data)
    original_keys = set(data.keys())
    normalized = apply_hrms_links(db, resource, {**before, **data}, record_id=record_id)
    allowed_columns = {column.name for column in model.__table__.columns}
    update_keys = (original_keys | derived_hrms_fields(resource)) & allowed_columns
    update_keys -= {"id", "created_at", "updated_at", "deleted_at"}
    data = {key: normalized[key] for key in update_keys if normalized.get(key) not in ("", None)}
    validate_required_relationships(db, resource, {**before, **data})
    for key, value in data.items():
        setattr(record, key, value)
    if resource == "quote-line-items":
        calculate_quote_line(record)
        db.flush()
        recalculate_quote(db, record.quotation_id)
    if resource == "tickets":
        calculate_ticket_sla(record)
    db.flush()
    after = serialize(record)
    audit(db, user, "update", resource, str(record.id), before=before, after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def delete_record(db: Session, resource: str, record_id: UUID, user: UserResponse) -> None:
    record = get_record(db, resource, record_id)
    require_crm_access(db, user, "delete", resource, record)
    before = serialize(record)
    if hasattr(record, "soft_deleted"):
        record.soft_deleted = True
        record.deleted_at = datetime.now(timezone.utc)
        if hasattr(record, "status"):
            record.status = "deleted"
    else:
        db.delete(record)
    audit(db, user, "delete", resource, str(record_id), before=before)
    db.commit()


def split_name(name: str) -> tuple[str, str]:
    parts = (name or "").strip().split()
    if not parts:
        return "Unknown", "Contact"
    return parts[0], " ".join(parts[1:]) if len(parts) > 1 else "Contact"


def convert_lead(db: Session, lead: CRMLead, user: UserResponse) -> dict[str, Any]:
    if lead.converted:
        raise HTTPException(status_code=409, detail="Lead has already been converted")
    if not lead.lead_source or not lead.assigned_to or not lead.status:
        raise HTTPException(status_code=422, detail="Lead source, owner, and status are required before conversion")

    account = db.query(CRMAccount).filter(CRMAccount.company_name.ilike(lead.company_name or lead.contact_name)).first()
    if not account:
        account = CRMAccount(
            company_name=lead.company_name or lead.contact_name,
            industry=lead.account_industry,
            website=lead.account_website,
            address=lead.account_address,
            account_manager=lead.assigned_to,
            owner_employee_id=lead.owner_employee_id,
            manager_employee_id=lead.manager_employee_id,
            country=lead.account_country,
            region=lead.account_region,
            vertical=lead.account_vertical,
            account_type=lead.account_type,
            email=lead.email,
            phone=lead.phone,
            account_status="active",
        )
        assign_business_id(db, CRMAccount, account)
        db.add(account)
        db.flush()

    first_name, last_name = split_name(lead.contact_name)
    contact = None
    if lead.email:
        contact = db.query(CRMContact).filter(CRMContact.account_id == account.id, CRMContact.email == lead.email).first()
    if not contact:
        contact = CRMContact(
            account_id=account.id,
            first_name=first_name,
            last_name=last_name,
            job_title=lead.contact_job_title,
            department=lead.contact_department,
            email=lead.email,
            phone=lead.phone,
            tags="primary",
            notes=f"Converted from lead {lead.business_id or lead.id}",
            owner_employee_id=lead.owner_employee_id,
        )
        db.add(contact)
        db.flush()

    opportunity = CRMOpportunity(
        account_id=account.id,
        title=f"{account.company_name} - {lead.service_scope or lead.arena or 'Opportunity'}",
        stage="Stage 1.a Discovery",
        opportunity_value=lead.estimated_value or 0,
        probability=10,
        expected_close_date=lead.expected_close_date,
        renewal_date=lead.expected_renewal_date,
        owner=lead.assigned_to,
        owner_employee_id=lead.owner_employee_id,
        manager_employee_id=lead.manager_employee_id,
        country=lead.account_country,
        vertical=lead.account_vertical,
        pipeline_type=lead.pipeline_type,
        arena=lead.arena,
        service_scope=lead.service_scope,
        status="open",
    )
    assign_business_id(db, CRMOpportunity, opportunity)
    db.add(opportunity)
    lead.converted = True
    lead.converted_account_id = account.id
    lead.converted_contact_id = contact.id
    lead.converted_opportunity_id = opportunity.id
    lead.status = "Converted"
    lead.qualification_status = "converted"
    db.flush()
    audit(db, user, "convert", "leads", str(lead.id), after={"account_id": str(account.id), "contact_id": str(contact.id), "opportunity_id": str(opportunity.id)})
    db.commit()
    return {"account": serialize(account), "contact": serialize(contact), "opportunity": serialize(opportunity), "lead": serialize(lead)}


def valid_stages(db: Session) -> list[str]:
    rows = db.query(CRMPipelineStageRule).filter(CRMPipelineStageRule.status == "active").order_by(CRMPipelineStageRule.stage_order).all()
    return [row.stage_name for row in rows] or DEFAULT_STAGES


def calculate_quote_line(line: CRMQuoteLineItem) -> None:
    gross = Decimal(str(line.quantity or 0)) * Decimal(str(line.unit_price or 0))
    discount = gross * (Decimal(str(line.discount_percent or 0)) / Decimal("100"))
    tax = (gross - discount) * (Decimal(str(line.tax_percent or 0)) / Decimal("100"))
    line.line_total = gross - discount + tax


def recalculate_quote(db: Session, quote_id: UUID) -> None:
    lines = db.query(CRMQuoteLineItem).filter(CRMQuoteLineItem.quotation_id == quote_id).all()
    subtotal = sum((Decimal(str(line.quantity or 0)) * Decimal(str(line.unit_price or 0)) for line in lines), Decimal("0"))
    discount_total = sum(
        (
            Decimal(str(line.quantity or 0))
            * Decimal(str(line.unit_price or 0))
            * (Decimal(str(line.discount_percent or 0)) / Decimal("100"))
            for line in lines
        ),
        Decimal("0"),
    )
    tax_total = sum(
        (
            (Decimal(str(line.quantity or 0)) * Decimal(str(line.unit_price or 0)))
            * (Decimal("1") - (Decimal(str(line.discount_percent or 0)) / Decimal("100")))
            * (Decimal(str(line.tax_percent or 0)) / Decimal("100"))
            for line in lines
        ),
        Decimal("0"),
    )
    total = subtotal - discount_total + tax_total
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quote_id).first()
    if quote:
        quote.subtotal = subtotal
        quote.discount_amount = discount_total
        quote.tax_amount = tax_total
        quote.total_amount = total


def calculate_ticket_sla(ticket: CRMTicket) -> None:
    opened_at = ticket.opened_at or datetime.now(timezone.utc)
    priority = (ticket.severity or "medium").lower()
    response_hours = {"critical": 1, "high": 4, "medium": 8, "low": 24}.get(priority, 8)
    resolution_hours = {"critical": 4, "high": 24, "medium": 72, "low": 120}.get(priority, 72)
    ticket.response_due_at = ticket.response_due_at or opened_at + timedelta(hours=response_hours)
    ticket.resolution_due_at = ticket.resolution_due_at or opened_at + timedelta(hours=resolution_hours)
    now = ticket.resolved_at or datetime.now(timezone.utc)
    ticket.sla_status = "breached" if ticket.resolution_due_at and now > ticket.resolution_due_at and ticket.status not in {"closed"} else "on_track"


def quote_requires_approval(db: Session, quote: CRMQuotation) -> bool:
    rules = db.query(CRMApprovalRule).filter(CRMApprovalRule.status == "active", CRMApprovalRule.module.in_(["quote", "discount"])).all()
    for rule in rules:
        amount_threshold = Decimal(str(rule.threshold_amount or 0))
        discount_threshold = Decimal(str(rule.discount_threshold_percent or 0))
        if amount_threshold > 0 and Decimal(str(quote.total_amount or 0)) >= amount_threshold:
            return True
        if discount_threshold > 0 and Decimal(str(quote.subtotal or 0)) and Decimal(str(quote.discount_amount or 0)) / Decimal(str(quote.subtotal or 1)) * Decimal("100") >= discount_threshold:
            return True
    return False


def workflow(db: Session, resource: str, record_id: UUID, action: str, user: UserResponse, payload: dict[str, Any] | None = None):
    payload = payload or {}
    record = get_record(db, resource, record_id)
    require_crm_access(db, user, action, resource, record)
    before = serialize(record)

    if resource == "leads":
        if action == "convert":
            return convert_lead(db, record, user)
        record.status = {"assign": "Assigned", "qualify": "Qualified", "disqualify": "Disqualified"}.get(action, record.status)
        if action == "qualify":
            record.qualification_status = "qualified"
        if action == "disqualify":
            record.qualification_status = "disqualified"
        if action == "assign":
            if payload.get("owner_employee_id"):
                owner = active_employee(db, payload["owner_employee_id"], allowed_departments=SALES_DEPARTMENTS)
                record.owner_employee_id = owner.id
                record.assigned_employee_id = owner.id
                record.manager_employee_id = getattr(owner, "supervisor_id", None)
                record.assigned_to = employee_name(owner)
            elif payload.get("owner"):
                record.assigned_to = payload["owner"]
    elif resource == "opportunities":
        if action == "move-stage":
            stage = payload.get("stage")
            if stage not in valid_stages(db):
                raise HTTPException(status_code=422, detail="Invalid pipeline stage")
            if payload.get("lpo_document_url"):
                record.lpo_document_url = payload["lpo_document_url"]
            if stage == "Stage 6.a Closed as Won" and not getattr(record, "lpo_document_url", None):
                raise HTTPException(status_code=422, detail="Won opportunities require LPO or contract confirmation")
            record.stage = stage
            if stage == "Stage 6.a Closed as Won":
                record.status = "closed_won"
                record.actual_close_date = date.today()
                record.closed_at = datetime.now(timezone.utc)
            elif stage == "Stage 6.b Closed as Lost":
                reason = payload.get("loss_reason") or payload.get("reason")
                if not reason:
                    raise HTTPException(status_code=422, detail="Closed-lost opportunities require a loss reason")
                record.status = "closed_lost"
                record.win_loss_reason = reason
                record.actual_close_date = date.today()
                record.closed_at = datetime.now(timezone.utc)
        elif action == "close-won":
            if payload.get("lpo_document_url"):
                record.lpo_document_url = payload["lpo_document_url"]
            if not getattr(record, "lpo_document_url", None):
                raise HTTPException(status_code=422, detail="Won opportunities require LPO or contract confirmation")
            record.status = "closed_won"
            record.stage = "Stage 6.a Closed as Won"
            record.actual_close_date = date.today()
            record.closed_at = datetime.now(timezone.utc)
        elif action == "close-lost":
            reason = payload.get("loss_reason") or payload.get("reason")
            if not reason:
                raise HTTPException(status_code=422, detail="Closed-lost opportunities require a loss reason")
            record.status = "closed_lost"
            record.stage = "Stage 6.b Closed as Lost"
            record.win_loss_reason = reason
            record.actual_close_date = date.today()
            record.closed_at = datetime.now(timezone.utc)
            record.description = f"{record.description or ''}\nLoss reason: {reason}".strip()
        elif action == "reopen":
            record.status = "open"
    elif resource == "quotations":
        if action == "accept" and record.valid_until and record.valid_until < date.today():
            raise HTTPException(status_code=422, detail="Expired quotes cannot be accepted")
        if action == "submit":
            record.approval_required = quote_requires_approval(db, record)
            record.approval_status = "pending" if record.approval_required else "not_required"
        elif action == "approve":
            record.approval_status = "approved"
            record.approved_by = user.full_name
        elif action == "reject":
            record.approval_status = "rejected"
        elif action == "revise":
            record.version_number = (record.version_number or 1) + 1
            record.approval_status = "draft"
        record.status = {"submit": "submitted", "approve": "approved", "reject": "rejected", "revise": "draft", "expire": "expired", "accept": "accepted"}.get(action, record.status)
    elif resource in {"lpos", "customer-lpos"}:
        if action == "approve":
            record.approval_status = "approved"
            record.status = "approved"
        elif action == "reject":
            record.approval_status = "rejected"
            record.status = "rejected"
        elif action == "submit":
            record.approval_status = "pending"
            record.status = "submitted"
        elif action == "cancel":
            record.status = "cancelled"
        else:
            raise HTTPException(status_code=422, detail="Unsupported LPO workflow action")
    elif resource == "contracts":
        record.status = {"activate": "active", "renew": "renewed", "terminate": "terminated", "expire": "expired"}.get(action, record.status)
    elif resource == "tickets":
        record.status = {"assign": "assigned", "escalate": "escalated", "resolve": "resolved", "close": "closed", "reopen": "open"}.get(action, record.status)
        if action == "escalate":
            record.escalated_at = datetime.now(timezone.utc)
        if action == "resolve":
            record.resolved_at = datetime.now(timezone.utc)
            record.resolution = payload.get("reason") or record.resolution
        calculate_ticket_sla(record)
    elif resource == "campaigns":
        record.status = {"launch": "launched", "pause": "paused", "complete": "completed"}.get(action, record.status)
    else:
        raise HTTPException(status_code=404, detail="Workflow action not supported for this resource")

    db.flush()
    after = serialize(record)
    audit(db, user, action, resource, str(record.id), before=before, after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def analytics_summary(db: Session) -> dict[str, Any]:
    open_pipeline = db.query(CRMOpportunity).filter(CRMOpportunity.status == "open").count()
    converted_leads = db.query(CRMLead).filter(CRMLead.converted.is_(True)).count()
    total_leads = db.query(CRMLead).count()
    won = db.query(CRMOpportunity).filter(CRMOpportunity.status == "closed_won").count()
    lost = db.query(CRMOpportunity).filter(CRMOpportunity.status == "closed_lost").count()
    tickets_open = db.query(CRMTicket).filter(CRMTicket.status.in_(["open", "assigned", "escalated"])).count()
    revenue_forecast = sum((row.opportunity_value or 0) for row in db.query(CRMOpportunity).filter(CRMOpportunity.status == "open").all())
    return {
        "accounts": db.query(CRMAccount).count(),
        "contacts": db.query(CRMContact).count(),
        "leads": {"total": total_leads, "converted": converted_leads, "conversion_rate": round((converted_leads / total_leads) * 100, 2) if total_leads else 0},
        "pipeline": {"open": open_pipeline, "forecast": float(revenue_forecast)},
        "win_loss": {"won": won, "lost": lost},
        "tickets": {"open": tickets_open},
        "campaigns": db.query(CRMCampaign).count(),
    }
