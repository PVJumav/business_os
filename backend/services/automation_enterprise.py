from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.models.automation import (
    AccessReview,
    ApprovalAction,
    ApprovalMatrix,
    ApprovalRequest,
    AuditLog,
    ComplianceControl,
    CorrectiveAction,
    EnterpriseEvent,
    EscalationRule,
    GovernancePolicy,
    KPI,
    KPIResult,
    PolicyAcknowledgement,
    PolicyCategory,
    PolicyException,
    PolicyVersion,
    RiskRegister,
    SLAInstance,
    SLAPolicy,
    SOP,
    SOPStep,
    UserAccessProfile,
    WorkflowInstance,
    WorkflowStage,
    WorkflowTask,
    WorkflowTemplate,
)
from backend.schemas.auth import UserResponse


RESOURCE_MAP = {
    "governance/categories": PolicyCategory,
    "governance/policies": GovernancePolicy,
    "governance/policy-versions": PolicyVersion,
    "governance/exceptions": PolicyException,
    "governance/acknowledgements": PolicyAcknowledgement,
    "sops": SOP,
    "sop-steps": SOPStep,
    "workflows/templates": WorkflowTemplate,
    "workflows/stages": WorkflowStage,
    "workflows/instances": WorkflowInstance,
    "workflows/tasks": WorkflowTask,
    "approvals/matrix": ApprovalMatrix,
    "approvals/requests": ApprovalRequest,
    "approvals/actions": ApprovalAction,
    "events": EnterpriseEvent,
    "audit/logs": AuditLog,
    "sla/policies": SLAPolicy,
    "sla/instances": SLAInstance,
    "escalations": EscalationRule,
    "iam/access-profiles": UserAccessProfile,
    "iam/access-reviews": AccessReview,
    "compliance/controls": ComplianceControl,
    "risk/register": RiskRegister,
    "kpis": KPI,
    "kpis/results": KPIResult,
    "corrective-actions": CorrectiveAction,
}

SEARCH_FIELDS = {
    "governance/categories": ["category_name", "owner_department"],
    "governance/policies": ["policy_code", "policy_name", "category", "owner_department", "policy_owner"],
    "governance/exceptions": ["exception_title", "department", "risk_level"],
    "sops": ["sop_code", "sop_name", "department", "owner"],
    "sop-steps": ["step_name", "responsible_role"],
    "workflows/templates": ["template_code", "template_name", "department", "trigger_event"],
    "workflows/instances": ["instance_number", "workflow_name", "source_module", "workflow_state", "owner"],
    "workflows/tasks": ["task_name", "assigned_role", "assigned_to", "priority"],
    "approvals/matrix": ["matrix_name", "process_name", "department", "approver_role"],
    "approvals/requests": ["request_number", "request_title", "module", "approver_role", "approver"],
    "events": ["event_key", "event_type", "source_module", "target_module", "event_status"],
    "audit/logs": ["user_email", "module", "action", "entity_type", "result"],
    "sla/policies": ["policy_name", "process_name", "department", "priority"],
    "sla/instances": ["module", "entity_type", "sla_status"],
    "escalations": ["rule_name", "process_name", "department", "escalate_to_role"],
    "iam/access-profiles": ["user_email", "department", "role_name", "provisioning_status"],
    "iam/access-reviews": ["review_name", "user_email", "reviewer", "review_status"],
    "compliance/controls": ["control_code", "control_name", "control_domain", "owner_department"],
    "risk/register": ["risk_code", "risk_title", "department", "risk_category", "owner"],
    "kpis": ["kpi_code", "kpi_name", "department", "owner", "linked_module"],
    "kpis/results": ["period_label", "approval_status"],
    "corrective-actions": ["action_title", "source_type", "department", "owner", "priority"],
}

WORKFLOW_STATES = {
    "draft": "Draft",
    "submit": "Submitted",
    "review": "Under Review",
    "approve": "Approved",
    "reject": "Rejected",
    "execute": "Executing",
    "wait-external": "Waiting for External Action",
    "escalate": "Escalated",
    "complete": "Completed",
    "close": "Closed",
    "cancel": "Cancelled",
}

SENSITIVE_ACTIONS = {"approve", "reject", "close", "delete", "escalate", "lock", "unlock", "provision", "deactivate"}
ADMIN_ROLES = {"admin", "super_admin", "auditor", "compliance_officer"}


def model_for(resource: str):
    model = RESOURCE_MAP.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Automation resource not found")
    return model


def serialize(row) -> dict[str, Any]:
    result = {}
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


def require_access(user: UserResponse, action: str, resource: str) -> None:
    role = str(user.role).lower()
    if action in SENSITIVE_ACTIONS and role not in ADMIN_ROLES and role not in {"manager", "finance_admin", "hr_admin", "hr_manager", "cfo"}:
        raise HTTPException(status_code=403, detail="Sensitive automation action requires elevated access")
    if resource.startswith("iam/") and role not in {"admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="IAM automation records require administrator access")


def audit(db: Session, user: UserResponse | None, module: str, action: str, entity_type: str, entity_id: UUID | None, before=None, after=None, result="success", failure_reason=None) -> None:
    db.add(
        AuditLog(
            user_email=getattr(user, "email", None),
            module=module,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=before,
            new_value=after,
            result=result,
            failure_reason=failure_reason,
            created_by=getattr(user, "email", None),
        )
    )


def validate(db: Session, resource: str, data: dict[str, Any], record: Any | None = None) -> None:
    if resource == "governance/policies":
        if not data.get("policy_name") or not data.get("owner_department"):
            raise HTTPException(status_code=422, detail="Policy name and owner department are required")
        existing = db.query(GovernancePolicy).filter(GovernancePolicy.policy_name == data["policy_name"], GovernancePolicy.soft_deleted.is_(False)).first()
        if existing and (not record or existing.id != record.id):
            raise HTTPException(status_code=409, detail="Duplicate active policy name")
    if resource == "sops":
        if not data.get("sop_name") or not data.get("department"):
            raise HTTPException(status_code=422, detail="SOP name and department are required")
        existing = db.query(SOP).filter(SOP.sop_name == data["sop_name"], SOP.department == data["department"], SOP.soft_deleted.is_(False)).first()
        if existing and (not record or existing.id != record.id):
            raise HTTPException(status_code=409, detail="Duplicate active SOP for department")
    if resource == "workflows/instances" and data.get("workflow_state") not in {None, *WORKFLOW_STATES.values()}:
        raise HTTPException(status_code=422, detail="Invalid workflow state")
    if resource == "approvals/requests" and not (data.get("approver") or data.get("approver_role")):
        raise HTTPException(status_code=422, detail="Approval request requires an approver or approver role")
    if resource == "kpis/results":
        target = Decimal(str(data.get("target_value") or 0))
        actual = Decimal(str(data.get("actual_value") or 0))
        data["achievement_percent"] = 0 if target == 0 else round((actual / target) * Decimal("100"), 2)


def list_records(db: Session, resource: str, user: UserResponse, query: str | None = None, status: str | None = None, limit: int = 200, offset: int = 0):
    require_access(user, "read", resource)
    model = model_for(resource)
    stmt = db.query(model)
    if hasattr(model, "soft_deleted"):
        stmt = stmt.filter(model.soft_deleted.is_(False))
    if status and hasattr(model, "status"):
        stmt = stmt.filter(model.status == status)
    if query:
        term = f"%{query}%"
        filters = [getattr(model, field).ilike(term) for field in SEARCH_FIELDS.get(resource, []) if hasattr(model, field)]
        if filters:
            stmt = stmt.filter(or_(*filters))
    if hasattr(model, "created_at"):
        stmt = stmt.order_by(model.created_at.desc())
    return [serialize(row) for row in stmt.offset(offset).limit(limit).all()]


def get_record(db: Session, resource: str, record_id: UUID):
    model = model_for(resource)
    record = db.query(model).filter(model.id == record_id).first()
    if not record or (hasattr(record, "soft_deleted") and record.soft_deleted):
        raise HTTPException(status_code=404, detail="Automation record not found")
    return record


def create_record(db: Session, resource: str, data: dict[str, Any], user: UserResponse):
    require_access(user, "create", resource)
    model = model_for(resource)
    data = clean_payload(model, data)
    validate(db, resource, data)
    if hasattr(model, "created_by"):
        data["created_by"] = data.get("created_by") or user.email
    record = model(**data)
    db.add(record)
    db.flush()
    after = serialize(record)
    audit(db, user, "automation", "create", resource, record.id, after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def update_record(db: Session, resource: str, record_id: UUID, data: dict[str, Any], user: UserResponse):
    require_access(user, "update", resource)
    model = model_for(resource)
    record = get_record(db, resource, record_id)
    before = serialize(record)
    data = clean_payload(model, data)
    validate(db, resource, {**before, **data}, record)
    for key, value in data.items():
        setattr(record, key, value)
    if hasattr(record, "updated_by"):
        record.updated_by = user.email
    db.flush()
    after = serialize(record)
    audit(db, user, "automation", "update", resource, record.id, before=before, after=after)
    db.commit()
    db.refresh(record)
    return serialize(record)


def delete_record(db: Session, resource: str, record_id: UUID, user: UserResponse):
    require_access(user, "delete", resource)
    record = get_record(db, resource, record_id)
    before = serialize(record)
    if hasattr(record, "soft_deleted"):
        record.soft_deleted = True
        record.deleted_at = datetime.now(timezone.utc)
        record.status = "deleted"
    else:
        db.delete(record)
    audit(db, user, "automation", "delete", resource, record_id, before=before)
    db.commit()


def workflow_action(db: Session, record_id: UUID, action: str, user: UserResponse, payload: dict[str, Any] | None = None):
    require_access(user, action, "workflows/instances")
    payload = payload or {}
    instance = get_record(db, "workflows/instances", record_id)
    if action not in WORKFLOW_STATES:
        raise HTTPException(status_code=422, detail="Invalid workflow action")
    if action in {"complete", "close"}:
        pending = db.query(WorkflowTask).filter(WorkflowTask.workflow_instance_id == instance.id, WorkflowTask.status.notin_(["completed", "closed", "cancelled", "deleted"])).count()
        if pending:
            raise HTTPException(status_code=422, detail="Workflow cannot close with pending tasks")
    before = serialize(instance)
    instance.workflow_state = WORKFLOW_STATES[action]
    if payload.get("current_stage"):
        instance.current_stage = payload["current_stage"]
    if action in {"complete", "close"}:
        instance.completed_at = datetime.now(timezone.utc)
    db.add(
        EnterpriseEvent(
            event_type=f"Workflow{WORKFLOW_STATES[action].replace(' ', '')}",
            source_module="automation",
            target_module=payload.get("target_module"),
            payload={"workflow_instance_id": str(instance.id), "action": action, **payload},
            event_status="processed",
            processed_by=user.email,
            processed_at=datetime.now(timezone.utc),
            created_by=user.email,
        )
    )
    audit(db, user, "workflow", action, "workflows/instances", instance.id, before=before, after=serialize(instance))
    db.commit()
    db.refresh(instance)
    return serialize(instance)


def approval_action(db: Session, request_id: UUID, action: str, user: UserResponse, comments: str | None = None):
    require_access(user, action, "approvals/requests")
    if action not in {"approve", "reject", "escalate", "cancel"}:
        raise HTTPException(status_code=422, detail="Invalid approval action")
    request = get_record(db, "approvals/requests", request_id)
    if request.requested_by and request.requested_by == user.email and action in {"approve", "reject"}:
        raise HTTPException(status_code=403, detail="Separation of duties: requester cannot approve or reject own request")
    before = serialize(request)
    request.approval_status = {"approve": "approved", "reject": "rejected", "escalate": "escalated", "cancel": "cancelled"}[action]
    request.comments = comments or request.comments
    db.add(ApprovalAction(approval_request_id=request.id, action=action, actor=user.email, comments=comments, created_by=user.email))
    audit(db, user, "approval", action, "approvals/requests", request.id, before=before, after=serialize(request))
    db.commit()
    db.refresh(request)
    return serialize(request)


def start_sla(db: Session, policy_id: UUID, payload: dict[str, Any], user: UserResponse):
    require_access(user, "create", "sla/instances")
    policy = get_record(db, "sla/policies", policy_id)
    now = datetime.now(timezone.utc)
    instance = SLAInstance(
        sla_policy_id=policy.id,
        workflow_instance_id=payload.get("workflow_instance_id"),
        module=payload.get("module"),
        entity_type=payload.get("entity_type"),
        entity_id=payload.get("entity_id"),
        starts_at=now,
        response_due_at=now + timedelta(minutes=policy.response_minutes or 0),
        resolution_due_at=now + timedelta(minutes=policy.resolution_minutes or 0),
        sla_status="running",
        created_by=user.email,
    )
    db.add(instance)
    db.flush()
    audit(db, user, "sla", "start", "sla/instances", instance.id, after=serialize(instance))
    db.commit()
    db.refresh(instance)
    return serialize(instance)


def dashboard(db: Session) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "governance": {
            "policies": db.query(GovernancePolicy).filter(GovernancePolicy.soft_deleted.is_(False)).count(),
            "pending_review": db.query(GovernancePolicy).filter(GovernancePolicy.review_date <= now.date(), GovernancePolicy.soft_deleted.is_(False)).count(),
            "exceptions": db.query(PolicyException).filter(PolicyException.approval_status == "pending", PolicyException.soft_deleted.is_(False)).count(),
            "compliance_controls": db.query(ComplianceControl).filter(ComplianceControl.soft_deleted.is_(False)).count(),
        },
        "sops": {
            "total": db.query(SOP).filter(SOP.soft_deleted.is_(False)).count(),
            "overdue_reviews": db.query(SOP).filter(SOP.review_date <= now.date(), SOP.soft_deleted.is_(False)).count(),
        },
        "workflows": {
            "active": db.query(WorkflowInstance).filter(WorkflowInstance.workflow_state.in_(["Submitted", "Under Review", "Executing", "Waiting for External Action", "Escalated"])).count(),
            "completed": db.query(WorkflowInstance).filter(WorkflowInstance.workflow_state.in_(["Completed", "Closed"])).count(),
            "escalated": db.query(WorkflowInstance).filter(WorkflowInstance.workflow_state == "Escalated").count(),
            "delayed": db.query(WorkflowInstance).filter(WorkflowInstance.due_at <= now, WorkflowInstance.workflow_state.notin_(["Completed", "Closed", "Cancelled"])).count(),
        },
        "approvals": {
            "pending": db.query(ApprovalRequest).filter(ApprovalRequest.approval_status == "pending").count(),
            "rejected": db.query(ApprovalRequest).filter(ApprovalRequest.approval_status == "rejected").count(),
            "overdue": db.query(ApprovalRequest).filter(ApprovalRequest.due_at <= now, ApprovalRequest.approval_status == "pending").count(),
        },
        "sla": {
            "running": db.query(SLAInstance).filter(SLAInstance.sla_status == "running").count(),
            "breached": db.query(SLAInstance).filter(SLAInstance.sla_status == "breached").count(),
            "near_breach": db.query(SLAInstance).filter(SLAInstance.resolution_due_at <= now + timedelta(hours=4), SLAInstance.sla_status == "running").count(),
        },
        "risk": {
            "high": db.query(RiskRegister).filter(RiskRegister.risk_score >= 8, RiskRegister.soft_deleted.is_(False)).count(),
            "corrective_actions": db.query(CorrectiveAction).filter(CorrectiveAction.action_status.in_(["open", "in_progress"])).count(),
        },
        "audit": {
            "events": db.query(EnterpriseEvent).count(),
            "audit_logs": db.query(AuditLog).count(),
        },
    }


def seed_defaults(db: Session) -> dict[str, int]:
    created = {"categories": 0, "policies": 0, "sops": 0, "templates": 0, "approval_rules": 0, "sla_policies": 0, "roles": 0, "kpis": 0, "risks": 0, "controls": 0}
    categories = [
        "Enterprise Governance", "Data Governance", "Information Security", "Finance Governance", "HR Governance",
        "Procurement Governance", "Sales Governance", "Legal Governance", "Project Governance", "Operations Governance",
        "Integration Governance", "Risk & Compliance",
    ]
    departments = ["HR", "Finance", "Sales", "Marketing", "Customer Desk", "Technical", "Projects", "Legal", "Operations", "Management"]
    for category in categories:
        if not db.query(PolicyCategory).filter(PolicyCategory.category_name == category).first():
            db.add(PolicyCategory(category_name=category, owner_department="Management", description=f"{category} policy category", created_by="system"))
            created["categories"] += 1
    policy_map = {
        "HR": ["Recruitment policy", "Employee onboarding policy", "Leave management policy", "Performance management policy", "Training policy", "Promotion and transfer policy", "Disciplinary policy", "Offboarding policy"],
        "Finance": ["Budget management policy", "Payroll policy", "Procurement payment policy", "Accounts payable policy", "Accounts receivable policy", "Expense approval policy", "Revenue recognition policy", "Financial reporting policy"],
        "Sales": ["Lead management policy", "Opportunity management policy", "Quotation policy", "Discount approval policy", "Customer onboarding policy", "Revenue forecasting policy"],
        "Marketing": ["Campaign approval policy", "Lead generation policy", "Brand approval policy", "Customer communication policy", "Event management policy", "Marketing budget policy"],
        "Customer Desk": ["Ticket management policy", "SLA policy", "Escalation policy", "Complaint handling policy", "Customer satisfaction policy"],
        "Technical": ["Account provisioning policy", "Asset allocation policy", "Infrastructure support policy", "Change management policy", "Incident response policy", "Security operations policy"],
        "Projects": ["Project initiation policy", "Resource allocation policy", "Milestone management policy", "Project budget policy", "Change request policy", "Project closure policy", "SLA transition policy"],
        "Legal": ["Contract management policy", "Legal review policy", "Risk assessment policy", "E-signature policy", "Contract renewal policy", "Compliance policy"],
        "Operations": ["Asset management policy", "Inventory management policy", "Vendor management policy", "Facilities policy", "Operational risk policy", "Business continuity policy"],
        "Management": ["Executive reporting policy", "KPI governance policy", "Strategic approval policy", "Enterprise risk review policy", "Governance committee policy"],
    }
    for department, names in policy_map.items():
        for name in names:
            if not db.query(GovernancePolicy).filter(GovernancePolicy.policy_name == name).first():
                db.add(GovernancePolicy(policy_code=f"POL-{department[:3].upper()}-{created['policies']+1:03d}", policy_name=name, category=f"{department} Governance", owner_department=department, policy_owner=f"{department} Owner", approval_status="approved", compliance_status="compliant", version="1.0", review_date=(datetime.now().date() + timedelta(days=180)), summary=f"Seeded {name} for Business OS 5.5", created_by="system"))
                created["policies"] += 1
    sop_templates = {
        "HR": ["Workforce request", "Recruitment", "Offer approval", "Employee onboarding", "Offboarding"],
        "Finance": ["Budget approval", "Payroll processing", "Invoice generation", "Payment approval", "Financial reconciliation"],
        "Sales": ["Lead creation", "Opportunity qualification", "Quotation creation", "Discount approval", "Contract initiation"],
        "Marketing": ["Campaign planning", "Lead handover to sales", "Campaign performance analytics"],
        "Customer Desk": ["Ticket creation", "SLA timer", "Escalation", "Resolution", "Root cause analysis"],
        "Technical": ["Account provisioning", "Access assignment", "Change request", "Incident handling"],
        "Projects": ["Project charter", "Resource assignment", "Milestone approval", "Go-live", "SLA activation"],
        "Legal": ["Contract drafting", "Legal review", "Risk scoring", "E-signature", "Contract archiving"],
        "Operations": ["Asset request", "Asset assignment", "Vendor onboarding", "Business continuity actions"],
        "Management": ["Executive dashboard", "KPI review", "Strategic approvals", "Risk review"],
    }
    for department, steps in sop_templates.items():
        name = f"{department} Operating SOP"
        sop = db.query(SOP).filter(SOP.sop_name == name).first()
        if not sop:
            sop = SOP(sop_code=f"SOP-{department[:3].upper()}", sop_name=name, department=department, owner=f"{department} Manager", review_date=datetime.now().date() + timedelta(days=180), required_evidence=["approval", "document", "audit trail"], description=f"Standard operating procedure for {department}", created_by="system")
            db.add(sop)
            db.flush()
            created["sops"] += 1
        if not db.query(SOPStep).filter(SOPStep.sop_id == sop.id).first():
            for index, step in enumerate(steps, start=1):
                db.add(SOPStep(sop_id=sop.id, step_order=index, step_name=step, responsible_role=f"{department} Officer", required_approval=index in {1, len(steps)}, sla_hours=24, created_by="system"))
    workflows = {
        "Hire-to-Retire": ["Workforce Planning", "Recruitment", "Candidate Evaluation", "Offer Management", "Contract Signing", "Employee Creation", "Account Provisioning", "Asset Allocation", "Payroll Activation", "KPI Assignment", "Training Assignment", "Performance Monitoring", "Promotion/Transfer", "Offboarding", "Account Deactivation", "Asset Recovery", "Final Settlement"],
        "Lead-to-Cash": ["Marketing Campaign", "Lead Creation", "Lead Scoring", "Sales Assignment", "Opportunity Qualification", "Presales Engagement", "Solution Design", "Quotation", "Margin Validation", "Discount Approval", "Contract Review", "Contract Signing", "Customer Creation", "Project Creation", "Procurement/Licensing", "Implementation", "Milestone Completion", "Invoice Generation", "Payment Tracking", "Revenue Recognition", "SLA Activation", "Support Handover", "Renewal/Upsell"],
        "Procure-to-Pay": ["Purchase Request", "Manager Approval", "Budget Validation", "Vendor Validation", "Legal Review", "Purchase Order", "Delivery", "Inspection", "Invoice Receipt", "Three-Way Matching", "Payment Approval", "Vendor Payment", "Audit Closure"],
        "Incident-to-Resolution": ["Incident Detection", "Ticket Creation", "Classification", "SLA Assignment", "Engineer Assignment", "Escalation", "Resolution", "Customer Confirmation", "Root Cause Analysis", "Corrective Action", "Closure"],
        "Project Implementation & SLA": ["Contract Signed", "Project Creation", "Project Charter", "Resource Allocation", "Task Planning", "Budget Allocation", "Procurement", "Implementation", "Milestone Review", "UAT", "Signoff", "Go-Live", "SLA Activation", "Health Checks", "Renewal Tracking"],
        "Contract Lifecycle": ["Contract Request", "Template Selection", "Drafting", "Legal Review", "Risk Assessment", "Finance Review", "Management Approval", "E-Signature", "Archive", "Renewal Reminder", "Amendment / Closure"],
        "Enterprise KPI Reporting": ["Data Collection", "Data Validation", "KPI Calculation", "Department Review", "Executive Dashboard", "Variance Analysis", "Corrective Action Assignment", "Progress Monitoring"],
    }
    for name, stages in workflows.items():
        template = db.query(WorkflowTemplate).filter(WorkflowTemplate.template_name == name).first()
        if not template:
            template = WorkflowTemplate(template_code=f"WFL-{created['templates']+1:03d}", template_name=name, department="Cross-Department", owner_department="Management", trigger_event=name.replace(" ", ""), description=f"Seeded enterprise workflow for {name}", created_by="system")
            db.add(template)
            db.flush()
            created["templates"] += 1
        if not db.query(WorkflowStage).filter(WorkflowStage.template_id == template.id).first():
            for index, stage in enumerate(stages, start=1):
                db.add(WorkflowStage(template_id=template.id, stage_order=index, stage_name=stage, approver_role="Manager" if "Approval" in stage or "Review" in stage else None, sla_hours=24, created_by="system"))
    approval_examples = [
        ("Recruitment approval", "HR", ["HR Manager", "Finance Manager", "Department Manager"]),
        ("Salary change", "HR", ["HR Manager", "Finance Manager", "Director"]),
        ("Procurement", "Finance", ["Manager", "Finance Manager", "Procurement Officer"]),
        ("Contract approval", "Legal", ["Legal Officer", "Executive"]),
        ("Discount approval", "Sales", ["Sales Manager", "Finance Manager"]),
        ("Budget overrun", "Projects", ["Finance Manager", "Executive"]),
        ("Project closure", "Projects", ["PMO", "Customer", "Finance Manager"]),
    ]
    for process, department, roles in approval_examples:
        for level, role in enumerate(roles, start=1):
            if not db.query(ApprovalMatrix).filter(ApprovalMatrix.process_name == process, ApprovalMatrix.approval_level == level, ApprovalMatrix.approver_role == role).first():
                db.add(ApprovalMatrix(matrix_name=f"{process} L{level}", process_name=process, department=department, approval_level=level, approver_role=role, dual_approval_required=level > 1, risk_level="medium", created_by="system"))
                created["approval_rules"] += 1
    sla_rules = [("Critical ticket response", "Customer Desk", "critical", 15, 240), ("High ticket response", "Customer Desk", "high", 60, 480), ("Medium ticket response", "Customer Desk", "medium", 240, 1440), ("Low ticket response", "Customer Desk", "low", 1440, 2880), ("Leave approval", "HR", "medium", 2880, 2880), ("Invoice approval", "Finance", "high", 1440, 1440), ("Account provisioning", "Technical", "high", 120, 120), ("Vendor onboarding", "Operations", "medium", 2400, 7200)]
    for name, department, priority, response, resolution in sla_rules:
        if not db.query(SLAPolicy).filter(SLAPolicy.policy_name == name).first():
            db.add(SLAPolicy(policy_name=name, process_name=name, department=department, priority=priority, response_minutes=response, resolution_minutes=resolution, escalation_role=f"{department} Manager", created_by="system"))
            created["sla_policies"] += 1
    roles = ["Super Admin", "Executive", "HR Manager", "HR Officer", "Finance Manager", "Finance Officer", "Sales Manager", "Sales Representative", "Marketing Manager", "Customer Desk Manager", "Support Agent", "Technical Manager", "Technical Engineer", "Project Manager", "Legal Officer", "Operations Manager", "Auditor", "Compliance Officer"]
    for role in roles:
        if not db.query(UserAccessProfile).filter(UserAccessProfile.user_email == f"{role.lower().replace(' ', '.')}@role.local").first():
            db.add(UserAccessProfile(user_email=f"{role.lower().replace(' ', '.')}@role.local", role_name=role, department=role.split()[0], access_level="role-template", privileged=role in {"Super Admin", "Executive", "Auditor", "Compliance Officer"}, provisioning_status="template", created_by="system"))
            created["roles"] += 1
    for department in departments:
        if not db.query(KPI).filter(KPI.kpi_name == f"{department} operating KPI").first():
            db.add(KPI(kpi_code=f"KPI-{department[:3].upper()}", kpi_name=f"{department} operating KPI", department=department, owner=f"{department} Manager", target_value=100, unit="score", linked_module=department, created_by="system"))
            created["kpis"] += 1
    for title in ["Overdue access review", "Unapproved vendor payment", "SLA breach concentration", "Policy exception backlog"]:
        if not db.query(RiskRegister).filter(RiskRegister.risk_title == title).first():
            db.add(RiskRegister(risk_code=f"RSK-{created['risks']+1:03d}", risk_title=title, department="Management", risk_category="Enterprise Risk", likelihood="medium", impact="high", risk_score=8, owner="Compliance Officer", mitigation_plan="Track through corrective action workflow", created_by="system"))
            created["risks"] += 1
    for name in ["Quarterly access review", "Policy acknowledgement", "Invoice approval evidence", "Contract legal review", "SLA breach RCA"]:
        if not db.query(ComplianceControl).filter(ComplianceControl.control_name == name).first():
            db.add(ComplianceControl(control_code=f"CTL-{created['controls']+1:03d}", control_name=name, control_domain="Risk & Compliance", owner_department="Compliance", testing_frequency="quarterly", evidence_required=True, description=f"Control for {name}", created_by="system"))
            created["controls"] += 1
    db.commit()
    return created
