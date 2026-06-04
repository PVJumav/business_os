from typing import Any

from pydantic import BaseModel


class CRMWorkflowPayload(BaseModel):
    reason: str | None = None
    comments: str | None = None
    stage: str | None = None
    owner: str | None = None
    loss_reason: str | None = None
    account_id: str | None = None
    contact_id: str | None = None
    opportunity_id: str | None = None
    data: dict[str, Any] | None = None
