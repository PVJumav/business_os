import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.core.database import Base


class CRMLicence(Base):
    __tablename__ = "licences"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    deal_id = Column(UUID(as_uuid=True), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    licence_name = Column(String(255), nullable=False)
    product_name = Column(String(255), nullable=True)
    distributor = Column(String(255), nullable=True)
    oem_name = Column(String(255), nullable=True)
    oem_contact_name = Column(String(255), nullable=True)
    oem_contact_email = Column(String(255), nullable=True)
    customer_contact_name = Column(String(255), nullable=True)
    customer_contact_email = Column(String(255), nullable=True)
    account_manager = Column(String(255), nullable=True)
    activation_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    renewal_date = Column(Date, nullable=True)
    renewal_notice_days = Column(Integer, default=60)
    purchase_status = Column(String(50), default="pending")
    delivery_status = Column(String(50), default="pending")
    invoice_status = Column(String(50), default="not_ready")
    notification_status = Column(String(50), default="pending")
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class IntegrationConnector(Base):
    __tablename__ = "integration_connectors"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    connector_name = Column(String(255), nullable=False)
    connector_type = Column(String(100), nullable=False)
    environment = Column(String(100), default="production")
    system_owner = Column(String(255), nullable=True)
    endpoint_url = Column(String(500), nullable=True)
    auth_method = Column(String(100), nullable=True)
    data_direction = Column(String(50), default="ingest")
    sync_frequency = Column(String(100), nullable=True)
    configuration = Column(JSONB, nullable=True)
    status = Column(String(50), default="draft")
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DataImportBatch(Base):
    __tablename__ = "data_import_batches"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    source_name = Column(String(255), nullable=True)
    source_format = Column(String(50), nullable=False)
    target_resource = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=True)
    parsed_rows = Column(Integer, default=0)
    imported_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    status = Column(String(50), default="uploaded")
    uploaded_by = Column(String(255), nullable=True)
    parse_summary = Column(Text, nullable=True)
    sample_payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EntitySequence(Base):
    __tablename__ = "entity_sequences"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_code = Column(String(20), default="IS")
    entity_key = Column(String(100), nullable=False, unique=True)
    prefix = Column(String(30), nullable=False)
    next_number = Column(Integer, default=1)
    padding = Column(Integer, default=5)
    active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StaffRoleAssignment(Base):
    __tablename__ = "staff_role_assignments"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=True)
    staff_name = Column(String(255), nullable=False)
    role_name = Column(String(150), nullable=False)
    department = Column(String(150), nullable=True)
    role_scope = Column(String(150), nullable=True)
    target_gp = Column(Numeric(14, 2), default=0)
    line_manager = Column(String(255), nullable=True)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkflowRule(Base):
    __tablename__ = "workflow_rules"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    rule_name = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)
    trigger_entity = Column(String(120), nullable=False)
    trigger_event = Column(String(80), nullable=False)
    condition_json = Column(JSONB, nullable=True)
    action_type = Column(String(100), nullable=False)
    action_payload = Column(JSONB, nullable=True)
    owner_role = Column(String(120), nullable=True)
    priority = Column(Integer, default=3)
    status = Column(String(50), default="active")
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkflowRunLog(Base):
    __tablename__ = "workflow_run_logs"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), nullable=True)
    entity_type = Column(String(120), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    event_name = Column(String(100), nullable=False)
    outcome = Column(String(50), default="success")
    message = Column(Text, nullable=True)
    context = Column(JSONB, nullable=True)
    run_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    module = Column(String(100), nullable=False)
    related_entity = Column(String(120), nullable=True)
    related_id = Column(UUID(as_uuid=True), nullable=True)
    channel = Column(String(50), default="email")
    recipient_name = Column(String(255), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="queued")
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    contact_id = Column(UUID(as_uuid=True), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    sla_id = Column(UUID(as_uuid=True), nullable=True)
    ticket_number = Column(String(80), nullable=True)
    subject = Column(String(255), nullable=False)
    channel = Column(String(80), default="email")
    category = Column(String(120), nullable=True)
    priority = Column(String(50), default="medium")
    assigned_team = Column(String(120), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    sla_policy = Column(String(150), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    resolution_summary = Column(Text, nullable=True)
    csat_score = Column(Numeric(5, 2), nullable=True)
    status = Column(String(50), default="open")
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KnowledgeBaseArticle(Base):
    __tablename__ = "knowledge_base_articles"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)
    article_type = Column(String(100), default="procedure")
    audience = Column(String(100), default="internal")
    body = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    owner = Column(String(255), nullable=True)
    status = Column(String(50), default="draft")
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProjectTask(Base):
    __tablename__ = "project_tasks"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    parent_task_id = Column(UUID(as_uuid=True), nullable=True)
    task_name = Column(String(255), nullable=False)
    workstream = Column(String(150), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    dependency_ids = Column(JSONB, nullable=True)
    estimated_hours = Column(Numeric(10, 2), default=0)
    actual_hours = Column(Numeric(10, 2), default=0)
    cost_estimate = Column(Numeric(14, 2), default=0)
    percent_complete = Column(Numeric(5, 2), default=0)
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="not_started")
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    milestone_name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=True)
    planned_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    billing_amount = Column(Numeric(14, 2), default=0)
    billing_status = Column(String(50), default="not_billed")
    status = Column(String(50), default="planned")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProjectRisk(Base):
    __tablename__ = "project_risks"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    risk_title = Column(String(255), nullable=False)
    risk_type = Column(String(100), nullable=True)
    probability = Column(String(50), default="medium")
    impact = Column(String(50), default="medium")
    mitigation_plan = Column(Text, nullable=True)
    owner = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ERPInventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    item_name = Column(String(255), nullable=False)
    item_type = Column(String(100), default="stock")
    sku = Column(String(120), nullable=True)
    category = Column(String(150), nullable=True)
    vendor_name = Column(String(255), nullable=True)
    unit_cost = Column(Numeric(14, 2), default=0)
    quantity_on_hand = Column(Numeric(14, 2), default=0)
    reorder_level = Column(Numeric(14, 2), default=0)
    warehouse_location = Column(String(255), nullable=True)
    custodian = Column(String(255), nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OrganizationGoal(Base):
    __tablename__ = "organization_goals"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    goal_name = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)
    department = Column(String(150), nullable=True)
    owner = Column(String(255), nullable=True)
    period_type = Column(String(50), default="annual")
    target_value = Column(Numeric(14, 2), default=0)
    actual_value = Column(Numeric(14, 2), default=0)
    metric = Column(String(120), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TerritoryRule(Base):
    __tablename__ = "territory_rules"
    __table_args__ = {"schema": "crm"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    territory_name = Column(String(255), nullable=False)
    country = Column(String(150), nullable=True)
    region = Column(String(150), nullable=True)
    vertical = Column(String(150), nullable=True)
    account_manager = Column(String(255), nullable=True)
    country_manager = Column(String(255), nullable=True)
    rule_priority = Column(Integer, default=1)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PortalRequest(Base):
    __tablename__ = "portal_requests"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    requester_name = Column(String(255), nullable=False)
    requester_type = Column(String(80), default="employee")
    requester_email = Column(String(255), nullable=True)
    module = Column(String(100), nullable=False)
    request_type = Column(String(120), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(String(255), nullable=True)
    priority = Column(String(50), default="medium")
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default="submitted")
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    module = Column(String(100), nullable=False)
    related_entity = Column(String(120), nullable=True)
    related_id = Column(UUID(as_uuid=True), nullable=True)
    channel = Column(String(80), nullable=False)
    direction = Column(String(50), default="outbound")
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    owner = Column(String(255), nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="logged")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    event_name = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)
    event_type = Column(String(100), default="meeting")
    related_entity = Column(String(120), nullable=True)
    related_id = Column(UUID(as_uuid=True), nullable=True)
    owner = Column(String(255), nullable=True)
    attendees = Column(JSONB, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    recurrence_rule = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), default="scheduled")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    resource_name = Column(String(255), nullable=False)
    resource_type = Column(String(100), default="staff")
    module = Column(String(100), nullable=False)
    allocation_target = Column(String(255), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    role_on_work = Column(String(150), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    capacity_percent = Column(Numeric(5, 2), default=100)
    planned_hours = Column(Numeric(10, 2), default=0)
    actual_hours = Column(Numeric(10, 2), default=0)
    cost_rate = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="planned")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FeatureCapability(Base):
    __tablename__ = "feature_capabilities"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(150), nullable=False)
    capability = Column(String(255), nullable=False)
    source_platforms = Column(String(500), nullable=True)
    module = Column(String(100), nullable=False)
    mechanism = Column(String(255), nullable=False)
    implementation_status = Column(String(50), default="implemented")
    route_path = Column(String(255), nullable=True)
    api_endpoint = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
