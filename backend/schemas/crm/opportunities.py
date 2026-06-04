from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class OpportunityBase(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    account_id: Optional[UUID] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    stage: str = Field(default="Discovery", max_length=100)
    opportunity_value: Optional[float] = Field(default=0, ge=0)
    probability: Optional[int] = Field(default=0, ge=0, le=100)
    expected_close_date: Optional[date] = None
    renewal_date: Optional[date] = None
    licence_expiry_date: Optional[date] = None
    owner: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    presales_employee_id: Optional[UUID] = None
    project_manager_employee_id: Optional[UUID] = None
    manager_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    lpo_document_url: Optional[str] = None
    handover_status: Optional[str] = Field(None, max_length=80)
    customer_success_owner_employee_id: Optional[UUID] = None
    technical_owner_employee_id: Optional[UUID] = None
    country: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    pipeline_type: Optional[str] = Field(None, max_length=100)
    arena: Optional[str] = Field(None, max_length=100)
    service_scope: Optional[str] = Field(None, max_length=100)
    distributor_cost: Optional[float] = Field(default=0, ge=0)
    vendor_cost: Optional[float] = Field(default=0, ge=0)
    internal_cost: Optional[float] = Field(default=0, ge=0)
    gross_profit: Optional[float] = Field(default=0)
    status: str = Field(default="open", max_length=50)


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    account_id: Optional[UUID] = None
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    stage: Optional[str] = Field(None, max_length=100)
    opportunity_value: Optional[float] = Field(None, ge=0)
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[date] = None
    renewal_date: Optional[date] = None
    licence_expiry_date: Optional[date] = None
    owner: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    presales_employee_id: Optional[UUID] = None
    project_manager_employee_id: Optional[UUID] = None
    manager_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    lpo_document_url: Optional[str] = None
    handover_status: Optional[str] = Field(None, max_length=80)
    customer_success_owner_employee_id: Optional[UUID] = None
    technical_owner_employee_id: Optional[UUID] = None
    country: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    pipeline_type: Optional[str] = Field(None, max_length=100)
    arena: Optional[str] = Field(None, max_length=100)
    service_scope: Optional[str] = Field(None, max_length=100)
    distributor_cost: Optional[float] = Field(None, ge=0)
    vendor_cost: Optional[float] = Field(None, ge=0)
    internal_cost: Optional[float] = Field(None, ge=0)
    gross_profit: Optional[float] = None
    status: Optional[str] = Field(None, max_length=50)


class OpportunityResponse(OpportunityBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


OpportunityOut = OpportunityResponse
