from typing import Any

from pydantic import BaseModel


class WorkflowPayload(BaseModel):
    reason: str | None = None
    comments: str | None = None
    adjustment_reason: str | None = None
    stage: str | None = None
    status: str | None = None
    data: dict[str, Any] | None = None
