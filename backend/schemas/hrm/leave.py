from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class LeaveBase(BaseModel):
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    total_days: Decimal
    reason: Optional[str] = None
    status: Optional[str] = "pending"
    approved_by: Optional[UUID] = None
    approval_comments: Optional[str] = None


class LeaveCreate(LeaveBase):
    pass


class LeaveUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_days: Optional[Decimal] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[UUID] = None
    approval_comments: Optional[str] = None


class LeaveResponse(LeaveBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveCalculationRequest(BaseModel):
    employee_id: UUID
    leave_type_id: Optional[UUID] = None
    leave_type: Optional[str] = None
    policy_id: Optional[UUID] = None
    start_date: date
    end_date: date
    start_day_type: str = "Full Day"
    end_day_type: str = "Full Day"


class LeaveRequestCreate(LeaveCalculationRequest):
    reason: Optional[str] = None
    supporting_document_id: Optional[UUID] = None
    submit: bool = True


class LeaveActionPayload(BaseModel):
    comments: Optional[str] = None
    reason: Optional[str] = None
    recall_date: Optional[date] = None
    new_end_date: Optional[date] = None


class LeaveBalanceAdjustmentPayload(BaseModel):
    leave_type: str
    adjustment_amount: Decimal
    effective_date: date
    reason: str = Field(min_length=3)


class LeavePolicyPayload(BaseModel):
    policy_name: str
    leave_type_id: Optional[UUID] = None
    annual_entitlement: Decimal = Decimal("0")
    accrual_frequency: str = "monthly"
    paid_or_unpaid: str = "paid"
    paid_percentage: Decimal = Decimal("100")
    requires_balance: bool = True
    requires_document: bool = False
    requires_manager_approval: bool = True
    requires_hr_review: bool = False
    allows_half_day: bool = True
    allows_backdating: bool = False
    allows_future_dating: bool = True
    excludes_weekends: bool = True
    excludes_public_holidays: bool = True
    minimum_notice_days: int = 0
    maximum_consecutive_days: Optional[Decimal] = None
    carry_forward_allowed: bool = False
    carry_forward_limit: Decimal = Decimal("0")
    encashment_allowed: bool = False
    max_encashable_days: Decimal = Decimal("0")
    document_type_required: Optional[str] = None


class LeavePolicyAssignmentPayload(BaseModel):
    employee_id: UUID
    effective_from: date
    effective_to: Optional[date] = None
    assignment_reason: Optional[str] = None


class PublicHolidayPayload(BaseModel):
    holiday_name: str
    holiday_date: date
    country: Optional[str] = None
    branch: Optional[str] = None
    status: str = "active"


class LeaveEncashmentPayload(BaseModel):
    employee_id: UUID
    leave_type: str
    encashed_days: Decimal = Field(gt=0)
    reason: Optional[str] = None


class LeaveReportExportPayload(BaseModel):
    report_type: str = "leave"
    export_format: str = "csv"
