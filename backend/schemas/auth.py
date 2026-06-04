from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginCredentials(BaseModel):
    email: str
    password: str


class RegisterUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=100)
    role: str = Field(default="user", max_length=100)


class GoogleLoginPayload(BaseModel):
    credential: str = Field(..., min_length=20)
    role: str = Field(default="user", max_length=100)


class AuthTokens(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID | int
    email: EmailStr
    username: Optional[str] = None
    full_name: str
    role: str
    auth_provider: str = "password"
    avatar_url: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
