from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.models.hrm import HRMBenefit
from backend.schemas.hrm.benefits import BenefitCreate, BenefitUpdate, BenefitResponse


router = APIRouter(prefix="/hrm/benefits", tags=["HRM Benefits"])


@router.post("", response_model=BenefitResponse, status_code=status.HTTP_201_CREATED)
def create_benefit(benefit: BenefitCreate, db: Session = Depends(get_db)):
    new_benefit = HRMBenefit(**benefit.model_dump())
    db.add(new_benefit)
    db.commit()
    db.refresh(new_benefit)
    return new_benefit


@router.get("", response_model=List[BenefitResponse])
def get_benefits(db: Session = Depends(get_db)):
    return db.query(HRMBenefit).order_by(HRMBenefit.created_at.desc()).all()


@router.get("/{benefit_id}", response_model=BenefitResponse)
def get_benefit(benefit_id: UUID, db: Session = Depends(get_db)):
    benefit = db.query(HRMBenefit).filter(HRMBenefit.id == benefit_id).first()

    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit record not found")

    return benefit


@router.put("/{benefit_id}", response_model=BenefitResponse)
def update_benefit(benefit_id: UUID, benefit_update: BenefitUpdate, db: Session = Depends(get_db)):
    benefit = db.query(HRMBenefit).filter(HRMBenefit.id == benefit_id).first()

    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit record not found")

    for field, value in benefit_update.model_dump(exclude_unset=True).items():
        setattr(benefit, field, value)

    db.commit()
    db.refresh(benefit)
    return benefit


@router.delete("/{benefit_id}")
def delete_benefit(benefit_id: UUID, db: Session = Depends(get_db)):
    benefit = db.query(HRMBenefit).filter(HRMBenefit.id == benefit_id).first()

    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit record not found")

    db.delete(benefit)
    db.commit()

    return {"status": "success", "message": "Benefit record deleted successfully"}