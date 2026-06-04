from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StatutoryIdentifierPayload(BaseModel):
    identifier_value: str = Field(min_length=2)
    country: Optional[str] = None
    document_id: Optional[UUID] = None
    verification_status: str = "Pending Verification"


class PassportPayload(BaseModel):
    passport_number: str = Field(min_length=2)
    passport_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: date
    document_id: Optional[UUID] = None
    verification_status: str = "Pending Verification"


class VisaPayload(BaseModel):
    visa_type: str = Field(min_length=2)
    visa_number: Optional[str] = None
    visa_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: date
    document_id: Optional[UUID] = None


class WorkPermitPayload(BaseModel):
    work_permit_number: str = Field(min_length=2)
    work_permit_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: date
    document_id: Optional[UUID] = None


class ContractTrackingPayload(BaseModel):
    contract_start_date: date
    contract_end_date: date
    contract_document_id: Optional[UUID] = None
    renewal_status: str = "not_started"


class CertificationTrackingPayload(BaseModel):
    certification_name: str = Field(min_length=2)
    issuing_body: Optional[str] = None
    certificate_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    document_id: Optional[UUID] = None


class AccessRequestPayload(BaseModel):
    request_type: str = "account_creation"
    requested_systems: list[str] = Field(default_factory=list)
    requested_roles: list[str] = Field(default_factory=list)
    business_justification: Optional[str] = None
    access_expiry_date: Optional[date] = None


class SystemRolePayload(BaseModel):
    system_name: str = Field(min_length=2)
    role_name: str = Field(min_length=2)
    access_level: str = "standard"
    effective_from: date
    effective_to: Optional[date] = None
    business_justification: Optional[str] = None


class AccessActionPayload(BaseModel):
    reason: str = Field(min_length=3)
    system_name: Optional[str] = None
    reset_type: Optional[str] = None
    temporary_until: Optional[date] = None


class SalaryPayload(BaseModel):
    base_salary: Decimal = Field(ge=0)
    currency: str = "KES"
    salary_band: Optional[str] = None
    pay_frequency: str = "monthly"
    effective_date: date
    payroll_eligible: bool = True
    reason: str = Field(default="Compensation update", min_length=3)


class SalaryAdjustmentPayload(BaseModel):
    amount: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    reason: str = Field(min_length=3)
    effective_date: date


class AllowancePayload(BaseModel):
    allowance_type: str = Field(min_length=2)
    amount: Decimal = Field(ge=0)
    currency: str = "KES"
    recurring: bool = True
    taxable: bool = True
    effective_from: date
    effective_to: Optional[date] = None
    reason: Optional[str] = None


class RemovePayload(BaseModel):
    reason: str = Field(min_length=3)
    end_date: date


class BenefitPayload(BaseModel):
    benefit_type: str = Field(min_length=2)
    benefit_name: str = Field(min_length=2)
    provider: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    dependant_ids: list[UUID] = Field(default_factory=list)


class InsurancePlanPayload(BaseModel):
    plan_name: str = Field(min_length=2)
    provider: Optional[str] = None
    policy_number: Optional[str] = None
    coverage_start: date
    coverage_end: Optional[date] = None
    dependant_ids: list[UUID] = Field(default_factory=list)


class SelfServiceChangeRequestPayload(BaseModel):
    section: str = Field(min_length=2)
    requested_changes: dict[str, Any]
    reason: str = Field(min_length=3)


class ExportPayload(BaseModel):
    export_format: str = "csv"
    filters: dict[str, Any] = Field(default_factory=dict)
    columns: list[str] = Field(default_factory=list)


class OffboardingPayload(BaseModel):
    separation_type: Optional[str] = None
    separation_reason: Optional[str] = None
    effective_date: Optional[date] = None
    notice_period_days: int = 0
    reason: Optional[str] = None
    asset_name: Optional[str] = None
    asset_status: Optional[str] = None
    document_types: list[str] = Field(default_factory=list)
    final_salary: Decimal = 0
    leave_payout: Decimal = 0
    deductions: Decimal = 0
    asset_deductions: Decimal = 0
    allowances: Decimal = 0
    benefits: Decimal = 0
    tax_deductions: Decimal = 0
