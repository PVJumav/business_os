from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.crud import create_record, delete_record, get_or_404, update_record
from backend.core.database import get_db
from backend.models.crm import CRMActivity
from backend.schemas.crm.activities import ActivityCreate, ActivityResponse, ActivityUpdate


router = APIRouter(prefix="/crm/activities", tags=["CRM Activities"])


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    return create_record(db, CRMActivity, activity)


@router.get("", response_model=List[ActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    return db.query(CRMActivity).order_by(CRMActivity.created_at.desc()).all()


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(activity_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, CRMActivity, activity_id, "Activity")


@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: UUID,
    activity_update: ActivityUpdate,
    db: Session = Depends(get_db),
):
    activity = get_or_404(db, CRMActivity, activity_id, "Activity")
    return update_record(db, activity, activity_update)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: UUID, db: Session = Depends(get_db)):
    activity = get_or_404(db, CRMActivity, activity_id, "Activity")
    return delete_record(db, activity)
