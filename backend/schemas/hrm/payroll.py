from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class PayrollBase(BaseModel):
    employee_id: UUID
    payroll_month: str
    basic_salary: Decimal

    allowances: Decimal = 0
    bonuses: Decimal = 0
    overtime_pay: Decimal = 0

    deductions: Decimal = 0
    tax_amount: Decimal = 0
    statutory_deductions: Decimal = 0

    gross_pay: Decimal
    net_pay: Decimal

    payment_status: Optional[str] = "pending"
    payment_date: Optional[date] = None
    remarks: Optional[str] = None


class PayrollCreate(PayrollBase):
    pass


class PayrollUpdate(BaseModel):
    allowances: Optional[Decimal] = None
    bonuses: Optional[Decimal] = None
    overtime_pay: Optional[Decimal] = None
    deductions: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    statutory_deductions: Optional[Decimal] = None
    gross_pay: Optional[Decimal] = None
    net_pay: Optional[Decimal] = None
    payment_status: Optional[str] = None
    payment_date: Optional[date] = None
    remarks: Optional[str] = None


class PayrollResponse(PayrollBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
