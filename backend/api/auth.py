import base64
import hashlib
import hmac
import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.auth import AuthUser
from backend.models.iam import IAMRole, IAMUserRole
from backend.policies.iam import effective_permissions, user_role_codes
from backend.schemas.auth import AuthTokens, GoogleLoginPayload, LoginCredentials, RegisterUser, UserResponse


router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "business-os-dev-secret")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
ALLOW_PUBLIC_ROLE_REGISTRATION = os.getenv("ALLOW_PUBLIC_ROLE_REGISTRATION", "false").lower() == "true"


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(digest).decode()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    try:
        salt_raw, digest_raw = stored_hash.split(":", 1)
        salt = base64.b64decode(salt_raw.encode())
        expected = base64.b64decode(digest_raw.encode())
    except ValueError:
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return hmac.compare_digest(actual, expected)


def _encode_token(user: UserResponse) -> str:
    payload = {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "auth_provider": user.auth_provider,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
    }
    payload["signature"] = hmac.new(
        SECRET_KEY.encode(),
        json.dumps(payload, sort_keys=True).encode(),
        hashlib.sha256,
    ).hexdigest()
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_token(token: str) -> UserResponse:
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        signature = payload.pop("signature")
        expected = hmac.new(
            SECRET_KEY.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid signature")
        return UserResponse(**payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc


def _assign_iam_role(db: Session, user: AuthUser) -> None:
    role = db.query(IAMRole).filter(
        IAMRole.role_code == str(user.role).lower(),
        IAMRole.status == "active",
    ).first()
    if not role:
        return
    exists = db.query(IAMUserRole).filter(
        IAMUserRole.user_id == user.id,
        IAMUserRole.role_id == role.id,
        IAMUserRole.status == "active",
    ).first()
    if not exists:
        db.add(IAMUserRole(user_id=user.id, role_id=role.id, status="active"))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterUser, db: Session = Depends(get_db)):
    email = payload.email.lower()
    username = payload.username.strip().lower() if payload.username else email.split("@", 1)[0].lower()
    existing = db.query(AuthUser).filter(or_(AuthUser.email == email, AuthUser.username == username)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists",
        )

    role = payload.role if ALLOW_PUBLIC_ROLE_REGISTRATION else "user"
    if not db.query(AuthUser).first():
        role = "admin"

    user = AuthUser(
        email=email,
        username=username,
        full_name=payload.full_name,
        role=role,
        hashed_password=_hash_password(payload.password),
        auth_provider="password",
    )
    db.add(user)
    db.flush()
    _assign_iam_role(db, user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=AuthTokens)
def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    identifier = credentials.email.strip().lower()
    user_record = db.query(AuthUser).filter(
        or_(AuthUser.email == identifier, AuthUser.username == identifier)
    ).first()
    if not user_record or not _verify_password(credentials.password, user_record.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive",
        )

    user = UserResponse.model_validate(user_record)
    return AuthTokens(access_token=_encode_token(user))


@router.post("/google", response_model=AuthTokens)
def google_login(payload: GoogleLoginPayload, db: Session = Depends(get_db)):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        google_user = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google sign-in token",
        ) from exc

    email = str(google_user.get("email", "")).lower()
    google_subject = str(google_user.get("sub", ""))
    if not email or not google_subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google sign-in did not return a usable account",
        )

    user_record = db.query(AuthUser).filter(
        or_(AuthUser.google_subject == google_subject, AuthUser.email == email)
    ).first()
    if not user_record:
        role = payload.role if ALLOW_PUBLIC_ROLE_REGISTRATION else "user"
        if not db.query(AuthUser).first():
            role = "admin"
        base_username = email.split("@", 1)[0].lower()
        username = base_username
        suffix = 1
        while db.query(AuthUser).filter(AuthUser.username == username).first():
            suffix += 1
            username = f"{base_username}{suffix}"
        user_record = AuthUser(
            email=email,
            username=username,
            full_name=str(google_user.get("name") or email),
            role=role,
            hashed_password=None,
            auth_provider="google",
            google_subject=google_subject,
            avatar_url=google_user.get("picture"),
            is_active=True,
        )
        db.add(user_record)
        db.flush()
        _assign_iam_role(db, user_record)
    else:
        user_record.auth_provider = user_record.auth_provider or "google"
        user_record.google_subject = user_record.google_subject or google_subject
        user_record.avatar_url = google_user.get("picture") or user_record.avatar_url
        _assign_iam_role(db, user_record)

    db.commit()
    db.refresh(user_record)
    if not user_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive",
        )
    user = UserResponse.model_validate(user_record)
    return AuthTokens(access_token=_encode_token(user))


@router.get("/me", response_model=UserResponse)
def get_current_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    user = _decode_token(token)
    user.roles = sorted(user_role_codes(db, user))
    user.permissions = effective_permissions(db, user)
    return user
