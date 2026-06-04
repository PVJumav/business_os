from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EnterpriseRecordCreate(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class EnterpriseRecordUpdate(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class WorkflowActionPayload(BaseModel):
    reason: str | None = None
    comments: str | None = None
    adjustment_reason: str | None = None


class EnterpriseRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: dict[str, Any]
