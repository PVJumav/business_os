from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class LeadBase(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    company_name: Optional[str] = Field(None, max_length=255)
    account_industry: Optional[str] = Field(None, max_length=150)
    account_website: Optional[str] = Field(None, max_length=255)
    account_address: Optional[str] = None
    account_country: Optional[str] = Field(None, max_length=150)
    account_region: Optional[str] = Field(None, max_length=150)
    account_vertical: Optional[str] = Field(None, max_length=150)
    account_type: Optional[str] = Field(None, max_length=100)
    contact_name: str = Field(..., min_length=2, max_length=255)
    contact_job_title: Optional[str] = Field(None, max_length=150)
    contact_department: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    lead_source: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="New", max_length=50)
    assigned_to: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    assigned_employee_id: Optional[UUID] = None
    manager_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    duplicate_flag: Optional[bool] = False
    duplicate_reason: Optional[str] = None
    disqualification_reason: Optional[str] = None
    estimated_value: Optional[float] = Field(None, ge=0)
    expected_close_date: Optional[date] = None
    expected_activation_date: Optional[date] = None
    expected_renewal_date: Optional[date] = None
    pipeline_type: Optional[str] = Field(None, max_length=100)
    arena: Optional[str] = Field(None, max_length=100)
    service_scope: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    converted: bool = False
    converted_account_id: Optional[UUID] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    company_name: Optional[str] = Field(None, max_length=255)
    account_industry: Optional[str] = Field(None, max_length=150)
    account_website: Optional[str] = Field(None, max_length=255)
    account_address: Optional[str] = None
    account_country: Optional[str] = Field(None, max_length=150)
    account_region: Optional[str] = Field(None, max_length=150)
    account_vertical: Optional[str] = Field(None, max_length=150)
    account_type: Optional[str] = Field(None, max_length=100)
    contact_name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_job_title: Optional[str] = Field(None, max_length=150)
    contact_department: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    lead_source: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    assigned_employee_id: Optional[UUID] = None
    manager_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    duplicate_flag: Optional[bool] = None
    duplicate_reason: Optional[str] = None
    disqualification_reason: Optional[str] = None
    estimated_value: Optional[float] = Field(None, ge=0)
    expected_close_date: Optional[date] = None
    expected_activation_date: Optional[date] = None
    expected_renewal_date: Optional[date] = None
    pipeline_type: Optional[str] = Field(None, max_length=100)
    arena: Optional[str] = Field(None, max_length=100)
    service_scope: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    converted: Optional[bool] = None
    converted_account_id: Optional[UUID] = None


class LeadResponse(LeadBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


LeadOut = LeadResponse
