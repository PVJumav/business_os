from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class BenefitBase(BaseModel):
    employee_id: UUID

    benefit_type: str
    benefit_name: str

    provider: Optional[str] = None
    policy_number: Optional[str] = None

    employer_contribution: Optional[Decimal] = 0
    employee_contribution: Optional[Decimal] = 0

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    status: Optional[str] = "active"
    remarks: Optional[str] = None


class BenefitCreate(BenefitBase):
    pass


class BenefitUpdate(BaseModel):
    benefit_type: Optional[str] = None
    benefit_name: Optional[str] = None

    provider: Optional[str] = None
    policy_number: Optional[str] = None

    employer_contribution: Optional[Decimal] = None
    employee_contribution: Optional[Decimal] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    status: Optional[str] = None
    remarks: Optional[str] = None


class BenefitResponse(BenefitBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
