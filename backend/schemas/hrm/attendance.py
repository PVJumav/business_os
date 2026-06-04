from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, time, datetime
from decimal import Decimal


class AttendanceBase(BaseModel):
    employee_id: UUID
    attendance_date: date

    clock_in: Optional[time] = None
    clock_out: Optional[time] = None

    total_hours: Optional[Decimal] = 0
    overtime_hours: Optional[Decimal] = 0

    status: Optional[str] = "present"
    work_mode: Optional[str] = "office"

    remarks: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    clock_in: Optional[time] = None
    clock_out: Optional[time] = None
    total_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    status: Optional[str] = None
    work_mode: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
