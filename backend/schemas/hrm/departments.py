from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    head_employee_id: Optional[UUID] = None
    status: str = Field(default="active")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    description: Optional[str] = None
    head_employee_id: Optional[UUID] = None
    status: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
