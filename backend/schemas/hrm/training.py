from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class TrainingBase(BaseModel):
    employee_id: UUID

    training_title: str
    training_provider: Optional[str] = None
    training_type: Optional[str] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    cost: Optional[Decimal] = 0
    certification_awarded: Optional[bool] = False
    certificate_name: Optional[str] = None

    completion_status: Optional[str] = "not_started"
    score: Optional[Decimal] = None

    remarks: Optional[str] = None


class TrainingCreate(TrainingBase):
    pass


class TrainingUpdate(BaseModel):
    training_title: Optional[str] = None
    training_provider: Optional[str] = None
    training_type: Optional[str] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    cost: Optional[Decimal] = None
    certification_awarded: Optional[bool] = None
    certificate_name: Optional[str] = None

    completion_status: Optional[str] = None
    score: Optional[Decimal] = None

    remarks: Optional[str] = None


class TrainingResponse(TrainingBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
