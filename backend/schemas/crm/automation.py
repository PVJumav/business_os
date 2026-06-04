from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AutomationRuleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    trigger: str = Field(..., min_length=2, max_length=255)
    action: str = Field(..., min_length=2)
    status: str = Field(default="active", max_length=50)


class AutomationRuleCreate(AutomationRuleBase):
    pass


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    trigger: Optional[str] = Field(None, min_length=2, max_length=255)
    action: Optional[str] = Field(None, min_length=2)
    status: Optional[str] = Field(None, max_length=50)


class AutomationRuleResponse(AutomationRuleBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
