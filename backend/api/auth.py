import base64
import hashlib
import hmac
import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.auth import AuthUser
from backend.policies.iam import effective_permissions, user_role_codes
from backend.schemas.auth import AuthTokens, LoginCredentials, RegisterUser, UserResponse


router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "business-os-dev-secret")


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(digest).decode()}"


def _verify_password(password: str, stored_hash: str) -> bool:
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
        "full_name": user.full_name,
        "role": user.role,
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterUser, db: Session = Depends(get_db)):
    existing = db.query(AuthUser).filter(AuthUser.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = AuthUser(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=_hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=AuthTokens)
def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    user_record = db.query(AuthUser).filter(AuthUser.email == credentials.email).first()
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
