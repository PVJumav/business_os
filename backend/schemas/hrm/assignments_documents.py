from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OrgAssignmentPayload(BaseModel):
    value: str = Field(min_length=1)
    effective_date: date
    reason: str = Field(min_length=3)


class ProjectAssignmentPayload(BaseModel):
    project_id: UUID
    project_name: Optional[str] = None
    role: str = Field(min_length=1)
    allocation_percentage: float = Field(ge=0, le=100)
    start_date: date
    end_date: Optional[date] = None
    reason: Optional[str] = None


class TeamAssignmentPayload(BaseModel):
    team_name: str = Field(min_length=1)
    department: str = Field(min_length=1)
    primary_team: bool = False
    effective_date: date
    reason: Optional[str] = None


class DocumentReviewPayload(BaseModel):
    comments: Optional[str] = None


class DocumentRejectPayload(BaseModel):
    reason: str = Field(min_length=3)


class DocumentArchivePayload(BaseModel):
    reason: str = Field(min_length=3)


class DocumentReplacePayload(BaseModel):
    replacement_reason: str = Field(min_length=3)
