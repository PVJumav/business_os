from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class LeadBase(BaseModel):
    company_name: Optional[str] = None
    contact_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    lead_source: Optional[str] = None
    status: Optional[str] = "New"
    assigned_to: Optional[str] = None
    estimated_value: Optional[Decimal] = 0
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    lead_source: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    estimated_value: Optional[Decimal] = None
    notes: Optional[str] = None
    converted: Optional[bool] = None


class LeadResponse(LeadBase):
    id: UUID
    converted: bool
    converted_account_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True