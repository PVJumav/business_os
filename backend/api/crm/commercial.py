from typing import List, Type
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.crud import create_record, delete_record, get_or_404, update_record
from backend.core.database import get_db
from backend.models.crm import (
    CRMAccountIssue,
    CRMCustomerEngagement,
    CRMDeal,
    CRMDepartmentWorkflow,
    CRMInvoice,
    CRMSalesTarget,
)
from backend.schemas.crm.commercial import (
    AccountIssueCreate,
    AccountIssueResponse,
    AccountIssueUpdate,
    DealCreate,
    DealResponse,
    DealUpdate,
    DepartmentWorkflowCreate,
    DepartmentWorkflowResponse,
    DepartmentWorkflowUpdate,
    EngagementCreate,
    EngagementResponse,
    EngagementUpdate,
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
    SalesTargetCreate,
    SalesTargetResponse,
    SalesTargetUpdate,
)


def crud_router(
    prefix: str,
    tag: str,
    model: Type,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    response_schema: Type[BaseModel],
    label: str,
):
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.post("", response_model=response_schema, status_code=status.HTTP_201_CREATED)
    def create_item(payload: create_schema, db: Session = Depends(get_db)):  # type: ignore[valid-type]
        return create_record(db, model, payload)

    @router.get("", response_model=List[response_schema])  # type: ignore[valid-type]
    def get_items(db: Session = Depends(get_db)):
        return db.query(model).order_by(model.created_at.desc()).all()

    @router.get("/{item_id}", response_model=response_schema)
    def get_item(item_id: UUID, db: Session = Depends(get_db)):  # type: ignore[valid-type]
        return get_or_404(db, model, item_id, label)

    @router.put("/{item_id}", response_model=response_schema)
    def update_item(  # type: ignore[valid-type]
        item_id: UUID,
        payload: update_schema,
        db: Session = Depends(get_db),
    ):
        item = get_or_404(db, model, item_id, label)
        return update_record(db, item, payload)

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: UUID, db: Session = Depends(get_db)):
        item = get_or_404(db, model, item_id, label)
        return delete_record(db, item)

    return router


deals_router = crud_router("/crm/deals", "CRM Deals", CRMDeal, DealCreate, DealUpdate, DealResponse, "Deal")
engagements_router = crud_router(
    "/crm/engagements",
    "CRM Customer Engagements",
    CRMCustomerEngagement,
    EngagementCreate,
    EngagementUpdate,
    EngagementResponse,
    "Customer engagement",
)
issues_router = crud_router(
    "/crm/account-issues",
    "CRM Account Issues",
    CRMAccountIssue,
    AccountIssueCreate,
    AccountIssueUpdate,
    AccountIssueResponse,
    "Account issue",
)
targets_router = crud_router(
    "/crm/sales-targets",
    "CRM Sales Targets",
    CRMSalesTarget,
    SalesTargetCreate,
    SalesTargetUpdate,
    SalesTargetResponse,
    "Sales target",
)
invoices_router = crud_router(
    "/crm/invoices",
    "CRM Invoices and Collections",
    CRMInvoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    "Invoice",
)
workflows_router = crud_router(
    "/crm/department-workflows",
    "CRM Department Workflows",
    CRMDepartmentWorkflow,
    DepartmentWorkflowCreate,
    DepartmentWorkflowUpdate,
    DepartmentWorkflowResponse,
    "Department workflow",
)
