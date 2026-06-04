from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class ActivityBase(BaseModel):
    related_type: str = Field(default="account", max_length=50)
    related_id: Optional[UUID] = None
    activity_type: str = Field(
        default="Follow-up",
        max_length=100,
        validation_alias=AliasChoices("activity_type", "type"),
    )
    subject: str = Field(
        ...,
        min_length=2,
        max_length=255,
        validation_alias=AliasChoices("subject", "activity"),
    )
    description: Optional[str] = None
    account_name: Optional[str] = Field(
        None,
        max_length=255,
        validation_alias=AliasChoices("account_name", "account"),
    )
    created_by: Optional[str] = Field(
        None,
        max_length=255,
        validation_alias=AliasChoices("created_by", "owner"),
    )
    activity_date: Optional[datetime] = None
    due_date: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("due_date", "dueDate"),
    )
    status: str = Field(default="pending", max_length=50)


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    related_type: Optional[str] = Field(None, max_length=50)
    related_id: Optional[UUID] = None
    activity_type: Optional[str] = Field(
        None,
        max_length=100,
        validation_alias=AliasChoices("activity_type", "type"),
    )
    subject: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        validation_alias=AliasChoices("subject", "activity"),
    )
    description: Optional[str] = None
    account_name: Optional[str] = Field(
        None,
        max_length=255,
        validation_alias=AliasChoices("account_name", "account"),
    )
    created_by: Optional[str] = Field(
        None,
        max_length=255,
        validation_alias=AliasChoices("created_by", "owner"),
    )
    activity_date: Optional[datetime] = None
    due_date: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("due_date", "dueDate"),
    )
    status: Optional[str] = Field(None, max_length=50)


class ActivityResponse(ActivityBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
