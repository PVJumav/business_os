from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.projects import Project, ProjectTeamMember
from backend.policies.iam import is_admin, require_permission, user_role_codes
from backend.schemas.auth import UserResponse


def can_view_project(db: Session, user: UserResponse, project: Project) -> bool:
    if is_admin(user):
        return True
    if str(user.role).lower() in {"manager", "project_manager", "pmo", "cto"}:
        return True
    if project.owner_user_id and project.owner_user_id == user.id:
        return True
    return (
        db.query(ProjectTeamMember)
        .filter(ProjectTeamMember.project_id == project.id, ProjectTeamMember.status == "active")
        .first()
        is not None
    )


def require_project_access(db: Session, user: UserResponse, action: str, resource: str, project: Project | None = None) -> None:
    if is_admin(user):
        return
    roles = user_role_codes(db, user)
    if roles & {"project_manager", "pmo", "cto", "operations", "manager"}:
        return
    if action == "read" and project and can_view_project(db, user, project):
        return
    require_permission(db, user, "projects", resource, action)


def deny_locked_project(project: Project) -> None:
    if project.locked or project.lifecycle_status in {"completed", "signed_off", "closed"}:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="This project is locked and requires a change request")
