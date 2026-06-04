from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class PerformanceBase(BaseModel):
    employee_id: UUID
    review_period: str

    reviewer_id: Optional[UUID] = None
    review_date: Optional[date] = None

    goals: Optional[str] = None
    achievements: Optional[str] = None
    areas_of_improvement: Optional[str] = None

    performance_score: Optional[Decimal] = None
    rating: Optional[str] = None

    promotion_recommendation: Optional[bool] = False
    training_recommendation: Optional[str] = None

    comments: Optional[str] = None
    status: Optional[str] = "draft"


class PerformanceCreate(PerformanceBase):
    pass


class PerformanceUpdate(BaseModel):
    review_period: Optional[str] = None
    reviewer_id: Optional[UUID] = None
    review_date: Optional[date] = None

    goals: Optional[str] = None
    achievements: Optional[str] = None
    areas_of_improvement: Optional[str] = None

    performance_score: Optional[Decimal] = None
    rating: Optional[str] = None

    promotion_recommendation: Optional[bool] = None
    training_recommendation: Optional[str] = None

    comments: Optional[str] = None
    status: Optional[str] = None


class PerformanceResponse(PerformanceBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
