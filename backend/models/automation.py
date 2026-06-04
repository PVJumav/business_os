import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID

from backend.core.database import Base


class AutomationMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    status = Column(String(80), default="active", index=True)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class PolicyCategory(Base, AutomationMixin):
    __tablename__ = "policy_categories"
    __table_args__ = {"schema": "automation"}

    category_name = Column(String(180), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_department = Column(String(120), nullable=True)


class GovernancePolicy(Base, AutomationMixin):
    __tablename__ = "governance_policies"
    __table_args__ = {"schema": "automation"}

    policy_code = Column(String(80), unique=True, nullable=True, index=True)
    policy_name = Column(String(255), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("automation.policy_categories.id"), nullable=True)
    category = Column(String(180), nullable=True, index=True)
    owner_department = Column(String(120), nullable=False, index=True)
    policy_owner = Column(String(255), nullable=True)
    approval_status = Column(String(80), default="draft", index=True)
    compliance_status = Column(String(80), default="not_assessed", index=True)
    version = Column(String(40), default="1.0")
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True, index=True)
    document_url = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)


class PolicyVersion(Base, AutomationMixin):
    __tablename__ = "policy_versions"
    __table_args__ = {"schema": "automation"}

    policy_id = Column(UUID(as_uuid=True), ForeignKey("automation.governance_policies.id"), nullable=False, index=True)
    version = Column(String(40), nullable=False)
    change_summary = Column(Text, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)


class PolicyException(Base, AutomationMixin):
    __tablename__ = "policy_exceptions"
    __table_args__ = {"schema": "automation"}

    policy_id = Column(UUID(as_uuid=True), ForeignKey("automation.governance_policies.id"), nullable=True, index=True)
    exception_title = Column(String(255), nullable=False)
    department = Column(String(120), nullable=True, index=True)
    risk_level = Column(String(80), default="medium", index=True)
    business_justification = Column(Text, nullable=False)
    approval_status = Column(String(80), default="pending", index=True)
    expiry_date = Column(Date, nullable=True)


class PolicyAcknowledgement(Base, AutomationMixin):
    __tablename__ = "policy_acknowledgements"
    __table_args__ = {"schema": "automation"}

    policy_id = Column(UUID(as_uuid=True), ForeignKey("automation.governance_policies.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledgement_status = Column(String(80), default="pending", index=True)


class SOP(Base, AutomationMixin):
    __tablename__ = "sops"
    __table_args__ = {"schema": "automation"}

    sop_code = Column(String(80), unique=True, nullable=True, index=True)
    sop_name = Column(String(255), nullable=False, index=True)
    department = Column(String(120), nullable=False, index=True)
    owner = Column(String(255), nullable=True)
    related_policy_id = Column(UUID(as_uuid=True), ForeignKey("automation.governance_policies.id"), nullable=True)
    related_workflow_template_id = Column(UUID(as_uuid=True), nullable=True)
    sla_hours = Column(Integer, nullable=True)
    version = Column(String(40), default="1.0")
    review_date = Column(Date, nullable=True, index=True)
    required_evidence = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)


class SOPStep(Base, AutomationMixin):
    __tablename__ = "sop_steps"
    __table_args__ = {"schema": "automation"}

    sop_id = Column(UUID(as_uuid=True), ForeignKey("automation.sops.id"), nullable=False, index=True)
    step_order = Column(Integer, default=1)
    step_name = Column(String(255), nullable=False)
    responsible_role = Column(String(180), nullable=True)
    required_approval = Column(Boolean, default=False)
    required_evidence = Column(Text, nullable=True)
    sla_hours = Column(Integer, nullable=True)


class WorkflowTemplate(Base, AutomationMixin):
    __tablename__ = "workflow_templates"
    __table_args__ = {"schema": "automation"}

    template_code = Column(String(80), unique=True, nullable=True, index=True)
    template_name = Column(String(255), nullable=False, index=True)
    department = Column(String(120), nullable=True, index=True)
    owner_department = Column(String(120), nullable=True)
    trigger_event = Column(String(180), nullable=True, index=True)
    related_sop_id = Column(UUID(as_uuid=True), ForeignKey("automation.sops.id"), nullable=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)


class WorkflowStage(Base, AutomationMixin):
    __tablename__ = "workflow_stages"
    __table_args__ = {"schema": "automation"}

    template_id = Column(UUID(as_uuid=True), ForeignKey("automation.workflow_templates.id"), nullable=False, index=True)
    stage_order = Column(Integer, default=1)
    stage_name = Column(String(255), nullable=False)
    approver_role = Column(String(180), nullable=True)
    sla_hours = Column(Integer, nullable=True)
    routing_rule = Column(JSON, nullable=True)


class WorkflowInstance(Base, AutomationMixin):
    __tablename__ = "workflow_instances"
    __table_args__ = {"schema": "automation"}

    instance_number = Column(String(80), unique=True, nullable=True, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("automation.workflow_templates.id"), nullable=True, index=True)
    workflow_name = Column(String(255), nullable=False, index=True)
    source_module = Column(String(120), nullable=True, index=True)
    source_entity_type = Column(String(120), nullable=True)
    source_entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    current_stage = Column(String(255), nullable=True)
    workflow_state = Column(String(80), default="Draft", index=True)
    owner = Column(String(255), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSON, nullable=True)


class WorkflowTask(Base, AutomationMixin):
    __tablename__ = "workflow_tasks"
    __table_args__ = {"schema": "automation"}

    workflow_instance_id = Column(UUID(as_uuid=True), ForeignKey("automation.workflow_instances.id"), nullable=False, index=True)
    task_name = Column(String(255), nullable=False, index=True)
    assigned_role = Column(String(180), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(80), default="medium", index=True)
    evidence_url = Column(String(500), nullable=True)


class ApprovalMatrix(Base, AutomationMixin):
    __tablename__ = "approval_matrix"
    __table_args__ = {"schema": "automation"}

    matrix_name = Column(String(255), nullable=False, index=True)
    process_name = Column(String(180), nullable=False, index=True)
    department = Column(String(120), nullable=True, index=True)
    approval_level = Column(Integer, default=1)
    approver_role = Column(String(180), nullable=False)
    amount_min = Column(Numeric(14, 2), nullable=True)
    amount_max = Column(Numeric(14, 2), nullable=True)
    risk_level = Column(String(80), nullable=True)
    dual_approval_required = Column(Boolean, default=False)
    escalation_role = Column(String(180), nullable=True)


class ApprovalRequest(Base, AutomationMixin):
    __tablename__ = "approval_requests"
    __table_args__ = {"schema": "automation"}

    request_number = Column(String(80), unique=True, nullable=True, index=True)
    workflow_instance_id = Column(UUID(as_uuid=True), ForeignKey("automation.workflow_instances.id"), nullable=True, index=True)
    matrix_id = Column(UUID(as_uuid=True), ForeignKey("automation.approval_matrix.id"), nullable=True)
    request_title = Column(String(255), nullable=False, index=True)
    module = Column(String(120), nullable=True, index=True)
    entity_type = Column(String(120), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    requested_by = Column(String(255), nullable=True)
    approver_role = Column(String(180), nullable=True)
    approver = Column(String(255), nullable=True)
    approval_status = Column(String(80), default="pending", index=True)
    amount = Column(Numeric(14, 2), nullable=True)
    risk_level = Column(String(80), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    comments = Column(Text, nullable=True)


class ApprovalAction(Base, AutomationMixin):
    __tablename__ = "approval_actions"
    __table_args__ = {"schema": "automation"}

    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("automation.approval_requests.id"), nullable=False, index=True)
    action = Column(String(80), nullable=False)
    actor = Column(String(255), nullable=True)
    comments = Column(Text, nullable=True)
    action_at = Column(DateTime(timezone=True), server_default=func.now())


class EnterpriseEvent(Base, AutomationMixin):
    __tablename__ = "enterprise_events"
    __table_args__ = {"schema": "automation"}

    event_key = Column(String(120), unique=True, nullable=True, index=True)
    event_type = Column(String(180), nullable=False, index=True)
    source_module = Column(String(120), nullable=False, index=True)
    target_module = Column(String(120), nullable=True, index=True)
    payload = Column(JSON, nullable=True)
    event_status = Column(String(80), default="pending", index=True)
    retry_count = Column(Integer, default=0)
    processed_by = Column(String(255), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)


class AuditLog(Base, AutomationMixin):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "automation"}

    user_email = Column(String(255), nullable=True, index=True)
    module = Column(String(120), nullable=False, index=True)
    action = Column(String(120), nullable=False, index=True)
    entity_type = Column(String(120), nullable=True, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String(100), nullable=True)
    device = Column(String(255), nullable=True)
    result = Column(String(80), default="success", index=True)
    failure_reason = Column(Text, nullable=True)


class SLAPolicy(Base, AutomationMixin):
    __tablename__ = "sla_policies"
    __table_args__ = {"schema": "automation"}

    policy_name = Column(String(255), nullable=False, index=True)
    process_name = Column(String(180), nullable=False, index=True)
    department = Column(String(120), nullable=True, index=True)
    priority = Column(String(80), default="medium", index=True)
    response_minutes = Column(Integer, default=240)
    resolution_minutes = Column(Integer, default=1440)
    warning_threshold_percent = Column(Integer, default=80)
    escalation_role = Column(String(180), nullable=True)


class SLAInstance(Base, AutomationMixin):
    __tablename__ = "sla_instances"
    __table_args__ = {"schema": "automation"}

    sla_policy_id = Column(UUID(as_uuid=True), ForeignKey("automation.sla_policies.id"), nullable=True, index=True)
    workflow_instance_id = Column(UUID(as_uuid=True), ForeignKey("automation.workflow_instances.id"), nullable=True, index=True)
    module = Column(String(120), nullable=True, index=True)
    entity_type = Column(String(120), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    response_due_at = Column(DateTime(timezone=True), nullable=True)
    resolution_due_at = Column(DateTime(timezone=True), nullable=True)
    breached_at = Column(DateTime(timezone=True), nullable=True)
    sla_status = Column(String(80), default="running", index=True)


class EscalationRule(Base, AutomationMixin):
    __tablename__ = "escalation_rules"
    __table_args__ = {"schema": "automation"}

    rule_name = Column(String(255), nullable=False, index=True)
    process_name = Column(String(180), nullable=True, index=True)
    department = Column(String(120), nullable=True)
    trigger_condition = Column(String(255), nullable=False)
    escalation_level = Column(Integer, default=1)
    escalate_to_role = Column(String(180), nullable=False)
    notify_channels = Column(JSON, nullable=True)


class UserAccessProfile(Base, AutomationMixin):
    __tablename__ = "user_access_profiles"
    __table_args__ = {"schema": "automation"}

    user_email = Column(String(255), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    department = Column(String(120), nullable=True, index=True)
    role_name = Column(String(180), nullable=True)
    access_level = Column(String(80), default="standard")
    privileged = Column(Boolean, default=False)
    provisioning_status = Column(String(80), default="pending", index=True)
    deactivation_status = Column(String(80), default="not_started")
    last_review_date = Column(Date, nullable=True)


class AccessReview(Base, AutomationMixin):
    __tablename__ = "access_reviews"
    __table_args__ = {"schema": "automation"}

    review_name = Column(String(255), nullable=False, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    reviewer = Column(String(255), nullable=True)
    review_period = Column(String(80), nullable=True)
    review_status = Column(String(80), default="pending", index=True)
    findings = Column(Text, nullable=True)
    remediation_due_date = Column(Date, nullable=True)


class ComplianceControl(Base, AutomationMixin):
    __tablename__ = "compliance_controls"
    __table_args__ = {"schema": "automation"}

    control_code = Column(String(80), unique=True, nullable=True, index=True)
    control_name = Column(String(255), nullable=False, index=True)
    control_domain = Column(String(120), nullable=False, index=True)
    owner_department = Column(String(120), nullable=True)
    control_status = Column(String(80), default="active", index=True)
    testing_frequency = Column(String(80), nullable=True)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    evidence_required = Column(Boolean, default=True)
    description = Column(Text, nullable=True)


class RiskRegister(Base, AutomationMixin):
    __tablename__ = "risk_register"
    __table_args__ = {"schema": "automation"}

    risk_code = Column(String(80), unique=True, nullable=True, index=True)
    risk_title = Column(String(255), nullable=False, index=True)
    department = Column(String(120), nullable=True, index=True)
    risk_category = Column(String(120), nullable=True)
    likelihood = Column(String(80), default="medium")
    impact = Column(String(80), default="medium")
    risk_score = Column(Integer, default=5, index=True)
    owner = Column(String(255), nullable=True)
    mitigation_plan = Column(Text, nullable=True)
    residual_risk = Column(String(80), nullable=True)


class KPI(Base, AutomationMixin):
    __tablename__ = "kpis"
    __table_args__ = {"schema": "automation"}

    kpi_code = Column(String(80), unique=True, nullable=True, index=True)
    kpi_name = Column(String(255), nullable=False, index=True)
    department = Column(String(120), nullable=True, index=True)
    owner = Column(String(255), nullable=True)
    target_value = Column(Numeric(14, 2), default=0)
    unit = Column(String(80), nullable=True)
    frequency = Column(String(80), default="monthly")
    linked_module = Column(String(120), nullable=True)
    approval_required_for_override = Column(Boolean, default=True)


class KPIResult(Base, AutomationMixin):
    __tablename__ = "kpi_results"
    __table_args__ = {"schema": "automation"}

    kpi_id = Column(UUID(as_uuid=True), ForeignKey("automation.kpis.id"), nullable=False, index=True)
    period_label = Column(String(80), nullable=False, index=True)
    actual_value = Column(Numeric(14, 2), default=0)
    target_value = Column(Numeric(14, 2), default=0)
    achievement_percent = Column(Numeric(8, 2), default=0)
    approval_status = Column(String(80), default="pending", index=True)
    override_reason = Column(Text, nullable=True)


class CorrectiveAction(Base, AutomationMixin):
    __tablename__ = "corrective_actions"
    __table_args__ = {"schema": "automation"}

    action_title = Column(String(255), nullable=False, index=True)
    source_type = Column(String(120), nullable=True, index=True)
    source_id = Column(UUID(as_uuid=True), nullable=True)
    department = Column(String(120), nullable=True, index=True)
    owner = Column(String(255), nullable=True)
    priority = Column(String(80), default="medium", index=True)
    due_date = Column(Date, nullable=True, index=True)
    completion_date = Column(Date, nullable=True)
    action_status = Column(String(80), default="open", index=True)
    description = Column(Text, nullable=True)
