import csv
import io
import json
import re
import uuid
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime, Integer, Numeric
from sqlalchemy.orm import Session

from backend.api.crud import assign_business_id
from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.crm import (
    CRMAccount,
    CRMAccountIssue,
    CRMActivity,
    CRMAutomationRule,
    CRMContact,
    CRMCustomerEngagement,
    CRMDepartmentWorkflow,
    CRMDeal,
    CRMInvoice,
    CRMLead,
    CRMOpportunity,
    CRMPMOProject,
    CRMQuotation,
    CRMSalesTarget,
    CRMSLAAssignment,
    CRMTask,
    CRMTechnicalService,
    CRMTender,
    CRMTenderRepositoryDocument,
    CRMTicket,
)
from backend.models.enterprise import (
    CRMLicence,
    DataImportBatch,
    EntitySequence,
    ERPInventoryItem,
    CommunicationLog,
    FeatureCapability,
    IntegrationConnector,
    KnowledgeBaseArticle,
    NotificationEvent,
    OrganizationGoal,
    PortalRequest,
    ProjectMilestone,
    ProjectRisk,
    ProjectTask,
    ResourceAllocation,
    ScheduleEvent,
    StaffRoleAssignment,
    SupportTicket,
    TerritoryRule,
    WorkflowRule,
    WorkflowRunLog,
)
from backend.models.finance import FinanceInvoice, FinanceRevenueRecord
from backend.api.finance import RESOURCE_REGISTRY as FINANCE_RESOURCE_REGISTRY, automate_invoice_payload
from backend.models.hrm import (
    HRMActivity,
    HRMAttendance,
    HRMAssetAssignment,
    HRMBenefit,
    HRMCompensation,
    HRMDepartment,
    HRMDocument,
    HRMEmployee,
    HRMEmployeeRelationCase,
    HRMGRCRecord,
    HRMLifecycleEvent,
    HRMLeave,
    HRMLeaveBalance,
    HRMOnboardingTask,
    HRMPayroll,
    HRMPerformance,
    HRMPolicyAcknowledgement,
    HRMPosition,
    HRMRecruitment,
    HRMSurvey,
    HRMTraining,
)
from backend.schemas.auth import UserResponse


router = APIRouter(tags=["Enterprise Intelligence"])


class FlexiblePayload(BaseModel):
    model_config = ConfigDict(extra="allow")


class BulkDeletePayload(BaseModel):
    endpoint: str
    ids: list[uuid.UUID]


CRUD_RESOURCES = {
    "licences": {
        "model": CRMLicence,
        "entity_key": "crm.licences",
        "search": ["business_id", "licence_name", "product_name", "account_manager", "distributor", "oem_name", "status"],
    },
    "connectors": {
        "model": IntegrationConnector,
        "entity_key": "auth.integration_connectors",
        "search": ["business_id", "connector_name", "connector_type", "environment", "system_owner", "status"],
    },
    "imports": {
        "model": DataImportBatch,
        "entity_key": "auth.data_import_batches",
        "search": ["business_id", "source_name", "source_format", "target_resource", "file_name", "status"],
    },
    "sequences": {
        "model": EntitySequence,
        "entity_key": "auth.entity_sequences",
        "search": ["organization_code", "entity_key", "prefix", "notes"],
    },
    "staff-roles": {
        "model": StaffRoleAssignment,
        "entity_key": "auth.staff_role_assignments",
        "search": ["staff_name", "role_name", "department", "role_scope", "line_manager", "status"],
    },
    "workflow-rules": {
        "model": WorkflowRule,
        "entity_key": "auth.workflow_rules",
        "search": ["business_id", "rule_name", "module", "trigger_entity", "trigger_event", "action_type", "status"],
    },
    "workflow-logs": {
        "model": WorkflowRunLog,
        "entity_key": "auth.workflow_run_logs",
        "search": ["entity_type", "event_name", "outcome", "message", "run_by"],
    },
    "notifications": {
        "model": NotificationEvent,
        "entity_key": "auth.notification_events",
        "search": ["business_id", "module", "related_entity", "recipient_name", "recipient_email", "subject", "status"],
    },
    "support-tickets": {
        "model": SupportTicket,
        "entity_key": "crm.support_tickets",
        "search": ["business_id", "ticket_number", "subject", "category", "assigned_to", "status"],
    },
    "knowledge-base": {
        "model": KnowledgeBaseArticle,
        "entity_key": "auth.knowledge_base_articles",
        "search": ["business_id", "title", "module", "article_type", "tags", "owner", "status"],
    },
    "project-tasks": {
        "model": ProjectTask,
        "entity_key": "crm.project_tasks",
        "search": ["business_id", "task_name", "workstream", "assigned_to", "priority", "status"],
    },
    "project-milestones": {
        "model": ProjectMilestone,
        "entity_key": "crm.project_milestones",
        "search": ["business_id", "milestone_name", "owner", "billing_status", "status"],
    },
    "project-risks": {
        "model": ProjectRisk,
        "entity_key": "crm.project_risks",
        "search": ["business_id", "risk_title", "risk_type", "owner", "status"],
    },
    "inventory-items": {
        "model": ERPInventoryItem,
        "entity_key": "finance.inventory_items",
        "search": ["business_id", "item_name", "item_type", "sku", "category", "vendor_name", "status"],
    },
    "goals": {
        "model": OrganizationGoal,
        "entity_key": "auth.organization_goals",
        "search": ["business_id", "goal_name", "module", "department", "owner", "status"],
    },
    "territories": {
        "model": TerritoryRule,
        "entity_key": "crm.territory_rules",
        "search": ["business_id", "territory_name", "country", "region", "vertical", "account_manager", "status"],
    },
    "portal-requests": {
        "model": PortalRequest,
        "entity_key": "auth.portal_requests",
        "search": ["business_id", "requester_name", "requester_type", "module", "request_type", "subject", "status"],
    },
    "communications": {
        "model": CommunicationLog,
        "entity_key": "auth.communication_logs",
        "search": ["business_id", "module", "channel", "contact_name", "contact_email", "subject", "owner", "status"],
    },
    "schedule-events": {
        "model": ScheduleEvent,
        "entity_key": "auth.schedule_events",
        "search": ["business_id", "event_name", "module", "event_type", "owner", "status"],
    },
    "resource-allocations": {
        "model": ResourceAllocation,
        "entity_key": "auth.resource_allocations",
        "search": ["business_id", "resource_name", "resource_type", "module", "allocation_target", "role_on_work", "status"],
    },
    "capabilities": {
        "model": FeatureCapability,
        "entity_key": "auth.feature_capabilities",
        "search": ["category", "capability", "source_platforms", "module", "mechanism", "implementation_status"],
    },
}

ADMIN_ONLY_RESOURCES = {"connectors", "imports", "sequences", "workflow-rules", "workflow-logs"}


CRM_BULK_MODELS = {
    "accounts": CRMAccount,
    "contacts": CRMContact,
    "leads": CRMLead,
    "opportunities": CRMOpportunity,
    "activities": CRMActivity,
    "deals": CRMDeal,
    "engagements": CRMCustomerEngagement,
    "account-issues": CRMAccountIssue,
    "sales-targets": CRMSalesTarget,
    "invoices": CRMInvoice,
    "department-workflows": CRMDepartmentWorkflow,
    "tenders": CRMTender,
    "tender-documents": CRMTenderRepositoryDocument,
    "pmo-projects": CRMPMOProject,
    "sla-assignments": CRMSLAAssignment,
    "technical-services": CRMTechnicalService,
    "customer-tickets": CRMTicket,
    "tasks": CRMTask,
    "quotes": CRMQuotation,
    "automation/rules": CRMAutomationRule,
}

HRM_BULK_MODELS = {
    "employees": HRMEmployee,
    "departments": HRMDepartment,
    "attendance": HRMAttendance,
    "leave": HRMLeave,
    "payroll": HRMPayroll,
    "recruitment": HRMRecruitment,
    "performance": HRMPerformance,
    "training": HRMTraining,
    "benefits": HRMBenefit,
    "documents": HRMDocument,
    "activities": HRMActivity,
    "grc": HRMGRCRecord,
    "positions": HRMPosition,
    "onboarding": HRMOnboardingTask,
    "leave-balances": HRMLeaveBalance,
    "compensation": HRMCompensation,
    "lifecycle": HRMLifecycleEvent,
    "policy-acknowledgements": HRMPolicyAcknowledgement,
    "employee-relations": HRMEmployeeRelationCase,
    "surveys": HRMSurvey,
    "asset-assignments": HRMAssetAssignment,
}


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date,)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _serialize(record: Any) -> dict[str, Any]:
    return {column.name: _json_value(getattr(record, column.name)) for column in record.__table__.columns}


def _next_business_id(db: Session, entity_key: str) -> str:
    sequence = db.query(EntitySequence).filter(EntitySequence.entity_key == entity_key).with_for_update().first()
    if not sequence:
        prefix = "IS-" + entity_key.split(".")[-1][:3].upper()
        sequence = EntitySequence(entity_key=entity_key, prefix=prefix, next_number=1, padding=5)
        db.add(sequence)
        db.flush()

    business_id = f"{sequence.prefix}-{str(sequence.next_number).zfill(sequence.padding or 5)}"
    sequence.next_number = (sequence.next_number or 1) + 1
    return business_id


def _clean_payload(model: Any, payload: dict[str, Any]) -> dict[str, Any]:
    columns = {column.name for column in model.__table__.columns}
    data = {key: value for key, value in payload.items() if key in columns and key not in {"id", "created_at", "updated_at"}}
    for key, value in list(data.items()):
        if value == "":
            data[key] = None
        elif key in {"configuration", "sample_payload", "condition_json", "action_payload", "context", "dependency_ids", "attendees"} and isinstance(value, str):
            try:
                data[key] = json.loads(value)
            except json.JSONDecodeError:
                data[key] = {"raw": value}
    return data


def _ensure_licence_invoice(db: Session, licence: CRMLicence):
    if not isinstance(licence, CRMLicence):
        return
    if (licence.purchase_status or "").lower() != "purchased" or (licence.delivery_status or "").lower() != "delivered":
        licence.invoice_status = "not_ready"
        return
    if licence.invoice_status == "generated":
        return
    existing = None
    if licence.deal_id:
        existing = db.query(FinanceInvoice).filter(FinanceInvoice.deal_id == licence.deal_id, FinanceInvoice.notes.ilike(f"%Licence ID: {licence.id}%")).first()
    if existing:
        licence.invoice_status = "generated"
        return

    deal = db.query(CRMDeal).filter(CRMDeal.id == licence.deal_id).first() if licence.deal_id else None
    subtotal = float(deal.revenue_amount or 0) if deal else 0
    tax_rate = 16
    tax_amount = subtotal * tax_rate / 100
    invoice_business_id = _next_business_id(db, "finance.invoices")
    invoice = FinanceInvoice(
        business_id=invoice_business_id,
        account_id=licence.account_id,
        deal_id=licence.deal_id,
        project_id=licence.project_id,
        invoice_number=invoice_business_id.replace("IS-INV", "INV"),
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=0,
        total_amount=subtotal + tax_amount,
        paid_amount=0,
        tax_country="Kenya",
        tax_region="standard",
        tax_rate=tax_rate,
        approval_status="draft",
        status="draft",
        notes=f"Automatically raised after licence purchase and delivery. Licence ID: {licence.id}",
    )
    db.add(invoice)
    licence.invoice_status = "generated"


def _log_workflow_event(db: Session, entity_type: str, event_name: str, entity_id: uuid.UUID | None, user: UserResponse, message: str):
    log = WorkflowRunLog(
        entity_type=entity_type,
        entity_id=entity_id,
        event_name=event_name,
        outcome="success",
        message=message,
        run_by=user.full_name,
    )
    db.add(log)


def _apply_simple_workflows(db: Session, resource: str, record: Any, user: UserResponse):
    if isinstance(record, WorkflowRunLog):
        return
    active_rules = (
        db.query(WorkflowRule)
        .filter(WorkflowRule.status == "active", WorkflowRule.trigger_entity.in_([resource, getattr(record, "__tablename__", "")]))
        .limit(25)
        .all()
    )
    for rule in active_rules:
        rule.last_run_at = datetime.utcnow()
        _log_workflow_event(
            db,
            resource,
            rule.trigger_event,
            getattr(record, "id", None),
            user,
            f"Workflow '{rule.rule_name}' evaluated action '{rule.action_type}'.",
        )
        if rule.action_type == "queue_notification":
            payload = rule.action_payload or {}
            db.add(
                NotificationEvent(
                    business_id=_next_business_id(db, "auth.notification_events"),
                    module=rule.module,
                    related_entity=resource,
                    related_id=getattr(record, "id", None),
                    recipient_name=payload.get("recipient_name") or getattr(record, "assigned_to", None) or getattr(record, "owner", None),
                    recipient_email=payload.get("recipient_email"),
                    subject=payload.get("subject") or f"{rule.rule_name} notification",
                    body=payload.get("body") or f"Workflow {rule.rule_name} was triggered.",
                    created_by=user.full_name,
                )
            )


def _require_admin_or_manager(user: UserResponse):
    if user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or manager access required")


def _require_admin(user: UserResponse):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System admin access required")


def _rows_from_csv(content: bytes) -> list[dict[str, Any]]:
    text_content = content.decode("utf-8-sig", errors="ignore")
    return list(csv.DictReader(io.StringIO(text_content)))


def _rows_from_json(content: bytes) -> list[dict[str, Any]]:
    payload = json.loads(content.decode("utf-8-sig", errors="ignore"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("rows", "data", "items", "records"):
            if isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
        return [payload]
    return []


def _rows_from_yaml(content: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for raw_line in content.decode("utf-8-sig", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            if current:
                rows.append(current)
            current = {}
            line = line[2:].strip()
        if ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip().strip("\"'")
    if current:
        rows.append(current)
    return rows


def _rows_from_xlsx(content: bytes) -> list[dict[str, Any]]:
    def column_index(cell_ref: str) -> int:
        letters = "".join(ch for ch in cell_ref if ch.isalpha()).upper()
        index = 0
        for letter in letters:
            index = index * 26 + (ord(letter) - 64)
        return max(index - 1, 0)

    def cell_text(cell, shared: list[str]) -> str:
        cell_type = cell.attrib.get("t")
        value_node = cell.find("{*}v")
        inline_node = cell.find("{*}is/{*}t")
        if cell_type == "inlineStr":
            return inline_node.text.strip() if inline_node is not None and inline_node.text else ""
        raw = value_node.text.strip() if value_node is not None and value_node.text else ""
        if cell_type == "s" and raw.isdigit() and int(raw) < len(shared):
            return shared[int(raw)]
        if cell_type == "b":
            return "true" if raw == "1" else "false"
        return raw

    parsed_rows: list[list[str]] = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("{*}si"):
                texts = [node.text or "" for node in item.findall(".//{*}t")]
                shared.append("".join(texts).strip())

        sheet_name = "xl/worksheets/sheet1.xml" if "xl/worksheets/sheet1.xml" in archive.namelist() else next((name for name in archive.namelist() if name.startswith("xl/worksheets/sheet")), "")
        if not sheet_name:
            return []
        sheet_root = ElementTree.fromstring(archive.read(sheet_name))
        for row in sheet_root.findall(".//{*}row"):
            values: list[str] = []
            for cell in row.findall("{*}c"):
                ref = cell.attrib.get("r", "")
                index = column_index(ref) if ref else len(values)
                while len(values) <= index:
                    values.append("")
                values[index] = cell_text(cell, shared)
            if any(value != "" for value in values):
                parsed_rows.append(values)
    if not parsed_rows:
        return []
    headers = [str(value).strip() for value in parsed_rows[0]]
    return [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in parsed_rows[1:] if any(str(value).strip() for value in row)]


def _extract_textish_summary(content: bytes, filename: str) -> tuple[list[dict[str, Any]], str]:
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "csv":
        rows = _rows_from_csv(content)
    elif suffix == "json":
        rows = _rows_from_json(content)
    elif suffix in {"yaml", "yml"}:
        rows = _rows_from_yaml(content)
    elif suffix == "xlsx":
        rows = _rows_from_xlsx(content)
    elif suffix == "docx":
        rows = []
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
            text_content = re.sub(r"<[^>]+>", " ", xml)
        return rows, " ".join(text_content.split())[:1500]
    else:
        rows = []
    return rows, f"Parsed {len(rows)} structured row(s) from {suffix or 'unknown'} file."


def _model_for_bulk_endpoint(endpoint: str):
    normalized = endpoint.strip().strip("/")
    if normalized.startswith("api/"):
        normalized = normalized[4:]
    parts = normalized.split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Upload target is not a valid API endpoint")

    domain = parts[0]
    resource = "/".join(parts[1:])
    if domain == "enterprise":
        config = CRUD_RESOURCES.get(resource)
        if not config:
            raise HTTPException(status_code=404, detail="Enterprise upload target not found")
        return config["model"], config["entity_key"]
    if domain == "crm":
        model = CRM_BULK_MODELS.get(resource)
        if not model:
            raise HTTPException(status_code=404, detail="CRM upload target not found")
        return model, f"crm.{model.__tablename__}"
    if domain == "hrm":
        model = HRM_BULK_MODELS.get(resource)
        if not model:
            raise HTTPException(status_code=404, detail="HRM upload target not found")
        return model, model.__tablename__
    if domain == "finance":
        model = FINANCE_RESOURCE_REGISTRY.get(resource)
        if not model:
            raise HTTPException(status_code=404, detail="Finance upload target not found")
        return model, f"finance.{model.__tablename__}"
    if domain == "admin":
        raise HTTPException(status_code=403, detail="Admin configuration imports must be entered by form for safety")
    raise HTTPException(status_code=404, detail="Upload target not found")


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


IMPORT_ALIASES = {
    "company_name": {"account", "account_name", "customer", "customer_name", "client", "client_name", "organization", "organisation", "company"},
    "account_country": {"country", "customer_country", "client_country", "account_country"},
    "account_region": {"region", "customer_region", "client_region", "account_region"},
    "account_vertical": {"vertical", "sector", "industry_vertical"},
    "account_manager": {"am", "owner", "relationship_manager", "sales_owner"},
    "relationship_owner": {"relationship_manager", "owner"},
    "account_status": {"status"},
    "email": {"email", "email_address", "e_mail"},
    "phone": {"phone", "phone_number", "mobile", "telephone"},
    "first_name": {"first", "given_name"},
    "last_name": {"last", "surname", "family_name"},
    "job_title": {"title", "designation", "role"},
    "contact_name": {"contact", "customer_contact", "lead_name", "full_name", "name"},
    "lead_source": {"source", "lead_source", "channel", "origin"},
    "assigned_to": {"owner", "assigned_to", "assigned", "am", "sales_owner", "lead_owner"},
    "issue_title": {"issue", "issue_title", "problem", "subject", "title", "name"},
    "activity_type": {"activity_type", "type", "task_type"},
    "subject": {"subject", "title", "name", "description"},
    "related_type": {"related_type", "entity_type", "module"},
    "engagement_type": {"engagement_type", "type", "activity_type"},
    "engagement_date": {"engagement_date", "date", "activity_date", "meeting_date"},
    "owner_type": {"owner_type", "target_type", "type"},
    "target_owner": {"target_owner", "owner", "am", "staff", "employee", "name"},
    "fiscal_year": {"fiscal_year", "fy", "year"},
    "period_type": {"period_type", "period", "target_period"},
    "period_label": {"period_label", "quarter", "month", "label"},
    "deal_name": {"deal", "opportunity", "opportunity_name", "pipeline_name", "project"},
    "title": {"opportunity", "opportunity_name", "subject", "name"},
    "revenue_amount": {"revenue", "amount", "value", "deal_value", "pipeline_value", "total", "total_amount"},
    "opportunity_value": {"revenue", "amount", "value", "deal_value", "pipeline_value", "total", "total_amount"},
    "estimated_value": {"revenue", "amount", "value", "deal_value", "pipeline_value", "total", "total_amount"},
    "deal_status": {"status"},
    "stage": {"pipeline_stage", "deal_stage", "sales_stage"},
    "service_scope": {"scope", "service_type", "deal_type"},
    "project_name": {"project", "implementation", "project_title", "name"},
    "solution": {"sla", "service", "product", "solution_name"},
    "licence_name": {"license_name", "licence", "license", "subscription", "product"},
    "product_name": {"product", "solution", "software", "service"},
    "expiry_date": {"expiration_date", "licence_expiry", "license_expiry", "license_expiry_date"},
    "renewal_date": {"renewal", "renewal_due", "renewal_due_date"},
    "employee_code": {"staff_id", "employee_id", "personnel_no", "staff_number"},
    "department": {"dept", "business_unit", "team"},
    "gross_salary": {"salary", "basic_salary", "monthly_salary"},
    "net_pay": {"net_salary", "pay"},
    "invoice_number": {"invoice_no", "invoice", "bill_number"},
    "invoice_date": {"invoice_date", "date", "bill_date"},
    "subtotal": {"sub_total", "amount_before_tax", "net_amount"},
    "discount_amount": {"discount"},
    "paid_amount": {"paid", "amount_paid"},
    "budget_name": {"budget", "budget_name", "name", "department"},
    "budget_type": {"budget_type", "type"},
    "approved_amount": {"budget", "approved_budget", "approved_amount", "amount", "value"},
    "actual_amount": {"actual", "actual_spend", "spent", "used"},
    "vendor_name": {"vendor", "supplier", "manufacturer", "oem", "distributor"},
    "bill_number": {"bill", "bill_no", "bill_number", "invoice_number"},
    "bill_date": {"bill_date", "date", "invoice_date"},
    "payment_number": {"payment", "payment_no", "payment_number", "reference", "ref"},
    "payment_type": {"payment_type", "type"},
    "payment_date": {"payment_date", "date"},
    "receipt_number": {"receipt", "receipt_no", "receipt_number"},
    "receipt_date": {"receipt_date", "date"},
    "claim_number": {"claim", "claim_no", "claim_number", "reference"},
    "expense_category": {"expense_category", "category", "type"},
    "expense_date": {"expense_date", "date"},
    "asset_code": {"asset_code", "asset_tag", "tag", "code", "serial_number"},
    "asset_name": {"asset", "asset_name", "item", "name", "description"},
    "item_name": {"item", "asset", "product", "name", "description", "item_description", "asset_name", "inventory_item", "stock_item", "device", "equipment", "model"},
    "item_type": {"type", "asset_type", "inventory_type", "category_type"},
    "sku": {"serial", "serial_no", "serial_number", "part_number", "asset_tag", "tag", "code", "item_code"},
    "category": {"class", "group", "asset_category", "inventory_category"},
    "unit_cost": {"cost", "price", "unit_price", "purchase_price", "amount", "value"},
    "quantity_on_hand": {"qty", "quantity", "stock", "stock_quantity", "on_hand", "available", "available_quantity", "count"},
    "reorder_level": {"reorder", "minimum_stock", "min_stock", "threshold"},
    "warehouse_location": {"location", "warehouse", "store", "office", "site"},
    "custodian": {"owner", "assigned_to", "holder", "employee", "staff", "user"},
    "requester_name": {"requester", "employee", "staff_name", "name"},
    "request_type": {"request_type", "type", "category"},
    "event_name": {"event", "meeting", "activity", "name"},
    "module": {"module", "department", "section"},
    "resource_name": {"resource", "staff", "employee", "engineer", "name"},
    "allocation_target": {"allocated_to", "target", "project", "task", "assignment"},
    "capability": {"feature", "functionality"},
    "rule_name": {"rule", "workflow", "automation", "name"},
    "trigger_entity": {"trigger_entity", "entity", "resource"},
    "trigger_event": {"trigger", "event", "trigger_event"},
    "action_type": {"action", "action_type"},
}

IGNORED_IMPORT_HEADERS = {"actions", "action", "view", "edit", "delete", "follow_up", "followup"}


def _column_lookup_for_model(model: Any) -> dict[str, str]:
    lookup = {_normalized_key(column.name): column.name for column in model.__table__.columns}
    columns = {column.name for column in model.__table__.columns}
    for target, aliases in IMPORT_ALIASES.items():
        if target not in columns:
            continue
        for alias in aliases:
            lookup.setdefault(_normalized_key(alias), target)
    return lookup


def _apply_row_transforms(model: Any, payload: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    table = model.__tablename__
    columns = {column.name for column in model.__table__.columns}
    normalized_row = {_normalized_key(str(key)): value for key, value in row.items() if key is not None}

    full_name = (
        payload.get("contact_name")
        or normalized_row.get("full_name")
        or normalized_row.get("name")
        or normalized_row.get("employee_name")
        or normalized_row.get("staff_name")
    )
    if table in {"contacts", "hrm_employees"} and full_name:
        parts = str(full_name).strip().split()
        if "first_name" in columns and not payload.get("first_name"):
            payload["first_name"] = parts[0]
        if "last_name" in columns and not payload.get("last_name"):
            payload["last_name"] = " ".join(parts[1:]) or parts[0]

    if table == "contacts" and "last_name" in columns and payload.get("first_name") and not payload.get("last_name"):
        payload["last_name"] = payload["first_name"]
    if table == "accounts" and "company_name" in columns and not payload.get("company_name"):
        payload["company_name"] = normalized_row.get("account") or normalized_row.get("customer") or normalized_row.get("name")
    if table == "opportunities" and "title" in columns and not payload.get("title"):
        payload["title"] = normalized_row.get("opportunity") or normalized_row.get("deal") or normalized_row.get("name")
    if table == "leads":
        if "account_country" in columns and not payload.get("account_country"):
            payload["account_country"] = normalized_row.get("country")
        if "lead_source" in columns and not payload.get("lead_source"):
            payload["lead_source"] = normalized_row.get("source")
        if "assigned_to" in columns and not payload.get("assigned_to"):
            payload["assigned_to"] = normalized_row.get("owner") or normalized_row.get("am")
        external_id = normalized_row.get("id")
        if external_id and "notes" in columns and not payload.get("notes"):
            payload["notes"] = f"Import key: {external_id}"
    if table == "deals" and "deal_name" in columns and not payload.get("deal_name"):
        payload["deal_name"] = normalized_row.get("deal") or normalized_row.get("opportunity") or normalized_row.get("name")
    if table == "support_tickets" and "subject" in columns and not payload.get("subject"):
        payload["subject"] = normalized_row.get("ticket") or normalized_row.get("issue") or normalized_row.get("name")
    if table == "inventory_items" and "item_name" in columns and not payload.get("item_name"):
        fallback_keys = [
            "item",
            "item_name",
            "description",
            "item_description",
            "asset",
            "asset_name",
            "product",
            "model",
            "name",
        ]
        payload["item_name"] = next((normalized_row.get(key) for key in fallback_keys if normalized_row.get(key)), None)
        if not payload.get("item_name"):
            payload["item_name"] = next((str(value).strip() for value in row.values() if str(value).strip()), None)
    if table == "inventory_items" and "quantity_on_hand" in columns and not payload.get("quantity_on_hand"):
        payload["quantity_on_hand"] = normalized_row.get("qty") or normalized_row.get("quantity") or normalized_row.get("stock") or 1
    if table == "inventory_items" and "item_type" in columns and not payload.get("item_type"):
        payload["item_type"] = normalized_row.get("type") or "stock"

    return payload


def _first_row_value(row: dict[str, Any], keys: list[str]) -> Any:
    normalized_row = {_normalized_key(str(key)): value for key, value in row.items() if key is not None}
    for key in keys:
        value = normalized_row.get(_normalized_key(key))
        if value not in {None, ""}:
            return value
    return None


def _date_value(value: Any) -> date | None:
    if value in {None, ""}:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text_value = str(value).strip()
    if not text_value:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", text_value):
        try:
            return (date(1899, 12, 30) + timedelta(days=int(float(text_value))))
        except Exception:
            return None
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text_value[:10], pattern).date()
        except ValueError:
            continue
    return None


def _string_value(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    return str(value).strip()


def _resolve_account_id(db: Session, payload: dict[str, Any], row: dict[str, Any]) -> uuid.UUID | None:
    if payload.get("account_id"):
        return payload["account_id"]
    account_name = _string_value(
        payload.get("company_name")
        or _first_row_value(row, ["account", "account_name", "company", "customer", "client", "organization"])
    )
    if not account_name:
        return None
    account = db.query(CRMAccount).filter(CRMAccount.company_name.ilike(account_name)).first()
    if not account:
        account = CRMAccount(
            company_name=account_name,
            country=_string_value(payload.get("account_country") or _first_row_value(row, ["country"])),
            account_manager=_string_value(payload.get("assigned_to") or payload.get("account_manager") or _first_row_value(row, ["owner", "am"])),
        )
        assign_business_id(db, CRMAccount, account)
        db.add(account)
        db.flush()
    return account.id


def _resolve_employee_id(db: Session, payload: dict[str, Any], row: dict[str, Any]) -> uuid.UUID | None:
    if payload.get("employee_id"):
        return payload["employee_id"]
    email = _string_value(payload.get("email") or _first_row_value(row, ["email", "employee_email", "staff_email"]))
    if email:
        employee = db.query(HRMEmployee).filter(HRMEmployee.email.ilike(email)).first()
        if employee:
            return employee.id
    name = _string_value(
        payload.get("employee_name")
        or payload.get("staff_name")
        or _first_row_value(row, ["employee", "employee_name", "staff", "staff_name", "name"])
    )
    if name:
        parts = name.split()
        query = db.query(HRMEmployee).filter(HRMEmployee.first_name.ilike(parts[0]))
        if len(parts) > 1:
            query = query.filter(HRMEmployee.last_name.ilike(" ".join(parts[1:])))
        employee = query.first()
        if employee:
            return employee.id
    return None


def _apply_system_defaults(db: Session, model: Any, payload: dict[str, Any], row: dict[str, Any], index: int) -> dict[str, Any]:
    table = model.__tablename__
    columns = {column.name for column in model.__table__.columns}
    today = date.today()
    label = _string_value(
        payload.get("title")
        or payload.get("subject")
        or payload.get("description")
        or payload.get("company_name")
        or payload.get("department")
        or payload.get("project_name")
        or payload.get("document_title")
        or payload.get("item_name")
        or _first_row_value(row, ["name", "title", "subject", "description"])
    )
    row_code = _string_value(_first_row_value(row, ["id", "code", "number", "reference", "ref"]))

    if "account_id" in columns and not payload.get("account_id"):
        payload["account_id"] = _resolve_account_id(db, payload, row)
    if "employee_id" in columns and not payload.get("employee_id"):
        payload["employee_id"] = _resolve_employee_id(db, payload, row)

    generated_number = row_code or f"IMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{index}"
    number_fields = {
        "invoice_number",
        "quote_number",
        "bill_number",
        "payment_number",
        "receipt_number",
        "credit_note_number",
        "claim_number",
        "request_number",
        "po_number",
        "entry_number",
        "account_code",
        "asset_code",
        "ticket_number",
    }
    for field in number_fields:
        if field in columns and not payload.get(field):
            payload[field] = generated_number

    for field in ["invoice_date", "bill_date", "payment_date", "receipt_date", "issue_date", "expense_date", "request_date", "po_date", "entry_date", "recognition_date", "attendance_date", "engagement_date"]:
        if field in columns and not payload.get(field):
            payload[field] = today
    if "start_date" in columns and not payload.get("start_date"):
        payload["start_date"] = today
    if "end_date" in columns and not payload.get("end_date") and table == "hrm_leave":
        payload["end_date"] = payload.get("start_date") or today
    if "total_days" in columns and not payload.get("total_days") and table == "hrm_leave":
        payload["total_days"] = 1

    title_defaults = {
        "issue_title": label,
        "subject": label,
        "title": label,
        "project_name": label,
        "tender_title": label,
        "document_title": label,
        "activity_title": label,
        "record_title": label,
        "training_title": label,
        "budget_name": label,
        "service_name": label,
        "rule_name": label,
        "goal_name": label,
        "territory_name": label,
        "milestone_name": label,
        "risk_title": label,
        "task_name": label,
        "event_name": label,
        "resource_name": label,
        "capability": label,
        "connector_name": label,
        "requester_name": _string_value(_first_row_value(row, ["requester", "employee", "staff", "name"])) or label,
        "staff_name": _string_value(_first_row_value(row, ["staff", "employee", "name"])) or label,
    }
    for field, value in title_defaults.items():
        if field in columns and not payload.get(field) and value:
            payload[field] = value

    static_defaults = {
        "related_type": "general",
        "activity_type": "task",
        "engagement_type": "meeting",
        "owner_type": "AM",
        "target_owner": "Unassigned",
        "period_type": "annual",
        "period_label": str(today.year),
        "fiscal_year": str(today.year),
        "document_category": "General",
        "document_type": "General",
        "arena": "Advisory",
        "service_name": "Imported Service",
        "solution": "Imported Solution",
        "assigned_engineer": "Unassigned",
        "benefit_type": "General",
        "benefit_name": "Imported Benefit",
        "leave_type": "Annual",
        "review_period": str(today.year),
        "training_title": "Imported Training",
        "grc_area": "Compliance",
        "normal_balance": "Debit",
        "payment_type": "general",
        "budget_type": "Department",
        "expense_category": "General",
        "revenue_source": "Import",
        "revenue_type": "General",
        "tax_type": "VAT",
        "tax_period": str(today.year),
        "approval_type": "General",
        "related_record_type": "Import",
        "entity_type": "Import",
        "action": "import",
        "module": "General",
        "request_type": "General",
        "channel": "email",
        "allocation_target": label or "General",
        "mechanism": "Imported capability mapping",
        "connector_type": "API",
        "trigger_entity": "general",
        "trigger_event": "created",
        "action_type": "queue_notification",
        "event_name": label or "Imported Event",
    }
    for field, value in static_defaults.items():
        if field in columns and not payload.get(field):
            payload[field] = value

    if table == "hrm_employees":
        from backend.api.hrm.employees import _next_employee_code

        name = _string_value(_first_row_value(row, ["employee", "employee_name", "staff", "staff_name", "name"])) or "Imported Staff"
        parts = name.split()
        payload.setdefault("first_name", parts[0])
        payload.setdefault("last_name", " ".join(parts[1:]) or parts[0])
        payload.pop("employee_code", None)
        payload["employee_code"] = _next_employee_code(db)
        payload.setdefault("email", _string_value(_first_row_value(row, ["email"])) or f"{payload['employee_code'].lower()}@import.local")
    if table == "contacts":
        payload.setdefault("first_name", label or "Imported")
        payload.setdefault("last_name", "Contact")
    if table == "chart_accounts":
        payload.setdefault("account_code", generated_number)
        payload.setdefault("account_name", label or generated_number)
        payload.setdefault("account_type", "Asset")
        payload.setdefault("normal_balance", "Debit")
    if table == "budgets":
        payload.setdefault("budget_name", label or f"Imported Budget {generated_number}")
        payload.setdefault("budget_type", "Department")
        payload.setdefault("fiscal_year", str(today.year))
    if table == "journal_lines" and (not payload.get("journal_entry_id") or not payload.get("account_id")):
        return payload

    return payload


def _clean_import_row(model: Any, row: dict[str, Any]) -> dict[str, Any]:
    by_normalized = _column_lookup_for_model(model)
    payload: dict[str, Any] = {}
    for raw_key, value in row.items():
        if raw_key is None:
            continue
        normalized_header = _normalized_key(str(raw_key))
        if normalized_header in IGNORED_IMPORT_HEADERS:
            continue
        column_name = by_normalized.get(normalized_header)
        if not column_name or column_name in {"id", "created_at", "updated_at"}:
            continue
        payload[column_name] = value

    payload = _apply_row_transforms(model, payload, row)

    for column in model.__table__.columns:
        if column.name not in payload:
            continue
        value = payload[column.name]
        if value in {"", None}:
            payload[column.name] = None
            continue
        column_type = column.type
        if isinstance(column_type, PG_UUID):
            try:
                payload[column.name] = uuid.UUID(str(value))
            except ValueError:
                if column.nullable:
                    payload[column.name] = None
                else:
                    raise HTTPException(status_code=422, detail=f"{column.name} must be a valid system UUID.")
        elif isinstance(column_type, Boolean):
            payload[column.name] = str(value).strip().lower() in {"1", "true", "yes", "y", "active"}
        elif isinstance(column_type, Integer):
            try:
                payload[column.name] = int(float(str(value).replace(",", "")))
            except ValueError:
                payload[column.name] = None
        elif isinstance(column_type, Numeric):
            try:
                numeric_text = re.sub(r"[^0-9.\-]", "", str(value))
                payload[column.name] = Decimal(numeric_text or "0")
            except Exception:
                payload[column.name] = Decimal("0")
        elif isinstance(column_type, DateTime):
            try:
                payload[column.name] = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                payload[column.name] = None
        elif isinstance(column_type, Date):
            try:
                payload[column.name] = date.fromisoformat(str(value)[:10])
            except ValueError:
                payload[column.name] = None
        elif column.name in {"configuration", "sample_payload", "condition_json", "action_payload", "context", "dependency_ids", "attendees"} and isinstance(value, str):
            try:
                payload[column.name] = json.loads(value)
            except json.JSONDecodeError:
                payload[column.name] = {"raw": value}

    if model is FinanceInvoice:
        payload = automate_invoice_payload(payload)
    return {key: value for key, value in payload.items() if value is not None}


def _required_import_fields(model: Any) -> list[str]:
    return [
        column.name
        for column in model.__table__.columns
        if not column.nullable
        and column.default is None
        and column.server_default is None
        and not column.primary_key
        and column.name not in {"created_at", "updated_at"}
    ]


def _validate_import_payload(model: Any, payload: dict[str, Any]) -> list[str]:
    missing = [field for field in _required_import_fields(model) if not payload.get(field)]
    if missing:
        return [f"missing required field(s): {', '.join(missing)}. Upload this file on the correct page or include columns for these fields."]

    useful_keys = [key for key, value in payload.items() if value not in {"", None, Decimal("0")}]
    if len(useful_keys) < 1:
        return ["no usable columns matched this section"]
    return []


def _find_existing_import_record(db: Session, model: Any, payload: dict[str, Any]):
    business_id = payload.get("business_id")
    if business_id and "business_id" in model.__table__.columns and str(business_id).startswith("IS-"):
        existing = db.query(model).filter(model.business_id == business_id).first()
        if existing:
            return existing

    table = model.__tablename__
    if table == "leads" and payload.get("company_name") and payload.get("contact_name"):
        return (
            db.query(model)
            .filter(model.company_name == payload["company_name"], model.contact_name == payload["contact_name"])
            .first()
        )
    if table == "accounts" and payload.get("company_name"):
        return db.query(model).filter(model.company_name == payload["company_name"]).first()
    if table == "contacts" and payload.get("email"):
        return db.query(model).filter(model.email == payload["email"]).first()
    if table == "deals" and payload.get("deal_name"):
        query = db.query(model).filter(model.deal_name == payload["deal_name"])
        if payload.get("owner"):
            query = query.filter(model.owner == payload["owner"])
        return query.first()
    if table == "opportunities" and payload.get("title"):
        query = db.query(model).filter(model.title == payload["title"])
        if payload.get("owner"):
            query = query.filter(model.owner == payload["owner"])
        return query.first()
    if table == "inventory_items":
        if payload.get("sku"):
            existing = db.query(model).filter(model.sku == payload["sku"]).first()
            if existing:
                return existing
        if payload.get("item_name"):
            query = db.query(model).filter(model.item_name == payload["item_name"])
            if payload.get("vendor_name"):
                query = query.filter(model.vendor_name == payload["vendor_name"])
            return query.first()
    if table == "hrm_employees" and payload.get("email"):
        return db.query(model).filter(model.email == payload["email"]).first()
    if table == "support_tickets" and payload.get("ticket_number"):
        return db.query(model).filter(model.ticket_number == payload["ticket_number"]).first()
    if table == "project_tasks" and payload.get("project_id") and payload.get("task_name"):
        return db.query(model).filter(model.project_id == payload["project_id"], model.task_name == payload["task_name"]).first()
    return None


def _import_rows_for_endpoint(db: Session, endpoint: str, rows: list[dict[str, Any]], user: UserResponse) -> tuple[int, int, int, list[str]]:
    model, _entity_key = _model_for_bulk_endpoint(endpoint)
    imported = 0
    updated = 0
    errors = 0
    messages: list[str] = []
    for index, row in enumerate(rows, start=2):
        try:
            payload = _clean_import_row(model, row)
            payload = _apply_system_defaults(db, model, payload, row, index)
            if not payload:
                errors += 1
                if len(messages) < 8:
                    messages.append(f"Row {index}: no usable columns matched this section")
                continue
            validation_errors = _validate_import_payload(model, payload)
            if validation_errors:
                errors += 1
                if len(messages) < 8:
                    messages.append(f"Row {index}: {'; '.join(validation_errors)}")
                continue
            if "created_by" in model.__table__.columns and not payload.get("created_by"):
                payload["created_by"] = user.full_name
            if "uploaded_by" in model.__table__.columns and not payload.get("uploaded_by"):
                payload["uploaded_by"] = user.full_name
            record = _find_existing_import_record(db, model, payload)
            if record:
                for key, value in payload.items():
                    if key in {"id", "business_id", "created_at"}:
                        continue
                    setattr(record, key, value)
                updated += 1
                is_new_record = False
            else:
                record = model(**payload)
                assign_business_id(db, model, record)
                db.add(record)
                imported += 1
                is_new_record = True
            db.flush()
            if isinstance(record, HRMEmployee):
                from backend.api.hrm.employees import _add_lifecycle_event, _audit_employee_number_generation, _sync_employee_foundation

                if is_new_record:
                    _audit_employee_number_generation(db, record, user, None)
                    _add_lifecycle_event(db, record, "hire", None, record.employment_status)
                _sync_employee_foundation(db, record)
            _ensure_licence_invoice(db, record)
            _apply_simple_workflows(db, endpoint, record, user)
            db.commit()
        except Exception as exc:
            db.rollback()
            errors += 1
            if len(messages) < 8:
                messages.append(f"Row {index}: {exc}")
    return imported, updated, errors, messages


def _import_pipeline_rows(db: Session, rows: list[dict[str, Any]]) -> int:
    imported = 0
    for row in rows:
        name = row.get("deal_name") or row.get("Deal") or row.get("deal") or row.get("Opportunity") or row.get("opportunity")
        if not name:
            continue
        amount = row.get("revenue_amount") or row.get("amount") or row.get("value") or 0
        deal = CRMDeal(
            business_id=_next_business_id(db, "crm.deals"),
            deal_name=str(name),
            owner=row.get("owner") or row.get("AM") or row.get("account_manager"),
            stage=row.get("stage") or "Stage 1.a Discovery",
            deal_status=row.get("status") or "open",
            pipeline_type=row.get("pipeline_type") or row.get("type"),
            arena=row.get("arena"),
            country=row.get("country"),
            vertical=row.get("vertical"),
            revenue_amount=amount or 0,
            renewal_date=row.get("renewal_date") or None,
            licence_expiry_date=row.get("licence_expiry_date") or row.get("expiry_date") or None,
            notes=row.get("notes"),
        )
        db.add(deal)
        imported += 1
    return imported


@router.get("/enterprise/{resource}")
def list_resource(
    resource: str,
    query: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    config = CRUD_RESOURCES.get(resource)
    if not config:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource in ADMIN_ONLY_RESOURCES:
        _require_admin(user)
    model = config["model"]
    stmt = db.query(model)
    if query:
        term = f"%{query}%"
        filters = [getattr(model, field).ilike(term) for field in config["search"] if hasattr(model, field)]
        if filters:
            stmt = stmt.filter(or_(*filters))
    return [_serialize(item) for item in stmt.order_by(model.created_at.desc() if hasattr(model, "created_at") else model.id.desc()).limit(200).all()]


@router.get("/integrations/summary")
def integrations_summary(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin_or_manager(user)
    connectors = db.query(IntegrationConnector).all()
    imports = db.query(DataImportBatch).order_by(DataImportBatch.created_at.desc()).limit(10).all()
    active = [item for item in connectors if (item.status or "").lower() == "active"]
    failed_imports = [item for item in imports if (item.status or "").lower() in {"failed", "error"} or (item.error_rows or 0) > 0]
    formats: dict[str, int] = {}
    for item in db.query(DataImportBatch).all():
        key = item.source_format or "unknown"
        formats[key] = formats.get(key, 0) + 1
    return {
        "connectors": {
            "total": len(connectors),
            "active": len(active),
            "inactive": max(len(connectors) - len(active), 0),
            "by_type": {
                connector_type: len([item for item in connectors if item.connector_type == connector_type])
                for connector_type in sorted({item.connector_type for item in connectors if item.connector_type})
            },
        },
        "imports": {
            "total": db.query(DataImportBatch).count(),
            "recent": [_serialize(item) for item in imports],
            "failed_recent": len(failed_imports),
            "formats": formats,
            "imported_rows": sum(item.imported_rows or 0 for item in db.query(DataImportBatch).all()),
            "error_rows": sum(item.error_rows or 0 for item in db.query(DataImportBatch).all()),
        },
        "readiness": [
            {"label": "Gateway configuration", "status": "ready" if connectors else "needs_setup"},
            {"label": "Data ingestion", "status": "ready" if imports else "needs_upload"},
            {"label": "Import quality", "status": "attention" if failed_imports else "healthy"},
        ],
    }


@router.post("/enterprise/{resource}", status_code=status.HTTP_201_CREATED)
def create_resource(
    resource: str,
    payload: FlexiblePayload,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    config = CRUD_RESOURCES.get(resource)
    if not config:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource in ADMIN_ONLY_RESOURCES:
        _require_admin(user)
    else:
        _require_admin_or_manager(user)
    model = config["model"]
    data = _clean_payload(model, payload.model_dump())
    if "business_id" in {column.name for column in model.__table__.columns} and not data.get("business_id"):
        data["business_id"] = _next_business_id(db, config["entity_key"])
    if model is HRMEmployee:
        from backend.api.hrm.employees import _next_employee_code

        data.pop("employee_code", None)
        data["employee_code"] = _next_employee_code(db)
    if "created_by" in {column.name for column in model.__table__.columns} and not data.get("created_by"):
        data["created_by"] = user.full_name
    record = model(**data)
    db.add(record)
    if isinstance(record, HRMEmployee):
        from backend.api.hrm.employees import _add_lifecycle_event, _audit_employee_number_generation, _sync_employee_foundation

        db.flush()
        _audit_employee_number_generation(db, record, user, None)
        _add_lifecycle_event(db, record, "hire", None, record.employment_status)
        _sync_employee_foundation(db, record)
    _ensure_licence_invoice(db, record)
    _apply_simple_workflows(db, resource, record, user)
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.put("/enterprise/{resource}/{record_id}")
def update_resource(
    resource: str,
    record_id: uuid.UUID,
    payload: FlexiblePayload,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    config = CRUD_RESOURCES.get(resource)
    if not config:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource in ADMIN_ONLY_RESOURCES:
        _require_admin(user)
    else:
        _require_admin_or_manager(user)
    model = config["model"]
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    for key, value in _clean_payload(model, payload.model_dump(exclude_unset=True)).items():
        if model is HRMEmployee and key == "employee_code":
            continue
        setattr(record, key, value)
    _ensure_licence_invoice(db, record)
    _apply_simple_workflows(db, resource, record, user)
    db.commit()
    db.refresh(record)
    return _serialize(record)


@router.delete("/enterprise/{resource}/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource: str,
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    config = CRUD_RESOURCES.get(resource)
    if not config:
        raise HTTPException(status_code=404, detail="Resource not found")
    _require_admin(user)
    model = config["model"]
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()


@router.get("/entities/search")
def entity_search(
    query: str = Query(..., min_length=2),
    entity_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    term = f"%{query}%"
    results: list[dict[str, Any]] = []
    include = lambda key: entity_type in {None, "", "all", key}

    if include("accounts"):
        for item in db.query(CRMAccount).filter(or_(CRMAccount.company_name.ilike(term), CRMAccount.account_manager.ilike(term), CRMAccount.business_id.ilike(term))).limit(10):
            results.append({"type": "accounts", "id": str(item.id), "title": item.company_name, "subtitle": f"{item.business_id or 'No ID'} | {item.account_manager or 'No AM'} | {item.country or 'No country'}"})
    if include("leads"):
        for item in db.query(CRMLead).filter(or_(CRMLead.contact_name.ilike(term), CRMLead.company_name.ilike(term), CRMLead.assigned_to.ilike(term), CRMLead.business_id.ilike(term))).limit(10):
            results.append({"type": "leads", "id": str(item.id), "title": item.contact_name, "subtitle": f"{item.business_id or 'No ID'} | {item.company_name or 'No company'} | {item.status or 'New'}"})
    if include("opportunities"):
        for item in db.query(CRMOpportunity).filter(or_(CRMOpportunity.title.ilike(term), CRMOpportunity.owner.ilike(term), CRMOpportunity.stage.ilike(term), CRMOpportunity.business_id.ilike(term))).limit(10):
            results.append({"type": "opportunities", "id": str(item.id), "title": item.title, "subtitle": f"{item.business_id or 'No ID'} | {item.owner or 'No owner'} | {item.stage or 'Discovery'}"})
    if include("deals"):
        for item in db.query(CRMDeal).filter(or_(CRMDeal.deal_name.ilike(term), CRMDeal.owner.ilike(term), CRMDeal.business_id.ilike(term))).limit(10):
            results.append({"type": "deals", "id": str(item.id), "title": item.deal_name, "subtitle": f"{item.business_id or 'No ID'} | {item.owner or 'No owner'} | {item.deal_status or 'open'}"})
    if include("projects"):
        for item in db.query(CRMPMOProject).filter(or_(CRMPMOProject.project_name.ilike(term), CRMPMOProject.project_manager.ilike(term))).limit(10):
            results.append({"type": "projects", "id": str(item.id), "title": item.project_name, "subtitle": f"{item.project_manager or 'No PM'} | {item.status or 'active'}"})
    if include("slas"):
        for item in db.query(CRMSLAAssignment).filter(or_(CRMSLAAssignment.solution.ilike(term), CRMSLAAssignment.assigned_engineer.ilike(term))).limit(10):
            results.append({"type": "slas", "id": str(item.id), "title": item.solution, "subtitle": f"{item.assigned_engineer or 'Unassigned'} | {item.status or 'active'}"})
    if include("departments") and user.role in {"admin", "manager"}:
        for item in db.query(HRMDepartment).filter(HRMDepartment.name.ilike(term)).limit(10):
            results.append({"type": "departments", "id": str(item.id), "title": item.name, "subtitle": item.status or "active"})
    if include("staff") and user.role in {"admin", "manager"}:
        for item in db.query(HRMEmployee).filter(or_(HRMEmployee.first_name.ilike(term), HRMEmployee.last_name.ilike(term), HRMEmployee.email.ilike(term))).limit(10):
            results.append({"type": "staff", "id": str(item.id), "title": f"{item.first_name} {item.last_name}", "subtitle": f"{item.department or 'No department'} | {item.job_title or 'No role'}"})
    if include("licences"):
        for item in db.query(CRMLicence).filter(or_(CRMLicence.licence_name.ilike(term), CRMLicence.product_name.ilike(term), CRMLicence.account_manager.ilike(term))).limit(10):
            results.append({"type": "licences", "id": str(item.id), "title": item.licence_name, "subtitle": f"{item.product_name or 'Licence'} | expires {item.expiry_date or 'not set'}"})
    if include("contacts"):
        for item in db.query(CRMContact).filter(or_(CRMContact.first_name.ilike(term), CRMContact.last_name.ilike(term), CRMContact.email.ilike(term))).limit(10):
            results.append({"type": "contacts", "id": str(item.id), "title": f"{item.first_name} {item.last_name}", "subtitle": item.email or item.job_title or "Contact"})
    if include("finance-invoices") and user.role == "admin":
        for item in db.query(FinanceInvoice).filter(or_(FinanceInvoice.invoice_number.ilike(term), FinanceInvoice.status.ilike(term), FinanceInvoice.business_id.ilike(term))).limit(10):
            results.append({"type": "finance-invoices", "id": str(item.id), "title": item.invoice_number, "subtitle": f"{item.business_id or 'No ID'} | {item.status or 'draft'} | {float(item.total_amount or 0):,.0f}"})
    if include("connectors") and user.role == "admin":
        for item in db.query(IntegrationConnector).filter(or_(IntegrationConnector.connector_name.ilike(term), IntegrationConnector.connector_type.ilike(term), IntegrationConnector.business_id.ilike(term))).limit(10):
            results.append({"type": "connectors", "id": str(item.id), "title": item.connector_name, "subtitle": f"{item.connector_type} | {item.status or 'draft'}"})
    if include("imports") and user.role == "admin":
        for item in db.query(DataImportBatch).filter(or_(DataImportBatch.source_name.ilike(term), DataImportBatch.file_name.ilike(term), DataImportBatch.business_id.ilike(term))).limit(10):
            results.append({"type": "imports", "id": str(item.id), "title": item.source_name or item.file_name or "Import", "subtitle": f"{item.target_resource} | {item.imported_rows or 0} imported"})
    if include("support-tickets"):
        for item in db.query(SupportTicket).filter(or_(SupportTicket.subject.ilike(term), SupportTicket.ticket_number.ilike(term), SupportTicket.business_id.ilike(term), SupportTicket.assigned_to.ilike(term))).limit(10):
            results.append({"type": "support-tickets", "id": str(item.id), "title": item.subject, "subtitle": f"{item.business_id or item.ticket_number or 'No ID'} | {item.status or 'open'}"})
    if include("project-tasks"):
        for item in db.query(ProjectTask).filter(or_(ProjectTask.task_name.ilike(term), ProjectTask.assigned_to.ilike(term), ProjectTask.business_id.ilike(term))).limit(10):
            results.append({"type": "project-tasks", "id": str(item.id), "title": item.task_name, "subtitle": f"{item.assigned_to or 'Unassigned'} | {item.status or 'not started'}"})
    if include("project-milestones"):
        for item in db.query(ProjectMilestone).filter(or_(ProjectMilestone.milestone_name.ilike(term), ProjectMilestone.owner.ilike(term), ProjectMilestone.business_id.ilike(term))).limit(10):
            results.append({"type": "project-milestones", "id": str(item.id), "title": item.milestone_name, "subtitle": f"{item.owner or 'No owner'} | {item.status or 'planned'}"})
    if include("project-risks"):
        for item in db.query(ProjectRisk).filter(or_(ProjectRisk.risk_title.ilike(term), ProjectRisk.owner.ilike(term), ProjectRisk.business_id.ilike(term))).limit(10):
            results.append({"type": "project-risks", "id": str(item.id), "title": item.risk_title, "subtitle": f"{item.impact or 'medium'} impact | {item.status or 'open'}"})
    if include("goals"):
        for item in db.query(OrganizationGoal).filter(or_(OrganizationGoal.goal_name.ilike(term), OrganizationGoal.owner.ilike(term), OrganizationGoal.business_id.ilike(term))).limit(10):
            results.append({"type": "goals", "id": str(item.id), "title": item.goal_name, "subtitle": f"{item.module} | {item.status or 'active'}"})
    if include("inventory-items"):
        for item in db.query(ERPInventoryItem).filter(or_(ERPInventoryItem.item_name.ilike(term), ERPInventoryItem.sku.ilike(term), ERPInventoryItem.business_id.ilike(term))).limit(10):
            results.append({"type": "inventory-items", "id": str(item.id), "title": item.item_name, "subtitle": f"{item.sku or 'No SKU'} | qty {item.quantity_on_hand or 0}"})
    if include("portal-requests"):
        for item in db.query(PortalRequest).filter(or_(PortalRequest.subject.ilike(term), PortalRequest.requester_name.ilike(term), PortalRequest.business_id.ilike(term))).limit(10):
            results.append({"type": "portal-requests", "id": str(item.id), "title": item.subject, "subtitle": f"{item.requester_name} | {item.status or 'submitted'}"})
    if include("communications"):
        for item in db.query(CommunicationLog).filter(or_(CommunicationLog.subject.ilike(term), CommunicationLog.contact_name.ilike(term), CommunicationLog.owner.ilike(term), CommunicationLog.business_id.ilike(term))).limit(10):
            results.append({"type": "communications", "id": str(item.id), "title": item.subject or item.summary or item.channel, "subtitle": f"{item.channel} | {item.owner or 'No owner'}"})
    if include("schedule-events"):
        for item in db.query(ScheduleEvent).filter(or_(ScheduleEvent.event_name.ilike(term), ScheduleEvent.owner.ilike(term), ScheduleEvent.business_id.ilike(term))).limit(10):
            results.append({"type": "schedule-events", "id": str(item.id), "title": item.event_name, "subtitle": f"{item.module} | {item.status or 'scheduled'}"})
    if include("resource-allocations"):
        for item in db.query(ResourceAllocation).filter(or_(ResourceAllocation.resource_name.ilike(term), ResourceAllocation.allocation_target.ilike(term), ResourceAllocation.business_id.ilike(term))).limit(10):
            results.append({"type": "resource-allocations", "id": str(item.id), "title": item.resource_name, "subtitle": f"{item.allocation_target} | {item.capacity_percent or 0}% capacity"})
    if include("capabilities"):
        for item in db.query(FeatureCapability).filter(or_(FeatureCapability.category.ilike(term), FeatureCapability.capability.ilike(term), FeatureCapability.module.ilike(term))).limit(10):
            results.append({"type": "capabilities", "id": str(item.id), "title": item.capability, "subtitle": f"{item.category} | {item.implementation_status}"})

    return results[:50]


@router.get("/entities/{entity_type}/{record_id}")
def entity_detail(
    entity_type: str,
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    if entity_type == "accounts":
        account = db.query(CRMAccount).filter(CRMAccount.id == record_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        deals = db.query(CRMDeal).filter(CRMDeal.account_id == account.id).all()
        opportunities = db.query(CRMOpportunity).filter(CRMOpportunity.account_id == account.id).all()
        crm_invoices = db.query(CRMInvoice).filter(CRMInvoice.account_id == account.id).all()
        finance_invoices = db.query(FinanceInvoice).filter(FinanceInvoice.account_id == account.id).all()
        contacts = db.query(CRMContact).filter(CRMContact.account_id == account.id).all()
        projects = db.query(CRMPMOProject).filter(CRMPMOProject.account_id == account.id).all()
        slas = db.query(CRMSLAAssignment).filter(CRMSLAAssignment.account_id == account.id).all()
        licences = db.query(CRMLicence).filter(CRMLicence.account_id == account.id).all()
        tickets = db.query(SupportTicket).filter(SupportTicket.account_id == account.id).all()
        revenue = sum(float(item.revenue_amount or 0) for item in deals) + sum(float(item.paid_amount or 0) for item in finance_invoices)
        team = sorted({value for row in deals + projects + slas for value in [getattr(row, "owner", None), getattr(row, "account_manager", None), getattr(row, "project_manager", None), getattr(row, "assigned_engineer", None), getattr(row, "technical_lead", None)] if value})
        return {
            "type": "accounts",
            "record": _serialize(account),
            "metrics": [
                {"label": "Total revenue", "value": revenue},
                {"label": "Deals", "value": len(deals)},
                {"label": "Projects", "value": len(projects)},
                {"label": "SLAs", "value": len(slas)},
                {"label": "Licences", "value": len(licences)},
                {"label": "Tickets", "value": len(tickets)},
            ],
            "sections": {
                "deals": [_serialize(item) for item in deals],
                "opportunities": [_serialize(item) for item in opportunities],
                "crm_invoices": [_serialize(item) for item in crm_invoices],
                "finance_invoices": [_serialize(item) for item in finance_invoices],
                "contacts": [_serialize(item) for item in contacts],
                "projects": [_serialize(item) for item in projects],
                "slas": [_serialize(item) for item in slas],
                "licences": [_serialize(item) for item in licences],
                "support_tickets": [_serialize(item) for item in tickets],
                "team": [{"name": name} for name in team],
            },
        }

    model_map = {
        "leads": CRMLead,
        "opportunities": CRMOpportunity,
        "deals": CRMDeal,
        "projects": CRMPMOProject,
        "slas": CRMSLAAssignment,
        "departments": HRMDepartment,
        "staff": HRMEmployee,
        "licences": CRMLicence,
        "contacts": CRMContact,
        "finance-invoices": FinanceInvoice,
        "connectors": IntegrationConnector,
        "imports": DataImportBatch,
        "staff-roles": StaffRoleAssignment,
        "workflow-rules": WorkflowRule,
        "workflow-logs": WorkflowRunLog,
        "notifications": NotificationEvent,
        "support-tickets": SupportTicket,
        "knowledge-base": KnowledgeBaseArticle,
        "project-tasks": ProjectTask,
        "project-milestones": ProjectMilestone,
        "project-risks": ProjectRisk,
        "inventory-items": ERPInventoryItem,
        "goals": OrganizationGoal,
        "territories": TerritoryRule,
        "portal-requests": PortalRequest,
        "communications": CommunicationLog,
        "schedule-events": ScheduleEvent,
        "resource-allocations": ResourceAllocation,
        "capabilities": FeatureCapability,
    }
    model = model_map.get(entity_type)
    if not model:
        raise HTTPException(status_code=404, detail="Entity type not found")
    if entity_type in {"departments", "staff"} and user.role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Restricted entity")
    if entity_type in {"finance-invoices", "connectors", "imports"} and user.role != "admin":
        raise HTTPException(status_code=403, detail="System admin access required")
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    sections: dict[str, list[dict[str, Any]]] = {}
    metrics: list[dict[str, Any]] = []

    if entity_type == "deals":
        account = db.query(CRMAccount).filter(CRMAccount.id == record.account_id).first() if record.account_id else None
        licences = db.query(CRMLicence).filter(CRMLicence.deal_id == record.id).all()
        projects = db.query(CRMPMOProject).filter(CRMPMOProject.deal_id == record.id).all()
        invoices = db.query(FinanceInvoice).filter(FinanceInvoice.deal_id == record.id).all()
        metrics = [
            {"label": "Revenue", "value": float(record.revenue_amount or 0)},
            {"label": "Gross profit", "value": float(record.gross_profit or 0)},
            {"label": "Licences", "value": len(licences)},
            {"label": "Projects", "value": len(projects)},
        ]
        sections = {
            "account": [_serialize(account)] if account else [],
            "licences": [_serialize(item) for item in licences],
            "projects": [_serialize(item) for item in projects],
            "finance_invoices": [_serialize(item) for item in invoices],
        }
    elif entity_type == "projects":
        account = db.query(CRMAccount).filter(CRMAccount.id == record.account_id).first() if record.account_id else None
        deal = db.query(CRMDeal).filter(CRMDeal.id == record.deal_id).first() if record.deal_id else None
        slas = db.query(CRMSLAAssignment).filter(CRMSLAAssignment.project_id == record.id).all()
        licences = db.query(CRMLicence).filter(CRMLicence.project_id == record.id).all()
        tasks = db.query(ProjectTask).filter(ProjectTask.project_id == record.id).all()
        milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == record.id).all()
        risks = db.query(ProjectRisk).filter(ProjectRisk.project_id == record.id).all()
        metrics = [{"label": "SLAs", "value": len(slas)}, {"label": "Licences", "value": len(licences)}, {"label": "Tasks", "value": len(tasks)}, {"label": "Risks", "value": len(risks)}]
        sections = {
            "account": [_serialize(account)] if account else [],
            "deal": [_serialize(deal)] if deal else [],
            "slas": [_serialize(item) for item in slas],
            "licences": [_serialize(item) for item in licences],
            "tasks": [_serialize(item) for item in tasks],
            "milestones": [_serialize(item) for item in milestones],
            "risks": [_serialize(item) for item in risks],
        }
    elif entity_type == "slas":
        account = db.query(CRMAccount).filter(CRMAccount.id == record.account_id).first() if record.account_id else None
        project = db.query(CRMPMOProject).filter(CRMPMOProject.id == record.project_id).first() if record.project_id else None
        sections = {
            "account": [_serialize(account)] if account else [],
            "project": [_serialize(project)] if project else [],
            "team": [{"name": value} for value in [record.assigned_engineer, record.technical_lead] if value],
        }
    elif entity_type == "licences":
        account = db.query(CRMAccount).filter(CRMAccount.id == record.account_id).first() if record.account_id else None
        deal = db.query(CRMDeal).filter(CRMDeal.id == record.deal_id).first() if record.deal_id else None
        project = db.query(CRMPMOProject).filter(CRMPMOProject.id == record.project_id).first() if record.project_id else None
        days_to_expiry = (record.expiry_date - date.today()).days if record.expiry_date else None
        metrics = [
            {"label": "Days to expiry", "value": days_to_expiry if days_to_expiry is not None else "Not set"},
            {"label": "Notice days", "value": record.renewal_notice_days or 60},
        ]
        sections = {
            "account": [_serialize(account)] if account else [],
            "deal": [_serialize(deal)] if deal else [],
            "project": [_serialize(project)] if project else [],
            "notification_plan": [
                {
                    "recipient": email,
                    "purpose": "Renewal reminder",
                    "status": record.notification_status,
                }
                for email in [record.account_manager, record.customer_contact_email, record.oem_contact_email]
                if email
            ],
        }
    elif entity_type == "departments":
        staff = db.query(HRMEmployee).filter(HRMEmployee.department == record.name).all()
        roles = db.query(StaffRoleAssignment).filter(StaffRoleAssignment.department == record.name).all()
        metrics = [{"label": "Staff", "value": len(staff)}, {"label": "Role assignments", "value": len(roles)}]
        sections = {"staff": [_serialize(item) for item in staff], "roles": [_serialize(item) for item in roles]}
    elif entity_type == "staff":
        name = f"{record.first_name} {record.last_name}"
        roles = db.query(StaffRoleAssignment).filter(StaffRoleAssignment.staff_name.ilike(f"%{name}%")).all()
        deals = db.query(CRMDeal).filter(CRMDeal.owner.ilike(f"%{name}%")).all()
        projects = db.query(CRMPMOProject).filter(or_(CRMPMOProject.project_manager.ilike(f"%{name}%"), CRMPMOProject.account_manager.ilike(f"%{name}%"), CRMPMOProject.technical_lead.ilike(f"%{name}%"))).all()
        slas = db.query(CRMSLAAssignment).filter(or_(CRMSLAAssignment.assigned_engineer.ilike(f"%{name}%"), CRMSLAAssignment.technical_lead.ilike(f"%{name}%"))).all()
        metrics = [{"label": "Roles", "value": len(roles)}, {"label": "Deals", "value": len(deals)}, {"label": "Projects", "value": len(projects)}, {"label": "SLAs", "value": len(slas)}]
        sections = {"roles": [_serialize(item) for item in roles], "deals": [_serialize(item) for item in deals], "projects": [_serialize(item) for item in projects], "slas": [_serialize(item) for item in slas]}

    return {"type": entity_type, "record": _serialize(record), "metrics": metrics, "sections": sections}


@router.get("/licences/renewal-alerts")
def licence_renewal_alerts(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin_or_manager(user)
    today = date.today()
    alerts = (
        db.query(CRMLicence)
        .filter(
            CRMLicence.status == "active",
            CRMLicence.expiry_date.isnot(None),
            CRMLicence.expiry_date <= today + timedelta(days=90),
        )
        .order_by(CRMLicence.expiry_date.asc())
        .limit(100)
        .all()
    )
    return [
        {
            **_serialize(item),
            "email_to": [email for email in [item.account_manager, item.customer_contact_email, item.oem_contact_email] if email],
            "message": f"Licence {item.licence_name} expires on {item.expiry_date}. Renewal owner: {item.account_manager or 'unassigned'}.",
        }
        for item in alerts
    ]


@router.post("/licences/renewal-alerts/schedule")
def schedule_licence_renewal_alerts(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin_or_manager(user)
    today = date.today()
    alerts = (
        db.query(CRMLicence)
        .filter(
            CRMLicence.status == "active",
            CRMLicence.expiry_date.isnot(None),
            CRMLicence.expiry_date <= today + timedelta(days=90),
        )
        .order_by(CRMLicence.expiry_date.asc())
        .limit(100)
        .all()
    )
    scheduled = []
    for item in alerts:
        recipients = [email for email in [item.account_manager, item.customer_contact_email, item.oem_contact_email] if email]
        item.notification_status = "scheduled" if recipients else "blocked"
        scheduled.append(
            {
                "licence_id": str(item.id),
                "licence_name": item.licence_name,
                "recipients": recipients,
                "status": item.notification_status,
                "subject": f"Licence renewal reminder: {item.licence_name}",
                "body": f"{item.licence_name} expires on {item.expiry_date}. Please initiate renewal before {item.renewal_date or item.expiry_date}.",
            }
        )
    db.commit()
    return {"scheduled_count": len([item for item in scheduled if item["status"] == "scheduled"]), "notifications": scheduled}


@router.post("/integrations/imports/upload", status_code=status.HTTP_201_CREATED)
async def upload_import_file(
    target_resource: str = Query(default="pipeline"),
    source_name: str | None = Query(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_admin_or_manager(user)
    content = await file.read()
    rows, summary = _extract_textish_summary(content, file.filename or "upload")
    imported = 0
    errors = 0
    if target_resource in {"pipeline", "deals"} and rows:
        try:
            imported = _import_pipeline_rows(db, rows)
        except Exception as exc:
            errors = len(rows)
            summary = f"{summary} Import failed: {exc}"

    batch = DataImportBatch(
        business_id=_next_business_id(db, "auth.data_import_batches"),
        source_name=source_name or "Manual upload",
        source_format=(file.filename or "").rsplit(".", 1)[-1].lower() or "unknown",
        target_resource=target_resource,
        file_name=file.filename,
        parsed_rows=len(rows),
        imported_rows=imported,
        error_rows=errors,
        status="imported" if imported else "parsed",
        uploaded_by=user.full_name,
        parse_summary=summary,
        sample_payload=rows[:5],
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return _serialize(batch)


@router.post("/integrations/imports/bulk-upload", status_code=status.HTTP_201_CREATED)
async def upload_resource_file(
    endpoint: str = Query(...),
    resource_title: str | None = Query(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_admin_or_manager(user)
    content = await file.read()
    rows, summary = _extract_textish_summary(content, file.filename or "upload")
    if not rows:
        raise HTTPException(status_code=422, detail="No structured rows were found. Upload a CSV or Excel file with column headers matching the form field names.")

    imported, updated, errors, messages = _import_rows_for_endpoint(db, endpoint, rows, user)
    if imported + updated == 0:
        detail = " ".join(messages)[:1500] or "The file was read, but no rows matched this section's fields."
        raise HTTPException(status_code=422, detail=detail)
    batch = DataImportBatch(
        business_id=_next_business_id(db, "auth.data_import_batches"),
        source_name=resource_title or "Section upload",
        source_format=(file.filename or "").rsplit(".", 1)[-1].lower() or "unknown",
        target_resource=endpoint,
        file_name=file.filename,
        parsed_rows=len(rows),
        imported_rows=imported + updated,
        error_rows=errors,
        status="imported" if imported + updated and not errors else "failed" if errors and imported + updated == 0 else "parsed",
        uploaded_by=user.full_name,
        parse_summary=" ".join([summary, f"Created {imported} row(s). Updated {updated} row(s).", *messages])[:2000],
        sample_payload=rows[:5],
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return _serialize(batch)


@router.post("/integrations/bulk-delete")
def bulk_delete_records(
    payload: BulkDeletePayload,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    _require_admin_or_manager(user)
    model, _entity_key = _model_for_bulk_endpoint(payload.endpoint)
    if not payload.ids:
        raise HTTPException(status_code=422, detail="Select at least one record to delete.")

    records = db.query(model).filter(model.id.in_(payload.ids)).all()
    deleted_ids = []
    for record in records:
        deleted_ids.append(str(record.id))
        db.delete(record)
    db.commit()
    return {"deleted_count": len(deleted_ids), "deleted_ids": deleted_ids}


DATA_OWNERSHIP_POLICIES = [
    {
        "domain": "HRM",
        "owner": "HR system",
        "master_records": ["employees", "departments", "attendance", "leave", "payroll", "performance", "training", "benefits", "recruitment"],
        "policy": "Employee-related data must be created and maintained in HRM. CRM, Projects, Finance and Support reference staff records instead of duplicating staff profiles.",
    },
    {
        "domain": "CRM",
        "owner": "CRM system",
        "master_records": ["accounts", "contacts", "opportunities", "leads", "deals", "quotes", "sales targets", "territories"],
        "policy": "Sales, accounts, contacts, leads and deals are mastered in CRM. Finance and Projects consume won deal/account references instead of creating separate customer copies.",
    },
    {
        "domain": "Finance",
        "owner": "Finance system",
        "master_records": ["ledger", "budgets", "bills", "payments", "receipts", "tax", "assets", "revenue records", "finance documents"],
        "policy": "Finance controls financial records and journal truth. CRM can initiate commercial events, but finance owns accounting, revenue, AP, AR, tax and audit records.",
    },
    {
        "domain": "Invoices",
        "owner": "Invoice management",
        "master_records": ["finance invoices", "payment status", "credit notes", "receipts", "billing documents"],
        "policy": "Invoices are controlled through the invoice/finance workflow. CRM quotes and won deals may trigger invoices, but invoice numbers and balances are mastered by the invoice system.",
    },
    {
        "domain": "Projects",
        "owner": "Projects/PMO system",
        "master_records": ["projects", "project tasks", "milestones", "risks", "SLAs", "resource allocations"],
        "policy": "Delivery records are mastered in Projects/PMO. CRM won deals and awarded tenders create project references, but PMO controls delivery status, tasks, milestones and SLAs.",
    },
]


def _duplicate_groups(db: Session, model: Any, fields: list[str], label_field: str, limit: int = 50):
    groups: dict[str, list[Any]] = {}
    for record in db.query(model).limit(2000).all():
        parts = [str(getattr(record, field, "") or "").strip().lower() for field in fields]
        if not any(parts):
            continue
        key = "|".join(parts)
        groups.setdefault(key, []).append(record)
    duplicates = []
    for key, records in groups.items():
        if len(records) < 2:
            continue
        duplicates.append(
            {
                "key": key,
                "count": len(records),
                "label": getattr(records[0], label_field, key),
                "ids": [str(record.id) for record in records],
            }
        )
    return duplicates[:limit]


@router.get("/data-governance/summary")
def data_governance_summary(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin_or_manager(user)
    duplicate_sections = [
        {"domain": "CRM", "resource": "Accounts", "owner": "CRM system", "duplicates": _duplicate_groups(db, CRMAccount, ["company_name"], "company_name")},
        {"domain": "CRM", "resource": "Contacts", "owner": "CRM system", "duplicates": _duplicate_groups(db, CRMContact, ["email"], "email")},
        {"domain": "CRM", "resource": "Leads", "owner": "CRM system", "duplicates": _duplicate_groups(db, CRMLead, ["company_name", "contact_name"], "contact_name")},
        {"domain": "CRM", "resource": "Deals", "owner": "CRM system", "duplicates": _duplicate_groups(db, CRMDeal, ["deal_name", "owner"], "deal_name")},
        {"domain": "HRM", "resource": "Employees", "owner": "HR system", "duplicates": _duplicate_groups(db, HRMEmployee, ["email"], "email")},
        {"domain": "Finance", "resource": "Invoices", "owner": "Invoice management", "duplicates": _duplicate_groups(db, FinanceInvoice, ["invoice_number"], "invoice_number")},
        {"domain": "ERP", "resource": "Inventory", "owner": "Finance/ERP system", "duplicates": _duplicate_groups(db, ERPInventoryItem, ["sku"], "item_name")},
        {"domain": "Projects", "resource": "PMO Projects", "owner": "Projects/PMO system", "duplicates": _duplicate_groups(db, CRMPMOProject, ["project_name"], "project_name")},
    ]
    total_duplicate_groups = sum(len(section["duplicates"]) for section in duplicate_sections)
    return {
        "policies": DATA_OWNERSHIP_POLICIES,
        "duplicate_sections": duplicate_sections,
        "summary": {
            "duplicate_groups": total_duplicate_groups,
            "status": "clean" if total_duplicate_groups == 0 else "review_required",
            "rule": "Each business object has one owning module. Other modules must reference the owner record through IDs or synchronized workflow outputs.",
        },
    }


@router.post("/system/sequences/{entity_key:path}/next")
def preview_next_id(entity_key: str, db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin(user)
    sequence = db.query(EntitySequence).filter(EntitySequence.entity_key == entity_key).first()
    if not sequence:
        prefix = "IS-" + entity_key.split(".")[-1][:3].upper()
        business_id = f"{prefix}-00001"
    else:
        business_id = f"{sequence.prefix}-{str(sequence.next_number or 1).zfill(sequence.padding or 5)}"
    return {"entity_key": entity_key, "next_id": business_id}


@router.post("/workflows/sync")
def sync_workflows(db: Session = Depends(get_db), user: UserResponse = Depends(get_current_user)):
    _require_admin_or_manager(user)
    from backend.api.crm.leads import _convert_lead, _sync_lead_account_and_contact
    from backend.api.crm.opportunities import _lead_from_opportunity
    from backend.api.crud import _ensure_pipeline_outputs

    counts = {
        "opportunities_checked": 0,
        "leads_checked": 0,
        "pipeline_checked": 0,
        "licences_checked": 0,
    }
    for opportunity in db.query(CRMOpportunity).all():
        _lead_from_opportunity(db, opportunity)
        counts["opportunities_checked"] += 1
    for lead in db.query(CRMLead).all():
        _sync_lead_account_and_contact(db, lead)
        _convert_lead(db, lead)
        counts["leads_checked"] += 1
    for deal in db.query(CRMDeal).all():
        _ensure_pipeline_outputs(db, deal)
        counts["pipeline_checked"] += 1
    for tender in db.query(CRMTender).all():
        _ensure_pipeline_outputs(db, tender)
        counts["pipeline_checked"] += 1
    for licence in db.query(CRMLicence).all():
        _ensure_licence_invoice(db, licence)
        counts["licences_checked"] += 1
    db.commit()
    return {"status": "success", **counts}
