from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.api.finance_bucs import create_project_financial_profile, generate_invoice_from_opportunity, next_number
from backend.core.database import get_db
from backend.models.auth import AuthUser
from backend.models.crm import CRMContract, CRMOpportunity
from backend.models.finance import FinanceInvoice, FinanceProjectFinance, FinanceRevenueRecord
from backend.models.projects import (
    BusinessInvoiceLifecycle,
    BusinessInvoiceSchedule,
    LicenseTracking,
    Project,
    ProjectAuditLog,
    ProjectBudget,
    ProjectMilestone,
    SLA,
    SLARenewal,
)
from backend.schemas.auth import UserResponse
from backend.schemas.enterprise_phase1 import WorkflowPayload
from backend.services.projects_enterprise import (
    RESOURCE_MAP,
    analytics_summary,
    create_record,
    delete_record,
    get_record,
    list_records,
    serialize,
    update_record,
    workflow,
)


router = APIRouter(tags=["Projects"])


def money(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def audit(db: Session, user: UserResponse, action: str, entity_type: str, entity_id: UUID | None, summary: str) -> None:
    actor_user_id = user.id if db.query(AuthUser).filter(AuthUser.id == user.id).first() else None
    db.add(ProjectAuditLog(actor_user_id=actor_user_id, actor_email=user.email, action=action, entity_type=entity_type, entity_id=entity_id, summary=summary))


def project_invoice_from_finance(db: Session, finance_invoice: FinanceInvoice, source_module: str, source_record_id: UUID | None, payload: dict[str, Any] | None = None) -> BusinessInvoiceLifecycle:
    payload = payload or {}
    existing = (
        db.query(BusinessInvoiceLifecycle)
        .filter(BusinessInvoiceLifecycle.finance_invoice_id == finance_invoice.id)
        .first()
    )
    if existing:
        return existing
    record = BusinessInvoiceLifecycle(
        invoice_number=finance_invoice.invoice_number,
        source_module=source_module,
        source_record_id=source_record_id,
        account_id=finance_invoice.account_id,
        project_id=finance_invoice.project_id,
        finance_invoice_id=finance_invoice.id,
        invoice_type=payload.get("invoice_type") or "tax_invoice",
        invoice_date=finance_invoice.invoice_date,
        due_date=finance_invoice.due_date,
        amount=finance_invoice.subtotal,
        tax_amount=finance_invoice.tax_amount,
        total_amount=finance_invoice.total_amount,
        approval_status=finance_invoice.approval_status or "draft",
        status=finance_invoice.status or "draft",
    )
    db.add(record)
    return record


def create_revenue_schedules(db: Session, invoice: BusinessInvoiceLifecycle, duration_months: int | None = None) -> list[BusinessInvoiceSchedule]:
    if not invoice.id:
        db.flush()
    if db.query(BusinessInvoiceSchedule).filter(BusinessInvoiceSchedule.invoice_id == invoice.id).first():
        return db.query(BusinessInvoiceSchedule).filter(BusinessInvoiceSchedule.invoice_id == invoice.id).all()
    months = max(int(duration_months or 1), 1)
    recognized = money(invoice.total_amount) / Decimal(months)
    rows: list[BusinessInvoiceSchedule] = []
    base_date = invoice.invoice_date or date.today()
    for offset in range(months):
        month = base_date.month + offset
        year = base_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        row = BusinessInvoiceSchedule(
            invoice_id=invoice.id,
            schedule_type="revenue_recognition",
            schedule_date=date(year, month, 1),
            recognized_revenue=recognized,
            deferred_revenue=max(money(invoice.total_amount) - (recognized * Decimal(offset + 1)), Decimal("0")),
        )
        db.add(row)
        rows.append(row)
    return rows

NESTED_RESOURCES = {
    "phases",
    "milestones",
    "tasks",
    "team",
    "budget",
    "documents",
    "charters",
    "scopes",
    "deliverables",
    "wbs",
    "timesheets",
    "resource-forecasts",
    "risks",
    "issues",
    "signoff",
    "lessons-learned",
}


@router.get("/projects/resources")
def resources():
    return {"resources": sorted(RESOURCE_MAP.keys())}


@router.get("/projects/analytics")
def analytics(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return analytics_summary(db)


@router.get("/projects/portfolio-dashboard")
def portfolio_dashboard(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    data = analytics_summary(db)
    projects = db.query(Project).filter(Project.soft_deleted.is_(False)).order_by(Project.created_at.desc()).limit(100).all()
    data["buc"] = "PJT-030"
    data["projects"] = [serialize(row) for row in projects]
    return data


@router.get("/projects/{project_id}/profitability")
def project_profitability(project_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    project = get_record(db, "projects", project_id)
    finance_profile = db.query(FinanceProjectFinance).filter(FinanceProjectFinance.project_id == project.id).first()
    revenue = money(getattr(finance_profile, "revenue_amount", None) or project.invoiced_amount)
    cost = money(getattr(finance_profile, "expense_amount", None) or project.actual_cost)
    profit = revenue - cost
    margin = (profit / revenue * Decimal("100")) if revenue else Decimal("0")
    return {"buc": "PJT-027", "profit": float(profit), "margin_percent": float(margin), "revenue": float(revenue), "cost": float(cost)}


@router.get("/projects/{project_id}/resource-utilization")
def project_resource_utilization(project_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    from backend.models.projects import ProjectTimesheet

    billable = money(db.query(func.coalesce(func.sum(ProjectTimesheet.billable_hours), 0)).filter(ProjectTimesheet.project_id == project_id, ProjectTimesheet.approval_status == "approved").scalar())
    available = money(db.query(func.coalesce(func.sum(ProjectTimesheet.available_hours), 0)).filter(ProjectTimesheet.project_id == project_id, ProjectTimesheet.approval_status == "approved").scalar())
    return {"buc": "PJT-015", "billable_hours": float(billable), "available_hours": float(available), "utilization_percent": float((billable / available * Decimal("100")) if available else 0)}


@router.post("/projects/automation/crm-won/{opportunity_id}")
def automate_crm_won_deal(opportunity_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == opportunity_id, CRMOpportunity.soft_deleted.is_(False)).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="CRM opportunity not found")
    if opportunity.status not in {"won", "closed_won"}:
        raise HTTPException(status_code=422, detail="Only won CRM opportunities can trigger project automation")
    project = db.query(Project).filter(Project.crm_opportunity_id == opportunity.id, Project.soft_deleted.is_(False)).first()
    if not project:
        owner_user_id = current_user.id if db.query(AuthUser).filter(AuthUser.id == current_user.id).first() else None
        project = Project(
            project_code=next_number("PJT"),
            project_name=payload.get("project_name") or opportunity.title,
            project_type="customer_implementation",
            lifecycle_status="approved",
            implementation_stage="initiation",
            owner_user_id=owner_user_id,
            project_manager_employee_id=payload.get("project_manager_employee_id") or opportunity.project_manager_employee_id,
            crm_account_id=opportunity.account_id,
            crm_opportunity_id=opportunity.id,
            start_date=payload.get("start_date") or date.today(),
            target_end_date=payload.get("target_end_date"),
            approved_budget=money(opportunity.distributor_cost) + money(opportunity.vendor_cost) + money(opportunity.internal_cost),
            invoiced_amount=money(opportunity.opportunity_value),
            budget_approval_status="approved",
            notes="Auto-created from CRM-019 won opportunity.",
        )
        db.add(project)
        db.flush()
        db.add(ProjectBudget(project_id=project.id, budget_name="CRM Won Deal Budget", budget_type="project", approved_amount=project.approved_budget, approval_status="approved", approved_by=current_user.email))
        db.add(ProjectMilestone(project_id=project.id, milestone_name="Customer Kickoff", due_date=date.today() + timedelta(days=7), status="open"))
    finance_invoice = generate_invoice_from_opportunity(db, opportunity)
    finance_invoice.project_id = project.id
    finance_profile = create_project_financial_profile(db, opportunity)
    finance_profile.project_id = project.id
    invoice_lifecycle = project_invoice_from_finance(db, finance_invoice, "crm.opportunity.won", opportunity.id, {"invoice_type": "tax_invoice"})
    create_revenue_schedules(db, invoice_lifecycle, payload.get("contract_duration_months"))
    license_record = None
    if opportunity.licence_expiry_date or payload.get("create_license", True):
        license_record = db.query(LicenseTracking).filter(LicenseTracking.opportunity_id == opportunity.id).first()
        if not license_record:
            purchased = int(payload.get("purchased_licenses") or 1)
            used = int(payload.get("used_licenses") or 0)
            license_record = LicenseTracking(
                license_number=next_number("LIC"),
                account_id=opportunity.account_id,
                project_id=project.id,
                opportunity_id=opportunity.id,
                license_name=payload.get("license_name") or opportunity.title,
                expiry_date=opportunity.licence_expiry_date or date.today() + timedelta(days=365),
                renewal_date=opportunity.renewal_date or opportunity.licence_expiry_date,
                purchased_licenses=purchased,
                used_licenses=used,
                consumption_percent=(Decimal(used) / Decimal(purchased) * Decimal("100")) if purchased else Decimal("0"),
                finance_revenue_amount=money(opportunity.opportunity_value),
            )
            db.add(license_record)
    sla = None
    contract = db.query(CRMContract).filter(CRMContract.opportunity_id == opportunity.id, CRMContract.status.in_(["active", "signed", "renewed"])).first()
    if contract or payload.get("create_sla", True):
        sla = db.query(SLA).filter(SLA.project_id == project.id).first()
        if not sla:
            sla = SLA(
                sla_number=next_number("SLA"),
                account_id=opportunity.account_id,
                contract_id=getattr(contract, "id", None),
                project_id=project.id,
                sla_name=payload.get("sla_name") or f"SLA - {opportunity.title}",
                start_date=getattr(contract, "start_date", None) or date.today(),
                end_date=getattr(contract, "end_date", None) or payload.get("sla_end_date"),
                status="active",
            )
            db.add(sla)
    opportunity.handover_status = "project_finance_license_sla_invoice_created"
    audit(db, current_user, "PJT_CRM_WON_AUTOMATION", "projects", project.id, "CRM won deal created Project, Finance profile, License, SLA, and Invoice lifecycle")
    db.commit()
    return {
        "bucs": ["PJT-001", "FIN-127", "LIC-003", "SLA-002", "INV-003", "FIN-057"],
        "project": serialize(project),
        "finance_invoice": serialize(finance_invoice),
        "finance_profile": serialize(finance_profile),
        "invoice_lifecycle": serialize(invoice_lifecycle),
        "license": serialize(license_record) if license_record else None,
        "sla": serialize(sla) if sla else None,
    }


@router.post("/licenses/{license_id}/renewal-opportunity")
def create_license_renewal_opportunity(license_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    license_record = get_record(db, "licenses", license_id)
    if not license_record.account_id:
        raise HTTPException(status_code=422, detail="License must link to a CRM customer account before renewal")
    existing = db.query(CRMOpportunity).filter(CRMOpportunity.account_id == license_record.account_id, CRMOpportunity.title == f"Renewal - {license_record.license_name}", CRMOpportunity.status == "open").first()
    if existing:
        return {"buc": "LIC-019", "opportunity": serialize(existing)}
    opportunity = CRMOpportunity(
        account_id=license_record.account_id,
        title=f"Renewal - {license_record.license_name}",
        description="Auto-created from license renewal tracking.",
        stage="Renewal",
        opportunity_value=payload.get("renewal_amount") or license_record.finance_revenue_amount,
        probability=payload.get("probability") or 70,
        expected_close_date=license_record.renewal_date or license_record.expiry_date,
        renewal_date=license_record.renewal_date or license_record.expiry_date,
        licence_expiry_date=license_record.expiry_date,
        status="open",
    )
    db.add(opportunity)
    license_record.notification_status = "renewal_opportunity_created"
    audit(db, current_user, "LIC-019_RENEWAL_OPPORTUNITY_CREATED", "licenses", license_record.id, "CRM renewal opportunity created")
    db.commit()
    return {"buc": "LIC-019", "opportunity": serialize(opportunity), "license": serialize(license_record)}


@router.post("/slas/{sla_id}/renewal-opportunity")
def create_sla_renewal_opportunity(sla_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    sla = get_record(db, "slas", sla_id)
    if not sla.account_id:
        raise HTTPException(status_code=422, detail="SLA must link to a CRM customer account before renewal")
    renewal_date = sla.end_date or date.today() + timedelta(days=30)
    opportunity = CRMOpportunity(
        account_id=sla.account_id,
        title=f"SLA Renewal - {sla.sla_name}",
        description="Auto-created from SLA renewal management.",
        stage="Renewal",
        opportunity_value=payload.get("renewal_amount") or 0,
        probability=payload.get("probability") or 70,
        expected_close_date=renewal_date,
        renewal_date=renewal_date,
        status="open",
    )
    db.add(opportunity)
    db.flush()
    db.add(SLARenewal(sla_id=sla.id, renewal_date=renewal_date, renewal_opportunity_id=opportunity.id, forecast_amount=payload.get("renewal_amount") or 0, status="opportunity_created"))
    audit(db, current_user, "SLA-014_RENEWAL_OPPORTUNITY_CREATED", "slas", sla.id, "CRM renewal opportunity created")
    db.commit()
    return {"buc": "SLA-014", "opportunity": serialize(opportunity)}


@router.get("/slas/{sla_id}/dashboard")
def sla_dashboard(sla_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    from backend.models.projects import SLAHealthCheck, SLATicket

    sla = get_record(db, "slas", sla_id)
    total_tickets = db.query(SLATicket).filter(SLATicket.sla_id == sla.id).count()
    within_sla = db.query(SLATicket).filter(SLATicket.sla_id == sla.id, SLATicket.sla_status == "within_sla").count()
    breached = db.query(SLATicket).filter(SLATicket.sla_id == sla.id, SLATicket.sla_status.in_(["breached", "response_breached"])).count()
    availability = money(db.query(func.coalesce(func.avg(SLAHealthCheck.uptime_percent), 100)).filter(SLAHealthCheck.sla_id == sla.id).scalar())
    compliance = (Decimal(within_sla) / Decimal(total_tickets) * Decimal("100")) if total_tickets else Decimal("100")
    resolved = db.query(SLATicket).filter(SLATicket.sla_id == sla.id, SLATicket.resolved_at.isnot(None)).all()
    total_resolution_hours = sum(((ticket.resolved_at - ticket.opened_at).total_seconds() / 3600) for ticket in resolved if ticket.opened_at and ticket.resolved_at)
    mttr = Decimal(str(total_resolution_hours / len(resolved))) if resolved else Decimal("0")
    return {"bucs": ["SLA-015", "SLA-016", "SLA-017", "SLA-019"], "sla": serialize(sla), "availability_percent": float(availability), "compliance_percent": float(compliance), "mttr_hours": float(mttr), "breached_tickets": breached}


@router.get("/licenses/dashboard")
def license_dashboard(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    licenses = db.query(LicenseTracking).order_by(LicenseTracking.expiry_date.asc().nullslast()).limit(200).all()
    purchased = money(db.query(func.coalesce(func.sum(LicenseTracking.purchased_licenses), 0)).scalar())
    used = money(db.query(func.coalesce(func.sum(LicenseTracking.used_licenses), 0)).scalar())
    expiring = db.query(LicenseTracking).filter(LicenseTracking.expiry_date <= date.today() + timedelta(days=90), LicenseTracking.status == "active").count()
    return {"buc": "LIC-020", "purchased": float(purchased), "used": float(used), "consumption_percent": float((used / purchased * Decimal("100")) if purchased else 0), "expiring_90_days": expiring, "licenses": [serialize(row) for row in licenses]}


@router.get("/projects")
def list_projects(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return list_records(db, "projects", current_user)


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return create_record(db, "projects", data, current_user)


@router.get("/projects/{project_id}")
def get_project(project_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return serialize(get_record(db, "projects", project_id))


@router.patch("/projects/{project_id}")
def patch_project(
    project_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, "projects", project_id, data, current_user)


@router.put("/projects/{project_id}")
def put_project(
    project_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, "projects", project_id, data, current_user)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    delete_record(db, "projects", project_id, current_user)
    return None


@router.post("/projects/{project_id}/workflow/{action}")
def project_workflow(
    project_id: UUID,
    action: str,
    payload: WorkflowPayload | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return workflow(db, "projects", project_id, action, current_user, payload.model_dump(exclude_none=True) if payload else {})


@router.get("/projects/{project_id}/{resource}")
def list_project_child(
    project_id: UUID,
    resource: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    mapped = "budgets" if resource == "budget" else "signoffs" if resource == "signoff" else resource
    return list_records(db, mapped, current_user, project_id=project_id)


@router.post("/projects/{project_id}/{resource}", status_code=status.HTTP_201_CREATED)
def create_project_child(
    project_id: UUID,
    resource: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    mapped = "budgets" if resource == "budget" else "signoffs" if resource == "signoff" else resource
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    data["project_id"] = str(project_id)
    return create_record(db, mapped, data, current_user)


@router.get("/project-resources/{resource}")
def list_project_resource(
    resource: str,
    project_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return list_records(db, resource, current_user, project_id=project_id)


@router.post("/project-resources/{resource}", status_code=status.HTTP_201_CREATED)
def create_project_resource(
    resource: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return create_record(db, resource, data, current_user)


@router.patch("/project-resources/{resource}/{record_id}")
def patch_project_resource(
    resource: str,
    record_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, resource, record_id, data, current_user)


@router.put("/project-resources/{resource}/{record_id}")
def put_project_resource(
    resource: str,
    record_id: UUID,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return update_record(db, resource, record_id, data, current_user)


@router.delete("/project-resources/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_resource(
    resource: str,
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    delete_record(db, resource, record_id, current_user)
    return None


@router.post("/project-resources/{resource}/{record_id}/{action}")
def project_resource_workflow(
    resource: str,
    record_id: UUID,
    action: str,
    payload: WorkflowPayload | None = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return workflow(db, resource, record_id, action, current_user, payload.model_dump(exclude_none=True) if payload else {})


def _standalone_list(resource: str, db: Session, user: UserResponse):
    return list_records(db, resource, user)


def _standalone_create(resource: str, payload: dict[str, Any], db: Session, user: UserResponse):
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return create_record(db, resource, data, user)


@router.get("/slas")
def list_slas(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_list("slas", db, current_user)


@router.post("/slas", status_code=status.HTTP_201_CREATED)
def create_sla(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_create("slas", payload, db, current_user)


@router.get("/sla-tickets")
def list_sla_tickets(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_list("sla-tickets", db, current_user)


@router.post("/sla-tickets", status_code=status.HTTP_201_CREATED)
def create_sla_ticket(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_create("sla-tickets", payload, db, current_user)


@router.get("/licenses")
def list_licenses(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_list("licenses", db, current_user)


@router.post("/licenses", status_code=status.HTTP_201_CREATED)
def create_license(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_create("licenses", payload, db, current_user)


@router.get("/invoicing")
def list_invoice_lifecycle(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return list_records(db, "invoice-lifecycle", current_user)


@router.post("/invoicing/generate", status_code=status.HTTP_201_CREATED)
def generate_business_invoice(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    account_id = payload.get("account_id")
    if not account_id:
        raise HTTPException(status_code=422, detail="CRM account is required for invoice generation")
    source_module = payload.get("source_module") or "manual"
    source_record_id = payload.get("source_record_id")
    existing = None
    if source_record_id:
        existing = db.query(BusinessInvoiceLifecycle).filter(BusinessInvoiceLifecycle.source_module == source_module, BusinessInvoiceLifecycle.source_record_id == UUID(str(source_record_id))).first()
    if existing:
        return {"buc": "INV-003", "invoice": serialize(existing)}
    subtotal = money(payload.get("amount") or payload.get("subtotal"))
    tax_amount = money(payload.get("tax_amount") or subtotal * money(payload.get("tax_rate") or 16) / Decimal("100"))
    finance_invoice = FinanceInvoice(
        invoice_number=payload.get("invoice_number") or next_number("INV"),
        account_id=UUID(str(account_id)),
        project_id=UUID(str(payload["project_id"])) if payload.get("project_id") else None,
        source_module=source_module,
        source_record_id=UUID(str(source_record_id)) if source_record_id else None,
        invoice_date=date.fromisoformat(str(payload.get("invoice_date") or date.today().isoformat())),
        due_date=date.fromisoformat(str(payload.get("due_date"))) if payload.get("due_date") else date.today() + timedelta(days=30),
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=subtotal + tax_amount,
        approval_status="draft",
        status="draft",
        notes=payload.get("notes") or "Generated by invoicing lifecycle module.",
    )
    db.add(finance_invoice)
    db.flush()
    invoice = project_invoice_from_finance(db, finance_invoice, source_module, UUID(str(source_record_id)) if source_record_id else None, payload)
    invoice.project_id = UUID(str(payload["project_id"])) if payload.get("project_id") else None
    invoice.license_id = UUID(str(payload["license_id"])) if payload.get("license_id") else None
    invoice.sla_id = UUID(str(payload["sla_id"])) if payload.get("sla_id") else None
    create_revenue_schedules(db, invoice, payload.get("contract_duration_months") or payload.get("duration_months"))
    audit(db, current_user, "INV-003_INVOICE_GENERATED", "invoice_lifecycle", invoice.id, f"Invoice {invoice.invoice_number} generated")
    db.commit()
    return {"buc": "INV-003", "invoice": serialize(invoice), "finance_invoice": serialize(finance_invoice)}


@router.post("/invoicing/{invoice_id}/approve")
def approve_business_invoice(invoice_id: UUID, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    invoice = get_record(db, "invoice-lifecycle", invoice_id)
    invoice.approval_status = "approved"
    invoice.status = "approved"
    finance_invoice = db.query(FinanceInvoice).filter(FinanceInvoice.id == invoice.finance_invoice_id).first() if invoice.finance_invoice_id else None
    if finance_invoice:
        finance_invoice.approval_status = "approved"
        finance_invoice.status = "approved"
    audit(db, current_user, "INV-010_INVOICE_APPROVED", "invoice_lifecycle", invoice.id, "Invoice approved for dispatch")
    db.commit()
    return {"buc": "INV-010", "invoice": serialize(invoice), "finance_invoice": serialize(finance_invoice) if finance_invoice else None}


@router.post("/invoicing/{invoice_id}/dispatch")
def dispatch_business_invoice(invoice_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    payload = payload or {}
    invoice = get_record(db, "invoice-lifecycle", invoice_id)
    if invoice.approval_status != "approved":
        raise HTTPException(status_code=422, detail="Only approved invoices can be dispatched")
    invoice.dispatch_status = "sent"
    invoice.status = "sent"
    finance_invoice = db.query(FinanceInvoice).filter(FinanceInvoice.id == invoice.finance_invoice_id).first() if invoice.finance_invoice_id else None
    if finance_invoice:
        finance_invoice.status = "sent"
        finance_invoice.delivery_method = payload.get("delivery_method") or "email"
    audit(db, current_user, "INV-011_INVOICE_DISPATCHED", "invoice_lifecycle", invoice.id, payload.get("delivery_method") or "email")
    db.commit()
    return {"buc": "INV-011", "invoice": serialize(invoice)}


@router.post("/invoicing/{invoice_id}/accept")
def accept_business_invoice(invoice_id: UUID, payload: dict[str, Any] | None = None, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    invoice = get_record(db, "invoice-lifecycle", invoice_id)
    invoice.acceptance_status = "accepted"
    invoice.status = "accepted"
    audit(db, current_user, "INV-013_INVOICE_ACCEPTED", "invoice_lifecycle", invoice.id, (payload or {}).get("comments") or "Customer accepted invoice")
    db.commit()
    return {"buc": "INV-013", "invoice": serialize(invoice)}


@router.post("/invoicing/{invoice_id}/cancel")
def cancel_business_invoice(invoice_id: UUID, payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if not payload.get("reason"):
        raise HTTPException(status_code=422, detail="Cancellation reason is required")
    invoice = get_record(db, "invoice-lifecycle", invoice_id)
    invoice.status = "cancelled"
    finance_invoice = db.query(FinanceInvoice).filter(FinanceInvoice.id == invoice.finance_invoice_id).first() if invoice.finance_invoice_id else None
    if finance_invoice:
        finance_invoice.status = "cancelled"
    audit(db, current_user, "INV-015_INVOICE_CANCELLED", "invoice_lifecycle", invoice.id, payload["reason"])
    db.commit()
    return {"buc": "INV-015", "invoice": serialize(invoice)}


@router.get("/invoicing/analytics")
def invoicing_analytics(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    total = money(db.query(func.coalesce(func.sum(BusinessInvoiceLifecycle.total_amount), 0)).filter(BusinessInvoiceLifecycle.status.notin_(["cancelled"])).scalar())
    accepted = money(db.query(func.coalesce(func.sum(BusinessInvoiceLifecycle.total_amount), 0)).filter(BusinessInvoiceLifecycle.acceptance_status == "accepted").scalar())
    overdue = db.query(BusinessInvoiceLifecycle).filter(BusinessInvoiceLifecycle.due_date < date.today(), BusinessInvoiceLifecycle.status.notin_(["cancelled", "paid"])).count()
    forecast = money(db.query(func.coalesce(func.sum(FinanceRevenueRecord.amount), 0)).filter(FinanceRevenueRecord.status.in_(["pending", "deferred"])).scalar())
    return {"buc": "INV-023", "total_invoiced": float(total), "accepted_value": float(accepted), "overdue_invoices": overdue, "revenue_forecast": float(forecast)}


@router.get("/invoicing/customer-billing-dashboard")
def customer_billing_dashboard(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    rows = db.query(BusinessInvoiceLifecycle).order_by(BusinessInvoiceLifecycle.created_at.desc()).limit(200).all()
    return {"buc": "INV-024", "invoices": [serialize(row) for row in rows]}


@router.get("/invoicing/revenue-forecast-dashboard")
def revenue_forecast_dashboard(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    schedules = db.query(BusinessInvoiceSchedule).order_by(BusinessInvoiceSchedule.schedule_date.asc()).limit(300).all()
    return {"buc": "INV-025", "schedules": [serialize(row) for row in schedules]}


@router.get("/vendor-engagements")
def list_vendor_engagements(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_list("vendor-engagements", db, current_user)


@router.post("/vendor-engagements", status_code=status.HTTP_201_CREATED)
def create_vendor_engagement(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_create("vendor-engagements", payload, db, current_user)


@router.get("/marketing-initiatives")
def list_marketing_initiatives(db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_list("marketing-initiatives", db, current_user)


@router.post("/marketing-initiatives", status_code=status.HTTP_201_CREATED)
def create_marketing_initiative(payload: dict[str, Any], db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    return _standalone_create("marketing-initiatives", payload, db, current_user)
