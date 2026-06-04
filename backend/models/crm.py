import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Date,
    Numeric,
    Integer,
    Boolean,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.core.database import Base


class CRMAccount(Base):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(150), nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    relationship_owner = Column(String(255), nullable=True)
    account_manager = Column(String(255), nullable=True)
    country = Column(String(150), nullable=True)
    region = Column(String(150), nullable=True)
    vertical = Column(String(150), nullable=True)
    account_type = Column(String(100), nullable=True)
    account_status = Column(String(50), default="active")
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    manager_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    created_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contacts = relationship("CRMContact", back_populates="account")
    opportunities = relationship("CRMOpportunity", back_populates="account")


class CRMContact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)

    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    job_title = Column(String(150), nullable=True)
    department = Column(String(150), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)
    contact_role = Column(String(150), nullable=True)
    is_primary = Column(Boolean, default=False)
    communication_preferences = Column(JSON, nullable=True)
    unlinked_prospect = Column(Boolean, default=False)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    created_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("CRMAccount", back_populates="contacts")


class CRMLead(Base):
    __tablename__ = "leads"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)

    company_name = Column(String(255), nullable=True)
    account_industry = Column(String(150), nullable=True)
    account_website = Column(String(255), nullable=True)
    account_address = Column(Text, nullable=True)
    account_country = Column(String(150), nullable=True)
    account_region = Column(String(150), nullable=True)
    account_vertical = Column(String(150), nullable=True)
    account_type = Column(String(100), nullable=True)
    contact_name = Column(String(255), nullable=False)
    contact_job_title = Column(String(150), nullable=True)
    contact_department = Column(String(150), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    lead_source = Column(String(100), nullable=True)
    lead_score = Column(Integer, default=0)
    qualification_status = Column(String(80), default="unqualified")
    status = Column(String(50), default="New")
    assigned_to = Column(String(255), nullable=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    assigned_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    manager_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    created_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    duplicate_flag = Column(Boolean, default=False)
    duplicate_reason = Column(Text, nullable=True)
    disqualification_reason = Column(Text, nullable=True)

    estimated_value = Column(Numeric(14, 2), default=0)
    expected_close_date = Column(Date, nullable=True)
    expected_activation_date = Column(Date, nullable=True)
    expected_renewal_date = Column(Date, nullable=True)
    pipeline_type = Column(String(100), nullable=True)
    arena = Column(String(100), nullable=True)
    service_scope = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    converted = Column(Boolean, default=False)
    converted_account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    converted_contact_id = Column(UUID(as_uuid=True), ForeignKey("crm.contacts.id"), nullable=True)
    converted_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMOpportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    stage = Column(String(100), default="Discovery")

    opportunity_value = Column(Numeric(14, 2), default=0)
    probability = Column(Integer, default=0)
    expected_close_date = Column(Date, nullable=True)
    actual_close_date = Column(Date, nullable=True)
    win_loss_reason = Column(Text, nullable=True)
    competitors = Column(Text, nullable=True)
    product_service_ids = Column(JSON, nullable=True)
    renewal_date = Column(Date, nullable=True)
    licence_expiry_date = Column(Date, nullable=True)

    owner = Column(String(255), nullable=True)
    country = Column(String(150), nullable=True)
    vertical = Column(String(150), nullable=True)
    pipeline_type = Column(String(100), nullable=True)
    arena = Column(String(100), nullable=True)
    service_scope = Column(String(100), nullable=True)
    distributor_cost = Column(Numeric(14, 2), default=0)
    vendor_cost = Column(Numeric(14, 2), default=0)
    internal_cost = Column(Numeric(14, 2), default=0)
    gross_profit = Column(Numeric(14, 2), default=0)
    approval_status = Column(String(50), default="not_required")
    status = Column(String(50), default="open")
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    presales_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    project_manager_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    manager_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    created_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    lpo_document_url = Column(String(500), nullable=True)
    handover_status = Column(String(80), default="not_started")
    customer_success_owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    technical_owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("CRMAccount", back_populates="opportunities")
    quotations = relationship("CRMQuotation", back_populates="opportunity")


class CRMDeal(Base):
    __tablename__ = "deals"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)

    deal_name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=True)
    stage = Column(String(150), default="Stage 1.a Discovery")
    deal_status = Column(String(50), default="open")
    pipeline_type = Column(String(100), nullable=True)
    arena = Column(String(100), nullable=True)
    service_scope = Column(String(100), nullable=True)
    country = Column(String(150), nullable=True)
    vertical = Column(String(150), nullable=True)

    revenue_amount = Column(Numeric(14, 2), default=0)
    distributor_cost = Column(Numeric(14, 2), default=0)
    vendor_cost = Column(Numeric(14, 2), default=0)
    internal_cost = Column(Numeric(14, 2), default=0)
    gross_profit = Column(Numeric(14, 2), default=0)

    expected_close_date = Column(Date, nullable=True)
    renewal_date = Column(Date, nullable=True)
    licence_expiry_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMCustomerEngagement(Base):
    __tablename__ = "customer_engagements"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=False)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)

    account_manager = Column(String(255), nullable=True)
    engagement_type = Column(String(100), nullable=False)
    quarter = Column(String(20), nullable=True)
    engagement_date = Column(Date, nullable=False)
    workshop_done = Column(Boolean, default=False)
    outcome = Column(Text, nullable=True)
    next_action = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CRMAccountIssue(Base):
    __tablename__ = "account_issues"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=False)

    issue_title = Column(String(255), nullable=False)
    issue_type = Column(String(100), nullable=True)
    severity = Column(String(50), default="medium")
    status = Column(String(50), default="open")
    reported_by = Column(String(255), nullable=True)
    owner = Column(String(255), nullable=True)
    feedback = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMSalesTarget(Base):
    __tablename__ = "sales_targets"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    owner_type = Column(String(50), nullable=False)
    target_owner = Column(String(255), nullable=False)
    fiscal_year = Column(String(20), nullable=False)
    period_type = Column(String(50), nullable=False)
    period_label = Column(String(50), nullable=False)
    arena = Column(String(100), nullable=True)
    country = Column(String(150), nullable=True)
    vertical = Column(String(150), nullable=True)

    target_gp = Column(Numeric(14, 2), default=0)
    achieved_gp = Column(Numeric(14, 2), default=0)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMInvoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm.deals.id"), nullable=True)

    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    amount = Column(Numeric(14, 2), default=0)
    paid_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="draft")
    debt_owner = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMDepartmentWorkflow(Base):
    __tablename__ = "department_workflows"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    department = Column(String(100), nullable=False)
    head_role = Column(String(100), nullable=True)
    responsibility = Column(Text, nullable=False)
    related_record_type = Column(String(100), nullable=True)
    related_record_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default="pending")
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMTender(Base):
    __tablename__ = "tenders"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    tender_number = Column(String(150), nullable=True)
    tender_title = Column(String(255), nullable=False)
    platform = Column(String(255), nullable=True)
    sector = Column(String(100), nullable=True)
    customer_name = Column(String(255), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)

    bid_manager = Column(String(255), nullable=True)
    account_manager = Column(String(255), nullable=True)
    technical_lead = Column(String(255), nullable=True)
    stage = Column(String(100), default="prequalification")
    qualification_status = Column(String(50), default="qualifying")
    response_status = Column(String(50), default="not_started")
    outcome = Column(String(50), default="pending")
    service_scope = Column(String(100), nullable=True)
    document_completion = Column(Integer, default=0)
    close_date = Column(Date, nullable=True)
    submission_date = Column(Date, nullable=True)
    estimated_value = Column(Numeric(14, 2), default=0)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMTenderRepositoryDocument(Base):
    __tablename__ = "tender_repository_documents"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_title = Column(String(255), nullable=False)
    document_category = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=True)
    owner_department = Column(String(100), default="Bids")
    expiry_date = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMPMOProject(Base):
    __tablename__ = "pmo_projects"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    project_name = Column(String(255), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm.deals.id"), nullable=True)
    project_manager = Column(String(255), nullable=True)
    account_manager = Column(String(255), nullable=True)
    technical_lead = Column(String(255), nullable=True)
    pit_team = Column(Text, nullable=True)
    stage = Column(String(100), default="planning")
    status = Column(String(50), default="active")
    start_date = Column(Date, nullable=True)
    target_end_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    scoping_document_url = Column(String(500), nullable=True)
    deliverables = Column(Text, nullable=True)
    stakeholder_notes = Column(Text, nullable=True)
    vendor_notes = Column(Text, nullable=True)
    legal_status = Column(String(100), nullable=True)
    documentation_source = Column(String(100), default="Bids")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMSLAAssignment(Base):
    __tablename__ = "sla_assignments"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("crm.pmo_projects.id"), nullable=True)
    solution = Column(String(255), nullable=False)
    assigned_engineer = Column(String(255), nullable=False)
    technical_lead = Column(String(255), nullable=True)
    sla_type = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    service_hours = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMTechnicalService(Base):
    __tablename__ = "technical_services"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arena = Column(String(100), nullable=False)
    cluster = Column(String(150), nullable=True)
    service_name = Column(String(255), nullable=False)
    service_lead = Column(String(255), nullable=True)
    account_manager = Column(String(255), nullable=True)
    delivery_team = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMTicket(Base):
    __tablename__ = "customer_tickets"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("crm.pmo_projects.id"), nullable=True)
    ticket_number = Column(String(150), nullable=True)
    solution = Column(String(255), nullable=True)
    issue_title = Column(String(255), nullable=False)
    severity = Column(String(50), default="medium")
    status = Column(String(50), default="open")
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm.contacts.id"), nullable=True)
    category = Column(String(100), nullable=True)
    sla_status = Column(String(50), default="on_track")
    response_due_at = Column(DateTime(timezone=True), nullable=True)
    resolution_due_at = Column(DateTime(timezone=True), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    assigned_engineer = Column(String(255), nullable=True)
    technical_lead = Column(String(255), nullable=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMActivity(Base):
    __tablename__ = "activities"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    related_type = Column(String(50), nullable=False)  # lead, account, contact, opportunity
    related_id = Column(UUID(as_uuid=True), nullable=True)

    activity_type = Column(String(100), nullable=False)  # call, email, meeting, note
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    account_name = Column(String(255), nullable=True)

    created_by = Column(String(255), nullable=True)
    activity_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CRMAutomationRule(Base):
    __tablename__ = "automation_rules"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    trigger = Column(String(255), nullable=False)
    action = Column(Text, nullable=False)
    status = Column(String(50), default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMTask(Base):
    __tablename__ = "tasks"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    related_type = Column(String(50), nullable=True)
    related_id = Column(UUID(as_uuid=True), nullable=True)

    assigned_to = Column(String(255), nullable=True)
    assigned_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="pending")

    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CRMQuotation(Base):
    __tablename__ = "quotations"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm.deals.id"), nullable=True)

    quote_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)

    subtotal = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)

    status = Column(String(50), default="draft")  # draft, sent, approved, rejected
    approval_status = Column(String(50), default="draft")
    approval_required = Column(Boolean, default=False)
    version_number = Column(Integer, default=1)
    valid_until = Column(Date, nullable=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    approved_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)

    created_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("CRMOpportunity", back_populates="quotations")
    items = relationship("CRMQuotationItem", back_populates="quotation")


class CRMQuotationItem(Base):
    __tablename__ = "quotation_items"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("crm.quotations.id"), nullable=False)

    item_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(14, 2), default=0)
    total_price = Column(Numeric(14, 2), default=0)

    quotation = relationship("CRMQuotation", back_populates="items")


class CRMProductService(Base):
    __tablename__ = "product_services"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_code = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    product_type = Column(String(80), default="service")
    sku = Column(String(120), nullable=True)
    category = Column(String(150), nullable=True)
    unit_price = Column(Numeric(14, 2), default=0)
    currency = Column(String(20), default="KES")
    recurring = Column(Boolean, default=False)
    license_term_months = Column(Integer, nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMPriceBook(Base):
    __tablename__ = "price_books"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    price_book_name = Column(String(255), nullable=False)
    currency = Column(String(20), default="KES")
    region = Column(String(150), nullable=True)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMQuoteLineItem(Base):
    __tablename__ = "quote_line_items"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("crm.quotations.id"), nullable=False, index=True)
    product_service_id = Column(UUID(as_uuid=True), ForeignKey("crm.product_services.id"), nullable=False)
    line_description = Column(Text, nullable=True)
    quantity = Column(Numeric(12, 2), default=1)
    unit_price = Column(Numeric(14, 2), default=0)
    discount_percent = Column(Numeric(8, 2), default=0)
    tax_percent = Column(Numeric(8, 2), default=0)
    line_total = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMCustomerLPO(Base):
    __tablename__ = "customer_lpos"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lpo_number = Column(String(120), unique=True, nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=False, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True, index=True)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("crm.quotations.id"), nullable=True, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("crm.contracts.id"), nullable=True)
    lpo_date = Column(Date, nullable=False)
    currency = Column(String(20), default="KES")
    subtotal = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    variance_amount = Column(Numeric(14, 2), default=0)
    variance_reason = Column(Text, nullable=True)
    validation_status = Column(String(80), default="pending")
    approval_status = Column(String(80), default="not_required")
    document_url = Column(String(500), nullable=True)
    uploaded_by = Column(String(255), nullable=True)
    status = Column(String(80), default="received", index=True)
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMContract(Base):
    __tablename__ = "contracts"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    contract_number = Column(String(120), unique=True, nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=False)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("crm.deals.id"), nullable=True)
    contract_title = Column(String(255), nullable=False)
    contract_type = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    renewal_date = Column(Date, nullable=True)
    contract_value = Column(Numeric(14, 2), default=0)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("crm.sla_assignments.id"), nullable=True)
    document_url = Column(String(500), nullable=True)
    renewal_reminder_days = Column(Integer, default=30)
    status = Column(String(50), default="draft")
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMCampaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(100), nullable=True)
    owner = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    budget_amount = Column(Numeric(14, 2), default=0)
    actual_cost = Column(Numeric(14, 2), default=0)
    expected_revenue = Column(Numeric(14, 2), default=0)
    generated_leads = Column(Integer, default=0)
    campaign_roi = Column(Numeric(10, 2), default=0)
    status = Column(String(50), default="draft")
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMCampaignResponse(Base):
    __tablename__ = "campaign_responses"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm.campaigns.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm.contacts.id"), nullable=True)
    response_type = Column(String(100), nullable=False)
    response_date = Column(DateTime(timezone=True), server_default=func.now())
    lead_created = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="logged")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CRMApprovalRule(Base):
    __tablename__ = "approval_rules"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rule_name = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)
    threshold_amount = Column(Numeric(14, 2), default=0)
    discount_threshold_percent = Column(Numeric(8, 2), default=0)
    approver_role = Column(String(100), nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CRMPipelineStageRule(Base):
    __tablename__ = "pipeline_stage_rules"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    pipeline_name = Column(String(150), default="default")
    stage_name = Column(String(150), nullable=False)
    stage_order = Column(Integer, nullable=False)
    probability = Column(Integer, default=0)
    is_closed_stage = Column(Boolean, default=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CRMRecordShare(Base):
    __tablename__ = "record_shares"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    shared_with = Column(String(255), nullable=False)
    access_level = Column(String(50), default="read")
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CRMAuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
