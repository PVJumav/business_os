import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from backend.core.database import Base


class OrganizationPolicy(Base):
    __tablename__ = "organization_policies"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_name = Column(String(255), nullable=True)
    module = Column(String(100), nullable=False)
    policy_area = Column(String(150), nullable=False)
    policy_name = Column(String(255), nullable=False)
    policy_value = Column(Text, nullable=False)
    applies_to_roles = Column(Text, nullable=True)
    effective_date = Column(String(50), nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AccessRight(Base):
    __tablename__ = "access_rights"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(100), nullable=False)
    module = Column(String(100), nullable=False)
    resource_path = Column(String(255), nullable=False)
    can_view = Column(Boolean, default=True)
    can_create = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_approve = Column(Boolean, default=False)
    can_export = Column(Boolean, default=False)
    data_scope = Column(String(100), default="assigned")
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
