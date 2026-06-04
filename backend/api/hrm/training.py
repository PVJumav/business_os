from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.models.hrm import HRMTraining
from backend.schemas.hrm.training import TrainingCreate, TrainingUpdate, TrainingResponse


router = APIRouter(prefix="/hrm/training", tags=["HRM Training"])


@router.post("", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def create_training(training: TrainingCreate, db: Session = Depends(get_db)):
    new_training = HRMTraining(**training.model_dump())
    db.add(new_training)
    db.commit()
    db.refresh(new_training)
    return new_training


@router.get("", response_model=List[TrainingResponse])
def get_training_records(db: Session = Depends(get_db)):
    return db.query(HRMTraining).order_by(HRMTraining.created_at.desc()).all()


@router.get("/{training_id}", response_model=TrainingResponse)
def get_training(training_id: UUID, db: Session = Depends(get_db)):
    training = db.query(HRMTraining).filter(HRMTraining.id == training_id).first()

    if not training:
        raise HTTPException(status_code=404, detail="Training record not found")

    return training


@router.put("/{training_id}", response_model=TrainingResponse)
def update_training(training_id: UUID, training_update: TrainingUpdate, db: Session = Depends(get_db)):
    training = db.query(HRMTraining).filter(HRMTraining.id == training_id).first()

    if not training:
        raise HTTPException(status_code=404, detail="Training record not found")

    for field, value in training_update.model_dump(exclude_unset=True).items():
        setattr(training, field, value)

    db.commit()
    db.refresh(training)
    return training


@router.delete("/{training_id}")
def delete_training(training_id: UUID, db: Session = Depends(get_db)):
    training = db.query(HRMTraining).filter(HRMTraining.id == training_id).first()

    if not training:
        raise HTTPException(status_code=404, detail="Training record not found")

    db.delete(training)
    db.commit()

    return {"status": "success", "message": "Training record deleted successfully"}