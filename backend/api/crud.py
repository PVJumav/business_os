from datetime import date
from typing import Type
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.enterprise import EntitySequence


def _entity_key(model: Type) -> str:
    schema = getattr(model, "__table_args__", {}) or {}
    if isinstance(schema, dict):
        schema_name = schema.get("schema")
    else:
        schema_name = None
    return f"{schema_name}.{model.__tablename__}" if schema_name else model.__tablename__


def _default_prefix(entity_key: str) -> str:
    known = {
        "crm.accounts": "IS-ACC",
        "crm.leads": "IS-LED",
        "crm.deals": "IS-DEA",
        "crm.opportunities": "IS-OPP",
        "crm.licences": "IS-LIC",
        "crm.pmo_projects": "IS-PRJ",
        "crm.sla_assignments": "IS-SLA",
        "crm.tenders": "IS-TEN",
        "finance.invoices": "IS-INV",
    }
    return known.get(entity_key, "IS-" + entity_key.split(".")[-1][:3].upper())


def assign_business_id(db: Session, model: Type, record):
    if "business_id" not in model.__table__.columns or getattr(record, "business_id", None):
        return
    key = _entity_key(model)
    sequence = db.query(EntitySequence).filter(EntitySequence.entity_key == key).with_for_update().first()
    if not sequence:
        sequence = EntitySequence(entity_key=key, prefix=_default_prefix(key), next_number=1, padding=5)
        db.add(sequence)
        db.flush()
    record.business_id = f"{sequence.prefix}-{str(sequence.next_number or 1).zfill(sequence.padding or 5)}"
    sequence.next_number = (sequence.next_number or 1) + 1


def _scope_requires(scope: str | None, token: str) -> bool:
    normalized = (scope or "").strip().lower().replace("-", "_").replace(" ", "_")
    if token == "licence":
        return normalized in {"licence", "licences", "licence_only", "licences_only", "licences_and_implementation"}
    if token == "implementation":
        return normalized in {"implementation", "licences_and_implementation", "licence_and_implementation"}
    if token == "sla":
        return normalized in {"sla", "sla_only"}
    return False


def _ensure_pipeline_outputs(db: Session, record):
    from backend.models.crm import CRMDeal, CRMPMOProject, CRMSLAAssignment, CRMTender
    from backend.models.enterprise import CRMLicence
    from backend.models.finance import FinanceRevenueRecord

    is_deal = isinstance(record, CRMDeal)
    is_tender = isinstance(record, CRMTender)
    if not is_deal and not is_tender:
        return

    won_values = {"won", "closed_won", "closed as won", "stage 6.a closed as won", "awarded", "award"}
    status_value = (record.deal_status if is_deal else record.outcome) or ""
    if status_value.strip().lower() not in won_values:
        return

    account_id = getattr(record, "account_id", None)
    amount = getattr(record, "revenue_amount", None) if is_deal else getattr(record, "estimated_value", None)
    owner = getattr(record, "owner", None) if is_deal else getattr(record, "account_manager", None)
    name = getattr(record, "deal_name", None) if is_deal else getattr(record, "tender_title", None)
    source_id = record.id
    scope = getattr(record, "service_scope", None)

    if _scope_requires(scope, "licence"):
        existing = db.query(CRMLicence).filter(CRMLicence.deal_id == source_id if is_deal else CRMLicence.notes.ilike(f"%Tender ID: {source_id}%")).first()
        if not existing:
            licence = CRMLicence(
                account_id=account_id,
                deal_id=source_id if is_deal else None,
                licence_name=f"{name} Licence",
                product_name=name,
                account_manager=owner,
                activation_date=date.today(),
                renewal_date=getattr(record, "renewal_date", None) if is_deal else None,
                expiry_date=getattr(record, "licence_expiry_date", None) if is_deal else None,
                notes=None if is_deal else f"Created from awarded tender. Tender ID: {source_id}",
            )
            assign_business_id(db, CRMLicence, licence)
            db.add(licence)

    if _scope_requires(scope, "implementation"):
        existing = db.query(CRMPMOProject).filter(CRMPMOProject.deal_id == source_id if is_deal else CRMPMOProject.notes.ilike(f"%Tender ID: {source_id}%")).first()
        if not existing:
            project = CRMPMOProject(
                project_name=f"{name} Implementation",
                account_id=account_id,
                deal_id=source_id if is_deal else None,
                account_manager=owner,
                stage="planning",
                status="active",
                start_date=date.today(),
                notes=None if is_deal else f"Created from awarded tender. Tender ID: {source_id}",
            )
            assign_business_id(db, CRMPMOProject, project)
            db.add(project)

    if _scope_requires(scope, "sla"):
        existing = db.query(CRMSLAAssignment).filter(CRMSLAAssignment.notes.ilike(f"%Source ID: {source_id}%")).first()
        if not existing:
            sla = CRMSLAAssignment(
                account_id=account_id,
                solution=name,
                assigned_engineer="Unassigned",
                technical_lead=getattr(record, "technical_lead", None) if is_tender else None,
                sla_type="Customer SLA",
                start_date=date.today(),
                status="active",
                notes=f"Created from {'won deal' if is_deal else 'awarded tender'}. Source ID: {source_id}",
            )
            assign_business_id(db, CRMSLAAssignment, sla)
            db.add(sla)

    existing_revenue = db.query(FinanceRevenueRecord).filter(
        FinanceRevenueRecord.deal_id == source_id if is_deal else FinanceRevenueRecord.revenue_source == f"Tender:{source_id}"
    ).first()
    if not existing_revenue:
        db.add(
            FinanceRevenueRecord(
                revenue_source="Won Deal" if is_deal else f"Tender:{source_id}",
                customer_name=None,
                account_id=account_id,
                deal_id=source_id if is_deal else None,
                revenue_type="pipeline_conversion",
                recognition_date=date.today(),
                amount=amount or 0,
                status="recognized",
            )
        )

def get_or_404(db: Session, model: Type, object_id: UUID, label: str):
    record = db.query(model).filter(model.id == object_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label} not found",
        )
    return record


def create_record(db: Session, model: Type, payload: BaseModel):
    record = model(**payload.model_dump())
    assign_business_id(db, model, record)
    db.add(record)
    db.flush()
    _ensure_pipeline_outputs(db, record)
    db.commit()
    db.refresh(record)
    return record


def update_record(db: Session, record, payload: BaseModel):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    _ensure_pipeline_outputs(db, record)
    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, record):
    db.delete(record)
    db.commit()
    return None
