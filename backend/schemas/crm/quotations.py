from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class QuotationBase(BaseModel):
    opportunity_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    quote_number: Optional[str] = Field(None, min_length=2, max_length=100)
    title: str = Field(..., min_length=2, max_length=255)
    subtotal: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    discount_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(default=0, ge=0)
    status: str = Field(default="draft", max_length=50)
    valid_until: Optional[date] = None
    created_by: Optional[str] = Field(None, max_length=255)
    approved_by: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    approved_by_employee_id: Optional[UUID] = None


class QuotationCreate(QuotationBase):
    pass


class QuotationUpdate(BaseModel):
    opportunity_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    quote_number: Optional[str] = Field(None, min_length=2, max_length=100)
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    subtotal: Optional[float] = Field(None, ge=0)
    tax_amount: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    total_amount: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)
    valid_until: Optional[date] = None
    created_by: Optional[str] = Field(None, max_length=255)
    approved_by: Optional[str] = Field(None, max_length=255)
    owner_employee_id: Optional[UUID] = None
    approved_by_employee_id: Optional[UUID] = None


class QuotationResponse(QuotationBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


QuotationOut = QuotationResponse
