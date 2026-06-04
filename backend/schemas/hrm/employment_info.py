from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EmploymentChangePayload(BaseModel):
    new_value: str = Field(min_length=1)
    effective_date: date
    reason: str = Field(min_length=3)
    supporting_document_url: Optional[str] = None


class ManagerChangePayload(BaseModel):
    manager_id: UUID
    effective_date: date
    reason: str = Field(min_length=3)
    authority_scope: Optional[str] = None
    supporting_document_url: Optional[str] = None


class EmploymentApprovalPayload(BaseModel):
    comments: Optional[str] = None


class EmploymentRejectPayload(BaseModel):
    reason: str = Field(min_length=3)


class EmploymentInfoResponse(BaseModel):
    employee_id: UUID
    current: dict[str, Any]
    pending_changes: list[dict[str, Any]]
    history: list[dict[str, Any]]
    salary_band_visible: bool


class EmploymentChangeResponse(BaseModel):
    request_id: Optional[UUID] = None
    status: str
    buc_code: str
    field_type: str
    previous_value: Optional[str] = None
    new_value: str
    effective_date: date
    approval_required: bool
    applied_at: Optional[datetime] = None
