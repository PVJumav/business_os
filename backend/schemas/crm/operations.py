from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TenderBase(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    tender_number: Optional[str] = Field(None, max_length=150)
    tender_title: str = Field(..., min_length=2, max_length=255)
    platform: Optional[str] = Field(None, max_length=255)
    sector: Optional[str] = Field(None, max_length=100)
    customer_name: Optional[str] = Field(None, max_length=255)
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    bid_manager: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    stage: str = Field(default="prequalification", max_length=100)
    qualification_status: str = Field(default="qualifying", max_length=50)
    response_status: str = Field(default="not_started", max_length=50)
    outcome: str = Field(default="pending", max_length=50)
    service_scope: Optional[str] = Field(None, max_length=100)
    document_completion: int = Field(default=0, ge=0, le=100)
    close_date: Optional[date] = None
    submission_date: Optional[date] = None
    estimated_value: float = Field(default=0, ge=0)
    notes: Optional[str] = None


class TenderCreate(TenderBase):
    pass


class TenderUpdate(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    tender_number: Optional[str] = Field(None, max_length=150)
    tender_title: Optional[str] = Field(None, min_length=2, max_length=255)
    platform: Optional[str] = Field(None, max_length=255)
    sector: Optional[str] = Field(None, max_length=100)
    customer_name: Optional[str] = Field(None, max_length=255)
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    bid_manager: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    stage: Optional[str] = Field(None, max_length=100)
    qualification_status: Optional[str] = Field(None, max_length=50)
    response_status: Optional[str] = Field(None, max_length=50)
    outcome: Optional[str] = Field(None, max_length=50)
    service_scope: Optional[str] = Field(None, max_length=100)
    document_completion: Optional[int] = Field(None, ge=0, le=100)
    close_date: Optional[date] = None
    submission_date: Optional[date] = None
    estimated_value: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class TenderResponse(TenderBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TenderDocumentBase(BaseModel):
    document_title: str = Field(..., min_length=2, max_length=255)
    document_category: str = Field(..., max_length=100)
    file_name: Optional[str] = Field(None, max_length=255)
    file_url: Optional[str] = Field(None, max_length=500)
    owner_department: str = Field(default="Bids", max_length=100)
    expiry_date: Optional[date] = None
    status: str = Field(default="active", max_length=50)
    notes: Optional[str] = None


class TenderDocumentCreate(TenderDocumentBase):
    pass


class TenderDocumentUpdate(BaseModel):
    document_title: Optional[str] = Field(None, min_length=2, max_length=255)
    document_category: Optional[str] = Field(None, max_length=100)
    file_name: Optional[str] = Field(None, max_length=255)
    file_url: Optional[str] = Field(None, max_length=500)
    owner_department: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class TenderDocumentResponse(TenderDocumentBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PMOProjectBase(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    project_name: str = Field(..., min_length=2, max_length=255)
    account_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    project_manager: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    pit_team: Optional[str] = None
    stage: str = Field(default="planning", max_length=100)
    status: str = Field(default="active", max_length=50)
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    scoping_document_url: Optional[str] = Field(None, max_length=500)
    deliverables: Optional[str] = None
    stakeholder_notes: Optional[str] = None
    vendor_notes: Optional[str] = None
    legal_status: Optional[str] = Field(None, max_length=100)
    documentation_source: Optional[str] = Field(default="Bids", max_length=100)
    notes: Optional[str] = None


class PMOProjectCreate(PMOProjectBase):
    pass


class PMOProjectUpdate(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    project_name: Optional[str] = Field(None, min_length=2, max_length=255)
    account_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    project_manager: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    pit_team: Optional[str] = None
    stage: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    scoping_document_url: Optional[str] = Field(None, max_length=500)
    deliverables: Optional[str] = None
    stakeholder_notes: Optional[str] = None
    vendor_notes: Optional[str] = None
    legal_status: Optional[str] = Field(None, max_length=100)
    documentation_source: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PMOProjectResponse(PMOProjectBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SLAAssignmentBase(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    account_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    solution: str = Field(..., min_length=2, max_length=255)
    assigned_engineer: str = Field(..., min_length=2, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    sla_type: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field(default="active", max_length=50)
    service_hours: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class SLAAssignmentCreate(SLAAssignmentBase):
    pass


class SLAAssignmentUpdate(BaseModel):
    business_id: Optional[str] = Field(None, max_length=80)
    account_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    solution: Optional[str] = Field(None, min_length=2, max_length=255)
    assigned_engineer: Optional[str] = Field(None, min_length=2, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    sla_type: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    service_hours: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class SLAAssignmentResponse(SLAAssignmentBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TechnicalServiceBase(BaseModel):
    arena: str = Field(..., max_length=100)
    cluster: Optional[str] = Field(None, max_length=150)
    service_name: str = Field(..., min_length=2, max_length=255)
    service_lead: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    delivery_team: Optional[str] = None
    status: str = Field(default="active", max_length=50)
    notes: Optional[str] = None


class TechnicalServiceCreate(TechnicalServiceBase):
    pass


class TechnicalServiceUpdate(BaseModel):
    arena: Optional[str] = Field(None, max_length=100)
    cluster: Optional[str] = Field(None, max_length=150)
    service_name: Optional[str] = Field(None, min_length=2, max_length=255)
    service_lead: Optional[str] = Field(None, max_length=255)
    account_manager: Optional[str] = Field(None, max_length=255)
    delivery_team: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class TechnicalServiceResponse(TechnicalServiceBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomerTicketBase(BaseModel):
    account_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    ticket_number: Optional[str] = Field(None, max_length=150)
    solution: Optional[str] = Field(None, max_length=255)
    issue_title: str = Field(..., min_length=2, max_length=255)
    severity: str = Field(default="medium", max_length=50)
    status: str = Field(default="open", max_length=50)
    assigned_engineer: Optional[str] = Field(None, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    opened_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None


class CustomerTicketCreate(CustomerTicketBase):
    pass


class CustomerTicketUpdate(BaseModel):
    account_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    ticket_number: Optional[str] = Field(None, max_length=150)
    solution: Optional[str] = Field(None, max_length=255)
    issue_title: Optional[str] = Field(None, min_length=2, max_length=255)
    severity: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    assigned_engineer: Optional[str] = Field(None, max_length=255)
    technical_lead: Optional[str] = Field(None, max_length=255)
    opened_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None


class CustomerTicketResponse(CustomerTicketBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
