from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RecruitmentBase(BaseModel):
    job_title: str
    department: Optional[str] = None
    branch: Optional[str] = None
    business_unit: Optional[str] = None
    hiring_manager_id: Optional[UUID] = None
    reporting_manager_id: Optional[UUID] = None
    candidate_name: str
    candidate_email: Optional[EmailStr] = None
    candidate_phone: Optional[str] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    application_date: Optional[date] = None
    interview_date: Optional[datetime] = None
    recruitment_stage: Optional[str] = "applied"
    application_status: Optional[str] = "pending"
    source_channel: Optional[str] = None
    opening_id: Optional[UUID] = None
    requisition_id: Optional[UUID] = None
    headcount_approved: bool = False
    budget_approved: bool = False
    offer_accepted: bool = False
    contract_signed: bool = False
    employment_contract_reference: Optional[str] = None
    target_start_date: Optional[date] = None
    approval_status: Optional[str] = "pending"
    employment_type: Optional[str] = None
    contract_end_date: Optional[date] = None
    salary_band: Optional[str] = None
    base_salary: Optional[Decimal] = None
    pay_frequency: Optional[str] = None
    probation_required: bool = False
    probation_duration_months: Optional[int] = None
    probation_end_date: Optional[date] = None
    expected_salary: Optional[Decimal] = None
    notes: Optional[str] = None


class RecruitmentCreate(RecruitmentBase):
    pass


class RecruitmentUpdate(BaseModel):
    job_title: Optional[str] = None
    department: Optional[str] = None
    branch: Optional[str] = None
    business_unit: Optional[str] = None
    hiring_manager_id: Optional[UUID] = None
    reporting_manager_id: Optional[UUID] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[EmailStr] = None
    candidate_phone: Optional[str] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    application_date: Optional[date] = None
    interview_date: Optional[datetime] = None
    recruitment_stage: Optional[str] = None
    application_status: Optional[str] = None
    source_channel: Optional[str] = None
    opening_id: Optional[UUID] = None
    requisition_id: Optional[UUID] = None
    headcount_approved: Optional[bool] = None
    budget_approved: Optional[bool] = None
    offer_accepted: Optional[bool] = None
    contract_signed: Optional[bool] = None
    employment_contract_reference: Optional[str] = None
    target_start_date: Optional[date] = None
    approval_status: Optional[str] = None
    employment_type: Optional[str] = None
    contract_end_date: Optional[date] = None
    salary_band: Optional[str] = None
    base_salary: Optional[Decimal] = None
    pay_frequency: Optional[str] = None
    probation_required: Optional[bool] = None
    probation_duration_months: Optional[int] = None
    probation_end_date: Optional[date] = None
    expected_salary: Optional[Decimal] = None
    notes: Optional[str] = None


class RecruitmentResponse(RecruitmentBase):
    id: UUID
    screening_score: Optional[Decimal] = None
    interview_score: Optional[Decimal] = None
    assessment_score: Optional[Decimal] = None
    background_score: Optional[Decimal] = None
    total_score: Optional[Decimal] = None
    ranking: Optional[int] = None
    background_check_status: Optional[str] = None
    offer_status: Optional[str] = None
    offer_expiry_date: Optional[date] = None
    successful_applicant_status: Optional[str] = None
    conversion_status: Optional[str] = None
    converted_employee_id: Optional[UUID] = None
    converted_at: Optional[datetime] = None
    document_readiness: Optional[str] = None
    compliance_readiness: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobRequisitionPayload(BaseModel):
    job_title: str
    department: str
    branch: Optional[str] = None
    business_unit: Optional[str] = None
    reporting_manager_id: Optional[UUID] = None
    hiring_manager_id: Optional[UUID] = None
    vacancies: int = Field(default=1, ge=1)
    employment_type: Optional[str] = None
    contract_duration: Optional[str] = None
    salary_band: Optional[str] = None
    budget_code: Optional[str] = None
    replacement_or_new_role: Optional[str] = None
    reason_for_hire: Optional[str] = None
    required_start_date: Optional[date] = None
    job_description: Optional[str] = None
    required_skills: list[str] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)


class ApprovalPayload(BaseModel):
    comments: Optional[str] = None
    reason: Optional[str] = None


class JobOpeningPayload(BaseModel):
    requisition_id: UUID
    description: Optional[str] = None
    closing_date: Optional[date] = None
    publishing_channels: list[str] = Field(default_factory=list)


class CandidatePayload(BaseModel):
    candidate_name: str
    candidate_email: Optional[EmailStr] = None
    candidate_phone: Optional[str] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    source_channel: Optional[str] = None
    notes: Optional[str] = None


class ApplicationPayload(CandidatePayload):
    opening_id: UUID
    expected_salary: Optional[Decimal] = None
    availability_date: Optional[date] = None
    cv_text: Optional[str] = None


class ScreeningPayload(BaseModel):
    screening_score: Decimal = Field(default=0, ge=0, le=100)
    assessment_score: Decimal = Field(default=0, ge=0, le=100)
    disqualified_reason: Optional[str] = None
    override_reason: Optional[str] = None


class InterviewPayload(BaseModel):
    recruitment_id: UUID
    opening_id: Optional[UUID] = None
    interview_stage: str = "First Interview"
    scheduled_at: datetime
    location_or_link: Optional[str] = None
    panel_member_ids: list[UUID] = Field(default_factory=list)


class InterviewFeedbackPayload(BaseModel):
    panel_member_id: Optional[UUID] = None
    technical_score: Decimal = Field(default=0, ge=0, le=100)
    culture_score: Decimal = Field(default=0, ge=0, le=100)
    communication_score: Decimal = Field(default=0, ge=0, le=100)
    experience_score: Decimal = Field(default=0, ge=0, le=100)
    recommendation: Optional[str] = None
    comments: Optional[str] = None


class OfferPayload(BaseModel):
    recruitment_id: UUID
    start_date: Optional[date] = None
    salary_band: Optional[str] = None
    base_salary: Optional[Decimal] = None
    benefits_summary: Optional[str] = None
    contract_end_date: Optional[date] = None
    probation_months: Optional[int] = None
    offer_expiry_date: Optional[date] = None


class OfferDecisionPayload(BaseModel):
    reason: Optional[str] = None


class CandidateDocumentPayload(BaseModel):
    recruitment_id: UUID
    document_type: str
    title: str
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_key: Optional[str] = None
    file_hash: Optional[str] = None
    is_confidential: bool = False
    expiry_date: Optional[date] = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ConvertApplicantPayload(BaseModel):
    confirm_missing_data: bool = True
    employee_overrides: dict[str, Any] = Field(default_factory=dict)


class BulkConvertPayload(BaseModel):
    applicant_ids: list[UUID]
    confirm_missing_data: bool = True
