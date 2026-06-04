from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class ContactBase(BaseModel):
    account_id: UUID
    first_name: str = Field(..., min_length=2, max_length=150)
    last_name: str = Field(..., min_length=2, max_length=150)
    job_title: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    owner_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    account_id: Optional[UUID] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=150)
    last_name: Optional[str] = Field(None, min_length=2, max_length=150)
    job_title: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    owner_employee_id: Optional[UUID] = None
    created_by_employee_id: Optional[UUID] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


ContactOut = ContactResponse
