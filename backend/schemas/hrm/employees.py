from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import date, datetime


class EmployeeBase(BaseModel):
    employee_code: Optional[str] = None
    candidate_id: Optional[UUID] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    preferred_name: Optional[str] = None
    national_id: Optional[str] = None
    tax_pin: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    place_of_birth: Optional[str] = None
    religion: Optional[str] = None
    marital_status: Optional[str] = None
    biography: Optional[str] = None
    professional_summary: Optional[str] = None
    skills: Optional[str] = None
    languages: Optional[str] = None
    certifications_summary: Optional[str] = None
    photo_url: Optional[str] = None
    profile_completion_percentage: Optional[float] = 0
    email: EmailStr
    personal_email: Optional[EmailStr] = None
    corporate_email: Optional[str] = None
    phone: Optional[str] = None
    alternative_phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    physical_address: Optional[str] = None
    postal_address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    country: Optional[str] = None

    department: Optional[str] = None
    business_unit: Optional[str] = None
    job_title: Optional[str] = None
    job_group: Optional[str] = None
    salary_grade: Optional[str] = None
    role_category: Optional[str] = None
    employment_type: Optional[str] = None
    employment_type_status: Optional[str] = "active"
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    institution: Optional[str] = None
    internship_supervisor: Optional[str] = None
    consultancy_agreement_ref: Optional[str] = None
    consultancy_project: Optional[str] = None
    extension_approved_until: Optional[date] = None
    probation_required: bool = False
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = "Not Applicable"
    probation_duration_months: Optional[int] = None
    probation_extended: bool = False
    probation_extension_count: int = 0
    probation_extension_reason: Optional[str] = None
    probation_confirmed_date: Optional[date] = None
    probation_confirmed_by: Optional[str] = None
    confirmation_status: Optional[str] = "Not Applicable"
    confirmation_date: Optional[date] = None
    confirmed_by: Optional[str] = None
    confirmation_notes: Optional[str] = None
    probation_review_id: Optional[UUID] = None
    next_confirmation_review_date: Optional[date] = None
    employment_status: Optional[str] = "active"
    internal_only: bool = True
    hire_date: Optional[date] = None
    pay_frequency: Optional[str] = "monthly"
    base_salary: Optional[float] = 0
    contract_signed: bool = False
    budget_approved: bool = False
    payroll_profile_status: Optional[str] = "pending"
    iam_request_status: Optional[str] = "pending"
    onboarding_status: Optional[str] = "pending"
    finance_mapping_status: Optional[str] = "pending"
    asset_request_status: Optional[str] = "pending"
    activation_date: Optional[datetime] = None
    activated_by: Optional[str] = None

    supervisor_id: Optional[UUID] = None
    branch: Optional[str] = None
    address: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    national_id: Optional[str] = None
    tax_pin: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    place_of_birth: Optional[str] = None
    religion: Optional[str] = None
    marital_status: Optional[str] = None
    biography: Optional[str] = None
    professional_summary: Optional[str] = None
    skills: Optional[str] = None
    languages: Optional[str] = None
    certifications_summary: Optional[str] = None
    photo_url: Optional[str] = None
    profile_completion_percentage: Optional[float] = None
    email: Optional[EmailStr] = None
    personal_email: Optional[EmailStr] = None
    corporate_email: Optional[str] = None
    phone: Optional[str] = None
    alternative_phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    physical_address: Optional[str] = None
    postal_address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    country: Optional[str] = None

    department: Optional[str] = None
    business_unit: Optional[str] = None
    job_title: Optional[str] = None
    job_group: Optional[str] = None
    salary_grade: Optional[str] = None
    role_category: Optional[str] = None
    employment_type: Optional[str] = None
    employment_type_status: Optional[str] = None
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    institution: Optional[str] = None
    internship_supervisor: Optional[str] = None
    consultancy_agreement_ref: Optional[str] = None
    consultancy_project: Optional[str] = None
    extension_approved_until: Optional[date] = None
    probation_required: Optional[bool] = None
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = None
    probation_duration_months: Optional[int] = None
    probation_extended: Optional[bool] = None
    probation_extension_count: Optional[int] = None
    probation_extension_reason: Optional[str] = None
    probation_confirmed_date: Optional[date] = None
    probation_confirmed_by: Optional[str] = None
    confirmation_status: Optional[str] = None
    confirmation_date: Optional[date] = None
    confirmed_by: Optional[str] = None
    confirmation_notes: Optional[str] = None
    probation_review_id: Optional[UUID] = None
    next_confirmation_review_date: Optional[date] = None
    employment_status: Optional[str] = None
    internal_only: Optional[bool] = None
    hire_date: Optional[date] = None
    pay_frequency: Optional[str] = None
    base_salary: Optional[float] = None
    contract_signed: Optional[bool] = None
    budget_approved: Optional[bool] = None
    payroll_profile_status: Optional[str] = None
    iam_request_status: Optional[str] = None
    onboarding_status: Optional[str] = None
    finance_mapping_status: Optional[str] = None
    asset_request_status: Optional[str] = None
    activation_date: Optional[datetime] = None
    activated_by: Optional[str] = None

    supervisor_id: Optional[UUID] = None
    branch: Optional[str] = None
    address: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
