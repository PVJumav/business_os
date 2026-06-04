from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class HRDocumentBase(BaseModel):
    employee_id: Optional[UUID] = None

    document_title: str
    document_type: str

    file_name: Optional[str] = None
    file_url: Optional[str] = None

    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None

    uploaded_by: Optional[UUID] = None
    confidentiality_level: Optional[str] = "internal"

    status: Optional[str] = "active"
    remarks: Optional[str] = None


class HRDocumentCreate(HRDocumentBase):
    pass


class HRDocumentUpdate(BaseModel):
    document_title: Optional[str] = None
    document_type: Optional[str] = None

    file_name: Optional[str] = None
    file_url: Optional[str] = None

    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None

    uploaded_by: Optional[UUID] = None
    confidentiality_level: Optional[str] = None

    status: Optional[str] = None
    remarks: Optional[str] = None


class HRDocumentResponse(HRDocumentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
