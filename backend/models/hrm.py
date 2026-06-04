import uuid

from sqlalchemy import Column, String, Date, DateTime, Numeric, Boolean, Text, Time, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.core.database import Base


class HRMEmployee(Base):
    __tablename__ = "hrm_employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_code = Column(String, unique=True, nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    preferred_name = Column(String, nullable=True)
    national_id = Column(String, unique=True, nullable=True, index=True)
    tax_pin = Column(String, unique=True, nullable=True, index=True)
    passport_number = Column(String, unique=True, nullable=True, index=True)
    nationality = Column(String, nullable=True)
    place_of_birth = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    biography = Column(Text, nullable=True)
    professional_summary = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    languages = Column(Text, nullable=True)
    certifications_summary = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    profile_completion_percentage = Column(Numeric(5, 2), default=0)
    email = Column(String, unique=True, nullable=False, index=True)
    personal_email = Column(String, unique=True, nullable=True, index=True)
    corporate_email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    alternative_phone = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    physical_address = Column(Text, nullable=True)
    postal_address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    county = Column(String, nullable=True)
    country = Column(String, nullable=True)

    department = Column(String, nullable=True)
    business_unit = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    job_group = Column(String, nullable=True)
    salary_grade = Column(String, nullable=True)
    salary_band = Column(String, nullable=True)
    cost_center_code = Column(String, nullable=True)
    functional_manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    functional_manager_scope = Column(String, nullable=True)
    role_category = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)
    employment_type_status = Column(String, default="active", nullable=False)
    employment_start_date = Column(Date, nullable=True)
    employment_end_date = Column(Date, nullable=True)
    institution = Column(String, nullable=True)
    internship_supervisor = Column(String, nullable=True)
    consultancy_agreement_ref = Column(String, nullable=True)
    consultancy_project = Column(String, nullable=True)
    extension_approved_until = Column(Date, nullable=True)
    probation_required = Column(Boolean, default=False, nullable=False)
    probation_start_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    probation_status = Column(String, default="Not Applicable", nullable=False)
    probation_duration_months = Column(Integer, nullable=True)
    probation_extended = Column(Boolean, default=False, nullable=False)
    probation_extension_count = Column(Integer, default=0, nullable=False)
    probation_extension_reason = Column(Text, nullable=True)
    probation_confirmed_date = Column(Date, nullable=True)
    probation_confirmed_by = Column(String, nullable=True)
    confirmation_status = Column(String, default="Not Applicable", nullable=False)
    confirmation_date = Column(Date, nullable=True)
    confirmed_by = Column(String, nullable=True)
    confirmation_notes = Column(Text, nullable=True)
    probation_review_id = Column(UUID(as_uuid=True), nullable=True)
    next_confirmation_review_date = Column(Date, nullable=True)
    employment_status = Column(String, default="active", nullable=False)
    internal_only = Column(Boolean, default=True, nullable=False)
    hire_date = Column(Date, nullable=True)
    pay_frequency = Column(String, default="monthly", nullable=True)
    base_salary = Column(Numeric(12, 2), default=0)
    contract_signed = Column(Boolean, default=False, nullable=False)
    budget_approved = Column(Boolean, default=False, nullable=False)
    payroll_profile_status = Column(String, default="pending", nullable=False)
    iam_request_status = Column(String, default="pending", nullable=False)
    onboarding_status = Column(String, default="pending", nullable=False)
    finance_mapping_status = Column(String, default="pending", nullable=False)
    asset_request_status = Column(String, default="pending", nullable=False)
    activation_date = Column(DateTime(timezone=True), nullable=True)
    activated_by = Column(String, nullable=True)

    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    branch = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMDepartment(Base):
    __tablename__ = "hrm_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    head_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String, default="active", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPayroll(Base):
    __tablename__ = "hrm_payroll"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)

    payroll_month = Column(String, nullable=False)
    basic_salary = Column(Numeric(12, 2), nullable=False)

    allowances = Column(Numeric(12, 2), default=0)
    bonuses = Column(Numeric(12, 2), default=0)
    overtime_pay = Column(Numeric(12, 2), default=0)

    deductions = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    statutory_deductions = Column(Numeric(12, 2), default=0)

    gross_pay = Column(Numeric(12, 2), nullable=False)
    net_pay = Column(Numeric(12, 2), nullable=False)

    payment_status = Column(String, default="pending")
    payment_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLeave(Base):
    __tablename__ = "hrm_leave"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)

    leave_type = Column(String, nullable=False)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave_types.id"), nullable=True, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave_policies.id"), nullable=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_day_type = Column(String, default="Full Day", nullable=False)
    end_day_type = Column(String, default="Full Day", nullable=False)
    calendar_days = Column(Numeric(8, 2), default=0)
    working_days = Column(Numeric(8, 2), default=0)
    leave_days = Column(Numeric(8, 2), default=0)
    excluded_weekends_count = Column(Integer, default=0)
    excluded_public_holidays_count = Column(Integer, default=0)
    return_to_work_date = Column(Date, nullable=True)
    total_days = Column(Numeric(5, 2), nullable=False)

    reason = Column(Text, nullable=True)
    supporting_document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=True)
    status = Column(String, default="pending")
    current_approver_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    payroll_lock_status = Column(String, default="open", nullable=False)
    attendance_sync_status = Column(String, default="pending", nullable=False)
    payroll_sync_status = Column(String, default="pending", nullable=False)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    payroll_impact = Column(JSON, nullable=True)
    attendance_impact = Column(JSON, nullable=True)

    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    approval_comments = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMAttendance(Base):
    __tablename__ = "hrm_attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    attendance_date = Column(Date, nullable=False)

    clock_in = Column(Time, nullable=True)
    clock_out = Column(Time, nullable=True)

    total_hours = Column(Numeric(5, 2), default=0)
    overtime_hours = Column(Numeric(5, 2), default=0)

    status = Column(String, default="present")
    work_mode = Column(String, default="office")

    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMRecruitment(Base):
    __tablename__ = "hrm_recruitment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    job_title = Column(String, nullable=False)
    department = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    business_unit = Column(String, nullable=True)
    hiring_manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    reporting_manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)

    candidate_name = Column(String, nullable=False)
    candidate_email = Column(String, nullable=True)
    candidate_phone = Column(String, nullable=True)
    national_id = Column(String, nullable=True)
    passport_number = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    application_date = Column(Date, nullable=True)
    interview_date = Column(DateTime(timezone=True), nullable=True)

    recruitment_stage = Column(String, default="applied")
    application_status = Column(String, default="pending")
    source_channel = Column(String, nullable=True)
    opening_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    requisition_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    headcount_approved = Column(Boolean, default=False, nullable=False)
    budget_approved = Column(Boolean, default=False, nullable=False)
    offer_accepted = Column(Boolean, default=False, nullable=False)
    contract_signed = Column(Boolean, default=False, nullable=False)
    employment_contract_reference = Column(String, nullable=True)
    target_start_date = Column(Date, nullable=True)
    approval_status = Column(String, default="pending", nullable=False)
    employment_type = Column(String, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    salary_band = Column(String, nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=True)
    pay_frequency = Column(String, nullable=True)
    probation_required = Column(Boolean, default=False, nullable=False)
    probation_duration_months = Column(Integer, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    screening_score = Column(Numeric(6, 2), default=0)
    interview_score = Column(Numeric(6, 2), default=0)
    assessment_score = Column(Numeric(6, 2), default=0)
    background_score = Column(Numeric(6, 2), default=0)
    total_score = Column(Numeric(6, 2), default=0)
    ranking = Column(Integer, nullable=True)
    background_check_status = Column(String, default="pending", nullable=False)
    offer_status = Column(String, default="draft", nullable=False)
    offer_expiry_date = Column(Date, nullable=True)
    successful_applicant_status = Column(String, default="not_ready", nullable=False)
    conversion_status = Column(String, default="not_converted", nullable=False)
    converted_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    parsed_cv_json = Column(JSON, nullable=True)
    document_readiness = Column(String, default="pending", nullable=False)
    compliance_readiness = Column(String, default="pending", nullable=False)

    expected_salary = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMCandidateDocument(Base):
    __tablename__ = "hrm_candidate_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    recruitment_id = Column(UUID(as_uuid=True), ForeignKey("hrm_recruitment.id"), nullable=False, index=True)
    document_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    file_key = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    version_number = Column(Integer, default=1, nullable=False)
    is_current_version = Column(Boolean, default=True, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)
    verification_status = Column(String, default="Pending Verification", nullable=False)
    expiry_date = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    uploaded_by = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMInterview(Base):
    __tablename__ = "hrm_interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    recruitment_id = Column(UUID(as_uuid=True), ForeignKey("hrm_recruitment.id"), nullable=False, index=True)
    opening_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    interview_stage = Column(String, default="First Interview", nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    location_or_link = Column(String, nullable=True)
    panel_member_ids = Column(JSON, nullable=True)
    status = Column(String, default="scheduled", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMCandidateEmployeeConversion(Base):
    __tablename__ = "hrm_candidate_employee_conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    recruitment_id = Column(UUID(as_uuid=True), ForeignKey("hrm_recruitment.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    conversion_status = Column(String, default="completed", nullable=False)
    readiness_snapshot = Column(JSON, nullable=True)
    integration_events = Column(JSON, nullable=True)
    converted_by = Column(String, nullable=True)
    converted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMRecruitmentAuditLog(Base):
    __tablename__ = "hrm_recruitment_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    recruitment_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action = Column(String, nullable=False)
    actor_email = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMPerformance(Base):
    __tablename__ = "hrm_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)

    review_period = Column(String, nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    review_date = Column(Date, nullable=True)

    goals = Column(Text, nullable=True)
    achievements = Column(Text, nullable=True)
    areas_of_improvement = Column(Text, nullable=True)

    performance_score = Column(Numeric(5, 2), nullable=True)
    rating = Column(String, nullable=True)

    promotion_recommendation = Column(Boolean, default=False)
    training_recommendation = Column(Text, nullable=True)

    comments = Column(Text, nullable=True)
    status = Column(String, default="draft")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMTraining(Base):
    __tablename__ = "hrm_training"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)

    training_title = Column(String, nullable=False)
    training_provider = Column(String, nullable=True)
    training_type = Column(String, nullable=True)

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    cost = Column(Numeric(12, 2), default=0)
    certification_awarded = Column(Boolean, default=False)
    certificate_name = Column(String, nullable=True)

    completion_status = Column(String, default="not_started")
    score = Column(Numeric(5, 2), nullable=True)

    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMBenefit(Base):
    __tablename__ = "hrm_benefits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)

    benefit_type = Column(String, nullable=False)
    benefit_name = Column(String, nullable=False)

    provider = Column(String, nullable=True)
    policy_number = Column(String, nullable=True)

    employer_contribution = Column(Numeric(12, 2), default=0)
    employee_contribution = Column(Numeric(12, 2), default=0)

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    status = Column(String, default="active")
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMDocument(Base):
    __tablename__ = "hrm_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)

    document_title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String, nullable=False)

    file_name = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    file_key = Column(String, nullable=True)
    file_extension = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    version_number = Column(Integer, default=1)
    current_version = Column(Boolean, default=True, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    visibility_level = Column(String, default="hr", nullable=False)

    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    uploaded_by_name = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    confidentiality_level = Column(String, default="internal")
    verification_status = Column(String, default="Pending Verification", nullable=False)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(String, nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by = Column(String, nullable=True)
    archive_reason = Column(Text, nullable=True)
    ocr_summary = Column(Text, nullable=True)

    status = Column(String, default="active")
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeDepartmentAssignment(Base):
    __tablename__ = "hrm_employee_department_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    department = Column(String, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    approval_status = Column(String, default="approved", nullable=False)
    status = Column(String, default="active", nullable=False)
    initiated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeBranchAssignment(Base):
    __tablename__ = "hrm_employee_branch_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    branch = Column(String, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    approval_status = Column(String, default="approved", nullable=False)
    status = Column(String, default="active", nullable=False)
    initiated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeBusinessUnitAssignment(Base):
    __tablename__ = "hrm_employee_business_unit_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    business_unit = Column(String, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    approval_status = Column(String, default="approved", nullable=False)
    status = Column(String, default="active", nullable=False)
    initiated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeProjectAssignment(Base):
    __tablename__ = "hrm_employee_project_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_name = Column(String, nullable=True)
    project_role = Column(String, nullable=False)
    allocation_percentage = Column(Numeric(5, 2), default=0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    initiated_by = Column(String, nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeTeamAssignment(Base):
    __tablename__ = "hrm_employee_team_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    team_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    primary_team = Column(Boolean, default=False, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    initiated_by = Column(String, nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeAssignmentHistory(Base):
    __tablename__ = "hrm_employee_assignment_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    buc_code = Column(String, nullable=False)
    assignment_type = Column(String, nullable=False)
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    initiated_by = Column(String, nullable=True)
    audit_reference = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeTransferRequest(Base):
    __tablename__ = "hrm_employee_transfer_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    transfer_type = Column(String, nullable=False)
    current_value = Column(String, nullable=True)
    new_value = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    approval_status = Column(String, default="pending", nullable=False)
    requested_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDocumentVersion(Base):
    __tablename__ = "hrm_employee_document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_key = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    replacement_reason = Column(Text, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    uploaded_by_name = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="current", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDocumentReview(Base):
    __tablename__ = "hrm_employee_document_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    decision = Column(String, nullable=False)
    review_action = Column(String, nullable=True)
    reviewer = Column(String, nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    comments = Column(Text, nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDocumentExpiryTracking(Base):
    __tablename__ = "hrm_employee_document_expiry_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    expiry_date = Column(Date, nullable=False)
    reminder_stage = Column(String, nullable=False)
    reminder_90_sent = Column(Boolean, default=False, nullable=False)
    reminder_60_sent = Column(Boolean, default=False, nullable=False)
    reminder_30_sent = Column(Boolean, default=False, nullable=False)
    reminder_7_sent = Column(Boolean, default=False, nullable=False)
    escalation_level = Column(String, default="employee", nullable=False)
    escalation_status = Column(String, default="not_escalated", nullable=False)
    notification_status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDocumentRejection(Base):
    __tablename__ = "hrm_employee_document_rejections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    rejection_reason = Column(Text, nullable=False)
    rejected_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDocumentArchive(Base):
    __tablename__ = "hrm_employee_document_archive"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    archived_by = Column(String, nullable=True)
    archive_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDocumentTypeConfig(Base):
    __tablename__ = "hrm_employee_document_type_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_type = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    requires_verification = Column(Boolean, default=True, nullable=False)
    allows_expiry_date = Column(Boolean, default=False, nullable=False)
    requires_issue_date = Column(Boolean, default=False, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)
    allowed_file_types = Column(JSON, nullable=True)
    max_file_size_mb = Column(Integer, default=15, nullable=False)
    retention_policy = Column(String, default="employee_lifecycle_plus_7_years")
    access_level_required = Column(String, default="hr")
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDocumentAccessLog(Base):
    __tablename__ = "hrm_employee_document_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    accessed_by = Column(String, nullable=True)
    access_type = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMActivity(Base):
    __tablename__ = "hrm_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    activity_title = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    department = Column(String, nullable=True)
    activity_date = Column(Date, nullable=True)
    budget_amount = Column(Numeric(12, 2), default=0)
    actual_cost = Column(Numeric(12, 2), default=0)
    participation_count = Column(Numeric(10, 0), default=0)
    status = Column(String, default="planned")
    outcomes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMGRCRecord(Base):
    __tablename__ = "hrm_grc_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    record_title = Column(String, nullable=False)
    grc_area = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    department = Column(String, nullable=True)
    risk_level = Column(String, default="medium")
    compliance_status = Column(String, default="pending")
    due_date = Column(Date, nullable=True)
    evidence_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMPosition(Base):
    __tablename__ = "hrm_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    position_code = Column(String, unique=True, nullable=False, index=True)
    position_title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    job_group = Column(String, nullable=True)
    salary_grade = Column(String, nullable=True)
    reports_to_position = Column(String, nullable=True)
    headcount_budget = Column(Numeric(10, 2), default=1)
    current_headcount = Column(Numeric(10, 2), default=0)
    status = Column(String, default="active")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMOnboardingTask(Base):
    __tablename__ = "hrm_onboarding_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    task_name = Column(String, nullable=False)
    task_category = Column(String, default="General")
    owner = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLeaveBalance(Base):
    __tablename__ = "hrm_leave_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    leave_type = Column(String, nullable=False)
    fiscal_year = Column(String, nullable=False)
    opening_balance = Column(Numeric(8, 2), default=0)
    accrued_days = Column(Numeric(8, 2), default=0)
    used_days = Column(Numeric(8, 2), default=0)
    adjusted_days = Column(Numeric(8, 2), default=0)
    available_days = Column(Numeric(8, 2), default=0)
    status = Column(String, default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLeavePolicyAssignment(Base):
    __tablename__ = "hrm_leave_policy_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave_policies.id"), nullable=False, index=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    assignment_reason = Column(Text, nullable=True)
    assigned_by = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLeaveRequestDay(Base):
    __tablename__ = "hrm_leave_request_days"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    leave_date = Column(Date, nullable=False, index=True)
    day_value = Column(Numeric(4, 2), default=1, nullable=False)
    is_working_day = Column(Boolean, default=True, nullable=False)
    is_public_holiday = Column(Boolean, default=False, nullable=False)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveRequestApproval(Base):
    __tablename__ = "hrm_leave_request_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    approval_step = Column(String, nullable=False)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    approver_name = Column(String, nullable=True)
    approval_status = Column(String, default="Pending", nullable=False, index=True)
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveBalanceTransaction(Base):
    __tablename__ = "hrm_leave_balance_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    leave_type = Column(String, nullable=False, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=True, index=True)
    transaction_type = Column(String, nullable=False, index=True)
    amount = Column(Numeric(8, 2), nullable=False)
    balance_before = Column(Numeric(8, 2), default=0)
    balance_after = Column(Numeric(8, 2), default=0)
    reason = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveBalanceAdjustment(Base):
    __tablename__ = "hrm_leave_balance_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    leave_type = Column(String, nullable=False, index=True)
    adjustment_amount = Column(Numeric(8, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    created_by = Column(String, nullable=True)
    status = Column(String, default="approved", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveCarryForwardRecord(Base):
    __tablename__ = "hrm_leave_carry_forward_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    leave_type = Column(String, nullable=False)
    from_cycle = Column(String, nullable=True)
    to_cycle = Column(String, nullable=True)
    carried_forward_days = Column(Numeric(8, 2), default=0)
    expired_days = Column(Numeric(8, 2), default=0)
    expiry_date = Column(Date, nullable=True)
    status = Column(String, default="processed", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveEncashment(Base):
    __tablename__ = "hrm_leave_encashments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    leave_type = Column(String, nullable=False)
    encashed_days = Column(Numeric(8, 2), nullable=False)
    daily_rate = Column(Numeric(12, 2), default=0)
    encashment_amount = Column(Numeric(12, 2), default=0)
    approval_status = Column(String, default="approved", nullable=False)
    payroll_sync_status = Column(String, default="queued", nullable=False)
    reason = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveCancellationRecord(Base):
    __tablename__ = "hrm_leave_cancellation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    cancelled_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveRecallRecord(Base):
    __tablename__ = "hrm_leave_recall_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    recall_date = Column(Date, nullable=False)
    used_days = Column(Numeric(8, 2), default=0)
    restored_days = Column(Numeric(8, 2), default=0)
    reason = Column(Text, nullable=False)
    recalled_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveExtensionRecord(Base):
    __tablename__ = "hrm_leave_extension_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    old_end_date = Column(Date, nullable=False)
    new_end_date = Column(Date, nullable=False)
    additional_days = Column(Numeric(8, 2), default=0)
    reason = Column(Text, nullable=False)
    approval_status = Column(String, default="approved", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveCalendarEvent(Base):
    __tablename__ = "hrm_leave_calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    event_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    visibility = Column(String, default="team", nullable=False)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeWorkSchedule(Base):
    __tablename__ = "hrm_employee_work_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    schedule_name = Column(String, default="Default Monday-Friday", nullable=False)
    working_days = Column(JSON, nullable=True)
    country = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMLeaveAuditLog(Base):
    __tablename__ = "hrm_leave_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    actor_email = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMCompensation(Base):
    __tablename__ = "hrm_compensation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    effective_date = Column(Date, nullable=False)
    compensation_type = Column(String, default="salary")
    base_salary = Column(Numeric(12, 2), default=0)
    allowances = Column(Numeric(12, 2), default=0)
    bonus_target = Column(Numeric(12, 2), default=0)
    currency = Column(String, default="KES")
    pay_frequency = Column(String, default="monthly")
    approval_status = Column(String, default="draft")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLifecycleEvent(Base):
    __tablename__ = "hrm_lifecycle_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    event_type = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False)
    from_value = Column(String, nullable=True)
    to_value = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String, default="approved")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeMovement(Base):
    __tablename__ = "hrm_employee_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    movement_code = Column(String, nullable=False, index=True)
    movement_type = Column(String, nullable=False, index=True)
    current_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    current_job_details = Column(JSON, nullable=True)
    new_job_details = Column(JSON, nullable=True)
    effective_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)
    reason = Column(Text, nullable=False)
    supporting_document_url = Column(String, nullable=True)
    initiated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approval_status = Column(String, default="approved", nullable=False, index=True)
    workflow_status = Column(String, default="completed", nullable=False)
    integration_events = Column(JSON, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeMovementApproval(Base):
    __tablename__ = "hrm_employee_movement_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    movement_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_movements.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    approval_level = Column(Integer, default=1, nullable=False)
    approver_role = Column(String, nullable=True)
    approver_name = Column(String, nullable=True)
    decision = Column(String, default="approved", nullable=False)
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeStatusHistory(Base):
    __tablename__ = "hrm_employee_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    status_code = Column(String, nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False, index=True)
    effective_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    initiated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approval_status = Column(String, default="approved", nullable=False)
    workflow_status = Column(String, default="completed", nullable=False)
    supporting_document_url = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMPolicyAcknowledgement(Base):
    __tablename__ = "hrm_policy_acknowledgements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    policy_name = Column(String, nullable=False)
    policy_version = Column(String, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeRelationCase(Base):
    __tablename__ = "hrm_employee_relation_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    case_type = Column(String, nullable=False)
    case_title = Column(String, nullable=False)
    opened_date = Column(Date, nullable=False)
    owner = Column(String, nullable=True)
    severity = Column(String, default="medium")
    status = Column(String, default="open")
    resolution = Column(Text, nullable=True)
    confidentiality_level = Column(String, default="confidential")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMSurvey(Base):
    __tablename__ = "hrm_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    survey_title = Column(String, nullable=False)
    survey_type = Column(String, default="engagement")
    department = Column(String, nullable=True)
    launch_date = Column(Date, nullable=True)
    close_date = Column(Date, nullable=True)
    response_count = Column(Numeric(10, 0), default=0)
    average_score = Column(Numeric(5, 2), default=0)
    status = Column(String, default="draft")
    insights = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMAssetAssignment(Base):
    __tablename__ = "hrm_asset_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    asset_name = Column(String, nullable=False)
    asset_tag = Column(String, nullable=True)
    assigned_date = Column(Date, nullable=False)
    return_due_date = Column(Date, nullable=True)
    returned_date = Column(Date, nullable=True)
    condition_on_issue = Column(String, nullable=True)
    condition_on_return = Column(String, nullable=True)
    status = Column(String, default="assigned")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMCompany(Base):
    __tablename__ = "hrm_companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_code = Column(String, unique=True, nullable=False, index=True)
    company_name = Column(String, nullable=False)
    legal_name = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    country = Column(String, nullable=True)
    currency = Column(String, default="KES")
    status = Column(String, default="active", nullable=False)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMBranch(Base):
    __tablename__ = "hrm_branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("hrm_companies.id"), nullable=True)
    branch_code = Column(String, unique=True, nullable=False, index=True)
    branch_name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMCostCenter(Base):
    __tablename__ = "hrm_cost_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    cost_center_code = Column(String, unique=True, nullable=False, index=True)
    cost_center_name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    budget_owner = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMJobGrade(Base):
    __tablename__ = "hrm_job_grades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    grade_code = Column(String, unique=True, nullable=False, index=True)
    grade_name = Column(String, nullable=False)
    level = Column(Integer, nullable=True)
    min_salary = Column(Numeric(12, 2), nullable=True)
    max_salary = Column(Numeric(12, 2), nullable=True)
    currency = Column(String, default="KES")
    status = Column(String, default="active", nullable=False)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMJobTitle(Base):
    __tablename__ = "hrm_job_titles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title_code = Column(String, unique=True, nullable=False, index=True)
    title_name = Column(String, nullable=False, index=True)
    department = Column(String, nullable=False)
    function = Column(String, nullable=True)
    compatible_grade_codes = Column(JSON, nullable=True)
    default_salary_band_code = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMSalaryBand(Base):
    __tablename__ = "hrm_salary_bands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    band_code = Column(String, unique=True, nullable=False, index=True)
    band_name = Column(String, nullable=False)
    grade_code = Column(String, nullable=True, index=True)
    min_salary = Column(Numeric(12, 2), nullable=True)
    max_salary = Column(Numeric(12, 2), nullable=True)
    currency = Column(String, default="KES")
    confidentiality_level = Column(String, default="restricted", nullable=False)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeEmploymentInfo(Base):
    __tablename__ = "hrm_employee_employment_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), unique=True, nullable=False, index=True)
    job_title = Column(String, nullable=True)
    job_grade = Column(String, nullable=True)
    salary_band = Column(String, nullable=True)
    cost_center_code = Column(String, nullable=True)
    reporting_manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    functional_manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    functional_manager_scope = Column(String, nullable=True)
    effective_from = Column(Date, nullable=True)
    status = Column(String, default="active", nullable=False)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeEmploymentHistory(Base):
    __tablename__ = "hrm_employee_employment_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    buc_code = Column(String, nullable=False, index=True)
    field_type = Column(String, nullable=False, index=True)
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    status = Column(String, default="active", nullable=False)
    reason = Column(Text, nullable=True)
    supporting_document_url = Column(String, nullable=True)
    initiated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    audit_trail_reference = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeManagerAssignment(Base):
    __tablename__ = "hrm_employee_manager_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    manager_type = Column(String, nullable=False, index=True)
    authority_scope = Column(String, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    status = Column(String, default="active", nullable=False)
    reason = Column(Text, nullable=True)
    initiated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmploymentChangeRequest(Base):
    __tablename__ = "hrm_employment_change_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    buc_code = Column(String, nullable=False, index=True)
    field_type = Column(String, nullable=False)
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    supporting_document_url = Column(String, nullable=True)
    authority_scope = Column(String, nullable=True)
    approval_status = Column(String, default="pending", nullable=False, index=True)
    requested_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmploymentApproval(Base):
    __tablename__ = "hrm_employment_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employment_change_requests.id"), nullable=False, index=True)
    approver_role = Column(String, nullable=False)
    approver_name = Column(String, nullable=True)
    decision = Column(String, default="pending", nullable=False)
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmploymentAuditLog(Base):
    __tablename__ = "hrm_employment_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    actor_email = Column(String, nullable=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    buc_code = Column(String, nullable=False)
    action = Column(String, nullable=False)
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    approval_reference = Column(UUID(as_uuid=True), nullable=True)
    reason = Column(Text, nullable=True)
    result = Column(String, default="success")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmploymentContract(Base):
    __tablename__ = "hrm_employment_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    contract_number = Column(String, unique=True, nullable=False, index=True)
    contract_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(String, default="draft", nullable=False)
    signed_document_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmergencyContact(Base):
    __tablename__ = "hrm_emergency_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    contact_name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    status = Column(String, default="active", nullable=False)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeProfile(Base):
    __tablename__ = "hrm_employee_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    preferred_name = Column(String, nullable=True)
    gender = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    nationality = Column(String, nullable=True)
    national_id = Column(String, nullable=True)
    passport_number = Column(String, nullable=True)
    place_of_birth = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    employee_status = Column(String, nullable=True)
    profile_completion_percentage = Column(Numeric(5, 2), default=0)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeProfileHistory(Base):
    __tablename__ = "hrm_employee_profile_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    section = Column(String, nullable=False)
    field_name = Column(String, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    approval_status = Column(String, default="applied", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeContactInformation(Base):
    __tablename__ = "hrm_employee_contact_information"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), unique=True, nullable=False, index=True)
    personal_email = Column(String, nullable=True, index=True)
    corporate_email = Column(String, nullable=True)
    mobile_number = Column(String, nullable=True)
    alternative_phone = Column(String, nullable=True)
    physical_address = Column(Text, nullable=True)
    postal_address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    county = Column(String, nullable=True)
    country = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeDependant(Base):
    __tablename__ = "hrm_employee_dependants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    full_name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    contact_information = Column(String, nullable=True)
    beneficiary_percentage = Column(Numeric(5, 2), default=0)
    medical_cover_eligible = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archive_reason = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeDependantHistory(Base):
    __tablename__ = "hrm_employee_dependant_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    dependant_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_dependants.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    changed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeEmergencyContactHistory(Base):
    __tablename__ = "hrm_employee_emergency_contact_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("hrm_emergency_contacts.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    changed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeBiography(Base):
    __tablename__ = "hrm_employee_biographies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), unique=True, nullable=False, index=True)
    employee_bio = Column(Text, nullable=True)
    professional_summary = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    languages = Column(Text, nullable=True)
    certifications_summary = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeProfilePhoto(Base):
    __tablename__ = "hrm_employee_profile_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeChangeRequest(Base):
    __tablename__ = "hrm_employee_change_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    section = Column(String, nullable=False)
    requested_changes = Column(JSON, nullable=False)
    reason = Column(Text, nullable=True)
    approval_status = Column(String, default="pending_hr_approval", nullable=False)
    requested_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMRole(Base):
    __tablename__ = "hrm_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    role_code = Column(String, unique=True, nullable=False, index=True)
    role_name = Column(String, nullable=False)
    role_scope = Column(String, default="hrm", nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPermission(Base):
    __tablename__ = "hrm_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    permission_code = Column(String, unique=True, nullable=False, index=True)
    module = Column(String, nullable=False)
    action = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMRolePermission(Base):
    __tablename__ = "hrm_role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("hrm_roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("hrm_permissions.id"), nullable=False)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMUserEmployeeLink(Base):
    __tablename__ = "hrm_user_employee_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    status = Column(String, default="active", nullable=False)
    linked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    unlinked_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class HRMAuditLog(Base):
    __tablename__ = "hrm_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    actor_email = Column(String, nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    sensitivity = Column(String, default="internal", nullable=False)
    summary = Column(Text, nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeImportBatch(Base):
    __tablename__ = "hrm_employee_import_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    batch_number = Column(String, unique=True, nullable=False, index=True)
    file_name = Column(String, nullable=True)
    file_hash = Column(String, nullable=True, index=True)
    source_format = Column(String, nullable=False)
    import_mode = Column(String, default="create")
    uploaded_by = Column(String, nullable=True)
    approval_status = Column(String, default="not_required", nullable=False)
    processing_status = Column(String, default="uploaded", nullable=False)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    created_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    parse_summary = Column(Text, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    rollback_status = Column(String, default="not_requested")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeImportRow(Base):
    __tablename__ = "hrm_employee_import_rows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_import_batches.id"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    employee_code = Column(String, nullable=True, index=True)
    row_payload = Column(JSON, nullable=True)
    normalized_payload = Column(JSON, nullable=True)
    row_status = Column(String, default="pending", nullable=False)
    action_taken = Column(String, nullable=True)
    error_messages = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeEmploymentDetail(Base):
    __tablename__ = "hrm_employee_employment_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    employment_type = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True, index=True)
    institution = Column(String, nullable=True)
    internship_supervisor = Column(String, nullable=True)
    consultancy_agreement_ref = Column(String, nullable=True)
    consultancy_project = Column(String, nullable=True)
    extension_approved_until = Column(Date, nullable=True)
    probation_required = Column(Boolean, default=False, nullable=False)
    probation_start_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    probation_status = Column(String, default="Not Applicable", nullable=False)
    probation_duration_months = Column(Integer, nullable=True)
    probation_extended = Column(Boolean, default=False, nullable=False)
    probation_extension_count = Column(Integer, default=0, nullable=False)
    probation_extension_reason = Column(Text, nullable=True)
    probation_confirmed_date = Column(Date, nullable=True)
    probation_confirmed_by = Column(String, nullable=True)
    expiry_status = Column(String, default="active", nullable=False, index=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmploymentTypeHistory(Base):
    __tablename__ = "hrm_employee_employment_type_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    previous_type = Column(String, nullable=True)
    new_type = Column(String, nullable=False)
    previous_end_date = Column(Date, nullable=True)
    new_end_date = Column(Date, nullable=True)
    change_reason = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMContractExtension(Base):
    __tablename__ = "hrm_employee_contract_extensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    employment_detail_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_employment_details.id"), nullable=True)
    previous_end_date = Column(Date, nullable=True)
    new_end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    approval_status = Column(String, default="approved", nullable=False, index=True)
    approved_by = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMProbationRecord(Base):
    __tablename__ = "hrm_employee_probation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    employment_detail_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_employment_details.id"), nullable=True)
    probation_required = Column(Boolean, default=False, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True, index=True)
    duration_months = Column(Integer, nullable=True)
    status = Column(String, default="Not Applicable", nullable=False, index=True)
    extended = Column(Boolean, default=False, nullable=False)
    extension_count = Column(Integer, default=0, nullable=False)
    max_extension_count = Column(Integer, default=2, nullable=False)
    extension_reason = Column(Text, nullable=True)
    confirmed_date = Column(Date, nullable=True)
    confirmed_by = Column(String, nullable=True)
    failed_date = Column(Date, nullable=True)
    failed_reason = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMProbationReview(Base):
    __tablename__ = "hrm_employee_probation_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    probation_record_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_probation_records.id"), nullable=False, index=True)
    review_type = Column(String, nullable=False)
    outcome = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    reviewer = Column(String, nullable=True)
    review_date = Column(Date, default=func.current_date(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMConfirmationRecord(Base):
    __tablename__ = "hrm_employee_confirmation_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    probation_record_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_probation_records.id"), nullable=True, index=True)
    probation_review_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_probation_reviews.id"), nullable=True, index=True)
    decision = Column(String, nullable=False, index=True)
    status = Column(String, default="Pending Confirmation", nullable=False, index=True)
    confirmation_date = Column(Date, nullable=True)
    confirmed_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    next_review_date = Column(Date, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLeaveType(Base):
    __tablename__ = "hrm_leave_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_code = Column(String, unique=True, nullable=False, index=True)
    leave_name = Column(String, nullable=False)
    paid = Column(Boolean, default=True, nullable=False)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLeavePolicy(Base):
    __tablename__ = "hrm_leave_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("hrm_leave_types.id"), nullable=True)
    policy_name = Column(String, nullable=False)
    annual_entitlement = Column(Numeric(8, 2), default=0)
    accrual_frequency = Column(String, default="monthly")
    allow_negative_balance = Column(Boolean, default=False, nullable=False)
    max_negative_days = Column(Numeric(8, 2), default=0)
    carry_forward_allowed = Column(Boolean, default=False, nullable=False)
    carry_forward_limit = Column(Numeric(8, 2), default=0)
    approval_required = Column(Boolean, default=True, nullable=False)
    applies_to_department = Column(String, nullable=True)
    paid_or_unpaid = Column(String, default="paid", nullable=False)
    paid_percentage = Column(Numeric(5, 2), default=100)
    requires_balance = Column(Boolean, default=True, nullable=False)
    requires_document = Column(Boolean, default=False, nullable=False)
    requires_manager_approval = Column(Boolean, default=True, nullable=False)
    requires_hr_review = Column(Boolean, default=False, nullable=False)
    allows_half_day = Column(Boolean, default=True, nullable=False)
    allows_backdating = Column(Boolean, default=False, nullable=False)
    allows_future_dating = Column(Boolean, default=True, nullable=False)
    excludes_weekends = Column(Boolean, default=True, nullable=False)
    excludes_public_holidays = Column(Boolean, default=True, nullable=False)
    minimum_notice_days = Column(Integer, default=0, nullable=False)
    maximum_consecutive_days = Column(Numeric(8, 2), nullable=True)
    maximum_days_per_cycle = Column(Numeric(8, 2), nullable=True)
    applicable_employment_types = Column(JSON, nullable=True)
    applicable_departments = Column(JSON, nullable=True)
    applicable_branches = Column(JSON, nullable=True)
    applicable_countries = Column(JSON, nullable=True)
    applicable_gender_rules = Column(JSON, nullable=True)
    applicable_confirmation_status = Column(JSON, nullable=True)
    payroll_impact_enabled = Column(Boolean, default=True, nullable=False)
    attendance_exclusion_enabled = Column(Boolean, default=True, nullable=False)
    document_type_required = Column(String, nullable=True)
    encashment_allowed = Column(Boolean, default=False, nullable=False)
    max_encashable_days = Column(Numeric(8, 2), default=0)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMLeaveBlackoutDate(Base):
    __tablename__ = "hrm_leave_blackout_dates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    blackout_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    applies_to_department = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMShift(Base):
    __tablename__ = "hrm_shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    shift_code = Column(String, unique=True, nullable=False, index=True)
    shift_name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    grace_minutes = Column(Integer, default=0)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMTimesheet(Base):
    __tablename__ = "hrm_timesheets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    regular_hours = Column(Numeric(8, 2), default=0)
    overtime_hours = Column(Numeric(8, 2), default=0)
    status = Column(String, default="draft", nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMOvertimeRequest(Base):
    __tablename__ = "hrm_overtime_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    overtime_date = Column(Date, nullable=False)
    hours = Column(Numeric(8, 2), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    approval_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMHoliday(Base):
    __tablename__ = "hrm_holidays"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    holiday_name = Column(String, nullable=False)
    holiday_date = Column(Date, nullable=False)
    country = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMAttendancePeriod(Base):
    __tablename__ = "hrm_attendance_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    period_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="open", nullable=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMSalaryStructure(Base):
    __tablename__ = "hrm_salary_structures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    structure_name = Column(String, nullable=False)
    base_salary = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="KES")
    pay_frequency = Column(String, default="monthly")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    status = Column(String, default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPayrollPeriod(Base):
    __tablename__ = "hrm_payroll_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    period_code = Column(String, unique=True, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="open", nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPayrollRun(Base):
    __tablename__ = "hrm_payroll_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    payroll_period_id = Column(UUID(as_uuid=True), ForeignKey("hrm_payroll_periods.id"), nullable=False)
    run_number = Column(String, nullable=False)
    total_gross = Column(Numeric(14, 2), default=0)
    total_net = Column(Numeric(14, 2), default=0)
    status = Column(String, default="draft", nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPayslip(Base):
    __tablename__ = "hrm_payslips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("hrm_payroll_runs.id"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    gross_pay = Column(Numeric(12, 2), default=0)
    net_pay = Column(Numeric(12, 2), default=0)
    status = Column(String, default="draft", nullable=False)
    payslip_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPayrollComponent(Base):
    __tablename__ = "hrm_payroll_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    component_code = Column(String, unique=True, nullable=False, index=True)
    component_name = Column(String, nullable=False)
    component_type = Column(String, nullable=False)
    taxable = Column(Boolean, default=False, nullable=False)
    calculation_rule = Column(JSON, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPayrollAdjustment(Base):
    __tablename__ = "hrm_payroll_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    payroll_period_id = Column(UUID(as_uuid=True), ForeignKey("hrm_payroll_periods.id"), nullable=True)
    adjustment_type = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="draft", nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMJobRequisition(Base):
    __tablename__ = "hrm_job_requisitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    requisition_number = Column(String, unique=True, nullable=False, index=True)
    position_title = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    department = Column(String, nullable=False)
    branch = Column(String, nullable=True)
    business_unit = Column(String, nullable=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    hiring_manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    reporting_manager_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    openings = Column(Integer, default=1)
    vacancies = Column(Integer, default=1)
    employment_type = Column(String, nullable=True)
    contract_duration = Column(String, nullable=True)
    salary_band = Column(String, nullable=True)
    budget_code = Column(String, nullable=True)
    replacement_or_new_role = Column(String, nullable=True)
    reason_for_hire = Column(Text, nullable=True)
    required_start_date = Column(Date, nullable=True)
    job_description = Column(Text, nullable=True)
    required_skills = Column(JSON, nullable=True)
    required_certifications = Column(JSON, nullable=True)
    approval_status = Column(String, default="pending", nullable=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    status = Column(String, default="draft", nullable=False)
    justification = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMJobOpening(Base):
    __tablename__ = "hrm_job_openings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("hrm_job_requisitions.id"), nullable=True)
    opening_title = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    department = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    business_unit = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)
    salary_band = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    publishing_channels = Column(JSON, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    posting_date = Column(Date, nullable=True)
    closing_date = Column(Date, nullable=True)
    status = Column(String, default="open", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMCandidate(Base):
    __tablename__ = "hrm_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    candidate_name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    source = Column(String, nullable=True)
    current_stage = Column(String, default="new", nullable=False)
    status = Column(String, default="active", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMApplication(Base):
    __tablename__ = "hrm_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_opening_id = Column(UUID(as_uuid=True), ForeignKey("hrm_job_openings.id"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("hrm_candidates.id"), nullable=False)
    application_date = Column(Date, nullable=True)
    stage = Column(String, default="applied", nullable=False)
    status = Column(String, default="active", nullable=False)
    score = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMInterviewStage(Base):
    __tablename__ = "hrm_interview_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("hrm_applications.id"), nullable=False)
    stage_name = Column(String, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String, default="scheduled", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMInterviewFeedback(Base):
    __tablename__ = "hrm_interview_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    interview_stage_id = Column(UUID(as_uuid=True), ForeignKey("hrm_interview_stages.id"), nullable=True)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("hrm_interviews.id"), nullable=True, index=True)
    recruitment_id = Column(UUID(as_uuid=True), ForeignKey("hrm_recruitment.id"), nullable=True, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    panel_member_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    rating = Column(Numeric(5, 2), nullable=True)
    technical_score = Column(Numeric(6, 2), default=0)
    culture_score = Column(Numeric(6, 2), default=0)
    communication_score = Column(Numeric(6, 2), default=0)
    experience_score = Column(Numeric(6, 2), default=0)
    recommendation = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    submitted_by = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMOfferLetter(Base):
    __tablename__ = "hrm_offer_letters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("hrm_applications.id"), nullable=True)
    recruitment_id = Column(UUID(as_uuid=True), ForeignKey("hrm_recruitment.id"), nullable=True, index=True)
    offer_number = Column(String, unique=True, nullable=False, index=True)
    offer_reference = Column(String, nullable=True, unique=True)
    job_title = Column(String, nullable=True)
    department = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    salary_band = Column(String, nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=True)
    salary_offer = Column(Numeric(12, 2), nullable=True)
    currency = Column(String, default="KES")
    benefits_summary = Column(Text, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    probation_months = Column(Integer, nullable=True)
    offer_expiry_date = Column(Date, nullable=True)
    approval_status = Column(String, default="pending", nullable=False)
    offer_status = Column(String, default="draft", nullable=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, nullable=True)
    status = Column(String, default="draft", nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    document_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMGoal(Base):
    __tablename__ = "hrm_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    goal_title = Column(String, nullable=False)
    goal_period = Column(String, nullable=False)
    target_value = Column(Numeric(12, 2), nullable=True)
    achieved_value = Column(Numeric(12, 2), nullable=True)
    status = Column(String, default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMKPI(Base):
    __tablename__ = "hrm_kpis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    department = Column(String, nullable=True)
    kpi_name = Column(String, nullable=False)
    weight = Column(Numeric(5, 2), default=0)
    target = Column(Numeric(12, 2), nullable=True)
    actual = Column(Numeric(12, 2), nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMReviewCycle(Base):
    __tablename__ = "hrm_review_cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    cycle_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMCompetency(Base):
    __tablename__ = "hrm_competencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    competency_name = Column(String, nullable=False)
    competency_group = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMPerformanceImprovementPlan(Base):
    __tablename__ = "hrm_performance_improvement_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    improvement_area = Column(Text, nullable=False)
    status = Column(String, default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMCourse(Base):
    __tablename__ = "hrm_courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    course_code = Column(String, unique=True, nullable=False, index=True)
    course_title = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    mandatory = Column(Boolean, default=False, nullable=False)
    validity_months = Column(Integer, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMTrainingSession(Base):
    __tablename__ = "hrm_training_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("hrm_courses.id"), nullable=True)
    session_title = Column(String, nullable=False)
    facilitator = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String, default="planned", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMCertification(Base):
    __tablename__ = "hrm_certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    certification_name = Column(String, nullable=False)
    issuing_body = Column(String, nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    status = Column(String, default="active", nullable=False)
    document_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMMandatoryTrainingPolicy(Base):
    __tablename__ = "hrm_mandatory_training_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("hrm_courses.id"), nullable=False)
    applies_to_department = Column(String, nullable=True)
    applies_to_role = Column(String, nullable=True)
    renewal_frequency_months = Column(Integer, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMCompanyAsset(Base):
    __tablename__ = "hrm_company_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    asset_code = Column(String, unique=True, nullable=False, index=True)
    asset_name = Column(String, nullable=False)
    asset_category = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Numeric(12, 2), nullable=True)
    custodian_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String, default="available", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMClearanceChecklist(Base):
    __tablename__ = "hrm_clearance_checklists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    checklist_item = Column(String, nullable=False)
    owner_department = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMExitInterview(Base):
    __tablename__ = "hrm_exit_interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    interview_date = Column(Date, nullable=True)
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    reason_for_leaving = Column(Text, nullable=True)
    rehire_eligible = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMTerminationRecord(Base):
    __tablename__ = "hrm_termination_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    termination_type = Column(String, nullable=False)
    termination_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeSuspensionRecord(Base):
    __tablename__ = "hrm_employee_suspension_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    suspension_type = Column(String, default="administrative", nullable=False)
    start_date = Column(Date, nullable=False)
    expected_end_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    paid = Column(Boolean, default=True, nullable=False)
    iam_access_disabled = Column(Boolean, default=True, nullable=False)
    payroll_notified = Column(Boolean, default=True, nullable=False)
    approval_status = Column(String, default="approved", nullable=False)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeReinstatementRecord(Base):
    __tablename__ = "hrm_employee_reinstatement_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    reinstatement_date = Column(Date, nullable=False)
    previous_status = Column(String, nullable=True)
    reason = Column(Text, nullable=False)
    payroll_review_status = Column(String, default="queued", nullable=False)
    iam_reactivation_status = Column(String, default="queued", nullable=False)
    approval_status = Column(String, default="approved", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeLeaveOfAbsenceRecord(Base):
    __tablename__ = "hrm_employee_leave_of_absence_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    leave_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    expected_return_date = Column(Date, nullable=False)
    actual_return_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=False)
    payroll_impact = Column(String, default="review_required", nullable=False)
    iam_access_impact = Column(String, default="review_required", nullable=False)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeRetirementRecord(Base):
    __tablename__ = "hrm_employee_retirement_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    retirement_type = Column(String, nullable=False)
    retirement_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    approval_status = Column(String, default="approved", nullable=False)
    final_benefits_status = Column(String, default="queued", nullable=False)
    clearance_status = Column(String, default="queued", nullable=False)
    iam_deactivation_status = Column(String, default="queued", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeDeathRecord(Base):
    __tablename__ = "hrm_employee_death_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    date_of_death = Column(Date, nullable=False)
    supporting_document_url = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    payroll_final_processing_status = Column(String, default="queued", nullable=False)
    benefits_workflow_status = Column(String, default="queued", nullable=False)
    iam_deactivation_status = Column(String, default="queued", nullable=False)
    clearance_status = Column(String, default="sensitive_review", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeComplianceRecord(Base):
    __tablename__ = "hrm_employee_compliance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    compliance_score = Column(Numeric(5, 2), default=0, nullable=False)
    compliance_status = Column(String, default="Missing Mandatory Data", nullable=False, index=True)
    missing_items = Column(JSON, nullable=True)
    expired_items = Column(JSON, nullable=True)
    pending_verification_items = Column(JSON, nullable=True)
    payroll_readiness = Column(String, default="incomplete", nullable=False)
    activation_readiness = Column(String, default="incomplete", nullable=False)
    access_readiness = Column(String, default="incomplete", nullable=False)
    validated_by = Column(String, nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeStatutoryIdentifier(Base):
    __tablename__ = "hrm_employee_statutory_identifiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    identifier_type = Column(String, nullable=False, index=True)
    identifier_value = Column(String, nullable=False, index=True)
    country = Column(String, nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=True)
    verification_status = Column(String, default="Pending Verification", nullable=False, index=True)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeePassportRecord(Base):
    __tablename__ = "hrm_employee_passport_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    passport_number = Column(String, nullable=False, index=True)
    passport_country = Column(String, nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=True)
    verification_status = Column(String, default="Pending Verification", nullable=False)
    expiry_status = Column(String, default="valid", nullable=False, index=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeVisaRecord(Base):
    __tablename__ = "hrm_employee_visa_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    visa_type = Column(String, nullable=False)
    visa_number = Column(String, nullable=True, index=True)
    visa_country = Column(String, nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    visa_status = Column(String, default="valid", nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeWorkPermit(Base):
    __tablename__ = "hrm_employee_work_permits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    work_permit_number = Column(String, nullable=False, index=True)
    work_permit_type = Column(String, nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=True)
    expiry_status = Column(String, default="valid", nullable=False, index=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeContractTracking(Base):
    __tablename__ = "hrm_employee_contract_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    contract_start_date = Column(Date, nullable=False)
    contract_end_date = Column(Date, nullable=False, index=True)
    contract_status = Column(String, default="active", nullable=False, index=True)
    contract_document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=True)
    renewal_status = Column(String, default="not_started", nullable=False)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeCertificationTracking(Base):
    __tablename__ = "hrm_employee_certification_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    certification_name = Column(String, nullable=False)
    issuing_body = Column(String, nullable=True)
    certificate_number = Column(String, nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("hrm_documents.id"), nullable=True)
    eligibility_impact = Column(String, default="review_required")
    status = Column(String, default="active", nullable=False, index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeAccessRequest(Base):
    __tablename__ = "hrm_employee_access_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    request_type = Column(String, nullable=False, index=True)
    requested_systems = Column(JSON, nullable=True)
    requested_roles = Column(JSON, nullable=True)
    business_justification = Column(Text, nullable=True)
    requested_by = Column(String, nullable=True)
    approval_status = Column(String, default="pending", nullable=False, index=True)
    provisioning_status = Column(String, default="queued", nullable=False, index=True)
    access_expiry_date = Column(Date, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeSystemRole(Base):
    __tablename__ = "hrm_employee_system_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    system_name = Column(String, nullable=False, index=True)
    role_name = Column(String, nullable=False, index=True)
    access_level = Column(String, default="standard", nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    assigned_by = Column(String, nullable=True)
    approval_status = Column(String, default="approved", nullable=False, index=True)
    provisioning_status = Column(String, default="queued", nullable=False)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeAccessLog(Base):
    __tablename__ = "hrm_employee_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    system_name = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    performed_by = Column(String, nullable=True)
    result = Column(String, default="success", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeAccountStatus(Base):
    __tablename__ = "hrm_employee_account_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    account_status = Column(String, default="active", nullable=False, index=True)
    lock_reason = Column(Text, nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    last_reset_type = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeSalaryHistory(Base):
    __tablename__ = "hrm_employee_salary_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    previous_salary = Column(Numeric(12, 2), nullable=True)
    new_salary = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="KES", nullable=False)
    salary_band = Column(String, nullable=True)
    pay_frequency = Column(String, default="monthly", nullable=False)
    effective_date = Column(Date, nullable=False, index=True)
    change_type = Column(String, default="capture", nullable=False, index=True)
    reason = Column(Text, nullable=False)
    approval_status = Column(String, default="approved", nullable=False, index=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeAllowance(Base):
    __tablename__ = "hrm_employee_allowances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    allowance_type = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), default=0, nullable=False)
    currency = Column(String, default="KES", nullable=False)
    recurring = Column(Boolean, default=True, nullable=False)
    taxable = Column(Boolean, default=True, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeBenefitAssignment(Base):
    __tablename__ = "hrm_employee_benefits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    benefit_type = Column(String, nullable=False)
    benefit_name = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    dependant_ids = Column(JSON, nullable=True)
    approval_status = Column(String, default="approved", nullable=False)
    status = Column(String, default="active", nullable=False, index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeInsurancePlan(Base):
    __tablename__ = "hrm_employee_insurance_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    plan_name = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    policy_number = Column(String, nullable=True)
    coverage_start = Column(Date, nullable=False)
    coverage_end = Column(Date, nullable=True)
    dependant_ids = Column(JSON, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeReportExport(Base):
    __tablename__ = "hrm_employee_reports_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    report_type = Column(String, nullable=False, index=True)
    export_format = Column(String, default="csv", nullable=False)
    filters = Column(JSON, nullable=True)
    columns = Column(JSON, nullable=True)
    exported_by = Column(String, nullable=True)
    row_count = Column(Integer, default=0, nullable=False)
    status = Column(String, default="completed", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeOffboardingCase(Base):
    __tablename__ = "hrm_employee_offboarding_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    separation_type = Column(String, nullable=False, index=True)
    separation_reason = Column(Text, nullable=False)
    effective_date = Column(Date, nullable=False, index=True)
    notice_period_days = Column(Integer, default=0, nullable=False)
    workflow_status = Column(String, default="initiated", nullable=False, index=True)
    clearance_status = Column(String, default="pending", nullable=False)
    asset_recovery_status = Column(String, default="pending", nullable=False)
    access_revocation_status = Column(String, default="pending", nullable=False)
    final_settlement_status = Column(String, default="pending", nullable=False)
    exit_document_status = Column(String, default="pending", nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeAssetRecovery(Base):
    __tablename__ = "hrm_employee_asset_recovery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    offboarding_case_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_offboarding_cases.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    asset_name = Column(String, nullable=False)
    asset_status = Column(String, default="pending", nullable=False)
    settlement_impact = Column(Numeric(12, 2), default=0)
    notes = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMEmployeeExitDocument(Base):
    __tablename__ = "hrm_employee_exit_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    offboarding_case_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_offboarding_cases.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    document_type = Column(String, nullable=False)
    document_status = Column(String, default="generated", nullable=False)
    file_url = Column(String, nullable=True)
    generated_by = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HRMEmployeeFinalSettlement(Base):
    __tablename__ = "hrm_employee_final_settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    offboarding_case_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employee_offboarding_cases.id"), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    final_salary = Column(Numeric(12, 2), default=0)
    leave_payout = Column(Numeric(12, 2), default=0)
    deductions = Column(Numeric(12, 2), default=0)
    asset_deductions = Column(Numeric(12, 2), default=0)
    allowances = Column(Numeric(12, 2), default=0)
    benefits = Column(Numeric(12, 2), default=0)
    tax_deductions = Column(Numeric(12, 2), default=0)
    net_settlement = Column(Numeric(12, 2), default=0)
    payroll_approval_status = Column(String, default="pending", nullable=False)
    finance_approval_status = Column(String, default="pending", nullable=False)
    status = Column(String, default="draft", nullable=False, index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class HRMOffboardingApproval(Base):
    __tablename__ = "hrm_offboarding_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    approval_area = Column(String, nullable=False)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String, default="pending", nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
