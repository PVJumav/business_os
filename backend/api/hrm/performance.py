from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.models.hrm import HRMPerformance
from backend.schemas.hrm.performance import PerformanceCreate, PerformanceUpdate, PerformanceResponse


router = APIRouter(prefix="/hrm/performance", tags=["HRM Performance"])


@router.post("", response_model=PerformanceResponse, status_code=status.HTTP_201_CREATED)
def create_performance(performance: PerformanceCreate, db: Session = Depends(get_db)):
    new_performance = HRMPerformance(**performance.model_dump())
    db.add(new_performance)
    db.commit()
    db.refresh(new_performance)
    return new_performance


@router.get("", response_model=List[PerformanceResponse])
def get_performance_records(db: Session = Depends(get_db)):
    return db.query(HRMPerformance).order_by(HRMPerformance.created_at.desc()).all()


@router.get("/{performance_id}", response_model=PerformanceResponse)
def get_performance(performance_id: UUID, db: Session = Depends(get_db)):
    performance = db.query(HRMPerformance).filter(HRMPerformance.id == performance_id).first()

    if not performance:
        raise HTTPException(status_code=404, detail="Performance record not found")

    return performance


@router.put("/{performance_id}", response_model=PerformanceResponse)
def update_performance(performance_id: UUID, performance_update: PerformanceUpdate, db: Session = Depends(get_db)):
    performance = db.query(HRMPerformance).filter(HRMPerformance.id == performance_id).first()

    if not performance:
        raise HTTPException(status_code=404, detail="Performance record not found")

    for field, value in performance_update.model_dump(exclude_unset=True).items():
        setattr(performance, field, value)

    db.commit()
    db.refresh(performance)
    return performance


@router.delete("/{performance_id}")
def delete_performance(performance_id: UUID, db: Session = Depends(get_db)):
    performance = db.query(HRMPerformance).filter(HRMPerformance.id == performance_id).first()

    if not performance:
        raise HTTPException(status_code=404, detail="Performance record not found")

    db.delete(performance)
    db.commit()

    return {"status": "success", "message": "Performance record deleted successfully"}