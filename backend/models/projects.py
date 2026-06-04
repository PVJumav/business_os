import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID

from backend.core.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_code = Column(String(120), unique=True, nullable=True, index=True)
    project_name = Column(String(255), nullable=False, index=True)
    project_type = Column(String(120), default="internal", nullable=False, index=True)
    lifecycle_status = Column(String(80), default="draft", nullable=False, index=True)
    implementation_stage = Column(String(120), nullable=True, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True, index=True)
    sponsor_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    project_manager_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True, index=True)
    crm_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True, index=True)
    crm_quotation_id = Column(UUID(as_uuid=True), ForeignKey("crm.quotations.id"), nullable=True)
    crm_contract_id = Column(UUID(as_uuid=True), ForeignKey("crm.contracts.id"), nullable=True)
    sla_id = Column(UUID(as_uuid=True), nullable=True)
    start_date = Column(Date, nullable=True)
    target_end_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    approved_budget = Column(Numeric(14, 2), default=0)
    actual_cost = Column(Numeric(14, 2), default=0)
    invoiced_amount = Column(Numeric(14, 2), default=0)
    progress_percent = Column(Integer, default=0)
    budget_approval_status = Column(String(80), default="draft", nullable=False)
    team_assignment_status = Column(String(80), default="pending", nullable=False)
    signoff_status = Column(String(80), default="pending", nullable=False)
    locked = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class ProjectPhase(Base):
    __tablename__ = "phases"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    phase_name = Column(String(255), nullable=False)
    sequence = Column(Integer, default=1)
    status = Column(String(80), default="not_started", nullable=False, index=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectMilestone(Base):
    __tablename__ = "milestones"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    phase_id = Column(UUID(as_uuid=True), ForeignKey("projects.phases.id"), nullable=True, index=True)
    milestone_name = Column(String(255), nullable=False)
    required_for_close = Column(Boolean, default=True, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(80), default="open", nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectTask(Base):
    __tablename__ = "tasks"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    phase_id = Column(UUID(as_uuid=True), ForeignKey("projects.phases.id"), nullable=True)
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("projects.milestones.id"), nullable=True)
    task_title = Column(String(255), nullable=False)
    assigned_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    priority = Column(String(50), default="medium", nullable=False, index=True)
    status = Column(String(80), default="open", nullable=False, index=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_hours = Column(Numeric(10, 2), default=0)
    actual_hours = Column(Numeric(10, 2), default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class ProjectSubtask(Base):
    __tablename__ = "subtasks"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("projects.tasks.id"), nullable=False, index=True)
    subtask_title = Column(String(255), nullable=False)
    assigned_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String(80), default="open", nullable=False)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectTeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    project_role = Column(String(120), default="member", nullable=False)
    allocation_percent = Column(Integer, default=100)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectRole(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(160), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_permissions = Column(JSON, nullable=True)
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectDocument(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    document_title = Column(String(255), nullable=False)
    document_type = Column(String(120), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=True)
    uploaded_by = Column(String(255), nullable=True)
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectCharter(Base):
    __tablename__ = "charters"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    charter_title = Column(String(255), nullable=False)
    business_case = Column(Text, nullable=True)
    objectives = Column(Text, nullable=True)
    success_criteria = Column(Text, nullable=True)
    sponsor_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    approval_status = Column(String(80), default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectScope(Base):
    __tablename__ = "scopes"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    scope_summary = Column(Text, nullable=False)
    in_scope = Column(Text, nullable=True)
    out_of_scope = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    status = Column(String(80), default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectDeliverable(Base):
    __tablename__ = "deliverables"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    deliverable_name = Column(String(255), nullable=False)
    acceptance_criteria = Column(Text, nullable=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    acceptance_status = Column(String(80), default="pending", nullable=False)
    status = Column(String(80), default="open", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectWBSItem(Base):
    __tablename__ = "wbs_items"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    parent_item_id = Column(UUID(as_uuid=True), ForeignKey("projects.wbs_items.id"), nullable=True)
    wbs_code = Column(String(120), nullable=True, index=True)
    work_package = Column(String(255), nullable=False)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    estimated_hours = Column(Numeric(10, 2), default=0)
    status = Column(String(80), default="open", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectBudget(Base):
    __tablename__ = "budgets"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    budget_name = Column(String(255), nullable=False)
    budget_type = Column(String(120), default="project", nullable=False)
    approved_amount = Column(Numeric(14, 2), default=0)
    actual_amount = Column(Numeric(14, 2), default=0)
    variance_amount = Column(Numeric(14, 2), default=0)
    approval_status = Column(String(80), default="draft", nullable=False, index=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectExpense(Base):
    __tablename__ = "expenses"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("projects.budgets.id"), nullable=True)
    expense_date = Column(Date, nullable=True)
    expense_category = Column(String(120), nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    incurred_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    approval_status = Column(String(80), default="draft", nullable=False, index=True)
    finance_expense_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectRisk(Base):
    __tablename__ = "risks"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    risk_title = Column(String(255), nullable=False)
    severity = Column(String(80), default="medium", nullable=False)
    probability = Column(String(80), default="medium", nullable=False)
    mitigation_plan = Column(Text, nullable=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String(80), default="open", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectIssue(Base):
    __tablename__ = "issues"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    issue_title = Column(String(255), nullable=False)
    priority = Column(String(80), default="medium", nullable=False)
    assigned_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(80), default="open", nullable=False, index=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectDependency(Base):
    __tablename__ = "dependencies"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    predecessor_task_id = Column(UUID(as_uuid=True), ForeignKey("projects.tasks.id"), nullable=False)
    successor_task_id = Column(UUID(as_uuid=True), ForeignKey("projects.tasks.id"), nullable=False)
    dependency_type = Column(String(80), default="finish_to_start", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectStatusUpdate(Base):
    __tablename__ = "status_updates"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    status_date = Column(Date, nullable=True)
    progress_percent = Column(Integer, default=0)
    summary = Column(Text, nullable=False)
    blockers = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectTimesheet(Base):
    __tablename__ = "timesheets"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("projects.tasks.id"), nullable=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False, index=True)
    work_date = Column(Date, nullable=False)
    billable_hours = Column(Numeric(10, 2), default=0)
    non_billable_hours = Column(Numeric(10, 2), default=0)
    available_hours = Column(Numeric(10, 2), default=8)
    approval_status = Column(String(80), default="submitted", nullable=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectResourceForecast(Base):
    __tablename__ = "resource_forecasts"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    role_name = Column(String(160), nullable=True)
    forecast_period = Column(Date, nullable=False)
    forecast_hours = Column(Numeric(10, 2), default=0)
    forecast_cost = Column(Numeric(14, 2), default=0)
    status = Column(String(80), default="planned", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectLessonLearned(Base):
    __tablename__ = "lessons_learned"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    lesson_title = Column(String(255), nullable=False)
    category = Column(String(120), nullable=True)
    lesson_detail = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectApproval(Base):
    __tablename__ = "approvals"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    approval_type = Column(String(120), nullable=False)
    requested_by = Column(String(255), nullable=True)
    approver = Column(String(255), nullable=True)
    status = Column(String(80), default="pending", nullable=False, index=True)
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectSignoff(Base):
    __tablename__ = "signoffs"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    signoff_type = Column(String(120), default="customer_acceptance", nullable=False)
    signed_by = Column(String(255), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("projects.approvals.id"), nullable=True)
    status = Column(String(80), default="pending", nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLA(Base):
    __tablename__ = "slas"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_number = Column(String(120), unique=True, nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("crm.contracts.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=True)
    sla_name = Column(String(255), nullable=False)
    tier = Column(String(80), default="standard", nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    response_hours = Column(Integer, default=8)
    resolution_hours = Column(Integer, default=48)
    status = Column(String(80), default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLATier(Base):
    __tablename__ = "sla_tiers"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier_name = Column(String(120), unique=True, nullable=False)
    priority = Column(String(80), default="medium", nullable=False)
    response_hours = Column(Integer, default=8)
    resolution_hours = Column(Integer, default=48)
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLATarget(Base):
    __tablename__ = "sla_targets"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=False, index=True)
    target_name = Column(String(160), nullable=False)
    target_type = Column(String(120), nullable=False)
    target_hours = Column(Numeric(10, 2), default=0)
    target_percent = Column(Numeric(5, 2), default=0)
    priority = Column(String(80), default="medium")
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLAServiceHour(Base):
    __tablename__ = "sla_service_hours"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=False, index=True)
    day_of_week = Column(String(20), nullable=False)
    start_time = Column(String(20), nullable=False)
    end_time = Column(String(20), nullable=False)
    timezone = Column(String(80), default="Africa/Nairobi")
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLASupportCoverage(Base):
    __tablename__ = "sla_support_coverage"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=False, index=True)
    coverage_name = Column(String(160), nullable=False)
    support_channel = Column(String(120), nullable=True)
    support_team = Column(String(160), nullable=True)
    primary_owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLAHealthCheck(Base):
    __tablename__ = "sla_health_checks"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=False, index=True)
    check_date = Column(Date, nullable=True)
    uptime_percent = Column(Numeric(5, 2), default=100)
    ticket_count = Column(Integer, default=0)
    breached_ticket_count = Column(Integer, default=0)
    health_status = Column(String(80), default="healthy", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLATicket(Base):
    __tablename__ = "sla_tickets"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(120), unique=True, nullable=True, index=True)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("crm.contacts.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=True)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("projects.issues.id"), nullable=True)
    subject = Column(String(255), nullable=False)
    priority = Column(String(80), default="medium", nullable=False, index=True)
    assigned_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    first_response_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    response_due_at = Column(DateTime(timezone=True), nullable=True)
    resolution_due_at = Column(DateTime(timezone=True), nullable=True)
    sla_status = Column(String(80), default="within_sla", nullable=False, index=True)
    status = Column(String(80), default="open", nullable=False, index=True)
    escalation_level = Column(Integer, default=0)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLAEscalation(Base):
    __tablename__ = "sla_escalations"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_ticket_id = Column(UUID(as_uuid=True), ForeignKey("projects.sla_tickets.id"), nullable=False, index=True)
    escalation_level = Column(Integer, default=1)
    escalated_to_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(80), default="open", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLAExceptionApproval(Base):
    __tablename__ = "sla_exception_approvals"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_ticket_id = Column(UUID(as_uuid=True), ForeignKey("projects.sla_tickets.id"), nullable=True, index=True)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=True)
    exception_reason = Column(Text, nullable=False)
    requested_by = Column(String(255), nullable=True)
    approval_status = Column(String(80), default="pending", nullable=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SLARenewal(Base):
    __tablename__ = "sla_renewals"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=False, index=True)
    renewal_date = Column(Date, nullable=False)
    renewal_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)
    forecast_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(80), default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LicenseTracking(Base):
    __tablename__ = "licenses"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_number = Column(String(120), unique=True, nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("crm.opportunities.id"), nullable=True)
    product_service_id = Column(UUID(as_uuid=True), ForeignKey("crm.product_services.id"), nullable=True)
    vendor_name = Column(String(255), nullable=True)
    customer_license = Column(Boolean, default=True, nullable=False)
    purchased_licenses = Column(Integer, default=0)
    used_licenses = Column(Integer, default=0)
    consumption_percent = Column(Numeric(5, 2), default=0)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    finance_cost_amount = Column(Numeric(14, 2), default=0)
    finance_revenue_amount = Column(Numeric(14, 2), default=0)
    license_name = Column(String(255), nullable=False)
    distributor = Column(String(255), nullable=True)
    oem_contact_name = Column(String(255), nullable=True)
    activation_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    renewal_date = Column(Date, nullable=True, index=True)
    renewal_owner = Column(String(255), nullable=True)
    notification_status = Column(String(80), default="pending", nullable=False)
    status = Column(String(80), default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LicenseAllocation(Base):
    __tablename__ = "license_allocations"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("projects.licenses.id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    allocated_quantity = Column(Integer, default=1)
    allocation_status = Column(String(80), default="allocated", nullable=False)
    allocated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LicenseSubscription(Base):
    __tablename__ = "license_subscriptions"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("projects.licenses.id"), nullable=False, index=True)
    subscription_name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    billing_frequency = Column(String(80), default="annual")
    renewal_forecast_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LicenseComplianceCheck(Base):
    __tablename__ = "license_compliance_checks"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("projects.licenses.id"), nullable=False, index=True)
    check_date = Column(Date, nullable=True)
    purchased_licenses = Column(Integer, default=0)
    used_licenses = Column(Integer, default=0)
    compliance_status = Column(String(80), default="compliant", nullable=False)
    findings = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BusinessInvoiceTemplate(Base):
    __tablename__ = "invoice_templates"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(255), nullable=False)
    invoice_type = Column(String(120), default="tax_invoice", nullable=False)
    terms = Column(Text, nullable=True)
    footer_notes = Column(Text, nullable=True)
    status = Column(String(80), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BusinessInvoiceLifecycle(Base):
    __tablename__ = "invoice_lifecycle"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(120), unique=True, nullable=True, index=True)
    source_module = Column(String(120), nullable=True, index=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=True)
    license_id = Column(UUID(as_uuid=True), ForeignKey("projects.licenses.id"), nullable=True)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("projects.slas.id"), nullable=True)
    finance_invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=True)
    invoice_type = Column(String(120), default="tax_invoice", nullable=False)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    amount = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    approval_status = Column(String(80), default="draft", nullable=False)
    dispatch_status = Column(String(80), default="not_sent", nullable=False)
    acceptance_status = Column(String(80), default="pending", nullable=False)
    status = Column(String(80), default="draft", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BusinessInvoiceSchedule(Base):
    __tablename__ = "invoice_schedules"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("projects.invoice_lifecycle.id"), nullable=False, index=True)
    schedule_type = Column(String(120), nullable=False)
    schedule_date = Column(Date, nullable=False)
    recognized_revenue = Column(Numeric(14, 2), default=0)
    deferred_revenue = Column(Numeric(14, 2), default=0)
    status = Column(String(80), default="scheduled", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class VendorEngagement(Base):
    __tablename__ = "vendor_engagements"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_name = Column(String(255), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    engagement_type = Column(String(120), nullable=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(80), default="active", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MarketingInitiative(Base):
    __tablename__ = "marketing_initiatives"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    initiative_name = Column(String(255), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("crm.campaigns.id"), nullable=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    budget_amount = Column(Numeric(14, 2), default=0)
    actual_cost = Column(Numeric(14, 2), default=0)
    expected_roi = Column(Numeric(14, 2), default=0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(80), default="draft", nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectChangeRequest(Base):
    __tablename__ = "change_requests"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.projects.id"), nullable=False, index=True)
    change_type = Column(String(120), nullable=False)
    reason = Column(Text, nullable=False)
    requested_by = Column(String(255), nullable=True)
    approval_status = Column(String(80), default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectAuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "projects"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(120), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
