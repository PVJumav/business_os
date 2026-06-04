from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class AccountBase(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    company_name: str = Field(..., min_length=2, max_length=255)
    industry: Optional[str] = Field(None, max_length=150)
    website: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    relationship_owner: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    manager_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    country: Optional[str] = Field(None, max_length=150)
    region: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    account_type: Optional[str] = Field(None, max_length=100)
    account_status: str = Field(default="active", max_length=50)
    notes: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    industry: Optional[str] = Field(None, max_length=150)
    website: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    relationship_owner: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    manager_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    country: Optional[str] = Field(None, max_length=150)
    region: Optional[str] = Field(None, max_length=150)
    vertical: Optional[str] = Field(None, max_length=150)
    account_type: Optional[str] = Field(None, max_length=100)
    account_status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class AccountOut(AccountBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
