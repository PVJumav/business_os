from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    related_type: Optional[str] = Field(None, max_length=50)
    related_id: Optional[UUID] = None
    assigned_to: Optional[str] = Field(None, max_length=255)
    assigned_employee_id: Optional[UUID] = None
    owner_employee_id: Optional[UUID] = None
    priority: Optional[str] = Field(default="medium", max_length=50)
    status: str = Field(default="pending", max_length=50)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    related_type: Optional[str] = Field(None, max_length=50)
    related_id: Optional[UUID] = None
    assigned_to: Optional[str] = Field(None, max_length=255)
    assigned_employee_id: Optional[UUID] = None
    owner_employee_id: Optional[UUID] = None
    priority: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


TaskOut = TaskResponse
