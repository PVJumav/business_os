from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.crm import CRMRecordShare
from backend.schemas.auth import UserResponse


ADMIN_ROLES = {"admin", "system_admin"}
MANAGER_ROLES = {"admin", "manager", "sales_manager", "sales_lead", "country_manager", "cfo", "cto"}
CRM_ROLES = MANAGER_ROLES | {"sales", "account_manager", "am", "user"}


def role(user: UserResponse | None) -> str:
    return (getattr(user, "role", "") or "").strip().lower()


def is_admin(user: UserResponse | None) -> bool:
    return role(user) in ADMIN_ROLES


def is_manager(user: UserResponse | None) -> bool:
    return role(user) in MANAGER_ROLES


def owner_matches(user: UserResponse, owner: str | None) -> bool:
    if not owner:
        return False
    identity = {user.email.lower(), user.full_name.lower()}
    return owner.lower() in identity


def is_shared(db: Session, user: UserResponse, entity_type: str, entity_id) -> bool:
    return (
        db.query(CRMRecordShare)
        .filter(
            CRMRecordShare.entity_type == entity_type,
            CRMRecordShare.entity_id == entity_id,
            CRMRecordShare.shared_with.in_([user.email, user.full_name]),
            CRMRecordShare.status == "active",
        )
        .first()
        is not None
    )


def require_crm_access(db: Session, user: UserResponse, action: str, entity_type: str, record=None) -> None:
    if is_admin(user) or is_manager(user):
        return
    if role(user) not in CRM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CRM access denied")
    if action == "create" or record is None:
        return
    owner = (
        getattr(record, "owner", None)
        or getattr(record, "assigned_to", None)
        or getattr(record, "account_manager", None)
        or getattr(record, "created_by", None)
    )
    if owner_matches(user, owner) or is_shared(db, user, entity_type, record.id):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only access CRM records you own, records shared with you, or records visible through your role",
    )
