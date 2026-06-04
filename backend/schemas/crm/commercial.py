from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DealBase(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    deal_name: str = Field(..., min_length=2, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    stage: str = Field(default="Stage 1.a Discovery", max_length=150)
    deal_status: str = Field(default="open", max_length=50)
    pipeline_type: Optional[str] = Field(None, max_length=100)
    arena: Optional[str] = Field(None, max_length=100)
    service_scope: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    revenue_amount: float = Field(default=0, ge=0)
    distributor_cost: float = Field(default=0, ge=0)
    vendor_cost: float = Field(default=0, ge=0)
    internal_cost: float = Field(default=0, ge=0)
    gross_profit: float = Field(default=0)
    expected_close_date: Optional[date] = None
    renewal_date: Optional[date] = None
    licence_expiry_date: Optional[date] = None
    closed_date: Optional[date] = None
    notes: Optional[str] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    deal_name: Optional[str] = Field(None, min_length=2, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    stage: Optional[str] = Field(None, max_length=150)
    deal_status: Optional[str] = Field(None, max_length=50)
    pipeline_type: Optional[str] = Field(None, max_length=100)
    arena: Optional[str] = Field(None, max_length=100)
    service_scope: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    revenue_amount: Optional[float] = Field(None, ge=0)
    distributor_cost: Optional[float] = Field(None, ge=0)
    vendor_cost: Optional[float] = Field(None, ge=0)
    internal_cost: Optional[float] = Field(None, ge=0)
    gross_profit: Optional[float] = None
    expected_close_date: Optional[date] = None
    renewal_date: Optional[date] = None
    licence_expiry_date: Optional[date] = None
    closed_date: Optional[date] = None
    notes: Optional[str] = None


class DealResponse(DealBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EngagementBase(BaseModel):
    account_id: UUID
    opportunity_id: Optional[UUID] = None
    account_manager: Optional[str] = Field(None, max_length=255)
    engagement_type: str = Field(..., min_length=2, max_length=100)
    quarter: Optional[str] = Field(None, max_length=20)
    engagement_date: date
    workshop_done: bool = False
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None


class EngagementCreate(EngagementBase):
    pass


class EngagementUpdate(BaseModel):
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    account_manager: Optional[str] = Field(None, max_length=255)
    engagement_type: Optional[str] = Field(None, min_length=2, max_length=100)
    quarter: Optional[str] = Field(None, max_length=20)
    engagement_date: Optional[date] = None
    workshop_done: Optional[bool] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None


class EngagementResponse(EngagementBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AccountIssueBase(BaseModel):
    account_id: UUID
    issue_title: str = Field(..., min_length=2, max_length=255)
    issue_type: Optional[str] = Field(None, max_length=100)
    severity: str = Field(default="medium", max_length=50)
    status: str = Field(default="open", max_length=50)
    reported_by: Optional[str] = Field(None, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    feedback: Optional[str] = None
    resolution: Optional[str] = None
    due_date: Optional[date] = None


class AccountIssueCreate(AccountIssueBase):
    pass


class AccountIssueUpdate(BaseModel):
    account_id: Optional[UUID] = None
    issue_title: Optional[str] = Field(None, min_length=2, max_length=255)
    issue_type: Optional[str] = Field(None, max_length=100)
    severity: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    reported_by: Optional[str] = Field(None, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    feedback: Optional[str] = None
    resolution: Optional[str] = None
    due_date: Optional[date] = None


class AccountIssueResponse(AccountIssueBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SalesTargetBase(BaseModel):
    owner_type: str = Field(..., max_length=50)
    target_owner: str = Field(..., max_length=255)
    fiscal_year: str = Field(..., max_length=20)
    period_type: str = Field(..., max_length=50)
    period_label: str = Field(..., max_length=50)
    arena: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    target_gp: float = Field(default=0, ge=0)
    achieved_gp: float = Field(default=0, ge=0)
    notes: Optional[str] = None


class SalesTargetCreate(SalesTargetBase):
    pass


class SalesTargetUpdate(BaseModel):
    owner_type: Optional[str] = Field(None, max_length=50)
    target_owner: Optional[str] = Field(None, max_length=255)
    fiscal_year: Optional[str] = Field(None, max_length=20)
    period_type: Optional[str] = Field(None, max_length=50)
    period_label: Optional[str] = Field(None, max_length=50)
    arena: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    target_gp: Optional[float] = Field(None, ge=0)
    achieved_gp: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class SalesTargetResponse(SalesTargetBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    account_id: UUID
    deal_id: Optional[UUID] = None
    invoice_number: str = Field(..., min_length=2, max_length=100)
    invoice_date: date
    due_date: Optional[date] = None
    amount: float = Field(default=0, ge=0)
    paid_amount: float = Field(default=0, ge=0)
    status: str = Field(default="draft", max_length=50)
    debt_owner: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    account_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(None, min_length=2, max_length=100)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    amount: Optional[float] = Field(None, ge=0)
    paid_amount: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)
    debt_owner: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentWorkflowBase(BaseModel):
    department: str = Field(..., max_length=100)
    head_role: Optional[str] = Field(None, max_length=100)
    responsibility: str
    related_record_type: Optional[str] = Field(None, max_length=100)
    related_record_id: Optional[UUID] = None
    status: str = Field(default="pending", max_length=50)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class DepartmentWorkflowCreate(DepartmentWorkflowBase):
    pass


class DepartmentWorkflowUpdate(BaseModel):
    department: Optional[str] = Field(None, max_length=100)
    head_role: Optional[str] = Field(None, max_length=100)
    responsibility: Optional[str] = None
    related_record_type: Optional[str] = Field(None, max_length=100)
    related_record_id: Optional[UUID] = None
    status: Optional[str] = Field(None, max_length=50)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class DepartmentWorkflowResponse(DepartmentWorkflowBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
