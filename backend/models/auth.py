import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from backend.core.database import Base


class AuthUser(Base):
    __tablename__ = "auth_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(100), default="user", nullable=False)
    hashed_password = Column(String(255), nullable=True)
    auth_provider = Column(String(50), default="password", nullable=False)
    google_subject = Column(String(255), unique=True, nullable=True, index=True)
    github_subject = Column(String(255), unique=True, nullable=True, index=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
