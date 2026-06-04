from datetime import date
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EmployeeMovementPayload(BaseModel):
    effective_date: date
    reason: str = Field(min_length=3)
    new_job_title: Optional[str] = None
    new_job_grade: Optional[str] = None
    new_salary_band: Optional[str] = None
    new_department: Optional[str] = None
    new_branch: Optional[str] = None
    new_business_unit: Optional[str] = None
    new_cost_center: Optional[str] = None
    new_manager_id: Optional[UUID] = None
    new_role: Optional[str] = None
    assignment_owner: Optional[str] = None
    host_unit: Optional[str] = None
    host_organization: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    return_date: Optional[date] = None
    allocation_percentage: Optional[float] = None
    cost_allocation_rule: Optional[str] = None
    supporting_document_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmployeeStatusPayload(BaseModel):
    effective_date: Optional[date] = None
    reason: str = Field(min_length=3)
    end_date: Optional[date] = None
    expected_return_date: Optional[date] = None
    return_date: Optional[date] = None
    leave_type: Optional[str] = None
    suspension_type: Optional[str] = None
    paid: Optional[bool] = None
    retirement_type: Optional[str] = None
    termination_type: Optional[str] = None
    date_of_death: Optional[date] = None
    supporting_document_url: Optional[str] = None
    payroll_impact: Optional[str] = None
    iam_access_impact: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
