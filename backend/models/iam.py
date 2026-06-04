import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID

from backend.core.database import Base


class IAMRole(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_code = Column(String(120), unique=True, nullable=False, index=True)
    role_name = Column(String(255), nullable=False)
    module_scope = Column(String(100), default="enterprise", nullable=False)
    description = Column(Text, nullable=True)
    requires_mfa = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="active", nullable=False, index=True)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class IAMPermission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("permission_code", name="uq_iam_permission_code"),
        {"schema": "auth"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permission_code = Column(String(160), nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    resource = Column(String(120), nullable=False, index=True)
    action = Column(String(80), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMRolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_iam_role_permission"),
        {"schema": "auth"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("auth.roles.id"), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("auth.permissions.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMUserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_iam_user_role"),
        {"schema": "auth"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("auth.roles.id"), nullable=False, index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMTeam(Base):
    __tablename__ = "teams"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_name = Column(String(255), nullable=False, index=True)
    module_scope = Column(String(100), default="enterprise", nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    soft_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMTeamMembership(Base):
    __tablename__ = "team_memberships"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_iam_team_member"),
        {"schema": "auth"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("auth.teams.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    membership_role = Column(String(100), default="member", nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMDepartmentAccess(Base):
    __tablename__ = "department_access"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    department = Column(String(150), nullable=False, index=True)
    access_level = Column(String(80), default="read", nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMBranchAccess(Base):
    __tablename__ = "branch_access"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    branch = Column(String(150), nullable=False, index=True)
    access_level = Column(String(80), default="read", nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMSession(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    session_token_hash = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMLoginHistory(Base):
    __tablename__ = "login_history"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    outcome = Column(String(80), nullable=False, index=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMMFASetting(Base):
    __tablename__ = "mfa_settings"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), unique=True, nullable=False, index=True)
    method = Column(String(80), default="totp", nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    enforced_by_role = Column(Boolean, default=False, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class IAMPasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMAPIKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True, index=True)
    service_account_id = Column(UUID(as_uuid=True), ForeignKey("auth.service_accounts.id"), nullable=True, index=True)
    scopes = Column(JSON, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMServiceAccount(Base):
    __tablename__ = "service_accounts"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name = Column(String(255), nullable=False, unique=True, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True)
    allowed_scopes = Column(JSON, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMAuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    module = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(140), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMAccessPolicy(Base):
    __tablename__ = "access_policies"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_name = Column(String(255), nullable=False, unique=True, index=True)
    module = Column(String(100), nullable=False, index=True)
    resource = Column(String(120), nullable=True)
    rules = Column(JSON, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class IAMApprovalDelegation(Base):
    __tablename__ = "approval_delegations"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delegator_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    delegate_user_id = Column(UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IAMDataAccessRule(Base):
    __tablename__ = "data_access_rules"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    principal_type = Column(String(50), nullable=False)
    principal_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    resource = Column(String(120), nullable=False, index=True)
    visibility_rule = Column(String(120), nullable=False)
    rule_payload = Column(JSON, nullable=True)
    priority = Column(Integer, default=100, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
