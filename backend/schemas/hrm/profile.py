from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class EmployeeProfilePayload(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    preferred_name: Optional[str] = None
    gender: str
    date_of_birth: date
    nationality: Optional[str] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    place_of_birth: Optional[str] = None
    religion: Optional[str] = None
    marital_status: Optional[str] = None
    change_reason: Optional[str] = None


class EmployeeProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    place_of_birth: Optional[str] = None
    religion: Optional[str] = None
    marital_status: Optional[str] = None
    change_reason: Optional[str] = None


class ContactInformationPayload(BaseModel):
    personal_email: Optional[EmailStr] = None
    corporate_email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    alternative_phone: Optional[str] = None
    physical_address: Optional[str] = None
    postal_address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    country: Optional[str] = None
    change_reason: Optional[str] = None


class DependantPayload(BaseModel):
    full_name: str
    relationship: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    contact_information: Optional[str] = None
    beneficiary_percentage: float = Field(default=0, ge=0, le=100)
    medical_cover_eligible: bool = False


class DependantUpdate(BaseModel):
    full_name: Optional[str] = None
    relationship: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    contact_information: Optional[str] = None
    beneficiary_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    medical_cover_eligible: Optional[bool] = None


class EmergencyContactPayload(BaseModel):
    full_name: str
    relationship: str
    phone_number: str
    alternative_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    is_primary: bool = False


class EmergencyContactUpdate(BaseModel):
    full_name: Optional[str] = None
    relationship: Optional[str] = None
    phone_number: Optional[str] = None
    alternative_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    is_primary: Optional[bool] = None


class BiographyPayload(BaseModel):
    employee_bio: Optional[str] = None
    professional_summary: Optional[str] = None
    skills: Optional[str] = None
    languages: Optional[str] = None
    certifications_summary: Optional[str] = None


class ProfileResponse(BaseModel):
    employee_id: UUID
    profile_completion_percentage: float
    personal_information: dict[str, Any]
    contact_information: dict[str, Any] | None
    dependants: list[dict[str, Any]]
    emergency_contacts: list[dict[str, Any]]
    biography: dict[str, Any] | None
    active_photo: dict[str, Any] | None
    change_requests: list[dict[str, Any]]
    audit_history: list[dict[str, Any]]

    class Config:
        from_attributes = True
